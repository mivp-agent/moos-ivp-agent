import unittest
import time
from threading import Thread

from mivp_agent.bridge import ModelBridgeClient
from mivp_agent.episodic_manager import EpisodicManager
from mivp_agent.const import KEY_ID, KEY_EPISODE_MGR_REPORT, KEY_EPISODE_MGR_STATE

DUMMY_STATE = {
  KEY_ID: 'felix',
  'MOOS_TIME': 16923.012,
  'NAV_X': 98.0,
  'NAV_Y': 40.0,
  'NAV_HEADING': 180,
  KEY_EPISODE_MGR_REPORT: 'NUM=0,DURATION=60.57,SUCCESS=false,WILL_PAUSE=false',
  KEY_EPISODE_MGR_STATE: 'PAUSED'
}

class FakeAgent:
  def __init__(self, id):
    self._id = id
    self.states = []
  
  def id(self):
    return self._id
  
  def obs_to_rpr(self, state):
    self.states.append(state)
  
  def rpr_to_act(self, rpr, state):
    pass

class TestEpisodicManager(unittest.TestCase):
  def setUp(self) -> None:
      super().setUp()
      self.agents = {
        'misha': FakeAgent('misha'),
        'mike': FakeAgent('mike')
      }

      # For each agent create a client
      self.clients = {}
      for name in self.agents:
        self.clients[name] = ModelBridgeClient()

      # Get list of agent names for episodic manager
      agnt_lst = [agent for _, agent in self.agents.items()]
      self.mgr = EpisodicManager(agnt_lst, 100)

      # Start manager in another thread
      self.mgr_thread = Thread(target=self.mgr.start, args=('tester',))
      self.mgr_thread.start()

      # Connect clients to server started by the manager
      all_connected = False
      while not all_connected:
        all_connected = True

        for c in self.clients:
          if not self.clients[c].is_connected():
            self.clients[c].connect()
            all_connected = False

  def tearDown(self) -> None:
      super().tearDown()
      if self.mgr.is_running():
        self.mgr.stop()

      self.mgr_thread.join()

      time.sleep(0.1)

      for c in self.clients:
        self.clients[c].close()

  def test_constructor(self):
    # Test failure with no args
    self.assertRaises(TypeError, EpisodicManager)

    agents = []
    agents.append(FakeAgent('joe'))
    agents.append(FakeAgent('carter'))

    # Test failure with with no episodes
    self.assertRaises(TypeError, EpisodicManager, agents)

    # Test success
    EpisodicManager(agents, 100)

  def test_stop(self):
    # Sanity check
    self.assertTrue(self.mgr.is_running())

    # Give the stop signal
    self.mgr.stop()

    # Allow time for release then assert
    time.sleep(0.2)
    self.assertFalse(self.mgr.is_running())

  def test_routing(self):
    # Setup two states to be sent
    misha_state = DUMMY_STATE.copy()
    misha_state[KEY_ID] = 'misha'
    misha_state['NAV_X'] = 1.0
    mike_state = DUMMY_STATE.copy()
    mike_state[KEY_ID] = 'mike'
    mike_state['NAV_X'] = 0.0

    # Send states
    self.clients['misha'].send_state(misha_state)
    self.clients['mike'].send_state(mike_state)

    # Allow time for propagation
    time.sleep(0.2)

    # Check that both received one state
    self.assertEqual(len(self.agents['misha'].states), 1)
    self.assertEqual(len(self.agents['mike'].states), 1)

    # Check that they received the proper state
    self.assertEqual(self.agents['misha'].states[0]['NAV_X'], 1.0)
    self.assertEqual(self.agents['mike'].states[0]['NAV_X'], 0.0)

if __name__ == '__main__':
  unittest.main()