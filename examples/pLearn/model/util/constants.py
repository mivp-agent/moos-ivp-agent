import os
THISDIR = os.path.dirname(os.path.realpath(__file__))

# Models
PLEARN_TOPMODEL = os.path.abspath(os.path.join(THISDIR, '../trained/topModel'))

# Translate pLearn actions 
PLEARN_ACTIONS = {
    '(2, 0)': {'speed':2.0, 'course':0.0, 'MOOS_VARS': {}},
    '(2, 60)': {'speed':2.0, 'course':60.0, 'MOOS_VARS': {}},
    '(2, 120)': {'speed':2.0, 'course':120.0, 'MOOS_VARS': {}},
    '(2, 180)': {'speed':2.0, 'course':180.0, 'MOOS_VARS': {}},
    '(2, 240)': {'speed':2.0, 'course':240.0, 'MOOS_VARS': {}},
    '(2, 300)': {'speed':2.0, 'course':300.0, 'MOOS_VARS': {}}
}

# Aquaticus X/Y pairsx
UPPER_LEFT_CORNER = (-83,-49)
UPPER_RIGHT_CORNER = (56, 16)
LOWER_LEFT_CORNER = (-53, -114)
LOWER_RIGHT_CORNER = (82, -56)

MY_FLAG = (50.0, -24.0)
ENEMY_FLAG = (-58.0, -71.0)