#!/usr/bin/env python3
import argparse
import time

from mivp_agent.episodic_manager import EpisodicManager
from mivp_agent.util.math import dist
#from mivp_agent.util.display import ModelConsole
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG
from constants import DEFAULT_RUN_MODEL
from model import load_model

class Agent:
  def __init__(self, own_id, opponent_id, model) -> None:
    self.own_id = own_id
    self.opponent_id = opponent_id
    self.q, self.attack_actions, self.retreat_actions = load_model(model)
    self.current_action = None

  def id(self):
      return self.own_id

  def obs_to_rpr(self, observation): 
    model_representation = self.q.get_state(
      observation['NAV_X'],
      observation['NAV_Y'],
      observation['NODE_REPORTS'][self.opponent_id]['NAV_X'],
      observation['NODE_REPORTS'][self.opponent_id]['NAV_Y'],
      observation['HAS_FLAG']
    )
    #console.tick(observation) #needs full msg, obervation is an msg.state

    return model_representation

  def rpr_to_act(self, rpr, observation): #why rpr and observation? we talked about this but can't remember
    self.current_action = self.q.get_action(rpr)
    
    # Determine action set
    if observation['HAS_FLAG']:
      current_action_set = self.retreat_actions
    else:
      current_action_set = self.attack_actions

    # Construct instruction for BHV_Agent
    action = {
      'speed': current_action_set[self.current_action]['speed'],
      'course': current_action_set[self.current_action]['course']
    }

    flag_dist = abs(dist((observation['NAV_X'], observation['NAV_Y']), FIELD_BLUE_FLAG))

    if flag_dist < 10:
      action['posts']= {
        'FLAG_GRAB_REQUEST': f'vname={self.own_id}'
      }

    return action


if __name__ == '__main__':
  # Create agents required
  parser = argparse.ArgumentParser()
  parser.add_argument('--model', default=DEFAULT_RUN_MODEL)
  args = parser.parse_args()

  agents = []
  wait_for = []
  for i in [1, 2, 3]:
    agents.append(Agent(f'agent_1{i}', f'drone_2{i}', args.model))
    wait_for.append(f'agent_1{i}')

  #console = ModelConsole() #where will this live? Do we care? Needs a full msg instead of msg.state
  mgr = EpisodicManager(agents, 13, wait_for=wait_for) #13 for 10 full episodes... not ideal
  mgr.start('runner')

