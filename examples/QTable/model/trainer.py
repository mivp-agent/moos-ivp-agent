#!/usr/bin/env python3
import argparse
from mivp_agent.episodic_manager import EpisodicManager
from mivp_agent.util.math import dist
from wandb_key import WANDB_KEY
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG
from constants import LEARNING_RATE, DISCOUNT, EPISODES
from constants import FIELD_RESOLUTION
from constants import EPSILON_START, EPSILON_DECAY_START, EPSILON_DECAY_AMT, EPSILON_DECAY_END
from constants import ATTACK_ACTIONS, RETREAT_ACTIONS, ACTION_SPACE_SIZE
from constants import REWARD_GRAB, REWARD_CAPTURE, REWARD_FAILURE, REWARD_STEP
from constants import SAVE_DIR, SAVE_EVERY
from model import QLearn

# The expected agents and their enemies
VEHICLE_PAIRING = {
  'agent_11': 'drone_21',
  'agent_12': 'drone_22',
  'agent_13': 'drone_23',
  #'agent_14': 'drone_24',
  #'agent_15': 'drone_25'
}
# Expect the agents to connect (so we can send instructions). The drones are on autopilot defined by the bhv files.
EXPECTED_VEHICLES = [key for key in VEHICLE_PAIRING]


class Agent:
  def __init__(self, own_id, opponent_id, q, config) -> None:
    self.own_id = own_id
    self.opponent_id = opponent_id
    self.q = q
    self.attack_actions = config['attack_actions']
    self.retreat_actions = config['retreat_actions']
    self.current_action = None
    self.config = config
    self.last_rpr = None

    # For debugging / output
    self.min_dist = None
    self.episode_reward = 0
    self.last_MOOS_time = None
    self.MOOS_deltas = []
    self.grab_time = None

  def id(self):
    '''
    Required hook for EpisodicManager to access agent ID
    '''
    return self.own_id

  def reset_tracking_vars(self):
    '''
    Reset per-episode tracking vars for this agent
    '''
    #Functional
    self.last_rpr = None
    self.had_flag = False
    self.current_action = None

    #Debugging and I/O
    self.min_dist = None
    self.episode_reward = 0
    self.last_MOOS_time = None
    self.MOOS_deltas.clear()
    self.grab_time = None

  def obs_to_rpr(self, observation):
    '''
    Hook for EpisodicManager to convert an observation to python representation 
    Called on each new oberservation, used to detect state transitions
    '''
    model_representation = self.q.get_state(
      observation['NAV_X'],
      observation['NAV_Y'],
      observation['NODE_REPORTS'][self.opponent_id]['NAV_X'],
      observation['NODE_REPORTS'][self.opponent_id]['NAV_Y'],
      observation['HAS_FLAG']
    )

    return model_representation

  def rpr_to_act(self, rpr, observation, em_report):
    '''
    Hook for EpisodicManager to get next action based on current state representation
    Called on each new state representation
    Most functional code goes here
    '''
    # Update previous state action pair
    reward = self.config['reward_step']
    if observation['HAS_FLAG'] and not self.had_flag:
      reward = self.config['reward_grab'] #Should this be += to also account for the step?
      self.had_flag = True
      # Capture time for debugging (time after grab)
      self.grab_time = observation['MOOS_TIME']

    if self.last_rpr is not None:
      self.q.update_table(
        self.last_rpr,
        self.current_action,
        reward,
        rpr
      )
      self.episode_reward += self.config['reward_step'] #shouldn't this just be += reward?

    #################### NO ####################
    global epsilon 
    ############# NO NO NO NO NO NO ############
    
    self.current_action = q.get_action(rpr, e=epsilon)
    self.last_rpr = rpr

    actions = self.attack_actions
    if observation['HAS_FLAG']: # Use retreat actions if already grabbed and... retreating
      actions = self.retreat_actions
    action = actions[self.current_action].copy() # Copy out of reference paranoia

    flag_dist = abs(dist((observation['NAV_X'], observation['NAV_Y']), FIELD_BLUE_FLAG))

    if flag_dist < 10:
      action['posts']= {
        'FLAG_GRAB_REQUEST': f'vname={self.own_id}'
      }

    return action

  def episode_end(self, rpr, observation, em_report):
    '''
    Hook for EpisodicManager, called at the end of each episode
    End rewards, model saving, etc. go here
    '''
    reward = self.config['reward_failure']
    if em_report['success']:
      reward = self.config['reward_capture']

    # Apply this reward to the QTable
    if self.last_rpr is not None:
      self.q.set_qvalue(
        self.last_rpr,
        self.current_action,
        reward
      )
    else:
      print("last_rpr was None")

    completed_episodes = em_report['completed_episodes']

    #################### NO ####################
    global epsilon 
    ############# NO NO NO NO NO NO ############

    # Decay epsilon
    if self.config['epsilon_decay_end'] >= completed_episodes >= self.config['epsilon_decay_start']:
      epsilon -= self.config['epsilon_decay_amt']

    self.reset_tracking_vars()

    # Save model if applicable
    if completed_episodes % config['save_every'] == 0:
      q.save(
        config['attack_actions'],
        config['retreat_actions'],
        name=f'episode_{completed_episodes}'
      )


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--debug', action='store_true')
  parser.add_argument('--no_wandb', action='store_true')
  
  args = parser.parse_args()

  # Error if wandb not set --no_wandb is not
  if not args.no_wandb and WANDB_KEY == "Your API key here":
    raise RuntimeError('WandB key not set and no --no_wandb flag. See documentation')

  # Construct config
  config = {
    'lr': LEARNING_RATE,
    'gamma': DISCOUNT,
    'episodes': EPISODES,
    'epsilon_start': EPSILON_START,
    'epsilon_decay_start': EPSILON_DECAY_START,
    'epsilon_decay_amt': EPSILON_DECAY_AMT,
    'epsilon_decay_end': EPSILON_DECAY_END,
    'field_res': FIELD_RESOLUTION,
    'attack_actions': ATTACK_ACTIONS,
    'retreat_actions': RETREAT_ACTIONS,
    'action_space_size': ACTION_SPACE_SIZE,
    'reward_grab': REWARD_GRAB,
    'reward_capture': REWARD_CAPTURE,
    'reward_failure': REWARD_FAILURE,
    'reward_step': REWARD_STEP,
    'save_every': SAVE_EVERY,
  }

  # Setup model
  q = QLearn(
    lr=config['lr'],
    gamma=config['gamma'],
    action_space_size=config['action_space_size'],
    field_res=config['field_res'],
    verbose=args.debug,
    save_dir=SAVE_DIR
  )
  epsilon = config['epsilon_start']

  agents = []
  wait_for = []
  for key in VEHICLE_PAIRING:
    agents.append(Agent(key, VEHICLE_PAIRING[key], q, config))

  mgr = EpisodicManager(agents, EPISODES, wait_for=wait_for) 
  mgr.start('trainer')