# General
import os
import time
from queue import Queue, Empty
from threading import Thread, Lock

# For core
from mivp_agent.const import KEY_ID, DATA_DIRECTORY
from mivp_agent.messages import MissionMessage, INSTR_SEND_STATE, INSTR_RESET_FAILURE, INSTR_RESET_SUCCESS
from mivp_agent.bridge import ModelBridgeServer

# For logging
from mivp_agent.log.directory import LogDirectory
from mivp_agent.proto.proto_logger import ProtoLogger
from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto import translate

class MissionManager:
    '''
    This is the primary method for interfacing with moos-ivp-agent's BHV_Agent

    Examples:
      It is recommended to use MissionManager with the python context manager

      ```
      from mivp_agent.manager import MissionManager

      with MissionManager('trainer') as mgr:
        mgr.wait_for(['felix', 'evan'])
        ...
      ```
    '''

    def __init__(self, task, log=True, immediate_transition=True, log_whitelist=None, id_suffix=None, output_dir=None):
        '''
        The initializer for MissionManager

        Args:
            task (str): For organization of saved data type is required to specify what task the MissionManager is preforming. For example a `MissionManager('trainer')` will log data under `generated_files/trainer/` in the current working directory.

            log (bool): Logging of agent transitions can be disabled by setting this to `False`.

            immediate_transition (bool): By default the the manager will assume that all messages received from BHV_Agents represent a new transition. If set to `False` one must manually tell set `msg.is_transition = True` on any objects returned from `get_message()`. This is helpful when you want to control what is considered a "state" in your Markov Decsion Process.

            log_whitelist (list): Setting this parameter will only log some transitions according to their reported `vnames`.

            id_suffix (str): Will be appended to the generated session id.

            output_dir (str): Path to a place to store files.
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
        
        if output_dir is None:
            output_dir = os.path.join(
                os.path.abspath(os.getcwd()),
                DATA_DIRECTORY
            )

        self._log_dir = LogDirectory(output_dir)
        self._id = self._init_session(id_suffix)

        # Calculate the path to the directories we will be writing to. This will be created when we first use them / return them to the user.
        self._model_path = os.path.join(
            self._log_dir.models_dir(),
            self._id
        )
        self._log_path = os.path.join(
            self._log_dir.task_dir(task),
            self._id
        )
        self._model_path = os.path.abspath(self._model_path)
        self._log_path = os.path.abspath(self._log_path)

        self._log = log
        self._imm_transition = immediate_transition
        if self._log:
            self._log_whitelist = log_whitelist
            # Create data structs needed to log data from each vehicle
            self._logs = {}
            self._last_state = {}
            self._last_act = {}

            # Go ahead and create the log path
            os.makedirs(self._log_path)

    def _init_session(self, id_suffix):
        # Start the session id with the current timestamp
        id = str(round(time.time()))

        # Add suffix if it exists
        if id_suffix is not None:
            id += f"-{id_suffix}"

        id = self._log_dir.meta.registry.register(id)

        return id

    def model_output_dir(self):
        if not os.path.isdir(self._model_path):
            os.makedirs(self._model_path)
        return self._model_path
    
    def log_output_dir(self):
        '''
        Returns the log path for the current session so custom files can be added to it.
        '''
        assert self._log, "This method should not be used, when logging is disabled"
        return self._log_path

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

                        assert address_map[msg[KEY_ID]] == addr, "Vehicle changed vname. This violates routing / logging assumptions made by MissionManager"

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
        if not self._log:
            return
        
        # Check in whitelist if exists
        if self._log_whitelist is not None:
            if msg.vname not in self._log_whitelist:
                return

        # Check if this is a new vehicle
        if msg.vname not in self._logs:
            path = os.path.join(self._log_path, f"log_{msg.vname}")
            self._logs[msg.vname] = ProtoLogger(path, Transition, mode='w')

        if msg._is_transition:
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
        try:
            return self._msg_queue.get(block=block)
        except Empty:
            return None

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
        if self._log:
            for vehicle in self._logs:
                self._logs[vehicle].close()


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
