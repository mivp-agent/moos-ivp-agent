import os
import sys
from google.protobuf import descriptor
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.core.series import Series

from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto.proto_logger import ProtoLogger

from mivp_agent.util.math import dist

from . import glog

def write_describe(describe, prefix='    ', file=sys.stdout):
  for t, l in describe.items():
    print(f'{prefix}{t}: {l}', file=file)

def do_dists(transitions, only=False):
  dists = []
  for t in transitions:
    x1 = t.s1.vinfo.NAV_X
    y1 = t.s1.vinfo.NAV_Y
    x2 = t.s2.vinfo.NAV_X
    y2 = t.s2.vinfo.NAV_Y

    dists.append(dist((x1,y1), (x2,y2)))
  
  print('Dist:')
  s = pd.DataFrame(dists)
  s.columns = ['distances',]
  write_describe(s.describe())

  if only:
    print('Showing plot, if you are in a terminal only session the behavior is undefined...')
    fig = px.histogram(s, x='distances')
    fig.show()

def do_tds(transitions, only=False):
# Parse the time which each transition takes
  td = []
  for t in transitions:
    td.append(t.s2.vinfo.MOOS_TIME - t.s1.vinfo.MOOS_TIME)

  print('Time Delta:')
  s = Series(td)
  write_describe(s.describe())

  if only:
    print('Showing plot, if you are in a terminal only session the behavior is undefined...')
    s.hist()
    plt.show()

commands = {
  'dist': do_dists,
  'td': do_tds,
  'glog': glog.do_glog
}

def help():
  print('Usage: angt ilog [PATH] [COMMANDS]\n')
  print('COMMANDS:')
  for c in commands:
    print(c)

def inspect(path, args):
  assert os.path.isdir(path), "Must point inspect to a path"

  log = ProtoLogger(path, Transition, mode='r')

  transitions = []
  while log.has_more():
    transitions.extend(log.read(100))
  if len(args) == 1:
    if args[0] not in commands:
      help()
      exit(1)
    
    commands[args[0]](transitions, only=True)
    return
  elif len(args) > 1:
    help()
    exit(1)


  print(f'\n%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
  print(f'Path: {path}')
  print(f'%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%')
  print(f'Transitions: {len(transitions)}')

  # Count episodes
  e_count = 0
  e_number = None
  for t in transitions:
    if t.s1.HasField('episode_report'):
      report = t.s1.episode_report
      if report.NUM != e_number:
        e_count +=1
      e_number = report.NUM
  print(f'Episodes: {e_count}')

  # Run any commands
  for _, runable in commands.items():
    runable(transitions)

  print(f'%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%\n')
