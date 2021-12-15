import os, sys
from pathlib import Path

from mivp_agent.const import DATA_DIRECTORY
from mivp_agent.log.directory import LogDirectory

from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto.proto_logger import ProtoLogger

# 1024 used for unit calculations
TWO_POW_TEN = 2**10
BYTES_PER_GIGA = 1073741824

def load_data_dir(print_error=False):
  '''
  This function is used to attempt to open the data storage directory in either the current working directory or under `DATA_DIRECTORY` in the current directory.

  Returns:
    `None` or an instance of `LogDirectory`
  '''

  data = None
  try:
    data = LogDirectory(DATA_DIRECTORY, must_exist=True)
  except RuntimeError:
    pass

  if data is None:
    try:
      data = LogDirectory(os.getcwd(), must_exist=True)
    except RuntimeError:
      pass

  if print_error and data is None:
    print(f'Error: Unable to load data directory in either under {DATA_DIRECTORY} current directory or by loading the current directory itself. Please check usage', file=sys.stderr)

  return data

def get_log(path):
  '''
  Returns:
    None or a ProtoLogger instance in read mode
  '''
  log = None
  try:
    log = ProtoLogger(path, Transition, mode='r')
  except:
    print(f'Error: Failed to load log at path: {path}', file=sys.stderr)
  return log

def size_of(path):
  '''
  Calculates the size of a directory's files.
  '''
  path = Path(path)

  return sum(f.stat().st_size for f in path.glob('**/*') if f.is_file())

POWER_LABELS = {0 : 'bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

def human_bytes(size):
  '''
  This function converts from bytes to rounded human readable format with KB, MB
  '''
  n = 0
  while size > TWO_POW_TEN:
    round(size, 2)
    size /= TWO_POW_TEN
    n += 1

  if n not in POWER_LABELS:
    return size, 'ERROR'

  return round(size, 2), POWER_LABELS[n]
