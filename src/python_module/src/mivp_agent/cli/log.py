from genericpath import exists, isdir
import os, sys

from mivp_agent.cli.util import load_data_dir, get_log

class Log:
  def __init__(self, parser):
    self.parser = parser

    parser.add_argument('log', nargs=1, help='The log file to preform the requested operations on. Can be the name of a session or a path.')

    self.parser.set_defaults(func=self.do_it)

  def handle_log(self, log, args):
    transitions = []
    while log.has_more():
      transitions.extend(log.read(100))
    
    vname = transitions[0].s1.vinfo.vname

    print(f'{vname}')
    print(f'=================================')
    print(f'Transitions: {len(transitions)}')
    print()

  def do_it(self, args):
    '''
    This is the function called by argparse to kick off the processing
    '''
    if os.path.isdir(args.log[0]):
      self.handle_log(get_log(args.log[0]), args)
      return

    data = load_data_dir(print_error=False)
    if data is None:
      return
    
    if not data.meta.registry.has_session(args.log[0]):
      print(f'Error: Input specified is neither path to a log nor a valid session ID', file=sys.stderr)
      return

    # Load the LogDirectory to check for session names
    logs = data.meta.get_logs(args.log[0])

    if len(logs) == 0:
      print(f'Error: Input specified is valid session ID but no logs associated with it were found', file=sys.stderr)
      return
    
    for log in logs:
      self.handle_log(log, args)