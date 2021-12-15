import struct
import unittest

from mivp_agent.util import packit

class TestPackitEncode(unittest.TestCase):
  def test_basic(self):
    message_str = 'MyTesting123&*219!___ String'
    message_bytes = message_str.encode('utf-8')
    
    # Make sure regular strings fail
    with self.assertRaises(AssertionError):
      packit.pack(message_str)
    
    # Byte strings should pass
    packed = packit.pack(message_bytes)

    # Test return is valid byte string through duck typing
    packed.decode()

    # Parse length and do assertions
    packed_len = struct.unpack('>L', packed[:packit.HEADER_SIZE])[0]
    self.assertTrue(isinstance(packed_len, int))
    self.assertEqual(len(message_bytes), packed_len)

    # Lambda function to return whole packed byte string
    more = lambda: packed  

class TestPackitDecode(unittest.TestCase):
  @classmethod
  def setUpClass(cls) -> None:
      cls.message_str = 'MyTesting123&*219!___ String' 
      cls.message_bytes = cls.message_str.encode('utf-8')
      cls.message_packed = packit.pack(cls.message_bytes)
      return super().setUpClass()
  
  def test_one_full(self):
    # Parse with supplying full message
    more = lambda: self.message_packed
    unpacked_msgs = packit.unpack(more)
    
    self.assertEqual(len(unpacked_msgs), 1)
    
    unpacked_msg = unpacked_msgs[0]
    self.assertTrue(isinstance(unpacked_msg, bytearray))
    
    unpacked_str = unpacked_msg.decode('utf-8')
    self.assertEqual(self.message_str, unpacked_str)
  
  def test_multiple_full(self):
    for x in range(1,20):
      # Return full byte string with multiple messages
      more = lambda: self.message_packed * x
      unpacked_msgs = packit.unpack(more)

      self.assertEqual(len(unpacked_msgs), x)

      for msg in unpacked_msgs:
        self.assertTrue(isinstance(msg, bytearray))
        msg_str = msg.decode('utf-8')
        self.assertEqual(msg_str, self.message_str)
  
  def test_multiple_partial(self):
    # Outer loop same as above
    for x in range(1, 20):
      # Here we vary the amount of bytes returned by more()
      for amt in range(1, 100):
        self.buffer = self.message_packed * x
        def more():
          # Get a bit of the message to return
          out = self.buffer[:amt]
          # Remove this from the buffer
          self.buffer = self.buffer[amt:]

          return out
        
        # NOTE: The below differs from previous test b/c we are not always returning the full data from more() and unpack() will stop if it parses a message and there are no remaining bits
        all_messages = []
        unpacked_msgs = packit.unpack(more)
        while len(unpacked_msgs) != 0:
          all_messages += unpacked_msgs
          unpacked_msgs = packit.unpack(more)

        self.assertEqual(len(all_messages), x)

        for msg in all_messages:
          self.assertTrue(isinstance(msg, bytearray))
          msg_str = msg.decode('utf-8')
          self.assertEqual(msg_str, self.message_str)
  
  def test_once(self):
    buffer = self.message_packed
    msgs = packit.unpack_buffer(buffer)
    self.assertEqual(len(msgs), 1)
    self.assertTrue(isinstance(msgs[0], bytearray))
    self.assertEqual(msgs[0].decode('utf-8'), self.message_str)

    # Assert runtime error on extra bytes
    buffer += b'h'
    with self.assertRaises(RuntimeError):
      packit.unpack_buffer(buffer)
    
    

if __name__ == '__main__':
  unittest.main()