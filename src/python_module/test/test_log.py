import os
from typing import Pattern
import unittest
from pathlib import Path

current_dir = os.path.dirname(os.path.realpath(__file__))
generated_dir = os.path.join(current_dir, '.generated')

from mivp_agent.log.metadata import LogMetadata, RegistryDatum
from mivp_agent.util.file_system import safe_clean

class TestMetadata(unittest.TestCase):

  def test_interface(self):
    meta_dir = os.path.join(generated_dir, '.meta')
    os.makedirs(meta_dir)

    # Test we do not fail on a new directory
    m = LogMetadata(generated_dir)

    self.assertEqual(m.registry.register('my_name'), 'my_name')
    self.assertNotEqual(m.registry.register('my_name'), 'my_name')

    safe_clean(generated_dir, patterns=['*.session'])

if __name__ == '__main__':
  unittest.main()