import os
THISDIR = os.path.dirname(os.path.realpath(__file__))

# Models
PLEARN_TOPMODEL = os.path.abspath(os.path.join(THISDIR, '../trained/topModel/model'))
JAYLAN_TESTDIR = os.path.abspath(os.path.join(THISDIR, '../trained/the-attack-of-jaylan'))

# Translate pLearn actions 
PLEARN_ACTIONS = {
    '(2, 0)': {'speed':2.0, 'course':0.0},
    '(2, 60)': {'speed':2.0, 'course':60.0},
    '(2, 120)': {'speed':2.0, 'course':120.0},
    '(2, 180)': {'speed':2.0, 'course':180.0},
    '(2, 240)': {'speed':2.0, 'course':240.0},
    '(2, 300)': {'speed':2.0, 'course':300.0}
}

# Aquaticus X/Y pairsx
UPPER_LEFT_CORNER = (-83,-49)
UPPER_RIGHT_CORNER = (56, 16)
LOWER_LEFT_CORNER = (-53, -114)
LOWER_RIGHT_CORNER = (82, -56)

MY_FLAG = (50.0, -24.0)
ENEMY_FLAG = (-58.0, -71.0)

def plearn_action_to_text(action):
    if action == '(2, 240)':
        return 'forward'
    elif action == '(2, 300)':
        return 'right'
    elif action == '(2, 0)':
        return 'hard right'
    elif action == '(2, 60)':
        return 'backward'
    elif action == '(2, 120)':
        return 'hard left'
    elif action == '(2, 180)':
        return 'left'