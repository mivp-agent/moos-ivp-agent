# General
import os
import time
from queue import Queue
from threading import Thread, Lock

# For core
from mivp_agent.const import KEY_ID
from mivp_agent.messages import MissionMessage, INSTR_SEND_STATE, INSTR_RESET_FAILURE, INSTR_RESET_SUCCESS
from mivp_agent.bridge import ModelBridgeServer

# For logging
from mivp_agent.util.file_system import safe_clean
from mivp_agent.proto.proto_logger import ProtoLogger
from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto import translate


LAST_LOG_DIR = '.last_manager_log'

class MissionManager:
    '''
    This is the primary method for interfacing with moos-ivp-agent's BHV_Agent

    Examples:
      It is recommended to use MissionManager with the python context manager

      ```
      from mivp_agent.manager import MissionManager

      with MissionManager() as mgr:
        mgr.wait_for(['felix', 'evan'])
        ...
      ```
    '''

    def __init__(self, logging=True, immediate_transition=True):
        '''
        The initializer for MissionManager

        Args:
            logging (bool): Enables logging of transition data

            immediate_transition (bool): Will set msg.is_transition by default to be `True` and assume that all next states are transitions. (Helpful when discretizing space rather than time)
        '''
        self._msg_queue = Queue()

        self._vnames = []
        self._vname_lock = Lock()
        self._vehicle_count = 0
        self._episode_manager_states = {}
        self._ems_lock = Lock()
        self._episode_manager_nums = {}
        self._emn_lock = Lock()

        # Dict to hold queues of vnames to reset
        self._vresets = Queue()

        self._thread = None
        self._stop_signal = False

        self._logging = logging
        self._imm_transition = immediate_transition
        if self._logging:
            print(os.getcwd())
            self._log_path = os.path.join(os.path.abspath(os.getcwd()), LAST_LOG_DIR)

            if not os.path.isdir(self._log_path):
                assert not os.path.isfile(self._log_path), f"There is a file in the expected log path '{self._log_path}' please remove or disable logging"

                os.makedirs(self._log_path)

            # Clean latests_dir
            assert safe_clean(self._log_path, patterns=["*.gz"]), f"Unable to clean log path '{self._log_path}' of files with given patterns. This directory may be corrupted. Clean manually or disable logging."

            # Create data structs needed to log data from each vehicle
            self._logs = {}
            self._last_state = {}
            self._last_act = {}

    def __enter__(self):
        self.start()
        return self

    def start(self):
        '''
        It is **not recommended** to use this method directly. Instead, consider using this class with the python context manager. This method starts a thread to read from the `ModelBridgeServer`.

        Returns:
          bool: False if thread has already been started, True otherwise
        '''
        if self._thread is not None:
            return False

        self._thread = Thread(target=self._server_thread, daemon=True)
        self._thread.start()

        return True

    def _server_thread(self):
        live_msg_list = []
        address_map = {}
        with ModelBridgeServer() as server:
            while not self._stop_signal:
                # Accept new clients
                addr = server.accept()
                if addr is not None:
                    print(f'Got new connection: {addr}')
                    server.send_instr(addr, INSTR_SEND_STATE)

                # Listen for messages from vehicles
                for addr in server._clients:
                    msg = server.listen(addr)

                    if msg is not None:
                        with self._vname_lock:
                            if msg[KEY_ID] not in self._vnames:
                                print(f'Got new vehicle: {msg[KEY_ID]}')
                                vname = msg[KEY_ID]
                                address_map[vname] = addr
                                self._vnames.append(vname)
                                self._vehicle_count += 1
                        assert address_map[vname] == addr, "Vehicle changed vname. This violates routing / logging assumptions made by MissionManager"

                        m = MissionMessage(
                          addr,
                          msg,
                          is_transition=self._imm_transition
                        )

                        with self._ems_lock:
                            self._episode_manager_states[m.vname] = m.episode_state
                        with self._emn_lock:
                            if m.episode_report is None:
                                self._episode_manager_nums[m.vname] = None
                            else:
                                self._episode_manager_nums[m.vname] = m.episode_report['NUM']

                        live_msg_list.append(m)
                        self._msg_queue.put(m)

                # Send responses to vehicle message if there are any
                for i, m in enumerate(live_msg_list):
                    with m._rsp_lock:
                        if m._response is None:
                            continue

                        # If we got there is response send and remove from list
                        live_msg_list.remove(m)
                        server.send_instr(m._addr, m._response)

                        # Do logging
                        self._do_logging(m)

                # Handle reseting of vehicles
                while not self._vresets.empty():
                    vname, success = self._vresets.get()

                    if vname not in address_map:
                        raise RuntimeError(
                            f'Received reset for unknown vehicle: {vname}')

                    instr = INSTR_RESET_FAILURE
                    if success:
                        instr = INSTR_RESET_SUCCESS

                    server.send_instr(address_map[vname], instr)

    # This message should only be called on msgs which have actions
    def _do_logging(self, msg):
        if not self._logging:
            return
        
        # Check if this is a new vehicle
        if msg.vname not in self._logs:
            path = os.path.join(self._log_path, msg.vname)
            self._logs[msg.vname] = ProtoLogger(path, Transition, mode='w')

        if msg.is_transition:
            # Write a transition if this is not the first state ever
            if msg.vname in self._last_state:
                t = Transition()
                t.s1.CopyFrom(translate.state_from_dict(self._last_state[msg.vname]))
                t.a.CopyFrom(translate.action_from_dict(self._last_act[msg.vname]))
                t.s2.CopyFrom(translate.state_from_dict(msg.state))

                self._logs[msg.vname].write(t)

            # Update the storage for next transition
            self._last_state[msg.vname] = msg.state
            self._last_act[msg.vname] = msg._response

    def are_present(self, vnames):
        '''
        Used to see if a specified list of vehicles has connected to the `MissionManager` instance yet.

        See also: [`wait_for()`][mivp_agent.manager.MissionManager.wait_for]

        Args:
          vnames (iterable): A list / tuple of `str` values to look for
        '''
        for vname in vnames:
            with self._vname_lock:
                if vname not in self._vnames:
                    return False
        return True

    def wait_for(self, vnames, sleep=0.1):
        '''
        Used to block until a specified list of vehicles has connect to the `MissionManager` instance.

        Args:
          vnames (iterable): A list / tuple of `str` values to look for
          sleep (float): Amount of time in seconds to sleep for between checks
        '''
        while not self.are_present(vnames):
            time.sleep(sleep)

    def get_message(self, block=True):
        '''
        Used as the primary method for receiving data from `BHV_Agent`.

        **NOTE:** Messages **MUST** be responded to as `BHV_Agent` will not send another update until it has a response to the last.

        Args:
          block (bool): A boolean specifying if the method will wait until a message present or return immediately

        Returns:
          obj: A instance of [`MissionMessage()`][mivp_agent.manager.MissionMessage] or `None` depending on the blocking behavior

        Example:
          ```
            msg = mgr.get_message()

            NAV_X = msg.state['NAV_X']
            NAV_Y = msg.state['NAV_Y']

            # ...
            # Some processing
            # ...

            msg.act({
              'speed': 1.0
              'course': 180.0
            })
          ```
        '''
        return self._msg_queue.get(block=block)

    def get_vehicle_count(self):
        '''
        Returns:
          int: The amount of vehicles that have connected to this instance of `MissionManager`
        '''
        return self._vehicle_count

    def episode_state(self, vname):
        '''
        This is used to interrogate the state of a connected vehicle's `pEpisodeManager`

        Args:
          vname (str): the vname of the vehicle

        Returns:
          str: The state of the `pEpisodeManager` on the vehicle 
        '''
        with self._ems_lock:
            # Should be all strings so no reference odd ness
            return self._episode_manager_states[vname]

    def episode_nums(self):
        '''
        Returns:
          dict: A key, value pair maping vnames to the episode numbers of the `pEpisodeManager` app on that vehicle
        '''
        with self._emn_lock:
            return self._episode_manager_nums.copy()

    def reset_vehicle(self, vname, success=False):
        # Untested
        self._vresets.append((vname, success))

    def close(self):
        if self._thread is not None:
            self._stop_signal = True
            self._thread.join()
        if self._logging:
            for vehicle in self._logs:
                self._logs[vehicle].close()

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
