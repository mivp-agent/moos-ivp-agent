from mivp_agent.episodic_manager import EpisodicManager

import unittest

class FakeAgent:
  def __init__(self, id):
    self._id = id
  
  def id(self):
    return self._id

class TestEpisodicManager(unittest.TestCase):
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

if __name__ == '__main__':
  unittest.main()