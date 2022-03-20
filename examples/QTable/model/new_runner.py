#!/usr/bin/env python3
import argparse
import time

from mivp_agent.episodic_manager import EpisodicManager
from mivp_agent.util.math import dist
from mivp_agent.util.display import ModelConsole
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

  '''
  Idea of the method bellow...
  Trainer was previously had to deal with state transitions itself. 
  msg1 - Message from v1 at time 1
  msg2 - Message from v1 at time 2
  # We can find when transitions by doing this
  obs_to_rpr(msg1.state) != obs_to_rpr(msg2.state)
  previous_state != obs_to_rpr(blah blah)
  '''
  #rename to msg_to_rpr? need full msg and not just msg.state for console.tick
  #observation.state doesn't make sense, gotta figure that out
  def obs_to_rpr(self, observation): 
    model_representation = self.q.get_state(
      observation.state['NAV_X'],
      observation.state['NAV_Y'],
      observation.state['NODE_REPORTS'][self.opponent_id]['NAV_X'],
      observation.state['NODE_REPORTS'][self.opponent_id]['NAV_Y'],
      observation.state['HAS_FLAG']
    )

    console.tick(observation)
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

  console = ModelConsole() #where will this live?
  mgr = EpisodicManager(agents, 13, wait_for=wait_for)
  mgr.start('runner')

