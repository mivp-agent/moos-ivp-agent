from genericpath import isdir
import os
import sys
import glob

def safe_clean(dir, patterns=[]):
  '''
  Recursively matches files by glob patterns and removes them. If after glob matched files are removed directories will be removed if empty.

  Args:
    dir (str): The path to the directory to be cleaned (this directory will **not** be removed)
    patterns (list of str): The patterns to match files against 
  Returns:
    True / False depending on if the directory is empty.
  '''
  if not os.path.isdir(dir):
    print(f"Warning: path given is not directory 'safe_clean({dir})'... skipping", file=sys.stderr)
    return None
  
  # First clean all subdirectories recursively
  for f in os.listdir(dir):
    filepath = os.path.join(dir, f)
    if os.path.isdir(filepath):
        if safe_clean(filepath, patterns=patterns):
          os.rmdir(filepath) # Remove if empty

  for p in patterns:
    files = glob.glob(f"{dir}/{p}")
    for f in files:
      filepath = os.path.join(dir, f)
      if not os.path.isdir(filepath):
        os.remove(filepath)

  if len(os.listdir(dir)) != 0:
    return False
  return True

def find_unique(path, ext=""):
  c = 0
  test_path = path
  while os.path.isdir(test_path) or os.path.isfile(test_path):
    test_path = f'{path}-{c}'
    c += 1
  
  return test_path