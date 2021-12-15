import os
import sys
import time
import gzip

from google.protobuf import message

from mivp_agent.util import packit

from google.protobuf.message import Message
from google.protobuf.reflection import GeneratedProtocolMessageType

MODE_READ = 'r'
MODE_WRITE = 'w'

MODES_SUPPORTED = (
  MODE_WRITE,
  MODE_READ
)

class ProtoLogger:
  '''
  max_msgs will not be used in MODE_READ
  '''
  def __init__(self, path, type, mode='r', max_msgs=1000):
    assert mode in MODES_SUPPORTED, f"Unsupported mode '{mode}'"

    if mode == MODE_WRITE:
      assert not os.path.isdir(path), "Provided path is existing directory"
      assert not os.path.isfile(path), "Provided path is existing file"
    if mode == MODE_READ:
      assert os.path.isdir(path), "Provided path is not existing directory"
      assert len(os.listdir(path)) != 0, "Provided directory is empty"
      for f in os.listdir(path):
        if f[-3:len(f)] != '.gz':
          raise RuntimeError(f"ProtoLogger dir contains non gzip file '{f}'")

    assert isinstance(type, GeneratedProtocolMessageType), "Type must be a generated MessageType class"

    assert isinstance(max_msgs, int), "Buffer size must be integer"
    assert max_msgs > 0, "Buffer size must be positive integer"

    self._path = path
    self._type = type
    self._mode = mode

    self._max_msgs = max_msgs
    self._msg_count = 0

    self._buffer = bytearray()

    # Open the directory
    if self._mode == MODE_WRITE:
      os.makedirs(self._path, exist_ok=False)
      self._time_stamp = str(round(time.time()))
      self._current_idx = 0
    if self._mode == MODE_READ:
      # Read save directory
      self._gzip_files = os.listdir(self._path)
      
      # Sort by index
      index = lambda x: int(x.split('.')[0].split('-')[1])
      self._gzip_files = sorted(self._gzip_files, key=index)

      # Current file index in self._gzip_files
      self._gzip_idx = 0

      # Messages from the most recently read file
      self._current_messages = []

  def path(self):
    return self._path

  def write(self, message):
    '''
    Method used to write protobuf messages of type specified in __init__ to a buffer. The buffer will be written to a .gz file when the length is greater than or equal to `max_messages` or open close() / context manager exit.

    Args:
      message (Message): A protobuf message of type specified in __init__
    '''

    assert self._mode == MODE_WRITE, "Method add() only supported in write mode"
    assert isinstance(message, Message), "Message must be protobuf message"
    assert isinstance(message, self._type), "Message not of type specified by constructor"

    self._buffer.extend(packit.pack(message.SerializeToString()))
    self._msg_count += 1

    if self._msg_count >= self._max_msgs:
      self._write_buffer()

  def _write_buffer(self):
    # The below might happen due to close()
    if self._msg_count == 0:
      return

    # Incase something goes wrong, don't crash
    try:
      save_path = os.path.join(self._path, f'{self._time_stamp}-{self._current_idx}.gz')

      # Use gzip in write bytes mode
      with gzip.open(save_path, 'wb') as gz:
        gz.write(self._buffer)

      # Clean up
      self._current_idx += 1
      self._msg_count = 0
      self._buffer.clear()
    except Exception as e:
      print(e, file=sys.stderr)
      print("Warning: unable to write to gzip file, deffering write", file=sys.stderr)
  
  def has_more(self):
    assert self._mode == MODE_READ, "Method has_more() only supported in write mode"

    return len(self._current_messages) != 0 or self._gzip_idx != len(self._gzip_files)
  
  def total_files(self):
    assert self._mode == MODE_READ, "Method total_files() only supported in write mode"

    return len(self._gzip_files)
  
  def current_file(self):
    assert self._mode == MODE_READ, "Method current_file() only supported in write mode"

    return self._gzip_idx

  def read(self, n: int):
    '''
    Method is used to read a specified number of messages from disk.

    Args:
      n (int): Number of messages to read
    Returns:
      A python list of protobuf messages. The length of this list will be less than or equal to `n`
    '''
    assert self._mode == MODE_READ, "Method read() only supported in write mode"

    messages_out = []
    while len(messages_out) < n:
      # See if we have messages to parse from previously read gz
      if len(self._current_messages) == 0:
        # Check if we have exhausted all files
        if self._gzip_idx == len(self._gzip_files):
          break # Out of messages

        # If there are more gzip files, read next
        filepath = os.path.join(self._path, self._gzip_files[self._gzip_idx])
        with gzip.open(filepath, mode='rb') as gz:
          buffer = gz.read()

          # Get binary messages and parse
          bmsgs = packit.unpack_buffer(buffer)
          for bmsg in bmsgs:
            msg = self._type()
            msg.ParseFromString(bmsg)

            self._current_messages.append(msg)
          
          # Indicate this file has been read
          self._gzip_idx += 1
      
      # Here we should have more messages, find out how many message we should add to message_out
      amt = min(n - len(messages_out), len(self._current_messages))

      # Add that amount to the returned list
      messages_out.extend(self._current_messages[:amt])

      # Remove that amount from the queue thing
      self._current_messages = self._current_messages[amt:]
    
    return messages_out

  # Not 100% if I need the following
  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, tracebac):
    self.close()
  
  def close(self):
    if self._mode == MODE_WRITE:
      self._write_buffer()
    elif self._mode == MODE_READ:
      pass # No file pointers to close
    else:
      raise RuntimeError(f'Unexpected mode "{self._mode}" on close')