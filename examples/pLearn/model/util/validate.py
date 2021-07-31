import os
from util.constants import PLEARN_ACTIONS

def check_model_dir(path):
  assert os.path.isdir(path), 'Model path must be directory'

  expected = []
  expected.append(os.path.join(path, 'environment.py'))
  for a in PLEARN_ACTIONS:
    expected.append(os.path.join(path, f'{a}.h5'))
  
  for f in expected:
    assert os.path.isfile(f), f'Expected to find file {f}'

  

