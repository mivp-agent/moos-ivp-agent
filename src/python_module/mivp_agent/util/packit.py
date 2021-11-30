import struct

HEADER_SIZE=4

def unpack(more):
  '''
  This method is used to parse messages in a stream which have been previously packed using the associated pack(data) method.

  Args:
    more (callable): Should return a python byte string when called
  Returns:
    messages (list): A list of unpacked messages in byte string format. This list can be empty if a more() call returns an empty byte string.
  '''

  assert callable(more), '"more" argument is not callable'

  tmp_data = b'' # To store data being processed
  messages = [] # To store complete messages 

  # When not None we are parsing a message
  current_len = None

  # Get some initial data
  tmp_data = more()
  
  if len(tmp_data) == 0:
    return []

  # While we have data to process into messages
  while len(tmp_data) != 0:
    # If necessary, get more data for the header
    while len(tmp_data) < HEADER_SIZE:
      tmp_data += more()
    
    # We will have a full header here, parse it into current_len
    current_len = struct.unpack('>L', tmp_data[:HEADER_SIZE])[0]
    
    # Remove the parsed header from tmp_data
    tmp_data = tmp_data[HEADER_SIZE:]

    # If necessary, get more data for our message
    while len(tmp_data) < current_len:
      tmp_data += more()

    # Here we will have a full message, parse it into messages
    messages.append(tmp_data[:current_len])

    # Remove the message data we just parsed from tmp_data
    tmp_data = tmp_data[current_len:]

    # NOTE: tmp_data might have more information, this will be parsed in the next pass

  return messages


def pack(message):
  '''
  Returns:
    A python byte string or byte array containing the input message and a 4 byte header containing the length of the message
  '''
  assert isinstance(message, bytes) or isinstance(message, bytearray), "message argument must either be 'bytes' or 'bytearray'"

  # Create C struct (in python bytes)
  # '>i' specifies a big-endian encoded integer (a standard size of 4 bytes)
  # '>LL' does two big-endian longs
  packed_size = struct.pack('>L', len(message))
  return b''+packed_size+message