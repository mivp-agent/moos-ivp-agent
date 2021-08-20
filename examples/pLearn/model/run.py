#!/usr/bin/env python3
import sys
import warnings
import argparse
import numpy as np

warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)

from mivp_agent.manager import MissionManager
from mivp_agent.util.display import ModelConsole
from state import make_state

from util.validate import check_model_dir
from util.constants import PLEARN_ACTIONS, PLEARN_TOPMODEL, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model
from util.graphing import DebugGrapher

def run_model(args):

    print('Loading model...')
    models, const = load_pLearn_model(args.model)

    # Construct debugging info
    graph = None
    last_episode_num = None
    expected_reward = []
    episode_iters = []
    episode_iter = 0
    if args.debug:
        graph = DebugGrapher()

    with MissionManager() as mgr:
        print('Waiting for vehicle connection...')
        mgr.wait_for(('felix',))

        model_state = None
        console = ModelConsole()

        while True:
            # Get state msg (state) from manager
            msg = mgr.get_message()


            if msg.episode_report is not None:
                
                # Watch for pEpisodeManager bug
                if msg.episode_report['DURATION'] < 4:
                    print('ERROR: Small duration value', file=sys.stderr)
                    print(msg.episode_report, file=sys.stderr)
                
                # Reset expected value tracking for debugging
                if args.debug:
                    if last_episode_num is None or last_episode_num != msg.episode_report['NUM']:
                        # We have a new episode 
                        episode_iter = 0
                        episode_iters = []
                        expected_reward = []

                    last_episode_num = msg.episode_report['NUM']

            # Translate state to be readable by model  
            model_state = make_state(const.state, const.num_states, msg.state)
            state_vec = state2vec(model_state, const)

            # Find optimal action & keep track of all for graping
            optimal = (0, None)
            values = {}
            for a in PLEARN_ACTIONS:
                value = models[a].predict(state_vec)
                if args.debug:
                    values[a] = value.item(0)

                if optimal[1] is None or optimal[0] < value:
                    optimal = (value, PLEARN_ACTIONS[a])

            # Create optimal action for BHV_Agent client
            action = {
                'course': optimal[1]['course'],
                'speed': optimal[1]['speed']
            }
            
            # Add FLAG_GRAB_REQUEST if in range
            if abs(dist((msg.state['NAV_X'], msg.state['NAV_Y']), ENEMY_FLAG)) < 10:
                action['posts'] = {
                    'FLAG_GRAB_REQUEST': f'vname={msg.vname}'
                }
            
            # Send action to BHV_Agent
            msg.act(action)

            # Update the console output
            console.tick(msg)
            if args.debug and console.iteration % 6 == 0:
                # Track the expect value over the iteration
                expected_reward.append(optimal[0])
                episode_iters.append(episode_iter)
                
                # Send debugging info to be graphed
                graph.add_iteration(
                    console.iteration,
                    values,
                    episode_iters,
                    expected_reward,
                    console.last_MOOS_delta
                )

                #Update the 
                episode_iter += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=PLEARN_TOPMODEL)
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args()

    check_model_dir(args.model)

    run_model(args)