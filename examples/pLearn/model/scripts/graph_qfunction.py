#!/usr/bin/env python3
import os, sys
import matplotlib
currentdir = os.path.dirname(os.path.realpath(__file__))
parrent = os.path.join(os.path.dirname(currentdir), '..')
sys.path.append(parrent)

from matplotlib.pyplot import plot
matplotlib.use('TkAgg') # For X11 forwarding in docker

from util.graphing import plot_rewards

import argparse
from keras.models import load_model
from trained.topModel.environment import Constants

from state import make_state
from util.validate import check_model_dir
from util.constants import PLEARN_ACTIONS, PLEARN_TOPMODEL
from util.state import state2vec

def graph_model(args):
    const = Constants()
    models = {}

    print('Loading model...')
    if const.alg_type == "fitted":
        for a in PLEARN_ACTIONS:
            models[a] = load_model(f'{args.model}/{a}.h5')
    else:
        raise TypeError(f'Unimplmented pLearn algorithm "{const.alg_type}"')

    def max_q_reward(MOOS_STATE):
      # Get state from BHV_Agent client and translate
      model_state = make_state(const.state, const.num_states, MOOS_STATE)
      state_vec = state2vec(model_state, const)

      # Find optimal action
      optimal = (0, None)
      for a in PLEARN_ACTIONS:
          value = models[a].predict(state_vec)

          if optimal[1] is None or optimal[0] < value:
              optimal = (value, PLEARN_ACTIONS[a])

      return optimal[0] # Return the value assocaited with the optimal value
    
    plot_rewards(max_q_reward)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=PLEARN_TOPMODEL)
    
    args = parser.parse_args()

    print(args.model)
    check_model_dir(args.model)

    graph_model(args)