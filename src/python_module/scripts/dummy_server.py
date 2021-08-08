import time
import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
bridgedir = os.path.join(os.path.dirname(currentdir), 'mivp_agent')
sys.path.append(bridgedir)

from bridge import ModelBridgeServer

if __name__ == '__main__':
  with ModelBridgeServer() as server:
    print('Starting server...')
    server.accept()

    print('Listing for state...')
    state = None
    while True:
      state = server.listen_state()
      print('Got state dict: ')
      print(state)

      time.sleep(0.25)