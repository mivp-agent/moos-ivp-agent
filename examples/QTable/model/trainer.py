#!/usr/bin/env python3
import os
import time
import wandb
import argparse
from tqdm import tqdm

from mivp_agent.manager import MissionManager
from mivp_agent.util.display import ModelConsole
from mivp_agent.util.math import dist
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG

from wandb_key import WANDB_KEY
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
  'agent_14': 'drone_24',
  'agent_15': 'drone_25'
}
EXPECTED_VEHICLES = [key for key in VEHICLE_PAIRING]

class AgentData:
  '''
  Used to encapsulate the data needed to run each indivdual
  agent, track state / episode transitions, and output useful
  information and statistics.
  '''
  def __init__(self, vname, enemy):
    self.vname = vname
    self.enemy = enemy
    
    # For running of simulation
    self.agent_episode_count = 0
    self.last_episode_num = None # Episode transitions
    self.last_state = None       # State transitions
    self.had_flag = False   # Capturing grab transitions for rewarding
    self.current_action = None 

    # For debugging / output
    self.min_dist = None
    self.episode_reward = 0
    self.last_MOOS_time = None
    self.MOOS_deltas = []
    self.grab_time = None
  
  def new_episode(self, last_num):
    self.last_episode_num = last_num
    self.agent_episode_count += 1

    self.last_state = None
    self.had_flag = False
    self.current_action = None

    self.min_dist = None
    self.episode_reward = 0
    self.last_MOOS_time = None
    self.MOOS_deltas.clear()
    self.grab_time = None


def train(args, config):
  # Setup model
  q = QLearn(
    lr=config['lr'],
    gamma=config['gamma'],
    action_space_size=config['action_space_size'],
    field_res=config['field_res'],
    verbose=args.debug,
    save_dir=args.save_dir
  )

  agents = {}
  with MissionManager(logging=True, immediate_transition=False) as mgr:
    print('Waiting for sim vehicle connection...')
    mgr.wait_for(EXPECTED_VEHICLES)

    # Construct agent data object with enemy specified
    agents = {}
    for a in VEHICLE_PAIRING:
      agents[a] = AgentData(a, VEHICLE_PAIRING[a])

    # While all vehicle's pEpisodeManager are not PAUSED
    print('Waiting for pEpisodeManager to enter PAUSED state...')
    while not all(mgr.episode_state(vname) == 'PAUSED' for vname in agents):
      msg = mgr.get_message()
      if mgr.episode_state(msg.vname) != 'PAUSED':
        # Instruct them to stop and pause
        msg.stop()
      else:
        # O/w just keep up to date on their state
        msg.request_new()

    # ---------------------------------------
    # Part 2: Global state initalization
    episode_count = 0
    epsilon = config['epsilon_start']
    progress_bar = tqdm(total=config['episodes'], desc='Training')
    # Debugging
    total_sim_time = 0

    # Initalize the epidode numbers from pEpisodeManager
    e_nums = mgr.episode_nums()
    for a in e_nums:
      agents[a].last_episode_num = e_nums[a]

    print('Running training...')
    while episode_count < config['episodes']:
      '''
      This loop handles an indivual msg from an indivual agent
      data from each agent is used during training
      '''
      # Listen for an agent's message & get it's data
      msg = mgr.get_message()
      # If pEpisodeManager is paused, start and continue to next agent
      if msg.episode_state == 'PAUSED':
        msg.mark_transition() # Initial state should be a transition
        msg.start()
        continue
      agent_data = agents[msg.vname]

      # Update debugging MOOS time
      if agent_data.last_MOOS_time is not None:
        agent_data.MOOS_deltas.append(msg.state['MOOS_TIME']-agent_data.last_MOOS_time)
      agent_data.last_MOOS_time = msg.state['MOOS_TIME']

      '''
      Part 1: Translate MOOS state to model's state representation
      '''
      #print(msg.state['HAS_FLAG'])
      model_state = q.get_state(
        msg.state['NAV_X'],
        msg.state['NAV_Y'],
        msg.state['NODE_REPORTS'][agent_data.enemy]['NAV_X'],
        msg.state['NODE_REPORTS'][agent_data.enemy]['NAV_Y'],
        msg.state['HAS_FLAG']
      )

      # Detect discrete state transitions
      if model_state != agent_data.last_state:
        '''
        Part 2: Handle the ending of episodes
        '''
        # Mark this state as a transition to record it to logs
        msg.mark_transition()

        if msg.episode_report is None:
          assert agent_data.agent_episode_count == 0
        elif msg.episode_report['DURATION'] < 2:
          # Bad episode, don't use data
          # Reset episode data and including 'last_episode_num'
          agent_data.new_episode(msg.episode_report['NUM'])
        elif msg.episode_report['NUM'] != agent_data.last_episode_num:
          # Calculate reward based on pEpisodeManager's report
          reward = config['reward_failure']
          if msg.episode_report['SUCCESS']:
            reward = config['reward_capture']

          # Apply this reward to the QTable
          q.set_qvalue(
            agent_data.last_state,
            agent_data.current_action,
            reward
          )

          # Update the total sim time
          total_sim_time += msg.episode_report['DURATION']

          # Construct report
          report = {
            'episode_count': episode_count,
            'reward': agent_data.episode_reward+reward,
            'epsilon': round(epsilon, 3),
            'duration': round(msg.episode_report['DURATION'],2),
            'success': msg.episode_report['SUCCESS'],
            'min_dist': round(agent_data.min_dist, 2),
            'had_flag': agent_data.had_flag,
            'sim_time': round(total_sim_time, 2),
            'sim_days': round(total_sim_time / 86400, 2)
          }

          if len(agent_data.MOOS_deltas) != 0:
            report['avg_delta'] = round(sum(agent_data.MOOS_deltas)/len(agent_data.MOOS_deltas),2)
          else:
            report['avg_delta'] = 0.0

          if agent_data.grab_time is not None:
            report['post_grab_duration'] = round(msg.state['MOOS_TIME'] - agent_data.grab_time, 2)
          else:
            report['post_grab_duration'] = 0.0

          # Log the report
          if not args.no_wandb:
            wandb.log(report)
          tqdm.write(f'[{msg.vname}] ', end='')
          tqdm.write(', '.join([f'{k}: {report[k]}' for k in report]))

          # Decay epsilon
          if config['epsilon_decay_end'] >= episode_count >= config['epsilon_decay_start']:
            epsilon -= config['epsilon_decay_amt']

          # Reset episode data and including 'last_episode_num'
          agent_data.new_episode(msg.episode_report['NUM'])
          # Update global episode count
          episode_count += 1
          progress_bar.update(1)

          # Save model if applicable
          if episode_count % SAVE_EVERY == 0:
            q.save(
              config['attack_actions'],
              config['retreat_actions'],
              name=f'episode_{episode_count}'
            )

        '''
        Part 3: Handle updating actions / qtable in new states
        '''

        # Update previous state action pair
        reward = config['reward_step']
        if msg.state['HAS_FLAG'] and not agent_data.had_flag:
          reward = config['reward_grab']
          agent_data.had_flag = True
          # Capture time for debugging (time after grab)
          agent_data.grab_time = msg.state['MOOS_TIME']

        if agent_data.last_state is not None:
          q.update_table(
            agent_data.last_state,
            agent_data.current_action,
            reward,
            model_state
          )
          agent_data.episode_reward += config['reward_step']
        
        # Update tracking data
        agent_data.current_action = q.get_action(model_state, e=epsilon)
        agent_data.last_state = model_state
      
      '''
      Part 4: Even when agent is not in new state, keep preforming
      the action that was calcualted on the when the state transitioned
      '''
      actions = config['attack_actions']
      if msg.state['HAS_FLAG']: # Use retreat actions if already grabbed and... retreating
        actions = config['retreat_actions']
      action = actions[agent_data.current_action].copy() # Copy out of reference paranoia
      
      flag_dist = abs(dist((msg.state['NAV_X'], msg.state['NAV_Y']), FIELD_BLUE_FLAG))
      # If this agent can grab the flag, do so
      if flag_dist < 10:
        action['posts'] = {
          'FLAG_GRAB_REQUEST': f'vname={msg.vname}'
        }

      # Send action
      msg.act(action)

      # Debugging stuff
      if agent_data.min_dist is None or agent_data.min_dist > flag_dist:
        agent_data.min_dist = flag_dist


if __name__ == '__main__':
  save_dir = os.path.join(SAVE_DIR, str(round(time.time())))

  parser = argparse.ArgumentParser()
  parser.add_argument('--debug', action='store_true')
  parser.add_argument('--save_dir', default=save_dir)
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
  }

  if args.no_wandb:
    train(args, config)
  else:
    wandb.login(key=WANDB_KEY)
    with wandb.init(project='mivp_agent_qtable', config=config):
      config = wandb.config
      args.save_dir = os.path.join(SAVE_DIR, f'{str(round(time.time()))}_{wandb.run.name}')
      train(args, config)