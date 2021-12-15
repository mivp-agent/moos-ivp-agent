import os
import glob
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(current_dir, '.generated')

import unittest

from google.protobuf.message import EncodeError
from google.protobuf.message import Message
from mivp_agent.proto import moos_pb2, mivp_agent_pb2
from mivp_agent.proto import translate
from mivp_agent.const import KEY_ID, KEY_EPISODE_MGR_REPORT


class TestProto(unittest.TestCase):

  def test_moos_var(self):
    var = moos_pb2.MOOSVar()
    self.assertRaises(EncodeError, var.SerializeToString)

    var.key = "MY_VAR"
    with self.assertRaises(TypeError):
      var.dval = "Hi"
    with self.assertRaises(TypeError):
      var.sval = 1203.2
  
  def do_translate_test(self, input, from_dict, to_dict, debug=False):
    proto = from_dict(input)

    # Make sure we can serialize
    proto.SerializeToString()

    # Untranslate and compare with original
    out = to_dict(proto)

    if debug:
      print("IN --------------------")
      print(input)
      print("OUT -------------------")
      print(out)

    self.assertEqual(input, out)

  def test_translate_state(self):
    state = {
      KEY_ID: 'felix',
      'MOOS_TIME': 16923.012,
      'NAV_X': 98.0,
      'NAV_Y': 40.0,
      'NAV_HEADING': 180,
      KEY_EPISODE_MGR_REPORT: None
    }

    self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )

    state['TAGGED'] = True
    self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )

    # Test with bad episode report
    state[KEY_EPISODE_MGR_REPORT] = {
      'NUM': 54,
      'SUCCESS': True,
      'WILL_PAUSE': False,
    }
    with self.assertRaises(KeyError):
      self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )

    state[KEY_EPISODE_MGR_REPORT]['DURATION'] = 2.0
    self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )

    # Test with bad other vehicle first
    state['NODE_REPORTS'] = {}
    state['NODE_REPORTS']['henry'] = {
      'vname': 'henry',
      'NAV_X': 2.354,
      'NAV_Y': 23.1,
      'NAV_HEADING': 140,
    }
    with self.assertRaises(KeyError):
      self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )
    
    state['NODE_REPORTS']['henry']['MOOS_TIME'] = 0.123
    self.do_translate_test(
      state, 
      translate.state_from_dict,
      translate.state_to_dict
    )

  def test_translate_action(self):
    action = {
      'speed': 2.0,
      'course': 120.0,
      'posts': {},
      'ctrl_msg': 'SEND_STATE'
    }

    self.do_translate_test(
      action, 
      translate.action_from_dict,
      translate.action_to_dict
    )

    action['posts']['myVar'] = True
    self.do_translate_test(
      action, 
      translate.action_from_dict,
      translate.action_to_dict
    )

    action['posts']['myVar'] = "String"
    self.do_translate_test(
      action, 
      translate.action_from_dict,
      translate.action_to_dict
    )

    action['posts']['myVar'] = 3.1415
    self.do_translate_test(
      action, 
      translate.action_from_dict,
      translate.action_to_dict
    )

    del action['speed']
    with self.assertRaises(AssertionError):
      self.do_translate_test(
      action, 
      translate.action_from_dict,
      translate.action_to_dict
    )

from mivp_agent.proto.proto_logger import ProtoLogger

def clean_dir(dir, file_pattern="*"):
  files = glob.glob(f'{dir}/{file_pattern}')
  for f in files:
    os.remove(f)

  assert len(os.listdir(dir)) ==  0, f"File written to {dir} that doesn't match pattern {file_pattern}"
  os.rmdir(dir)

class TestLogger(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
    # Add some helpful initializations 
    cls.report = moos_pb2.NodeReport()
    cls.report.vname = "agent"
    cls.report.NAV_X = 40.1
    cls.report.NAV_Y = -50.4
    cls.report.NAV_HEADING = 143.2
    cls.report.MOOS_TIME = 4.0
    cls.report.SerializeToString()

    cls.reports = []
    for i in range(100):
      report = moos_pb2.NodeReport()
      report.vname = f"vname{i}"
      report.NAV_X = 40.1
      report.NAV_Y = -50.4
      report.NAV_HEADING = 143.2
      report.MOOS_TIME = 4.0
      # Test is valid 
      report.SerializeToString()

      cls.reports.append(report)

    cls.other = moos_pb2.MOOSVar()
    cls.other.key = "Hello"
    cls.other.sval = "Yo"
    cls.other.SerializeToString()
    return super().setUpClass()

  def test_basic(self):
    with self.assertRaises(AssertionError):
      ProtoLogger(generated_dir, moos_pb2.NodeReport, 'w')

    save_dir = os.path.join(generated_dir, 'test')
    log = ProtoLogger(save_dir, moos_pb2.NodeReport, 'w', max_msgs=2)
    
    with self.assertRaises(AssertionError):
      log.write('WrongType')
    with self.assertRaises(AssertionError):
      log.write(self.other)
    
    # First add should not write to file
    self.assertEqual(len(log._buffer), 0, "Initialization error")
    log.write(self.report)
    self.assertGreater(len(log._buffer), 0, "Message was not written to buffer")
    self.assertEqual(len(os.listdir(save_dir)), 0, "Unexpected write to save directory")

    # Second add should write to file
    log.write(self.report)
    self.assertEqual(len(os.listdir(save_dir)), 1, "Messages were not written to file")
    self.assertEqual(len(log._buffer), 0, "Messages were not clear from buffer")

    # Make sure the logs are written to file on close
    log.write(self.report)
    log.close()
    self.assertEqual(len(os.listdir(save_dir)), 2, "Logs not written on close")

    # Test reading fails with non-existing directory
    with self.assertRaises(AssertionError):
      ProtoLogger(os.path.join(generated_dir, 'non-exist'), moos_pb2.NodeReport, 'r')
    
    # Test fail on empty directory
    test2_dir = os.path.join(generated_dir, 'test2')
    os.makedirs(test2_dir)
    with self.assertRaises(AssertionError):
      ProtoLogger(test2_dir, moos_pb2.NodeReport, 'r')
    
    # Test fail on non gz file
    Path(os.path.join(test2_dir, 'file.txt')).touch()
    with self.assertRaises(RuntimeError):
      ProtoLogger(test2_dir, moos_pb2.NodeReport, 'r')
    
    clean_dir(test2_dir, file_pattern="*.txt")
    
    log = ProtoLogger(save_dir, moos_pb2.NodeReport, 'r')

    # Test that we can get the amount request
    msgs = log.read(1)
    self.assertEqual(len(msgs), 1)
    self.assertTrue(isinstance(msgs[0], Message))
    self.assertTrue(isinstance(msgs[0], moos_pb2.NodeReport))
    self.assertEqual(msgs[0], self.report)

    # Test that reading separate files will happen seemlessly (remember 2 messages per file in the above)
    # Test that a too high n won't break
    msgs = log.read(3)
    self.assertEqual(len(msgs), 2, "Expected only 2 messages to remain on disk")
    
    for msg in msgs:
      self.assertTrue(isinstance(msg, Message))
      self.assertTrue(isinstance(msg, moos_pb2.NodeReport))
      self.assertEqual(msg, self.report)

      # Sanity check
      self.assertNotEqual(msg, self.other)
    
    # Test subsequent reads just return nothing =
    self.assertEqual(len(log.read(1)), 0)

    # Clean up
    clean_dir(save_dir, file_pattern="*.gz")
  
  def test_matrix(self):
    matrix_dir = os.path.join(generated_dir, 'matrix')
    for store_amt in range(1, 50, 5):
      for read_amt in range(1, 50, 5):
        # Make sure the directory not created yet
        self.assertFalse(os.path.isdir(matrix_dir), "Expected matrix directory to be empty at begining of test")

        # Write the messages with max_msgs set to store_amount
        with ProtoLogger(
            matrix_dir,
            moos_pb2.NodeReport,
            'w',
            max_msgs=store_amt) as log:
          for msg in self.reports:
            log.write(msg)
        
        # Check that the proper number of files have been generated
        # NOTE: Reference https://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
        file_amt = -(len(self.reports) // -store_amt)
        self.assertEqual(len(os.listdir(matrix_dir)), file_amt)

        # Open previously written dir in read mode 
        all_messages = []
        with ProtoLogger(
            matrix_dir,
            moos_pb2.NodeReport,
            'r',) as log:
            
            while len(all_messages) != len(self.reports):
              msgs = log.read(read_amt)

              self.assertNotEqual(len(msgs), 0, "Read returned empty list before all messages were decoded")

              if len(msgs) != read_amt:
                self.assertEqual(len(log.read(read_amt)), 0, "Read did not fulfill `n` requested when more messages were remaining")

              all_messages.extend(msgs)

        for i, msg in enumerate(all_messages):
          self.assertTrue(isinstance(msg, Message))
          self.assertTrue(isinstance(msg, moos_pb2.NodeReport))
          self.assertEqual(msg, self.reports[i], "Message either corrupted or out of order")
        
        # Clean up
        clean_dir(matrix_dir, file_pattern="*.gz")

if __name__ == '__main__':
  unittest.main()