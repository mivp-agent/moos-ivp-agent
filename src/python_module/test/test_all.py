#!/usr/bin/env python3

# Add the module's surrounding dir to the path
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(currentdir))

import unittest
import test_bridge
import test_manager
import test_data_structures

if __name__ == '__main__':
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(test_bridge.TestBridge))
  suite.addTest(unittest.makeSuite(test_manager.TestManager))
  suite.addTest(unittest.makeSuite(test_data_structures.TestLimitedHistory))

  
  runner = unittest.TextTestRunner()
  runner.run(suite)