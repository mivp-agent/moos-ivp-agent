import socket
import pickle
import struct
import sys

'''
ModelBridgeServer (MODEL SIDE):
  - Receives:
    - MOOSDB Subscribed to (mainly for state construction)
  - Sends:
    - Heartbeat?
    - Actions:
      - IvP function actions (speed, course)
      - MOOSDB actions (var, value) pairs to post
ModelBridgeClient (MOOSDB SIDE):
  - Receives:
    - Actions:
      - See above
  - Sends:
    - Heartbeat?
    - MOOSDB variables
'''

# Socket Helpers ===========================

HEADER_SIZE=4
MAX_BUFFER_SIZE=8192

def recv_full(socket, timeout=None):
  total_data=[] # To keep track of each payload segment
  total_len=0 # Current len of payload
  size=sys.maxsize # Size of message assumed to be large for the loop to work
  size_data = sock_data = b'' # Empty byte string
  recv_size=MAX_BUFFER_SIZE

  # Preform an inital recv with a timeout and then disable the timeout
  try:
    socket.settimeout(timeout)
    sock_data = socket.recv(recv_size)
  finally:
    # Reset timeout regardless 
    socket.settimeout(None)
  
  while total_len < size:
    if not total_data:
      # If first message decode the header
      if len(sock_data)>HEADER_SIZE:
        size_data += sock_data
        # Unpack big-endian encoded size integer
        size = struct.unpack('>i', size_data[:HEADER_SIZE])[0]
        print(f'Got packet of size: {size}')

        # Update buffer size to be max the size of the message (with max of 81)
        recv_size = min(size, MAX_BUFFER_SIZE)

        # Add any data stored that was not used in header to our output list
        total_data.append(size_data[HEADER_SIZE:])
      else:
        size_data += sock_data
    else:
      # If header has been read already
      total_data.append(sock_data)
    total_len=sum([len(i) for i in total_data])

    # TODO: Slopy code below (changed b/c timeout edit)
    if total_len < size: 
      # Pull more data
      sock_data = socket.recv(recv_size)

  return b"".join(total_data)

def send_full(socket, data):
  # Create C struct (in python bytes)
  # '>i' specifies a big-endian encoded integer (a standard size of 4 bytes)
  packed_size = struct.pack('>i', len(data))
  # Concat the size (our 4 bytes header) and data then send
  socket.sendall(packed_size+data)

# Assertion Helpers ===========================

def checkAction(action):
  assert isinstance(action, dict), "Action must be a dict"
  assert "speed" in action, "Action must have key 'speed'"
  assert "course" in action, "Action must have key 'course'"
  assert "MOOS_VARS" in action, "Action must have key 'MOOS_VARS'"

def checkState(state):
  assert isinstance(state, dict), "State must be dict"

class ModelBridgeServer:
  def __init__(self, hostname="localhost", port=57722):
    self.host = hostname
    self.port = port

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    self._client = None
    self._address = None
  
  def __enter__(self):
    return self

  def start(self):
    self._socket.bind((self.host, self.port))
    self._socket.listen(0) # Only accept one connection

    # Wait for client
    self._client, self._address = self._socket.accept()
    print(f"Client connected from {self._address}.")
  
  def send_action(self, action):
    # Fail if no client connected
    if self._client is None:
      return False

    # Test submitted action
    checkAction(action)

    send_full(self._client, pickle.dumps(action))

    return True
  
  def listen_state(self):
    if self._client is None:
      return False

    state = pickle.loads(recv_full(self._client))

    checkState(state)

    return state

  def close(self):
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

class ModelBridgeClient:
  def __init__(self, hostname="localhost", port=57722):
    self.host = hostname
    self.port = port

    self._socket = None
  
  def __enter__(self):
    return self

  def connect(self, timeout=1):
    success = True
    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Attempt connection with timeout
    try:
      self._socket.settimeout(timeout)
      self._socket.connect((self.host, self.port))
    except (socket.timeout, ConnectionRefusedError) as e:
      # Signal failure in event of timeout
      success = False
    finally:
      # Reset timeout regardless
      self._socket.settimeout(None)
    
    # Return status
    return success
  
  def send_state(self, state):
    if self._socket is None:
      return False

    # Test submitted action
    checkState(state)

    send_full(self._socket, pickle.dumps(state))

    return True

  def listen_action(self, timeout=1):
    if self._socket is None:
      return False
    action = pickle.loads(recv_full(self._socket, timeout=timeout))

    checkAction(action)

    return action
  
  def close(self):
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()