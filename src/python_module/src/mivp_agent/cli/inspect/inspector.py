import os, sys
from tqdm import tqdm

from mivp_agent.cli.util import get_log

from .graphers import tdist, flagdist, prcnt_success

options = {}
options['tdist'] = {
  'class': tdist.TransitionDist,
  'help': 'This command show a scatter plot of the transition distance (the distance between s1 and s2)'
}
options['flagdist'] = {
  'class': flagdist.FlagDist,
  'help': 'Plot the min distance that the agent gets to the blue flag for each episode'
}
options['prcnt_success'] = {
  'class': prcnt_success.PrcntSuccess,
  'help': 'Plot the precent success on a rolling basis. Use --window to set the window size'
}

class Inspector:
  def __init__(self, parser):
    self.parser = parser

    parser.add_argument('log', nargs=1, help='The log file to preform the requested operations on. Can be the name of a session or a path.')

    parser.add_argument('--limit', type=int, default=None, help='Limit the number of log files read.')
    parser.add_argument('--window', type=int, default=100, help='Sets the window size for averages, precentages, etc that do calculations on a rolling basis.')

    for opt in options:
      parser.add_argument(f'--{opt}', action='store_true', help=options[opt]['help'])

    self.parser.set_defaults(func=self.do_it)

  def handle_log(self, log, graphers, args):
    # Initialize all graphers
    for i, g in enumerate(graphers):
      graphers[i] = g(args)

    last_idx = None
    progress_bar = tqdm(total=log.total_files(), desc="Log Files")
    while log.has_more():
      t = log.read(1)[0]

      # Update all graphers
      for g in graphers:
        g._inject(t)

      if args.limit is not None:
        if args.limit == log.current_file():
          break

      # If we are on a new file update the progress bar
      if log.current_file() != last_idx:
        progress_bar.update(1)
        last_idx = log.current_file()
    
    # Show all graphers
    for g in graphers:
      g._get_fig(log.path()).show()

  def do_it(self, args):
    '''
    This is the function called by argparse to kick off the processing
    '''
    assert os.path.isdir(args.log[0]), 'To use the inspect command you must point it to a log folder. See usage with --help'

    log = get_log(args.log[0])

    if log is None:
      return

    graphers = []
    var_args = vars(args)
    for opt in options:
      if var_args[opt]:
        graphers.append(options[opt]['class'])
    
    if len(graphers) == 0:
      print('You must select at least one grapher. See usage.', file=sys.stderr)
      return

    self.handle_log(log, graphers, args)