import unittest
import time
import timeout_decorator

import os, sys

currentdir = os.path.dirname(os.path.realpath(__file__))
bridgedir = os.path.join(os.path.dirname(currentdir), 'mivp_agent')
sys.path.append(bridgedir)

from manager import MissionManager, MissionMessage, INSTR_SEND_STATE
from bridge import ModelBridgeClient
from const import KEY_ID, KEY_EPISODE_MGR_REPORT, KEY_EPISODE_MGR_STATE

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

DUMMY_REPORT ={
  'NUM': 0,
  'DURATION': 60.57,
  'SUCCESS': False,
  'WILL_PAUSE': False
}

def dummy_connect_client(client):
  while not client.connect():
    time.sleep(0.2)

class TestManager(unittest.TestCase):
  @timeout_decorator.timeout(5)
  def test_basic(self):
    with ModelBridgeClient() as client:
      with MissionManager() as mgr:
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
        self.assertEqual(msg.state, DUMMY_STATE)
        self.assertEqual(msg.episode_report, DUMMY_REPORT)
        self.assertEqual(msg.episode_mgr_state, 'PAUSED')
        # Make sure there are no messages for the client yet
        self.assertFalse(client.listen())
        # Respond to message
        msg.act(DUMMY_ACTION)
        time.sleep(0.1) # Allow propogate time
        self.assertEqual(client.listen(), DUMMY_INSTR)


if __name__ == '__main__':
  unittest.main()