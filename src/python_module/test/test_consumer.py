import os
import glob
import unittest

current_dir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(current_dir, '.generated')

from google.protobuf.message import Message

from mivp_agent.proto import moos_pb2, mivp_agent_pb2
from mivp_agent.proto import translate
from mivp_agent.log.consumer import Consumer
from mivp_agent.proto.proto_logger import ProtoLogger

# Define some consumers to test
class BadConsumer(Consumer):
  def __init__(self):
    pass

class ProtoConsumer(Consumer):
  def pb2_data(self, data):
    self.data = data

class DictConsumer(Consumer):
      def dict_data(self, s1, a, s2):
        self.s1 = s1
        self.a = a
        self.s2 = s2

def clean_dir(dir, file_pattern="*"):
  files = glob.glob(f'{dir}/{file_pattern}')
  for f in files:
    os.remove(f)

  assert len(os.listdir(dir)) ==  0, f"File written to {dir} that doesn't match pattern {file_pattern}"
  os.rmdir(dir)

class TestConsumer(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:

    cls.transition = []
    for i in range(100):
      report = moos_pb2.NodeReport()
      report.vname = f"vname{i}"
      report.NAV_X = 40.1
      report.NAV_Y = -50.4
      report.NAV_HEADING = 143.2
      report.MOOS_TIME = 4.0
      
      state = mivp_agent_pb2.State()
      state.vinfo.CopyFrom(report)
      # Test is valid 
      state.SerializeToString()

      action = translate.action_from_dict({
        'course': 0+i % 360,
        'speed': 2,
        'posts': {},
        'ctrl_msg': 'Yo'
      })
      action.SerializeToString()

      t = mivp_agent_pb2.Transition()
      t.s1.CopyFrom(state)
      t.s2.CopyFrom(state)
      t.a.CopyFrom(action)


      cls.transition.append(t)
    return super().setUpClass()
  
  def test_basic(self):
    t = self.transition[0]
    # Test error states
    bad = BadConsumer()
    with self.assertRaises(AttributeError):
      bad._inject(t)

    # Test protobuf consumer
    pc = ProtoConsumer()
    pc._inject(t)
    self.assertEqual(pc.data, t)

    # Test dict consumer
    dc = DictConsumer()
    dc._inject(t)
    self.assertEqual(dc.s1, translate.state_to_dict(t.s1))
    self.assertEqual(dc.s2, translate.state_to_dict(t.s2))
    self.assertEqual(dc.a, translate.action_to_dict(t.a))

  def test_matrix(self):
    '''
    This matrix test is based on the one in the ProtoLogger tests. That test should be run before this one.
    '''
    matrix_dir = os.path.join(generated_dir, 'matrix')
    for store_amt in range(1, 50, 5):
      for read_amt in range(1, 50, 5):
        # Make sure the directory not created yet
        self.assertFalse(os.path.isdir(matrix_dir), "Expected matrix directory to be empty at begining of test")

        # Write the messages with max_msgs set to store_amount
        with ProtoLogger(
            matrix_dir,
            mivp_agent_pb2.Transition,
            'w',
            max_msgs=store_amt) as log:
          for msg in self.transition:
            log.write(msg)
        
        # Check that the proper number of files have been generated
        # NOTE: Reference https://stackoverflow.com/questions/14822184/is-there-a-ceiling-equivalent-of-operator-in-python
        file_amt = -(len(self.transition) // -store_amt)
        self.assertEqual(len(os.listdir(matrix_dir)), file_amt)

        # Open previously written dir in read mode 
        all_messages = []
        with ProtoLogger(
            matrix_dir,
            mivp_agent_pb2.Transition,
            'r',) as log:
            
            pc = ProtoConsumer()
            dc = DictConsumer()

            c = 0
            while log.has_more():
              t = log.read(1)[0]
              pc._inject(t)
              dc._inject(t)

              self.assertEqual(pc.data, self.transition[c])
              self.assertEqual(
                dc.s1,
                translate.state_to_dict(self.transition[c].s1)
              )
              self.assertEqual(
                dc.s2,
                translate.state_to_dict(self.transition[c].s2)
              )
              self.assertEqual(
                dc.a,
                translate.action_to_dict(self.transition[c].a)
              )

              c += 1
        
        # Clean up
        clean_dir(matrix_dir, file_pattern="*.gz")

if __name__ == '__main__':
  unittest.main()