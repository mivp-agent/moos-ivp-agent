import os
import glob
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(current_dir, '.generated')

import unittest

from google.protobuf.message import EncodeError
from google.protobuf.message import Message
from mivp_agent.proto import agent_state_pb2, node_report_pb2, aquaticus_vehicle_pb2

class TestProto(unittest.TestCase):

  def test_basic(self):
    # The following test that we are able to serialize

    report = node_report_pb2.NodeReport()
    self.assertRaises(EncodeError, report.SerializeToString)

    report.vname = "agent"
    report.NAV_X = 40.1
    report.NAV_Y = -50.4
    report.NAV_HEADING = 143.2
    report.SerializeToString()

    aquaticus = aquaticus_vehicle_pb2.AquaticusVehicle()
    self.assertRaises(EncodeError, aquaticus.SerializeToString)

    aquaticus.tagged = False
    aquaticus.has_flag = True
    aquaticus.node_report.CopyFrom(report)
    aquaticus.SerializeToString()

    agent = agent_state_pb2.AgentState()  
    self.assertRaises(EncodeError, agent.SerializeToString)
    agent.MOOS_TIME = 0.0
    agent.vehicle.CopyFrom(aquaticus)
    
    other_report1 = agent.other_reports.add()
    other_report1.CopyFrom(report)

    other_report2 = agent.other_reports.add()
    other_report2.CopyFrom(report)

    agent.SerializeToString()


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
    cls.report = node_report_pb2.NodeReport()
    cls.report.vname = "agent"
    cls.report.NAV_X = 40.1
    cls.report.NAV_Y = -50.4
    cls.report.NAV_HEADING = 143.2
    cls.report.SerializeToString()

    cls.vehicle = aquaticus_vehicle_pb2.AquaticusVehicle()
    cls.vehicle.tagged = False
    cls.vehicle.has_flag = True
    cls.vehicle.node_report.CopyFrom(cls.report)
    return super().setUpClass()

  def test_basic(self):
    with self.assertRaises(AssertionError):
      ProtoLogger(generated_dir, node_report_pb2.NodeReport, 'w')

    save_dir = os.path.join(generated_dir, 'test')
    log = ProtoLogger(save_dir, node_report_pb2.NodeReport, 'w', max_msgs=2)
    
    with self.assertRaises(AssertionError):
      log.write('WrongType')
    with self.assertRaises(AssertionError):
      log.write(self.vehicle)
    
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
      ProtoLogger(os.path.join(generated_dir, 'non-exist'), node_report_pb2.NodeReport, 'r')
    
    # Test fail on empty directory
    test2_dir = os.path.join(generated_dir, 'test2')
    os.makedirs(test2_dir)
    with self.assertRaises(AssertionError):
      ProtoLogger(test2_dir, node_report_pb2.NodeReport, 'r')
    
    # Test fail on non gz file
    Path(os.path.join(test2_dir, 'file.txt')).touch()
    with self.assertRaises(RuntimeError):
      ProtoLogger(test2_dir, node_report_pb2.NodeReport, 'r')
    
    clean_dir(test2_dir, file_pattern="*.txt")
    
    log = ProtoLogger(save_dir, node_report_pb2.NodeReport, 'r')

    # Test that we can get the amount request
    msgs = log.read(1)
    self.assertEqual(len(msgs), 1)
    self.assertTrue(isinstance(msgs[0], Message))
    self.assertTrue(isinstance(msgs[0], node_report_pb2.NodeReport))
    self.assertEqual(msgs[0], self.report)

    # Test that reading separate files will happen seemlessly (remember 2 messages per file in the above)
    # Test that a too high n won't break
    msgs = log.read(3)
    self.assertEqual(len(msgs), 2, "Expected only 2 messages to remain on disk")
    
    for msg in msgs:
      self.assertTrue(isinstance(msg, Message))
      self.assertTrue(isinstance(msg, node_report_pb2.NodeReport))
      self.assertEqual(msg, self.report)

      # Sanity check
      self.assertNotEqual(msg, self.vehicle)
    
    # Test subsequent reads just return nothing =
    self.assertEqual(len(log.read(1)), 0)

    # Clean up
    clean_dir(save_dir, file_pattern="*.gz")
    
if __name__ == '__main__':
  unittest.main()