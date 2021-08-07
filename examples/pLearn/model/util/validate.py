import os
import re
from util.constants import PLEARN_ACTIONS

ITERATION_PATH_PATTERN = 'iteration_[0-9]+'

def check_model_dir(path):
  assert os.path.isdir(path), 'Model path must be directory'

  expected = []
  expected.append(os.path.join(path, '../environment.py'))
  for a in PLEARN_ACTIONS:
    expected.append(os.path.join(path, f'{a}.h5'))
  
  for f in expected:
    assert os.path.isfile(f), f'Expected to find file {f}'

def check_test_dir(path):
  assert os.path.isdir(path), "Test directory must be a path"

  for subpath in os.listdir(path):
    if subpath == '__pycache__':
      continue
      
    full_subpath = os.path.join(path, subpath)
    if os.path.isdir(full_subpath):
      # Check that it is an iteration folder
      if not re.match(ITERATION_PATH_PATTERN, subpath):
        raise RuntimeError(f"Expected test subdirectories to be of form {ITERATION_PATH_PATTERN} found '{subpath}'")
      
      # Check that it is a valid model directory
      check_model_dir(full_subpath)


