import unittest
import os
import time
import timeout_decorator

from mivp_agent.manager import MissionManager
from mivp_agent.messages import MissionMessage, INSTR_SEND_STATE
from mivp_agent.bridge import ModelBridgeClient
from mivp_agent.const import KEY_ID, KEY_EPISODE_MGR_REPORT, KEY_EPISODE_MGR_STATE

from mivp_agent.util.parse import parse_report
from mivp_agent.util.file_system import safe_clean
from mivp_agent.proto.proto_logger import ProtoLogger
from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto import translate

DUMMY_INSTR = {
  'speed': 2.0,
  'course': 120.0,
  'posts': {
    'FAKE_VAR': 'fake_val'
  },
  'ctrl_msg': 'SEND_STATE'
}

DUMMY_ACTION = {
  'speed': DUMMY_INSTR['speed'],
  'course': DUMMY_INSTR['course'],
  'posts': DUMMY_INSTR['posts']
}

DUMMY_STATE = {
  KEY_ID: 'felix',
  'MOOS_TIME': 16923.012,
  'NAV_X': 98.0,
  'NAV_Y': 40.0,
  'NAV_HEADING': 180,
  KEY_EPISODE_MGR_REPORT: 'NUM=0,DURATION=60.57,SUCCESS=false,WILL_PAUSE=false',
  KEY_EPISODE_MGR_STATE: 'PAUSED'
}

DUMMY_STATE_PARSED = DUMMY_STATE.copy()
DUMMY_STATE_PARSED[KEY_EPISODE_MGR_REPORT] = parse_report(DUMMY_STATE_PARSED[KEY_EPISODE_MGR_REPORT] )

DUMMY_REPORT ={
  'NUM': 0,
  'DURATION': 60.57,
  'SUCCESS': False,
  'WILL_PAUSE': False
}

def dummy_connect_client(client):
  while not client.connect():
    time.sleep(0.2)

class TestManagerCore(unittest.TestCase):
  @timeout_decorator.timeout(5)
  def test_basic(self):
    with ModelBridgeClient() as client:
      with MissionManager('test', log=False) as mgr:
        # Test client connection
        #
        while not client.connect():
          time.sleep(0.1)
        
        time.sleep(0.1)
        self.assertEqual(client.listen(), INSTR_SEND_STATE)
        
        # Send client message
        self.assertTrue(client.send_state(DUMMY_STATE))
        # Check recving of state
        msg = mgr.get_message(block=True)
        self.assertTrue(isinstance(msg, MissionMessage))
        self.assertEqual(msg.state, DUMMY_STATE_PARSED)
        self.assertEqual(msg.episode_report, DUMMY_REPORT)
        self.assertEqual(msg.episode_state, 'PAUSED')
        # Make sure there are no messages for the client yet
        self.assertFalse(client.listen())
        # Respond to message
        msg.act(DUMMY_ACTION)
        time.sleep(0.1) # Allow propogate time
        self.assertEqual(client.listen(), DUMMY_INSTR)
  
  @timeout_decorator.timeout(5)
  def test_wait_for(self):
    with MissionManager('test', log=False) as mgr:
      # Make sure manager doesn't know about evan or felix
      self.assertFalse(mgr.are_present(['evan', 'felix']))

      # Connect evan
      with ModelBridgeClient() as client:
        # Wait for client to connect
        while not client.connect():
          time.sleep(0.1)
        
        # Send evan's connection message
        state = DUMMY_STATE.copy()
        state[KEY_ID] = 'evan'
        self.assertTrue(client.send_state(state))

        # Allow propogation time
        time.sleep(0.1)
        
        # Test for presence of evan with manager
        self.assertTrue(mgr.are_present(['evan', ]))
        mgr.wait_for(['evan', ]) # Timeout decorator will handle this test

        # Test for absence of felix
        self.assertFalse(mgr.are_present(['evan', 'felix']))

        # Connect felix
        with ModelBridgeClient() as client2:
          # Wait for client to connect
          while not client2.connect():
            time.sleep(0.1)
          
          # Send felix's connection message
          state = DUMMY_STATE.copy()
          state[KEY_ID] = 'felix'
          self.assertTrue(client2.send_state(state))
        
        time.sleep(0.1)
        self.assertTrue(mgr.are_present(['evan', 'felix']))

class TestManagerLogger(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
      cls.states = []
      for i in range(10):
        cls.states.append({
          KEY_ID: 'felix',
          'MOOS_TIME': 16923.012+i,
          'NAV_X': 98.0-i,
          'NAV_Y': 40.0+i,
          'NAV_HEADING': 180.0-i,
          KEY_EPISODE_MGR_REPORT: f'NUM={i},DURATION=6{i}.57,SUCCESS=false,WILL_PAUSE=false',
          KEY_EPISODE_MGR_STATE: 'PAUSED'
        })

      cls.states_parsed = []
      for s in cls.states:
        sp = s.copy()
        sp[KEY_EPISODE_MGR_REPORT] = parse_report(sp[KEY_EPISODE_MGR_REPORT])
        cls.states_parsed.append(sp)
      
      cls.actions = []
      for i in range(10):
        cls.actions.append({
          'speed': 2.0+i,
          'course': 120.0-i,
          'posts': {
            'FAKE_VAR': f'fake_val_{i}'
          },
          'ctrl_msg': 'SEND_STATE'
        })

      return super().setUpClass()

  def test_basic(self):
    path = None
    with ModelBridgeClient() as client:
      with MissionManager('test', log=True) as mgr:
        path = mgr.log_output_dir()
        
        # Basic existence checks
        self.assertTrue(os.path.exists(path))
        self.assertEqual(len(os.listdir(path)), 0)

        # Connect client
        while not client.connect():
          time.sleep(0.1)

        for i in range(10):
          client.send_state(self.states[i])
          time.sleep(0.1)
          msg = mgr.get_message()
          msg.act(self.actions[i])

    log = ProtoLogger(os.path.join(path, 'log_felix'), Transition, mode='r')
    
    transitions = []
    while log.has_more():
      transitions.append(log.read(1)[0])
    
    self.assertEqual(len(transitions), 9)

    for i, t in enumerate(transitions):
      s1 = translate.state_to_dict(t.s1)
      a = translate.action_to_dict(t.a)
      s2 = translate.state_to_dict(t.s2)
      self.assertEqual(s1, self.states_parsed[i])
      self.assertEqual(a, self.actions[i])
      self.assertEqual(s2, self.states_parsed[i+1])

    # Clean up
    safe_clean(path, patterns=['*.gz'])
    os.rmdir(path)
  
  def test_transition(self):
    path = None
    with ModelBridgeClient() as client:
      with MissionManager('test', log=True, immediate_transition=False) as mgr:
        path = mgr.log_output_dir()

        # Basic existence checks
        self.assertTrue(os.path.exists(path))
        self.assertEqual(len(os.listdir(path)), 0)

        # Connect client
        while not client.connect():
          time.sleep(0.1)

        for i in range(10):
          client.send_state(self.states[i])
          time.sleep(0.1)
          msg = mgr.get_message()
          if i == 0 or i == 5:
            msg.mark_transition()
          msg.act(self.actions[i])

    log = ProtoLogger(os.path.join(path, 'log_felix'), Transition, mode='r')

    transitions = []
    while log.has_more():
      transitions.append(log.read(1)[0])

    self.assertEqual(len(transitions), 1)

    t = transitions[0]
    s1 = translate.state_to_dict(t.s1)
    a = translate.action_to_dict(t.a)
    s2 = translate.state_to_dict(t.s2)
    self.assertEqual(s1, self.states_parsed[0])
    self.assertEqual(a, self.actions[0])
    self.assertEqual(s2, self.states_parsed[5])

    # Clean up
    safe_clean(path, patterns=['*.gz'])
    os.rmdir(path)
  
  def test_whitelist(self):
    path = None
    clients = {
      'felix': ModelBridgeClient(),
      'henry': ModelBridgeClient(),
      'alpha': ModelBridgeClient()
    }
    with MissionManager('test', log=True, immediate_transition=False, log_whitelist=('felix', 'henry')) as mgr:
      path = mgr.log_output_dir()

      # Basic existence checks
      self.assertTrue(os.path.exists(path))
      self.assertEqual(len(os.listdir(path)), 0)

      # Connect all client
      all_connected = False
      while not all_connected:
        all_connected = True
        for c in clients:
          if not clients[c].is_connected():
            # Attempt to connect until the timeout
            clients[c].connect()
            all_connected = False
        time.sleep(0.1)

      for i in range(10):
        # Send states for 
        for vname in clients:
          s = self.states[i].copy()
          s[KEY_ID] = vname
          clients[vname].send_state(s)
        time.sleep(0.1)

        msg = mgr.get_message(block=False)
        while msg is not None:
          if i == 0 or i == 5:
            msg.mark_transition()
          msg.act(self.actions[i])

          # Try to get new 
          msg = mgr.get_message(block=False)
    
    for c in clients:
      clients[c].close()

    self.assertTrue(os.path.isdir(os.path.join(path, 'log_felix')))
    self.assertTrue(os.path.isdir(os.path.join(path, 'log_henry')))
    self.assertFalse(os.path.isdir(os.path.join(path, 'log_alpha')))

    for c in clients:
      if c != 'alpha':
        log = ProtoLogger(os.path.join(path, f'log_{c}'), Transition, mode='r')

        transitions = []
        while log.has_more():
          transitions.append(log.read(1)[0])

        self.assertEqual(len(transitions), 1)

    safe_clean(path, patterns=['*.gz'])
    os.rmdir(path)
if __name__ == '__main__':
  unittest.main()