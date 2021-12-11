import os

from mivp_agent.logger import inspect
from mivp_agent.const import LAST_LOG_DIR

def help():
  print('Usage: agnt <command> [OPTIONS]\n')
  print('COMMANDS:')
  print('   ilog [PATH] [COMMANDS]')
  print('       Inspects log files. If path is left blank the command will attempt to find the log directories in the current working directory.')

def main(argv):
  argc = len(argv)
  if argc < 2:
    help()
    exit(1)

  if argv[1] == 'ilog':
    if argc <= 3 or not os.path.isdir(argv[2]):
      # Attempt to find logs
      if not os.path.isdir(LAST_LOG_DIR):
        print(f'Error: Unable to find {LAST_LOG_DIR} in current directory either change directory or specify a <path> to inspect.')
        help()
        exit(1)
      
      for directory in os.listdir(LAST_LOG_DIR):
        
        path = os.path.join(LAST_LOG_DIR, directory)

        if os.path.isdir(path):
          # Call inspect with the rest of the args
          inspect.inspect(path, argv[2:])
    else:
      inspect.inspect(argv[2], argv[3:])
  else:
    raise RuntimeError(f'Unrecognized command: {argv[1]}')
