#!/usr/bin/env python3
import os
import time
import wandb
import argparse
from tqdm import tqdm

from mivp_agent.manager import MissionManager
from mivp_agent.util.math import dist
from mivp_agent.util.display import ModelConsole
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG

from constants import DEFAULT_RUN_MODEL
from model import load_model


EPISODES = 100

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

def test(args):
    q, attack_actions, retreat_actions = load_model(args.model)

    # Do testing
    with MissionManager() as mgr:
        print('Waiting for sim vehicle connection...')
        mgr.wait_for(EXPECTED_VEHICLES)

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

        # Init globals
        episode_count = 0
        success_count = 0
        min_dists = []
        durations = []

        # Initalize the episodes numbers from pEpisodeManager
        for a, num in mgr.episode_nums().items():
            agents[a].last_episode_num = num

        print('Testing...')
        progress_bar = tqdm(total=args.episodes, desc="Testing")
        while episode_count < args.episodes - 1:
            msg = mgr.get_message()

            # Start any pEpisodeManager that is not started:
            if msg.episode_state == 'PAUSED':
                msg.start()
                continue
            
            # Get current agent's data
            agent = agents[msg.vname]

            # Update debugging MOOS time
            if agent.last_MOOS_time is not None:
                agent.MOOS_deltas.append(msg.state['MOOS_TIME']-agent.last_MOOS_time)
            agent.last_MOOS_time = msg.state['MOOS_TIME']

            '''
            Part 1: Translate MOOS state to model's state representation
            '''
            # Translate to model readable state
            model_state = q.get_state(
                msg.state['NAV_X'],
                msg.state['NAV_Y'],
                msg.state['NODE_REPORTS'][agent.enemy]['NAV_X'],
                msg.state['NODE_REPORTS'][agent.enemy]['NAV_Y'],
                msg.state['HAS_FLAG']
            )

            # Detect discrete state transitions
            if model_state != agent.last_state:
                '''
                Part 2: Handle the ending of episodes
                '''
                if msg.episode_report is None:
                    assert agent.agent_episode_count == 0
                elif msg.episode_report['DURATION'] < 2:
                    # Bad episode, don't use data
                    # Reset episode data and including 'last_episode_num'
                    agent.new_episode(msg.episode_report['NUM'])
                elif msg.episode_report['NUM'] != agent.last_episode_num:
                    # Only stats we care about, for now, are those about grabing not returning
                    # b/c trying to compare to pLearn
                    episode_count += 1
                    progress_bar.update(1)

                    if agent.grab_time is not None:
                        # Only car about this time
                        durations.append(msg.state['MOOS_TIME']-agent.grab_time)
                    else:
                        # Agent didn't grab flag, so add total episode duration
                        durations.append(msg.episode_report['DURATION'])

                    min_dists.append(agent.min_dist)

                    if agent.had_flag:
                        success_count += 1

                    # Construct report
                    report = {
                        'episode': episode_count,
                        'duration': round(durations[-1],2),
                        'success': agent.had_flag,
                        'min_dist': round(agent.min_dist, 2),
                    }

                    if len(agent.MOOS_deltas) != 0:
                        report['avg_delta'] = round(sum(agent.MOOS_deltas)/len(agent.MOOS_deltas),2)
                    else:
                        report['avg_delta'] = 0.0

                    tqdm.write(f'[{msg.vname}] ', end='')
                    tqdm.write(', '.join([f'{k}: {report[k]}' for k in report]))

                    # Reset episode data and including 'last_episode_num'
                    agent.new_episode(msg.episode_report['NUM'])
                '''
                Part 3: Handle updating actions
                '''

                # Get new action
                agent.current_action = q.get_action(model_state)
                agent.last_state = model_state

                # Store vars needed for time to grab duration calculation
                if msg.state['HAS_FLAG'] and not agent.had_flag:
                    agent.had_flag = True
                    agent.grab_time = msg.state['MOOS_TIME']


            '''
            Part 4: Even when agent is not in new state, keep preforming
            the action that was calcualted on the when the state transitioned
            '''
            actions = attack_actions
            if msg.state['HAS_FLAG']: # Use retreat actions if already grabbed and... retreating
                actions = retreat_actions
            action = actions[agent.current_action].copy() # Copy out of reference paranoia
            
            flag_dist = abs(dist((msg.state['NAV_X'], msg.state['NAV_Y']), FIELD_BLUE_FLAG))
            # If this agent can grab the flag, do so
            if flag_dist < 10:
                action['posts'] = {
                'FLAG_GRAB_REQUEST': f'vname={msg.vname}'
                }

            # Send action
            msg.act(action)

            # Debugging stuff
            if agent.min_dist is None or agent.min_dist > flag_dist:
                agent.min_dist = flag_dist


        progress_bar.close()

        # Calculate stats
        success_precent  = round(success_count / episode_count * 100, 2)
        avg_duration = round(sum(durations) / len(durations), 2)
        avg_min_dist = round(sum(min_dists) / len(min_dists), 2)


        print('\n--------------------------------------------')
        print(f'Episodes:        {episode_count+1}')
        print(f'Precent Success: {success_precent}')
        print(f'Avg Duration:    {avg_duration}')
        print(f'Avg Min Dist:    {avg_min_dist}')
        print('--------------------------------------------')

    input("\n\nPress any key to exit...")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=DEFAULT_RUN_MODEL)
    parser.add_argument('--episodes', default=EPISODES)
    args = parser.parse_args()

    test(args)