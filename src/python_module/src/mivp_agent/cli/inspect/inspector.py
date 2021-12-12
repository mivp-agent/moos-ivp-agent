import os, sys
from tqdm import tqdm

from mivp_agent.cli.util import get_log

from .import tdist

class Inspector:
  def __init__(self, parser):
    self.parser = parser

    parser.add_argument('log', nargs=1, help='The log file to preform the requested operations on. Can be the name of a session or a path.')

    self.parser.set_defaults(func=self.do_it)

  def handle_log(self, log, args):
    g = tdist.TransitionDist()

    last_idx = None
    progress_bar = tqdm(total=log.total_files(), desc="Log Files")
    while log.has_more():
      t = log.read(1)[0]
      g._inject(t)

      if log.current_file() == 10:
        break

      # If we are on a new file update the progress bar
      if log.current_file() != last_idx:
        progress_bar.update(1)
        last_idx = log.current_file()
    
    g._get_fig().show()

  def do_it(self, args):
    '''
    This is the function called by argparse to kick off the processing
    '''
    assert os.path.isdir(args.log[0]), 'To use the inspect command you must point it to a log folder. See usage with --help'

    log = get_log(args.log[0])

    if log is None:
      return

    self.handle_log(log, args)