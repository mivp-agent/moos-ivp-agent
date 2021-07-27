import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
bridgedir = os.path.join(os.path.dirname(currentdir), 'RLquaticus')
sys.path.append(bridgedir)

from bridge import ModelBridgeServer

if __name__ == '__main__':
  with ModelBridgeServer() as server:
    server.start()
    input("Press any key to continue...")