import os
import sys
import time
import gzip

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
  def __init__(self, path, type, mode='r', max_msgs=1000):
    assert mode in MODES_SUPPORTED, f"Unsupported mode '{mode}'"

    if mode == MODE_WRITE:
      assert not os.path.isdir(path), "Provided path is existing directory"
      assert not os.path.isfile(path), "Provided path is existing file"
    if mode == MODE_READ:
      assert os.path.isdir(path), "Provided path is not existing directory"
      assert len(os.listdir(path)) != 0, "Provided directory is empty"
      for f in os.listdir(path):
        if f[-3] != '.gz':
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
  
  def write(self, message):
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
      save_path = os.path.join(self._path, str(time.time())+'.gz')

      # Use gzip in write bytes mode
      with gzip.open(save_path, 'wb') as f:
        f.write(self._buffer)

      # Clean up
      self._msg_count = 0
      self._buffer.clear()
    except Exception as e:
      print(e, file=sys.stderr)
      print("Warning: unable to write to gzip file, deffering write", file=sys.stderr)

  # Not 100% if I need the following
  def __enter__(self):
    pass

  def __exit__(self):
    self.close()
  
  def close(self):
    if self._mode == MODE_WRITE:
      self._write_buffer()
    elif self._mode == MODE_READ:
      raise RuntimeError('Implement')
    else:
      raise RuntimeError(f'Unexpected mode "{self._mode}" on close')