#!/usr/bin/env python3
import sys
import warnings
import argparse
import numpy as np

warnings.filterwarnings("ignore", message=r"Passing", category=FutureWarning)

from mivp_agent.bridge import ModelBridgeServer
from mivp_agent.util.display import ModelConsole
from mivp_agent.util.parse import csp_to_dict
from state import make_state

from util.validate import check_model_dir
from util.constants import PLEARN_ACTIONS, PLEARN_TOPMODEL, ENEMY_FLAG
from util.state import state2vec, dist
from util.model_loader import load_pLearn_model
from util.graphing import DebugGrapher

def run_model(args):
    # Create instruction for use later
    instr_action = {
        'speed': 0.0,
        'course': 0.0,
        'posts': { # This will only be sent the first time, after that it is turrned off
            'EPISODE_MNGR_CTRL': 'type=start'
        },
        'ctrl_msg': 'SEND_STATE'
    }

    print('Loading model...')
    models, const = load_pLearn_model(args.model)

    graph = None
    if args.debug:
        graph = DebugGrapher()

    print('Starting server...')
    with ModelBridgeServer() as server:
        server.accept() # This will block until cleint connects

        MOOS_STATE = None
        model_state = None
        console = ModelConsole()

        # Send a dummy instr to get a state back
        server.send_instr(instr_action)
        while True:
            # Get state from BHV_Agent client and translate
            MOOS_STATE = server.listen_state()
            if MOOS_STATE['EPISODE_MNGR_REPORT'] is not None:
                report = csp_to_dict(MOOS_STATE['EPISODE_MNGR_REPORT'])
                report['DURATION'] = float(report['DURATION'])

                if report['DURATION'] < 4:
                    print('ERROR: Small duration value', file=sys.stderr)
                    print(report, file=sys.stderr)
                #print(report)
                
            model_state = make_state(const.state, const.num_states, MOOS_STATE)
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

            # Send optimal action to BHV_Agent client
            instr_action['course'] = optimal[1]['course']
            instr_action['speed'] = optimal[1]['speed']
            instr_action['posts'] = {}
            
            if abs(dist((MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y']), ENEMY_FLAG)) < 10:
                instr_action['posts']['FLAG_GRAB_REQUEST'] = f'vname={MOOS_STATE["VNAME"]}'
            
            server.send_instr(instr_action)
            console.tick(MOOS_STATE)
            if args.debug and console.iteration % 6 == 0:
                graph.add_iteration(console.iteration, values, console.last_MOOS_delta)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=PLEARN_TOPMODEL)
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args()

    check_model_dir(args.model)

    run_model(args)