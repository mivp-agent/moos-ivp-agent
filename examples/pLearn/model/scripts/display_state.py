#!/usr/bin/env python3
import time
import os, sys
THISDIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(THISDIR, '../'))

from state import make_state
from trained.topModel.environment import Constants

from mivp_agent.bridge import ModelBridgeServer

const = Constants()

with ModelBridgeServer() as server:
    print('Accepting server connection....')
    server.accept()

    last_time = 0

    while True:
        MOOS_STATE = server.listen_state()
        
        print('@@@@@@@@@@@@@@@@@@@@@@ MOOS @@@@@@@@@@@@@@@@@@@@@@@@@')
        print(MOOS_STATE)
        state = make_state(const.state, const.num_states, MOOS_STATE)
        print('====================== pLearn =========================')
        print(state)
        print(f'Elapsed time: {MOOS_STATE["HELM_TIME"]-last_time}')
        last_time = MOOS_STATE['HELM_TIME']