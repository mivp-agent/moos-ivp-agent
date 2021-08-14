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
  

class MissionManager:
  def __init__(self):
    self._msg_queue = Queue()
    self._vehicle_count = 0
    self._episode_manager_states = {}
    self._ems_lock = Lock()
    self._episode_manager_nums = {}
    self._emn_lock = Lock()
  
    self._thread = None
    self._stop_signal = False

  def __enter__(self):
    self.start()
    return self

  def start(self):
    if self._thread is not None:
      return False

    self._thread = Thread(target=self._server_thread, daemon=True)
    self._thread.start()

    return True

  def _server_thread(self):
    live_msg_list = []
    # TODO: Hash table? 
    vnames = []
    with ModelBridgeServer() as server:
      while not self._stop_signal:
        # Accept new clients & send new message
        addr = server.accept()
        if addr is not None:
          print(f'Got new connection: {addr}')
          server.send_instr(addr, INSTR_SEND_STATE)

        for addr in server._clients:
          msg = server.listen(addr)

          if msg is not None:
            if msg[KEY_ID] not in vnames:
              vname = msg[KEY_ID]
              vnames.append(vname)
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

        for i, m in enumerate(live_msg_list):
          with m._rsp_lock:
            if m._response is None:
              continue 
            
            # If we got there is response send and remove from list
            live_msg_list.remove(m)
            server.send_instr(m._addr, m._response)

  def get_message(self, block=True):
    return self._msg_queue.get(block=block)

  def get_vehicle_count(self):
    return self._vehicle_count

  def episode_state(self, vname):
    with self._ems_lock:
      # Should be all strings so no reference odd ness
      return self._episode_manager_states[vname]
  
  def episode_nums(self):
    with self._emn_lock:
      return self._episode_manager_nums.copy()

  def close(self):
    if self._thread is not None:
      self._stop_signal = True
      self._thread.join()

  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

class MissionMessage:
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
      self.episode_report = parse_report(self.state[KEY_EPISODE_MGR_REPORT])
    if self.state[KEY_EPISODE_MGR_STATE] is not None:
      self.episode_state = self.state[KEY_EPISODE_MGR_STATE]

  def _assert_no_rsp(self):
    assert self._response is None, 'This message has already been responded to'
  
  def act(self, action):
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
    self._assert_no_rsp()
    with self._rsp_lock:
      self._response = INSTR_START

  def pause(self):
    self._assert_no_rsp()
    with self._rsp_lock:
      self._response = INSTR_PAUSE

  def stop(self):
    self._assert_no_rsp()

    with self._rsp_lock:
      self._response = INSTR_STOP

  def request_new(self):
    self._assert_no_rsp()

    with self._rsp_lock:
      self._response = INSTR_SEND_STATE