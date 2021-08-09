#!/usr/bin/env python3
import argparse

from mivp_agent.bridge import ModelBridgeServer
from mivp_agent.util.parse import parse_report
from mivp_agent.util.math import dist
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG

from model.util.constants import ACTIONS
from model.model import load_model

MNGR_STATE = 'EPISODE_MNGR_STATE'
MNGR_REPORT = 'EPISODE_MNGR_REPORT'

def run(args):
  q = load_model(args.model)

  with ModelBridgeServer() as server:
    print('Waiting for sim connection...')
    server.accept()

    # ---------------------------------------
    # Part 1: Asserting simulation state

    # Create instruction object
    instr = {
      'speed': 0.0,
      'course': 0.0,
      'posts': {},
      'ctrl_msg': 'SEND_STATE'
    }
    
    last_state = None
    current_action = None

    server.send_instr(instr)
    while True:
      # Listen for state
      MOOS_STATE = server.listen_state()
      MOOS_STATE[MNGR_REPORT] = parse_report(MOOS_STATE[MNGR_REPORT])

      # Detect state transitions
      model_state = q.get_state(
        MOOS_STATE['NAV_X'],
        MOOS_STATE['NAV_Y'],
        MOOS_STATE['NODE_REPORTS']['evan']['NAV_X'],
        MOOS_STATE['NODE_REPORTS']['evan']['NAV_Y']
      )

      # Detect state transition
      if model_state != last_state:
        current_action = q.get_action(model_state)
        last_state = model_state
      
      # Construct instruction for BHV_Agent
      instr['speed'] = ACTIONS[current_action]['speed']
      instr['course'] = ACTIONS[current_action]['course']
      instr['posts'] = {}

      flag_dist = abs(dist((MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y']), FIELD_BLUE_FLAG))
      if flag_dist < 10:
        instr['posts']['FLAG_GRAB_REQUEST'] = f'vname={MOOS_STATE["VNAME"]}'
      
      server.send_instr(instr)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--model')
  args = parser.parse_args()
  run(args)