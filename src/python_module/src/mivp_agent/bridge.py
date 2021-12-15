import socket
import pickle
import struct
import sys
import traceback

from mivp_agent.util.validate import validateInstruction, validateState
from mivp_agent.util.parse import parse_report
from mivp_agent.const import KEY_EPISODE_MGR_REPORT

HEADER_SIZE=4
MAX_BUFFER_SIZE=8192

def recv_full(connection):
  messages = []
  current_len = None
  last_read = None
  total_read = None
  # Create byte string for storing the header in
  tmp_data = b''

  tmp_data = connection.recv(MAX_BUFFER_SIZE)
  last_read = len(tmp_data)
  total_read = last_read

  # If buffer read was full, call until not full
  # Attempt to empty the recv queue
  while last_read == MAX_BUFFER_SIZE:
    print('WARNING: ModelBridge got max buffer size', file=sys.stderr)

  # While we have data to process into messages
  while len(tmp_data) != 0:
    # Get more data if message is incomplete
    if (current_len is None and len(tmp_data) < HEADER_SIZE) or (current_len is not None and len(tmp_data) < current_len): 
      orig_timeout = connection.gettimeout()
      connection.settimeout(None)
      tmp_data += connection.recv(MAX_BUFFER_SIZE)
      connection.settimeout(orig_timeout)
      
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

  return messages


def send_full(connection, data):
  # Create C struct (in python bytes)
  # '>i' specifies a big-endian encoded integer (a standard size of 4 bytes)
  # '>ii' does two big-endian numbers
  packed_size = struct.pack('>i', len(data))
  # Concat the size (our 8 bytes header) and data then send
  result = connection.sendall(packed_size+data)
  assert result is None

class ModelBridgeServer:
  def __init__(self, hostname="localhost", port=57721, max_listen=None):
    self.host = hostname
    self.port = port

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Line below reuses the socket address if previous socket closed but improperly
    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self._socket.bind((self.host, self.port))
    self._socket.settimeout(0.0) # We will handle the errors from this

    if max_listen is None:
      max_listen = 0

    self._socket.listen(max_listen)
    self._clients = {}

  def __enter__(self):
    return self

  def accept(self):
    # Accept any connection
    try:
      conn, addr = self._socket.accept()
      assert addr not in self._clients

      conn.settimeout(0.0)
      self._clients[addr] = conn
    except BlockingIOError:
      return None 

    return addr

  def send_instr(self, addr, instr):
    if addr not in self._clients:
      raise RuntimeError('Address not in client list')

    validateInstruction(instr)
    send_full(self._clients[addr], pickle.dumps(instr))
    return True

  def listen(self, addr):
    if addr not in self._clients:
      raise RuntimeError('Address not in client list')

    try:
      msgs = recv_full(self._clients[addr])
    except BlockingIOError:
      return None 

    assert len(msgs) == 1, 'State should only come one at a time'
    state = pickle.loads(msgs[0])

    if state[KEY_EPISODE_MGR_REPORT] is not None:
      state[KEY_EPISODE_MGR_REPORT] = parse_report(state[KEY_EPISODE_MGR_REPORT])

    return state

  def close_clients(self):
    for client in self._clients:
      self._clients[client].close()

  def close(self):
    self.close_clients()
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()

class ModelBridgeClient:
  def __init__(self, hostname="localhost", port=57721):
    self.host = hostname
    self.port = port

    self._socket = None
  
  def __enter__(self):
    return self

  def is_connected(self):
    return self._socket is not None

  def connect(self):
    if self._socket is not None:
      raise RuntimeError("Clients should not be connect more than once")

    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Attempt connection with timeout
    try:
      # Not 0.0 timeout cause connect is strang with that
      self._socket.settimeout(0.001)
      self._socket.connect((self.host, self.port))
      self._socket.settimeout(0.0)
    except (socket.timeout, ConnectionRefusedError) as e:
      # Clean up socket
      self._socket.close()
      self._socket = None
      # Signal failure in event of timeout
      return False
    # Return status
    return True
  
  def send_state(self, msg):
    if self._socket is None:
      return False

    validateState(msg)
    send_full(self._socket, pickle.dumps(msg))
    return True

  def listen(self):
    if self._socket is None:
      return False

    try:
      msgs = recv_full(self._socket)
    except BlockingIOError:
      return False
    
    assert len(msgs) == 1, 'Instructions should only come one at a time'
    instr = pickle.loads(msgs[0])

    validateInstruction(instr)

    return instr
  
  def close(self):
    if self._socket is not None:
      self._socket.close()
  
  def __exit__(self, exc_type, exc_value, traceback):
    self.close()