from mivp_agent.proto import translate
from google.protobuf.message import Message

class Consumer:
  '''
  This is an abstract class meant to help with providing a general interface to consume transition data.
  '''

  def __init__(self, *args, **kwargs):
    if self._has_setup():
      self.setup(*args, **kwargs)

  def _has_setup(self):
    try:
      test = self.setup
      return True
    except AttributeError:
      return False

  def _inject(self, data):
    assert isinstance(data, Message)

    pb2_run = False
    try:
      self.pb2_data(data)
      pb2_run = True
    except AttributeError as e:
      pass

    if not pb2_run:
      try:
        s1 = translate.state_to_dict(data.s1)
        a = translate.action_to_dict(data.a)
        s2 = translate.state_to_dict(data.s2)
        self.dict_data(s1, a, s2)
      except AttributeError as e:
        raise AttributeError('No consumer method found to parse data') from None

    return pb2_run
