#!/usr/bin/env python3
import sys
import argparse
import numpy as np

from RLquaticus.bridge import ModelBridgeServer
from RLquaticus.util.display import ModelConsole
from RLquaticus.util.parse import csp_to_dict
from state import make_state

from util.validate import check_model_dir
from util.constants import PLEARN_ACTIONS, PLEARN_TOPMODEL, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model

def run_model(args):
    print('Loading model...')
    models, const = load_pLearn_model(args.model)

    print('Starting server...')
    with ModelBridgeServer() as server:
        server.accept() # This will block until cleint connects

        MOOS_STATE = None
        model_state = None
        console = ModelConsole()
        while True:
            # Get state from BHV_Agent client and translate
            MOOS_STATE = server.listen_state()
            if MOOS_STATE['EPISODE_MNGR_REPORT'] is not None:
                report = csp_to_dict(MOOS_STATE['EPISODE_MNGR_REPORT'])
                report['DURATION'] = float(report['DURATION'])

                if report['DURATION'] < 4:
                    print('ERROR: Small duration value', file=sys.stderr)
                    print(report, file=sys.stderr)
                print(report)
                
            model_state = make_state(const.state, const.num_states, MOOS_STATE)
            state_vec = state2vec(model_state, const)

            # Find optimal action
            optimal = (0, None)
            for a in PLEARN_ACTIONS:
                value = models[a].predict(state_vec)

                if optimal[1] is None or optimal[0] < value:
                    optimal = (value, PLEARN_ACTIONS[a])

            # Send optimal action to BHV_Agent client
            action = optimal[1]
            action['MOOS_VARS'] = {}
            
            if abs(dist((MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y']), ENEMY_FLAG)) < 10:
                action['MOOS_VARS']['FLAG_GRAB_REQUEST'] = f'vname={MOOS_STATE["VNAME"]}'
            if console.iteration == 0:
                server.send_must_post({
                    'EPISODE_MNGR_CTRL': 'type=start'
                })
            server.send_action(optimal[1])

            console.tick(MOOS_STATE)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=PLEARN_TOPMODEL)
    
    args = parser.parse_args()

    check_model_dir(args.model)

    run_model(args)