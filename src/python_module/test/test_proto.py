import unittest

from google.protobuf.message import EncodeError
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

if __name__ == '__main__':
  unittest.main()