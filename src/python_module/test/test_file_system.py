import os
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(current_dir, '.generated')

from mivp_agent.util.file_system import safe_clean, find_unique

class TestSafeClean(unittest.TestCase):

  def test_non_dir(self):
    path = os.path.join(generated_dir, 'file.txt')
    Path(path).touch()

    safe_clean(path)

    self.assertTrue(os.path.isfile(path))

    # Clean up
    os.remove(path)
  
  def test_basic(self):
    path = os.path.join(generated_dir, 'safe_clean')
    os.makedirs(path)

    safe_clean(path)

    self.assertTrue(os.path.isdir(path), "Safe clean removed top level directory")

    subdir1 = os.path.join(path, 'vname_henry')
    subdir2 = os.path.join(path, 'vname_echo')
    os.makedirs(subdir1)
    os.makedirs(subdir2)

    result = safe_clean(path)

    self.assertFalse(os.path.isdir(subdir1), "Safe clean did not remove empty directory")
    self.assertFalse(os.path.isdir(subdir2), "Safe clean did not remove empty directory")
    self.assertTrue(result, "Safe clean did not return true after fully cleaning directory")

    file1 = os.path.join(subdir1, 'file.some')
    file2 = os.path.join(subdir2, 'file.other')
    file3 = os.path.join(path, 'file.another')
    os.makedirs(subdir1)
    os.makedirs(subdir2)
    Path(file1).touch()
    Path(file2).touch()
    Path(file3).touch()

    result = safe_clean(path)

    self.assertTrue(os.path.isfile(file1))
    self.assertTrue(os.path.isfile(file2))
    self.assertTrue(os.path.isfile(file3))
    self.assertFalse(result)

    result = safe_clean(path, patterns=['*.some'])

    self.assertFalse(os.path.isdir(subdir1))
    self.assertTrue(os.path.isfile(file2))
    self.assertTrue(os.path.isfile(file3))
    self.assertFalse(result)

    result = safe_clean(path, patterns=['*.other', '*.another'])
    self.assertFalse(os.path.isdir(subdir1))
    self.assertFalse(os.path.isdir(subdir2))
    self.assertFalse(os.path.isfile(file3))
    self.assertTrue(result)

    os.rmdir(path)

class TestUnique(unittest.TestCase):

  def test_basic(self):
    name = find_unique(generated_dir, 'file', ext='.txt')
    self.assertEqual(name, 'file')

    path = os.path.join(generated_dir, 'file.txt')
    Path(path).touch()

    name = find_unique(generated_dir, 'file', ext='.txt')
    self.assertEqual(name, 'file-0')

    # Clean up
    os.remove(path)

if __name__ == '__main__':
  unittest.main()