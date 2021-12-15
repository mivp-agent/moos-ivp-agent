import os, sys
import argparse

from mivp_agent.cli.util import load_data_dir, size_of, human_bytes
from mivp_agent.const import DATA_DIRECTORY
from mivp_agent.log.directory import LogDirectory

class Info:
  def __init__(self, parser):
    self.parser = parser

    # Setup parser
    self.parser.add_argument('-a', '--all', action='store_true', help="Used to print extensive information.")

    self.parser.set_defaults(func=self.do_it)

  def do_it(self, args):
    data = load_data_dir()

    print(f'Path: {data.path()}\n')
    print(f'Sessions: {data.meta.registry.session_count()}')
    if args.all:
      for session in data.meta.registry.list_sessions():
        print(f' - {session}')

    size, label = human_bytes(size_of(data.path()))
    print(f'Folder Size: {size} {label}')
