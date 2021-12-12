import os
import sys
from pathlib import Path

from mivp_agent.util.file_system import find_unique
from mivp_agent.log.const import CORE_DIRS

from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto.proto_logger import ProtoLogger

class RegistryDatum:
  '''
  This class is for managing a "registry" of MissionManager session ids to assure that they are unique with respect to a certain logging directory.

  **NOTE:** The following is **NOT** thread safe. It is unlikely to fail silently, but still need to be cautious.
  '''
  def __init__(self, path):
    '''
    Args:
      path (str): The registry directory.
    '''
    self.path = path

    if not os.path.isdir(self.path):
      try:
        os.makedirs(self.path)
      except FileExistsError:
        return FileExistsError('There is a file in the place of the specified registry directory')

  def validate(self):
    for p in os.listdir(self.path):
      if not os.path.isfile(p):
        print('WARNING: There is a directory in the metadata registry. This indicates a corrupted registry.', file=sys.stderr)

  def has_session(self, id):
    return os.path.isfile(os.path.join(self.path, f'{id}.session'))

  def list_sessions(self):
    for p in os.listdir(self.path):
      if os.path.isfile(os.path.join(self.path, p)):
        yield p
  
  def session_count(self):
    return len(list(self.list_sessions()))
  
  def register(self, name):
    # Find a unique name
    id = find_unique(self.path, name, ext='.session')

    # Register it
    entry = os.path.join(self.path, f'{id}.session')
    Path(entry).touch(exist_ok=False)

    return id

class LogMetadata:
  '''
  The following is for managing metadata associated with a perticular logging directory.
  '''
  def __init__(self, path):
    '''
    Args:
      path (str): The logging directory.
    '''
    self._data_dir = path
    self._path = os.path.join(path, '.meta')

    # We don't init here because .meta is a signal that the directory is a valid logging directory
    assert os.path.isdir(self._path), "Metadata directory not found, is this a valid log directory?"

    self.registry = RegistryDatum(os.path.join(self._path, 'registry'))
  
  def get_logs(self, id):
    '''
    This function is used to get the logs associated with a specific session id
    '''
    # Check if the session id is valid in this context
    if not self.registry.has_session(id):
      return None
    
    logs = []
    for subdir in os.listdir(self._data_dir):
      if subdir not in CORE_DIRS:
        # We have a task folder
        session_path = os.path.join(
          self._data_dir,
          subdir,
          id
        )

        if os.path.isdir(session_path):
          for log_dir in os.listdir(session_path):
            path = os.path.join(session_path, log_dir)
            logs.append(ProtoLogger(path, Transition, mode='r'))
    
    return logs

  
