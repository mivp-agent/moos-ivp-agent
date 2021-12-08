#!/usr/bin/env python3

# Test generated file dir
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(currentdir, '.generated')
assert os.listdir(generated_dir) == ['README.txt'], 'test/.generated directory corrupted'

os.chdir(generated_dir)

import unittest
import test_file_system
import test_bridge
import test_manager
import test_data_structures
import test_proto
import test_packit

if __name__ == '__main__':
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(test_file_system.TestSafeClean))
  suite.addTest(unittest.makeSuite(test_packit.TestPackitEncode))
  suite.addTest(unittest.makeSuite(test_packit.TestPackitDecode))
  suite.addTest(unittest.makeSuite(test_bridge.TestBridge))
  suite.addTest(unittest.makeSuite(test_manager.TestManagerCore))
  suite.addTest(unittest.makeSuite(test_manager.TestManagerLogger))
  suite.addTest(unittest.makeSuite(test_data_structures.TestLimitedHistory))
  suite.addTest(unittest.makeSuite(test_proto.TestProto))
  suite.addTest(unittest.makeSuite(test_proto.TestLogger))

  
  runner = unittest.TextTestRunner()
  result = runner.run(suite)

  if len(result.failures) != 0 or len(result.errors) != 0:
    exit(1)