#!/usr/bin/env python3
import time
from util.getch import Getch
from RLquaticus.bridge import ModelBridgeServer

if __name__ == '__main__':
  with ModelBridgeServer() as server:
    print('Accepting server connection...')
    server.accept()

    # Construct getch utility for char reading from stdin
    getch = Getch()

    print("==================================")
    print("Begining loop (press 'b' to exit)")
    print("==================================")


    action = {
      'speed': 2,
      'course': 0,
      'MOOS_VARS': ()
    }
    state = None
    c = None
    while True and c != 'b':
      c = getch().lower()

      if c == 'w':
        action['course'] = 0
      elif c == 's':
        action['course'] = 180
      elif c == 'd':
        action['course'] = 90
      elif c == 'a':
        action['course'] = 270

      print(f'Sending action {action}')
      server.send_action(action)

      state = server.listen_state(timeout=0.1)
      if state:
        print(f'Got state {state}')