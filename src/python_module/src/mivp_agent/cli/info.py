from genericpath import exists
import os, sys
import argparse

from mivp_agent.const import DATA_DIRECTORY
from mivp_agent.log.directory import LogDirectory

class Info:
  def __init__(self, parser):
    self.parser = parser

    self.parser.set_defaults(func=self.do_it)
  
  def do_it(self, args):
    log = None
    try:
      log = LogDirectory(DATA_DIRECTORY, must_exist=True)
    except RuntimeError:
      print('Error: Unable to find log directory', file=sys.stderr)
    
    print(f'Sessions: {log.meta.registry.session_count()}')
    