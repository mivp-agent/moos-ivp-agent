import os, sys
currentdir = os.path.dirname(os.path.realpath(__file__))
parrent = os.path.join(os.path.dirname(currentdir), '..')
sys.path.append(parrent)

from keras.models import load_model
from util.constants import PLEARN_ACTIONS

def load_pLearn_model(model_dir, enviroment_dir=None):
  if enviroment_dir is not None:
    sys.path.append(enviroment_dir)
  else:
    sys.path.append(os.path.join(model_dir, '..'))
  from environment import Constants

  const = Constants()
  models = {}

  if const.alg_type == "fitted":
      for a in PLEARN_ACTIONS:
          models[a] = load_model(f'{model_dir}/{a}.h5')
  else:
      raise TypeError(f'Unimplmented pLearn algorithm "{const.alg_type}"')
  
  return models, const