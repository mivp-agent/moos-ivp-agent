#!/usr/bin/env python3
import os
import sys
import argparse
import numpy as np
from tqdm.auto import trange
from tqdm.std import tqdm

from RLquaticus.bridge import ModelBridgeServer
from RLquaticus.util.display import ModelConsole
from RLquaticus.util.parse import parse_report
from state import make_state

from util.validate import check_test_dir
from util.constants import PLEARN_ACTIONS, JAYLAN_TESTDIR, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model
from util.graphing import TestGrapher

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

        for i in trange(len(iterations), desc="Models"):
            tqdm.write(f'Loading model #{i}...')
            model_path = os.path.join(args.test_dir, f'iteration_{i}')
            models, const = load_pLearn_model(model_path)

            # Assert pEpisodeManager is in PAUSED state
            tqdm.write('Waiting for pEpisodeManager...')
            MOOS_STATE, read = server.listen_state()
            graph.add_iteration(i, read, 0, 0)
            print(read)
            while MOOS_STATE['EPISODE_MNGR_STATE'] != 'PAUSED':
                #print(MOOS_STATE, file=sys.stderr)
                MOOS_STATE, read = server.listen_state()

            # Initalize trail set 
            iteration = 0
            episode_count = 0
            success_count = 0
            failure_count = 0
            server.send_must_post({
                    'EPISODE_MNGR_CTRL': 'type=start'
            })

            p = tqdm(total=EPISODES_PER_TEST, desc="Trails")
            while episode_count <= EPISODES_PER_TEST:
                #print(f'iteration {iteration}')
                #print(f'episode_count {episode_count}')
                    
                # Increment iteration
                iteration += 1

                MOOS_STATE, read = server.listen_state()
                MOOS_STATE[REPORT] = parse_report(MOOS_STATE[REPORT])

                # Detect new episode
                if MOOS_STATE[REPORT] is None:
                    # Sanity checks
                    assert i == 0
                    assert episode_count == 0
                elif last_episode_num != MOOS_STATE[REPORT]['EPISODE']:
                    tqdm.write(f'Finished episode #{episode_count}')
                    #tqdm.write(f'Report: {MOOS_STATE[REPORT]}')
                    last_episode_num = MOOS_STATE[REPORT]['EPISODE']
                    iteration = 0

                    if MOOS_STATE[REPORT]['DURATION'] < 1:
                        tqdm.write("WARNING: discarding episode due to small duration", file=sys.stderr)
                        last_episode_num = MOOS_STATE[REPORT]['EPISODE']
                    else:
                        p.update(1)
                        episode_count += 1
                        if MOOS_STATE[REPORT]['SUCCESS']:
                            success_count += 1
                        else:
                            failure_count += 1

                        if episode_count == EPISODES_PER_TEST:
                            server.send_must_post({
                                'EPISODE_MNGR_CTRL': 'type=hardstop'
                            })
                            break

                # Construct pLearn state
                pLearn_state = make_state(const.state, const.num_states, MOOS_STATE)
                pLearn_state = state2vec(pLearn_state, const)

                # Find optimal action
                optimal = (0, None)
                for a in PLEARN_ACTIONS:
                    value = models[a].predict(pLearn_state)

                    if optimal[1] is None or optimal[0] < value:
                        optimal = (value, PLEARN_ACTIONS[a])
                action = optimal[1]

                # Add grab flag action if within flag bounds
                action['MOOS_VARS'] = {}
                if abs(dist((MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y']), ENEMY_FLAG)) < 10:
                    action['MOOS_VARS']['FLAG_GRAB_REQUEST'] = f'vname={MOOS_STATE["VNAME"]}'
                
                # Send action to BHV_Agent
                server.send_action(action)
            
            p.close()
            tqdm.write("\n========================================")
            tqdm.write(f"Report for model #{i}")
            tqdm.write(f"\npath: {model_path}")
            tqdm.write(f"\nSuccess: {success_count}")
            tqdm.write(f"Failure: {failure_count}")
            tqdm.write("========================================\n")
    
    
    input("\n\nPress any key to continue...")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test_dir', default=JAYLAN_TESTDIR)
    
    args = parser.parse_args()

    check_test_dir(args.test_dir)

    test_dir(args)