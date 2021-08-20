import socket
import pickle
import struct
import sys
from typing import Iterable
import traceback

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

TYPE_CTRL=0
TYPE_ACTION=1
TYPE_MUST_POST=2
TYPE_STATE=3

TYPES = (TYPE_CTRL, TYPE_ACTION, TYPE_MUST_POST, TYPE_STATE)

HEADER_SIZE=4
MAX_BUFFER_SIZE=8192

def recv_full(connection, timeout=None, return_read=False):
  messages = []
  current_len = None
  last_read = None
  total_read = None
  # Create byte string for storing the header in
  tmp_data = b''

  # Attempt first receive with timeout
  try:
    connection.settimeout(timeout)
    tmp_data = connection.recv(MAX_BUFFER_SIZE)
  finally:
    # Cleanup regardless
    connection.settimeout(None)
  
  last_read = len(tmp_data)
  total_read = last_read

  # If buffer read was full, call until not full
  # Attempt to empty the recv queue
  while last_read == MAX_BUFFER_SIZE:
    print('WARNING: Got max buffer attempting to clear queue...')
    try:
      # Non blocking, just checking if there is more in queue
      connection.settimeout(0.001) 
      tmp_data += connection.recv(MAX_BUFFER_SIZE)

      last_read = len(tmp_data)
      total_read += last_read
    except socket.timeout:
      last_read = 0
    finally:
      connection.settimeout(None)


  # While we have data to process into messages
  while len(tmp_data) != 0:
    # Get more data if message is incomplete
    if (current_len is None and len(tmp_data) < HEADER_SIZE) or (current_len is not None and len(tmp_data) < current_len): 
      tmp_data += connection.recv(MAX_BUFFER_SIZE)
      
      last_read = len(tmp_data)
      total_read += last_read

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

  if return_read:
    return messages, total_read
  return messages


def send_full(connection, data, type):
  assert type < 5
  # Create C struct (in python bytes)
  # '>i' specifies a big-endian encoded integer (a standard size of 4 bytes)
  # '>ii' does two big-endian numbers
  packed_size = struct.pack('>i', len(data))
  # Concat the size (our 8 bytes header) and data then send
  result = connection.sendall(packed_size+data)
  assert result is None

# Assertion Helpers ===========================

def checkFloat(var, error_string):
  try:
    return float(var)
  except ValueError:
    raise ValueError(error_string)

def checkInstruction(instr):
  assert isinstance(instr, dict), "Instruction must be a dict"

  assert "speed" in instr, "Instruction must have key 'speed'"
  instr['speed'] = checkFloat(instr['speed'], "Instruction['speed'] must be a float")
  
  assert "course" in instr, "Action must have key 'course'"
  instr['course'] = checkFloat(instr['course'], "Instruction['course'] must be a float")

  assert "posts" in instr, "Instruction must have key 'posts'"
  assert isinstance(instr["posts"], dict), "posts must be a dict"

  assert "ctrl_msg" in instr, "Instruction must have key 'ctrl_str'"
  assert isinstance(instr['ctrl_msg'], str), 'ctrl_msg must be string'

def checkState(state):
  assert isinstance(state, dict), "State must be dict"
  assert "NAV_X" in state, "State must have 'NAV_X' key"
  assert "NAV_Y" in state, "State must have 'NAV_Y' key"

def checkMustPost(must_post):
  assert isinstance(must_post, dict), "TYPE_MUST_POSTs must have type"

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
    self.last_read = 0

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
    print(f"Client connected from {self._address}")
  
  def send_instr(self, instr):
    # Test submitted instruction
    checkInstruction(instr)

    # Fail if no client connected
    if self._client is None:
      return False

    try:
      send_full(self._client, pickle.dumps(instr), TYPE_ACTION)
    except ConnectionResetError:
      # Client has left
      self.close_client()
      return False

    return True

  def listen_state(self, timeout=None):
    if self._client is None:
      return False

    try:
      msgs, self.last_read = recv_full(self._client, timeout=timeout, return_read=True)
    except socket.timeout:
      return False

    assert len(msgs) == 1, 'State should only come one at a time'
    state = pickle.loads(msgs[0])
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
      send_full(self._socket, pickle.dumps(state), TYPE_STATE)
    except BrokenPipeError:
      # Server has disconnected, reset
      self.close()
      return False

    return True

  def listen(self, timeout=0.0005):
    if self._socket is None:
      return False

    try:
      msgs = recv_full(self._socket, timeout=timeout)
    except socket.timeout:
      return False

    assert len(msgs) == 1, 'Instructions should only come one at a time'
    instr = pickle.loads(msgs[0])

    checkInstruction(instr)

    return instr
  
  def close(self):
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()