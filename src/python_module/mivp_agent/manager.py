import time
from queue import Queue
from threading import Thread, Lock

from mivp_agent.const import KEY_ID
from mivp_agent.const import KEY_EPISODE_MGR_REPORT, KEY_EPISODE_MGR_STATE
from mivp_agent.bridge import ModelBridgeServer
from mivp_agent.util.validate import validateAction
from mivp_agent.util.parse import parse_report

INSTR_SEND_STATE = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {},
    'ctrl_msg': 'SEND_STATE'
}
INSTR_START = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {
        'EPISODE_MGR_CTRL': 'type=start'
    },
    'ctrl_msg': 'SEND_STATE'
}
INSTR_PAUSE = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {
        'EPISODE_MGR_CTRL': 'type=pause'
    },
    'ctrl_msg': 'SEND_STATE'
}
INSTR_STOP = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {
        'EPISODE_MGR_CTRL': 'type=hardstop'
    },
    'ctrl_msg': 'SEND_STATE'
}
INSTR_RESET_SUCCESS = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {
        'EPISODE_MGR_CTRL': 'type=reset,success=true'
    },
    'ctrl_msg': 'SEND_STATE'
}
INSTR_RESET_FAILURE = {
    'speed': 0.0,
    'course': 0.0,
    'posts': {
        'EPISODE_MGR_CTRL': 'type=reset,success=false'
    },
    'ctrl_msg': 'SEND_STATE'
}


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

    def __init__(self):
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

                        m = MissionMessage(addr, msg)

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

                # Handle reseting of vehicles
                while not self._vresets.empty():
                    vname, success = self._vresets.get()

                    if vname not in address_map:
                        raise RuntimeError(
                            f'Receeived reset for unknown vehicle: {vname}')

                    instr = INSTR_RESET_FAILURE
                    if success:
                        instr = INSTR_RESET_SUCCESS

                    server.send_instr(address_map[vname], instr)

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

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class MissionMessage:
    '''
    This class is used to parse incoming messages into attributes (see bellow) and provide a simple interface for responding to each message.

    **IMPORTANT NOTE:** Messages **MUST** be responded by one of the following methods to as `BHV_Agent` will not send another update until it has a response to the last.

      - [`act(action)`][mivp_agent.manager.MissionMessage.act] **<---- Most common**
      - [`request_new()`][mivp_agent.manager.MissionMessage.request_new]
      - [`start()`][mivp_agent.manager.MissionMessage.start]
      - [`pause()`][mivp_agent.manager.MissionMessage.pause]
      - [`stop()`][mivp_agent.manager.MissionMessage.stop]

    Attributes:
      vname (str): The vehicle's name which generated the message.
      state (dict): A dictionary containing key, value pairs of MOOS vars and their associated value at the time the message was created by `BHV_Agent`.
      episode_report (dict or None): If `pEpisodeManager` is present on the vehicle this message will contain any "report" generated by it at the end of episodes. If no `pEpisodeManager` is present, the **value will be** `None`.
      episode_state (str or None): If `pEpisodeManager` is present on the vehicle this message will be the state which that app is broadcasting. Otherwise, it will be `None`.

    '''

    def __init__(self, addr, msg):
        # For use my MissionManager
        self._addr = addr
        self._response = None
        self._rsp_lock = Lock()

        # For use by client
        self.state = msg
        self.vname = msg[KEY_ID]
        self.episode_report = None
        self.episode_state = None
        if self.state[KEY_EPISODE_MGR_REPORT] is not None:
            self.episode_report = parse_report(
                self.state[KEY_EPISODE_MGR_REPORT])
        if self.state[KEY_EPISODE_MGR_STATE] is not None:
            self.episode_state = self.state[KEY_EPISODE_MGR_STATE]

    def _assert_no_rsp(self):
        assert self._response is None, 'This message has already been responded to'

    def act(self, action):
        '''
        This is used to send an action for the `BHV_Agent` to execute.

        Args:
          action (dict): An action to send (see below)

        Example:
          Actions submitted through `MissionMessage` are python dictionaries with the following **required** fields.
          ```
          msg.act({
              'speed': 1.0
              'course': 180.0
          })
          ```
        Example:
          Optionally, one can add a MOOS var and value they would like to post.
          ```
          msg.act({
              'speed': 0.0
              'course': 0.0
              'posts': {
                'ACTION': 'ATTACK_LEFT'
              },
          })
          ``` 
        '''
        self._assert_no_rsp()
        # Copy so we don't run into threading errors if client reuses the action dict
        instr = action.copy()
        if 'posts' not in action:
            instr['posts'] = {}
        validateAction(instr)
        instr['ctrl_msg'] = 'SEND_STATE'

        with self._rsp_lock:
            self._response = instr

    def start(self):
        '''
        This method is used to send a message to `pEpisodeManager` to **start** an episode. The following message will be constructed and dispatched.

        ```
        {
          'speed': 0.0,
          'course': 0.0,
          'posts': {
            'EPISODE_MGR_CTRL': 'type=start'
          },
        }
        ```
        '''
        self._assert_no_rsp()
        with self._rsp_lock:
            self._response = INSTR_START

    def pause(self):
        '''
        This method is used to send a message to `pEpisodeManager` to **pause** after the current episode. The following messagewill be constructed and dispatched.

        ```
        {
          'speed': 0.0,
          'course': 0.0,
          'posts': {
            'EPISODE_MGR_CTRL': 'type=pause'
          },
        }
        ```
        '''
        self._assert_no_rsp()
        with self._rsp_lock:
            self._response = INSTR_PAUSE

    def stop(self):
        '''
        This method is used to send a message to `pEpisodeManager` to **hardstop** an episode immediately. The following messagewill be constructed and dispatched.

        ```
        {
          'speed': 0.0,
          'course': 0.0,
          'posts': {
            'EPISODE_MGR_CTRL': 'type=hardstop'
          },
        }
        ```
        '''
        self._assert_no_rsp()

        with self._rsp_lock:
            self._response = INSTR_STOP

    def request_new(self):
        '''
        This method is used to send ask `BHV_Agent` to send another action.
        '''
        self._assert_no_rsp()

        with self._rsp_lock:
            self._response = INSTR_SEND_STATE
