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

def find_unique(path, name, ext=""):
  '''
  This a function for making sure that a file name is unique under a given path. The function will append numbers for example `my_file-0.txt` or `my_file-1.txt` until a unique name, which does not conflict with existing files is found. This function does not preform any file creation.

  **NOTE:** For efficiency, this should not be used as the primary means of unique-ness in naming. Especially in directories which have many files.

  Args:
    path (str): The path to test names under.
    name (str): The starting name to base generation on.
    ext (str): The file extension.

  Returns:
    The input name if it was unique under the given path, or a modified unique version.
  '''
  exists = lambda path: os.path.isdir(path) or os.path.isfile(path)

  c = 0
  test_name = name
  while exists(os.path.join(path, f'{test_name}{ext}')):
    test_name = f'{name}-{c}'
    c += 1
  
  return f'{test_name}'