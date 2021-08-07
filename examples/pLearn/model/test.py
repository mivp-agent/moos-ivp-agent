#!/usr/bin/env python3
import os
import sys
import warnings
import argparse
import numpy as np
from tqdm.auto import trange
from tqdm.std import tqdm

warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)

from RLquaticus.bridge import ModelBridgeServer
from RLquaticus.util.display import ModelConsole
from RLquaticus.util.parse import parse_report
from state import make_state

from util.validate import check_test_dir
from util.constants import PLEARN_ACTIONS, JAYLAN_TESTDIR, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model
from util.graphing import TestGrapher

PAUSE_INSTR= {
    'speed': 0.0,
    'course': 0.0,
    'posts': { # This will only be sent the first time, after that it is turrned off
        'EPISODE_MNGR_CTRL': 'type=hardstop'
    },
    'ctrl_msg': 'PAUSE'
}

REPORT = 'EPISODE_MNGR_REPORT'
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
    with ModelBridgeServer() as server:
        print('Waiting for sim connection...')
        server.accept()

        # Keep track of the last report, to detect new once
        last_episode_num = None

        graph = TestGrapher(save_dir=args.test_dir)

        for i in trange(len(iterations), desc="Total Progress"):
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

            # request state from BHV_agent to validate pEpisodeManager state
            instr_action = {
                'speed': 0.0,
                'course': 0.0,
                'posts': {},
                'ctrl_msg': 'SEND_STATE'
            }
            server.send_instr(instr_action)
            MOOS_STATE = server.listen_state()
            if MOOS_STATE['EPISODE_MNGR_STATE'] != 'PAUSED':
                tqdm.write('Waiting for pEpisodeManager...')
            while MOOS_STATE['EPISODE_MNGR_STATE'] != 'PAUSED':
                # Request state and read until pEpisode manager is online
                server.send_instr(instr_action)
                MOOS_STATE = server.listen_state()

            # Start pEpisode manager
            instr_action['posts'] = {
                'EPISODE_MNGR_CTRL': 'type=start'
            }
            server.send_instr(instr_action)
            while episode_count <= EPISODES_PER_TEST:
                #print(f'iteration {iteration}')
                #print(f'episode_count {episode_count}')

                MOOS_STATE = server.listen_state()
                MOOS_STATE[REPORT] = parse_report(MOOS_STATE[REPORT])

                # Detect new episode
                if MOOS_STATE[REPORT] is None:
                    # Sanity checks
                    assert i == 0
                    assert episode_count == 0
                elif last_episode_num != MOOS_STATE[REPORT]['EPISODE']:
                    #tqdm.write(f'Report: {MOOS_STATE[REPORT]}')
                    last_episode_num = MOOS_STATE[REPORT]['EPISODE']

                    if MOOS_STATE[REPORT]['DURATION'] < 1:
                        tqdm.write("WARNING: discarding episode due to small duration", file=sys.stderr)
                        last_episode_num = MOOS_STATE[REPORT]['EPISODE']
                    else:
                        tqdm.write(f'Finished episode #{episode_count}')
                        p.update(1)
                        
                        durations.append(MOOS_STATE[REPORT]['DURATION'])

                        episode_count += 1
                        if MOOS_STATE[REPORT]['SUCCESS']:
                            success_count += 1
                        
                        # If we are done with this trail set, send pause instr
                        if episode_count == EPISODES_PER_TEST:
                            server.send_instr(PAUSE_INSTR)
                            break # Break so we don't send an action 

                # Construct pLearn state
                pLearn_state = make_state(const.state, const.num_states, MOOS_STATE)
                pLearn_state = state2vec(pLearn_state, const)

                # Find optimal action
                optimal = (0, None)
                for a in PLEARN_ACTIONS:
                    value = models[a].predict(pLearn_state)

                    if optimal[1] is None or optimal[0] < value:
                        optimal = (value, PLEARN_ACTIONS[a])
                # Send optimal action to BHV_Agent client
                instr_action['course'] = optimal[1]['course']
                instr_action['speed'] = optimal[1]['speed']
                instr_action['posts'] = {}
                
                flag_dist = abs(dist((MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y']), ENEMY_FLAG))
                if flag_dist < 10:
                    instr_action['posts']['FLAG_GRAB_REQUEST'] = f'vname={MOOS_STATE["VNAME"]}'
                
                server.send_instr(instr_action)

                # Store min flag dist for scoring
                if min_flag_dist is None or flag_dist < min_flag_dist:
                    min_flag_dist = flag_dist
                # Calculate the dtime from last_helm_time for debugging
                if last_helm_time is not None:
                    time_deltas.append(MOOS_STATE['HELM_TIME'] - last_helm_time)
                last_helm_time = MOOS_STATE['HELM_TIME']
            
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