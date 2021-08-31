#!/usr/bin/env python3
import os
import sys
import warnings
import argparse
import numpy as np
from tqdm.auto import trange
from tqdm.std import tqdm

warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)
import keras

from mivp_agent.manager import MissionManager
from mivp_agent.util.display import ModelConsole
from state import make_state

from model.util.validate import check_model_dir
from model.util.constants import PLEARN_ACTIONS, ENEMY_FLAG, PLEARN_TOPMODEL
from model.util.state import state2vec, dist
from model.util.model_loader import load_pLearn_model

EPISODES = 20
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
    self.last_episode_num = None # Episode transitions
    self.had_flag = False   # Capturing grab transitions for rewarding

    # For debugging / output
    self.min_dist = None
    self.episode_reward = 0
  
  def new_episode(self, last_num):
    self.last_episode_num = last_num

    self.had_flag = False

    self.min_dist = None
    self.episode_reward = 0

def test(args):
    model, const = load_pLearn_model(args.model)
    # Do testing
    with MissionManager() as mgr:
        print('Waiting for vehicle connection...')
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

        print('Testing')
        progress_bar = tqdm(total=args.episodes, desc="Testing")
        while episode_count < args.episodes - 1:
            msg = mgr.get_message()

            # Start any pEpisodeManager that is not started:
            if msg.episode_state == 'PAUSED':
                msg.start()
                continue
            
            # Get current agent's data
            agent = agents[msg.vname]

            # Check for ending of episodes
            if msg.episode_report is None:
                assert episode_count == 0
            elif agent.last_episode_num != msg.episode_report['NUM']:
                # Test for episode manager bug
                if msg.episode_report['DURATION'] > 2:
                    episode_count += 1
                    progress_bar.update(1)

                    durations.append(msg.episode_report['DURATION'])
                    min_dists.append(agent.min_dist)

                    if msg.episode_report['SUCCESS']:
                        success_count += 1

                    tqdm.write(f'[{msg.vname}] episode: {episode_count} duration: {msg.episode_report["DURATION"]}, success: {msg.episode_report["SUCCESS"]}, min_dist: {agent.min_dist}')

                # Update / reset the agents data
                agent.new_episode(msg.episode_report['NUM'])

            # Calculate action
            pLearn_state = make_state(const.state, const.num_states, msg.state, agent.enemy)
            pLearn_state = state2vec(pLearn_state, const)

            optimal = (0, None)
            for a in PLEARN_ACTIONS:
                value = model[a].predict(pLearn_state)

                if optimal[1] is None or optimal[0] < value:
                    optimal = (value, PLEARN_ACTIONS[a])

            # Send optimal action to BHV_Agent client
            action = {
                'course': optimal[1]['course'],
                'speed': optimal[1]['speed'],
            }

            flag_dist = abs(dist((msg.state['NAV_X'], msg.state['NAV_Y']), ENEMY_FLAG))
            if flag_dist < 10:
                action['posts'] = {
                    'FLAG_GRAB_REQUEST': f'vname={msg.vname}'
                }
            if agent.min_dist is None or agent.min_dist > flag_dist:
                agent.min_dist = flag_dist
            
            msg.act(action)

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
    parser.add_argument('--model', default=PLEARN_TOPMODEL)
    parser.add_argument('--episodes', default=EPISODES)
    args = parser.parse_args()

    print(args.model)

    check_model_dir(args.model)

    test(args)