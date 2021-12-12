#!/usr/bin/env python3

# Test generated file dir
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(currentdir, '.generated')
if not os.path.isdir(generated_dir):
  os.makedirs(generated_dir)
assert os.listdir(generated_dir) == ['README.txt'], 'test/.generated directory corrupted'

os.chdir(generated_dir)

import unittest
import test_file_system
import test_bridge
import test_log
import test_manager
import test_data_structures
import test_proto
import test_consumer
import test_packit

from mivp_agent.util.file_system import safe_clean
from mivp_agent.const import DATA_DIRECTORY


if __name__ == '__main__':
  suite = unittest.TestSuite()
  suite.addTest(unittest.makeSuite(test_file_system.TestSafeClean))
  suite.addTest(unittest.makeSuite(test_file_system.TestUnique))
  suite.addTest(unittest.makeSuite(test_packit.TestPackitEncode))
  suite.addTest(unittest.makeSuite(test_packit.TestPackitDecode))
  suite.addTest(unittest.makeSuite(test_bridge.TestBridge))
  suite.addTest(unittest.makeSuite(test_log.TestMetadata))
  suite.addTest(unittest.makeSuite(test_proto.TestProto))
  suite.addTest(unittest.makeSuite(test_consumer.TestConsumer))
  suite.addTest(unittest.makeSuite(test_manager.TestManagerCore))
  suite.addTest(unittest.makeSuite(test_manager.TestManagerLogger))
  suite.addTest(unittest.makeSuite(test_data_structures.TestLimitedHistory))
  suite.addTest(unittest.makeSuite(test_proto.TestLogger))
  
  runner = unittest.TextTestRunner()
  result = runner.run(suite)

  # Clean any log files
  log_dir = os.path.join(generated_dir, DATA_DIRECTORY)
  safe_clean(log_dir, patterns=['*.gz', '*.session'])
  os.rmdir(log_dir)

  if len(result.failures) != 0 or len(result.errors) != 0:
    exit(1)