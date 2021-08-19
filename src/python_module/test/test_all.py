#!/usr/bin/env python3
import unittest
import test_bridge
import test_manager

if __name__ == '__main__':
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(test_bridge.TestBridge))
  suite.addTest(unittest.makeSuite(test_manager.TestManager))
  
  runner = unittest.TextTestRunner()
  runner.run(suite)