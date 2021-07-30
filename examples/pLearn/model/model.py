#!/usr/bin/env python3
import os
THISDIR = os.path.dirname(os.path.realpath(__file__))

import numpy as np
from keras.models import load_model
from trained.topModel.environment import Constants

from RLquaticus.bridge import ModelBridgeServer
from RLquaticus.util.display import ModelConsole
from state import make_state


PLEARN_TOPMODEL = os.path.join(THISDIR, 'trained/topModel')
PLEARN_ACTIONS = {
    '(2, 0)': {'speed':2.0, 'course':0.0, 'MOOS_VARS': ()},
    '(2, 60)': {'speed':2.0, 'course':60.0, 'MOOS_VARS': ()},
    '(2, 120)': {'speed':2.0, 'course':120.0, 'MOOS_VARS': ()},
    '(2, 180)': {'speed':2.0, 'course':180.0, 'MOOS_VARS': ()},
    '(2, 240)': {'speed':2.0, 'course':240.0, 'MOOS_VARS': ()},
    '(2, 300)': {'speed':2.0, 'course':300.0, 'MOOS_VARS': ()}
}

def state2vec(s, const):
    #print("state2vec")
    if(s==None):
        print("NULL STATE")
    temp = []
    #print("Preprocessed State: "+str(s))
    for state in s:
        temp.append(float(state))
    temp.append(1)
    for param in const.state:
        #print("on "+param)
        if const.state[param].standardized:
            if const.state[param].type != "binary":
                temp[const.state[param].index]=float(int(temp[Constants.state[param].index])-Constants.state[param].range[0])/Constants.state[param].range[1]
    #print("state2Vec finishing with value: "+str(temp))
    return np.array([temp])

if __name__ == '__main__':
    const = Constants()
    models = {}

    print('Loading model...')
    if const.alg_type == "fitted":
        for a in PLEARN_ACTIONS:
            models[a] = load_model(f'{PLEARN_TOPMODEL}/{a}.h5')
    else:
        raise TypeError(f'Unimplmented pLearn algorithm "{const.alg_type}"')

    print('Starting server...')
    with ModelBridgeServer() as server:
        server.accept() # This will block until cleint connects

        MOOS_STATE = None
        model_state = None
        console = ModelConsole()
        while True:
            # Get state from BHV_Agent client and translate
            MOOS_STATE = server.listen_state()
            model_state = make_state(const.state, const.num_states, MOOS_STATE)
            state_vec = state2vec(model_state, const)

            # Find optimal action
            optimal = (0, None)
            for a in PLEARN_ACTIONS:
                value = models[a].predict(state_vec)

                if optimal[1] is None or optimal[0] < value:
                    optimal = (value, PLEARN_ACTIONS[a])

            # Send optimal action to BHV_Agent client
            server.send_action(optimal[1])

            console.tick(MOOS_STATE)