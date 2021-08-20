import os
import time
import json 
import numpy as np

from mivp_agent.aquaticus.field import FieldDiscretizer
from model.util.constants import LEARNING_RATE, DISCOUNT
from model.util.constants import ACTION_SPACE_SIZE, FIELD_RESOLUTION
from model.util.constants import QTABLE_INIT_HIGH, QTABLE_INIT_LOW

def construct_qtable(shape, print_shape=False):
  table = np.random.uniform(
    low=QTABLE_INIT_LOW,
    high=QTABLE_INIT_HIGH,
    size=shape
  )

  if print_shape:
    print(f'QTable shape: {table.shape}')
  
  return table

def load_model(path):
  config_path = os.path.dirname(path)
  config_path = os.path.join(config_path, 'config.json')

  config = None
  with open(config_path, 'r') as config_file:
    config = json.load(config_file)

  q = QLearn(
    lr=config['lr'],
    gamma=config['gamma'],
    action_space_size=config['action_space_size'],
    field_res=config['field_res']
  )
  qtable = np.load(path)
  q._qtable = qtable

  return q, config['attack_actions'], config['retreat_actions']

class QLearn:
  def __init__(
    self,
    lr=LEARNING_RATE,
    gamma=DISCOUNT,
    action_space_size=ACTION_SPACE_SIZE,
    field_res=FIELD_RESOLUTION,
    save_dir=None,
    verbose=False
  ):
    self._lr = lr
    self._gamma = gamma
    self._action_space_size = ACTION_SPACE_SIZE
    self._field_res = field_res
    self.save_dir = save_dir
    self.verbose = verbose

    # Initalize the continous -> discrete mapping
    self._discrete_field = FieldDiscretizer(resolution=self._field_res)

    # Initalize qtable
    self._qtable_shape = (
      self._discrete_field.space_size, # For own position
      self._discrete_field.space_size, # For enemy position
      2, # For has flag boolean
      self._action_space_size # Google 'Q learning' / QTable
    )
    self._qtable = construct_qtable(self._qtable_shape, print_shape=self.verbose)
  
  def get_state(self, own_x, own_y, enemy_x, enemy_y, has_flag):
    own_idx = self._discrete_field.to_discrete_idx(own_x, own_y)
    enemy_idx = self._discrete_field.to_discrete_idx(enemy_x, enemy_y)
    has_flag_idx = int(has_flag)

    return (own_idx, enemy_idx, has_flag_idx)

  def get_action(self, state, e=None):
    # If called with epsilon value, run e-greedy
    if e is not None:
      min(max(0, e), 1)
      
      if np.random.random() < e:
        return np.random.randint(0, self._action_space_size)
    
    # If e-greedy didn't choose random or not egreedy, take expected optimal action
    return np.argmax(self._qtable[state])
  
  def update_table(self, state, action, reward, new_state):
    expected_future_q = np.max(self._qtable[new_state])
    existing_q = self._qtable[state + (action,)]

    # Update the qtable
    updated_q = (1 - self._lr) * existing_q + self._lr * (reward + self._gamma * expected_future_q)
    self._qtable[state + (action,)] = updated_q
  
  # Used at the goal state, as there is no future state b/c robot get's reset
  def set_qvalue(self, state, action, q):
    self._qtable[state + (action,)] = q
  
  def save(self, attack_actions, retreat_actions, save_dir=None, name=None):
    if save_dir is None:
      if self.save_dir is None:
        raise RuntimeError('Model cannot save without save_dir')
      save_dir = self.save_dir
    
    if name is None:
      name = round(time.time())
    
    if not os.path.isdir(save_dir):
      os.makedirs(save_dir)
    
    config_path = os.path.join(save_dir, 'config.json')
    if not os.path.isfile(config_path):
      # Construct config dict
      config = {
        'lr': self._lr,
        'gamma': self._gamma,
        'action_space_size': self._action_space_size,
        'attack_actions': attack_actions,
        'retreat_actions': retreat_actions,
        'field_res': self._field_res,
        'qtable_shape': self._qtable_shape
      }

      with open(os.path.join(save_dir, 'config.json'), 'w') as config_file:
        json.dump(config, config_file, indent=4)

    # Save model
    np.save(os.path.join(save_dir, f'{name}.npy'), self._qtable)
  
