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

from util.validate import check_test_dir
from util.constants import PLEARN_ACTIONS, JAYLAN_TESTDIR, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model
from util.graphing import TestGrapher

EPISODES_PER_TEST = 5

def test_dir(args):
    # Find the iteration numbers and sort
    iterations = []
    for subpath in os.listdir(args.test_dir):
        if subpath == '__pycache__':
            continue
        if os.path.isdir(os.path.join(args.test_dir, subpath)):
            iterations.append(int(subpath.split('_')[1]))
    iterations.sort()

    # Do testing
    with MissionManager('tester', log=False) as mgr:
        print('Waiting for vehicle connection...')
        mgr.wait_for(('felix',))

        # Keep track of the last report, to detect new once
        last_episode_num = None

        graph = TestGrapher(save_dir=args.test_dir)

        for i in trange(len(iterations), desc="Total Progress"):
            # Clear kera's backend so we don't slow down
            # See: https://www.tensorflow.org/api_docs/python/tf/keras/backend/clear_session
            keras.backend.clear_session()

            # Load model
            iteration_num = iterations[i]
            tqdm.write(f'Loading model #{iteration_num}...')
            model_path = os.path.join(args.test_dir, f'iteration_{iteration_num}')
            models, const = load_pLearn_model(model_path)

            # Initalize trail set data
            episode_count = 0
            success_count = 0
            min_flag_dist = None

            time_deltas = []
            max_time_delta = -1
            last_helm_time = None
            durations = []
            p = tqdm(total=EPISODES_PER_TEST, desc=f"Model #{i}")
            
            # Instruct pEpisodeManager to stop and enter PAUSED state
            msg = mgr.get_message()
            msg.stop()

            # Start pEpisodeManager again
            msg = mgr.get_message()
            msg.start()
            while episode_count <= EPISODES_PER_TEST:
                # Get state from manager
                msg = mgr.get_message()

                # Detect new episode
                if msg.episode_report is None:
                    # Sanity checks
                    assert i == 0
                    assert episode_count == 0
                elif last_episode_num != msg.episode_report['NUM']:
                    last_episode_num = msg.episode_report['NUM']

                    if msg.episode_report['DURATION'] < 1:
                        tqdm.write("WARNING: discarding episode due to small duration", file=sys.stderr)
                        last_episode_num = msg.episode_report['NUM']
                    else:
                        tqdm.write(f'Finished episode #{episode_count}')
                        p.update(1)
                        
                        durations.append(msg.episode_report['DURATION'])

                        episode_count += 1
                        if msg.episode_report['SUCCESS']:
                            success_count += 1
                        
                        # If we are done with this trail set, send pause instr
                        if episode_count == EPISODES_PER_TEST:
                            msg.request_new() # Just pass
                            break

                # Construct pLearn state
                pLearn_state = make_state(const.state, const.num_states, msg.state)
                pLearn_state = state2vec(pLearn_state, const)

                # Find optimal action
                optimal = (0, None)
                for a in PLEARN_ACTIONS:
                    value = models[a].predict(pLearn_state)

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

                msg.act(action)

                # Store min flag dist for scoring
                if min_flag_dist is None or flag_dist < min_flag_dist:
                    min_flag_dist = flag_dist
                # Calculate the dtime from last_helm_time for debugging
                if last_helm_time is not None:
                    time_deltas.append(msg.state['MOOS_TIME'] - last_helm_time)
                last_helm_time = msg.state['MOOS_TIME']

            # Calculate scoring
            success_precent = round(success_count / episode_count * 100, 2)
            avg_duration = round(sum(durations) / len(durations), 2)

            # Calculate debugging
            max_td = max(time_deltas)
            avg_td = round(sum(time_deltas) / len(time_deltas), 3)

            # Send info to graph and console
            graph.add_iteration(iteration_num, success_precent, min_flag_dist, avg_duration, avg_td)
            tqdm.write("\n========================================")
            tqdm.write(f"Report for model #{i}")
            tqdm.write(f"\npath: {model_path}")
            tqdm.write(f"\nSuccess: {success_count}/{episode_count}")
            tqdm.write(f"Min Flag Dist: {min_flag_dist}")
            tqdm.write(f"Avg Duration: {avg_duration}")
            tqdm.write(f"\nMax TD: {max_td}")
            tqdm.write(f"Avg TD: {avg_td}")
            tqdm.write("========================================\n")

            p.close()
    
    
    input("\n\nPress any key to exit...")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dir', default=JAYLAN_TESTDIR)
    
    args = parser.parse_args()

    check_test_dir(args.test_dir)

    test_dir(args)