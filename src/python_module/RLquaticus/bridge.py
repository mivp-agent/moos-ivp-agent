import socket
import pickle
import struct
import sys
from typing import Iterable

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
  messages = []
  current_len = None
  # Create byte string for storing the header in
  tmp_data = b''

  # Attempt first receive with timeout
  try:
    socket.settimeout(timeout)
    tmp_data = socket.recv(MAX_BUFFER_SIZE)
  finally:
    # Cleanup regardless
    socket.settimeout(None)

  # While we have data to process into messages
  while len(tmp_data) != 0:
    # Get more data if needed
    if (current_len is None and len(tmp_data) < HEADER_SIZE) or (current_len is not None and len(tmp_data) < current_len): 
      tmp_data += socket.recv(MAX_BUFFER_SIZE)

    if current_len is None:
      # We should be looking for a header

      if len(tmp_data) >= HEADER_SIZE:
        # We can construct a header (current_len)
        current_len = struct.unpack('>i', tmp_data[:HEADER_SIZE])[0]
        
        # Remove header data from our data store
        tmp_data = tmp_data[HEADER_SIZE:]
    
    # Not else b/c previous clause might have constructed it
    if current_len is not None:
      # We should be looking for a message
      if len(tmp_data) >= current_len:
        # We can construct a packed
        messages.append(tmp_data[:current_len])

        # Remove the packet just constructed from out data store
        tmp_data = tmp_data[current_len:]
        current_len = None # Signal we are looking for another header

  return messages


def send_full(socket, data):
  # Create C struct (in python bytes)
  # '>i' specifies a big-endian encoded integer (a standard size of 4 bytes)
  packed_size = struct.pack('>i', len(data))
  # Concat the size (our 4 bytes header) and data then send
  result = socket.sendall(packed_size+data)
  assert result is None

# Assertion Helpers ===========================

def checkFloat(var, error_string):
  try:
    return float(var)
  except ValueError:
    raise ValueError(error_string)

def checkAction(action):
  assert isinstance(action, dict), "Action must be a dict"

  assert "speed" in action, "Action must have key 'speed'"
  action['speed'] = checkFloat(action['speed'], "action['speed'] must be a float")
  
  assert "course" in action, "Action must have key 'course'"
  action['course'] = checkFloat(action['course'], "action['course'] must be a float")

  assert "MOOS_VARS" in action, "Action must have key 'MOOS_VARS'"
  assert isinstance(action["MOOS_VARS"], tuple), "MOOS_VARS must be a tuple"

def checkState(state):
  assert isinstance(state, dict), "State must be dict"
  assert "NAV_X" in state, "State must have 'NAV_X' key"
  assert "NAV_Y" in state, "State must have 'NAV_Y' key"

class ModelBridgeServer:
  def __init__(self, hostname="localhost", port=57722):
    self.host = hostname
    self.port = port

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Line below reuses the socket address if previous socket closed but improperly
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._socket.bind((self.host, self.port))

    self._client = None
    self._address = None

  def __enter__(self):
    return self

  def accept(self):
    # Close current connection if we have one
    if self._client is not None:
      self._client.close()
      self._client = None


    self._socket.listen(0) # Only accept one connection
    # Wait for client
    self._client, self._address = self._socket.accept()
    print(f"Client connected from {self._address}.")
  
  def send_action(self, action):
    # Test submitted action
    checkAction(action)

    # Fail if no client connected
    if self._client is None:
      return False

    try:
      send_full(self._client, pickle.dumps(action))
    except ConnectionResetError:
      # Client has left
      self.close_client()
      return False

    return True

  def listen_state(self, timeout=None):
    if self._client is None:
      return False

    try:
      msgs = recv_full(self._client, timeout=timeout)
    except socket.timeout:
      return False

    state = pickle.loads(msgs[len(msgs)-1]) # Only use most recent state
    checkState(state)

    return state

  def close_client(self):
    if self._client is not None:
      self._client.close()

  def close(self):
    self.close_client()
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
    if self._socket is not None:
      raise RuntimeError("Clients should not be connect more than once")

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Attempt connection with timeout
    try:
      self._socket.settimeout(timeout)
      self._socket.connect((self.host, self.port))
      # Dont hold onto the timeout if we succeed
      self._socket.settimeout(None)
    except (socket.timeout, ConnectionRefusedError) as e:
      # Clean up socket
      self._socket.close()
      self._socket = None
      # Signal failure in event of timeout
      return False
    
    # Return status
    return True
  
  def send_state(self, state):
    if self._socket is None:
      return False

    # Test submitted action
    checkState(state)

    try:
      send_full(self._socket, pickle.dumps(state))
    except BrokenPipeError:
      # Server has disconnected, reset
      self.close()
      return False

    return True

  def listen_action(self, timeout=0.0005):
    if self._socket is None:
      return False

    try:
      msgs = recv_full(self._socket, timeout=timeout)
    except socket.timeout:
      return False
    action = pickle.loads(msgs[len(msgs)-1])

    checkAction(action)

    return action
  
  def close(self):
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()