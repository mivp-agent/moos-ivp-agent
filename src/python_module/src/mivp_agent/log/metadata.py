import os
import sys
from pathlib import Path

from mivp_agent.util.file_system import find_unique

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
    self._path = os.path.join(path, '.meta')

    # We don't init here because .meta is a signal that the directory is a valid logging directory
    assert os.path.isdir(self._path), "Metadata directory not found, is this a valid log directory?"

    self.registry = RegistryDatum(os.path.join(self._path, 'registry'))
  
