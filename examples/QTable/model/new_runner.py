#!/usr/bin/env python3
import argparse
import time

from mivp_agent.episodic_manager import EpisodicManager
from mivp_agent.util.math import dist
from mivp_agent.util.display import ModelConsole
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG

from constants import DEFAULT_RUN_MODEL
from model import load_model


def run(args):
  q, attack_actions, retreat_actions = load_model(args.model)

  with EpisodicManager('runner', log=False) as mgr:
    print('Waiting for sim vehicle connections...')
    while mgr.get_vehicle_count() < 1:
      time.sleep(0.1)
    # ---------------------------------------
    # Part 1: Asserting simulation state

    last_state = None
    current_action = None
    current_action_set = None
    console = ModelConsole()

    while True:
      # Listen for state
      msg = mgr.get_message()
      while False:
        print('-------------------------------------------')
        print(f"({msg.vname}) {msg.state['HAS_FLAG']}")  
        print('-------------------------------------------')
        msg.request_new()
        msg = mgr.get_message()

      console.tick(msg)

      # Detect state transitions
      model_state = q.get_state(
        msg.state['NAV_X'],
        msg.state['NAV_Y'],
        msg.state['NODE_REPORTS'][args.enemy]['NAV_X'],
        msg.state['NODE_REPORTS'][args.enemy]['NAV_Y'],
        msg.state['HAS_FLAG']
      )

      # Detect state transition
      if model_state != last_state:
        current_action = q.get_action(model_state)
        last_state = model_state
      
      # Determine action set
      if msg.state['HAS_FLAG']:
        current_action_set = retreat_actions
      else:
        current_action_set = attack_actions

      # Construct instruction for BHV_Agent
      action = {
        'speed': current_action_set[current_action]['speed'],
        'course': current_action_set[current_action]['course']
      }

      flag_dist = abs(dist((msg.state['NAV_X'], msg.state['NAV_Y']), FIELD_BLUE_FLAG))
      if flag_dist < 10:
        action['posts']= {
          'FLAG_GRAB_REQUEST': f'vname={msg.vname}'
        }
      
      msg.act(action)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', default=DEFAULT_RUN_MODEL)
  parser.add_argument('--enemy', default='drone_21')
  args = parser.parse_args()
  run(args)