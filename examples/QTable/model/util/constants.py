import os
from datetime import datetime

# Get this file's dirname for use later
DIRNAME = os.path.abspath(os.path.dirname(__file__))

LEARNING_RATE = 0.1
DISCOUNT = 0.95
EPISODES = 5000

EPSILON_START = 0.5
EPSILON_DECAY_START = 1
EPSILON_DECAY_END = EPISODES // 2 # Half way through
EPSILON_DECAY_AMT = EPSILON_START / (EPSILON_DECAY_END - EPSILON_DECAY_START)

FIELD_RESOLUTION=8

ACTIONS = [
    #{'speed':2.0, 'course':0.0},
    #{'speed':2.0, 'course':60.0},
    #{'speed':2.0, 'course':120.0},
    {'speed':2.0, 'course':180.0},
    {'speed':2.0, 'course':240.0},
    {'speed':2.0, 'course':300.0}
]
ACTION_SPACE_SIZE = len(ACTIONS)

REWARD_SUCCESS = 5
REWARD_FAILURE = -40
REWARD_STEP = -1

QTABLE_INIT_LOW = -2
QTABLE_INIT_HIGH = 0

SAVE_DIR = os.path.abspath(os.path.join(DIRNAME, '../../trained'))
SAVE_EVERY = 100

DEFAULT_RUN_MODEL = 'trained/1628500096/1628522198.npy'