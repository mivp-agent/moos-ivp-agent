import os

from mivp_agent.log.const import META_DIR, MODELS_DIR
from mivp_agent.log.metadata import LogMetadata

class LogDirectory:
  def __init__(self, path, must_exist=False):
    self._path = path

    assert not os.path.isfile(self._path), 'There is a file in the place of the log directory, please remove this file if you wish a log directory to be created'

    self._meta_path = os.path.join(self._path, META_DIR)
    self._models_path = os.path.join(self._path, MODELS_DIR)

    # Initialize if it doesn't exist
    if not os.path.isdir(self._path):
      if must_exist:
        raise RuntimeError('Could not find specified log directory')
      self._init_directory()

    self.meta = LogMetadata(self._path)

  def _init_directory(self):
    os.makedirs(self._path)
    os.makedirs(self._meta_path)
    os.makedirs(self._models_path)
  
  def path(self):
    return self._path

  def task_dir(self, task):
    path = os.path.join(self._path, task)

    if not os.path.isdir:
      os.makedirs(path)
    
    return path
  
  def models_dir(self):
    return self._models_path