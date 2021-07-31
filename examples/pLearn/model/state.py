import math
from typing import Type

from util.constants import UPPER_LEFT_CORNER, UPPER_RIGHT_CORNER, LOWER_LEFT_CORNER, LOWER_RIGHT_CORNER
from util.constants import MY_FLAG, ENEMY_FLAG

# From: https://github.com/mnovitzky/moos-ivp-pLearn/blob/master/src/lib_behaviors-test/BHV_Input.cpp#L656
def process_dist(goal_x, goal_y, bucket_size, x, y):
  dist = math.sqrt(pow(x-goal_x, 2)+pow(y-goal_y,2))
  return dist/bucket_size

# From: https://github.com/mnovitzky/moos-ivp-pLearn/blob/master/src/lib_behaviors-test/BHV_Input.cpp#L662
def process_angle(goal_x, goal_y, bucket_size, x, y, nav_heading=None):
  theta = math.atan2(y-goal_y, x-goal_x)*180/math.pi
  
  if nav_heading is not None:
    theta=90+nav_heading+theta
  
  if theta < 0:
    theta += 360
  
  return theta/bucket_size

# From: https://github.com/mnovitzky/moos-ivp-pLearn/blob/master/src/lib_behaviors-test/BHV_Input.cpp#L694
def process_tagged(MOOS_STATE):
  if MOOS_STATE['TAGGED']:
    return 1.0
  x = MOOS_STATE['NAV_X'] + 53
  y = MOOS_STATE['NAV_Y'] + 114

  x_proj=x*.908+y*.41906
  y_proj=-x*.41906+y*.908

  if x_proj<0 or x_proj>146 or y_proj<0 or y_proj>71:
    return 1.0
  return 0.0

# From: https://github.com/mnovitzky/moos-ivp-pLearn/blob/master/src/lib_behaviors-test/BHV_Input.cpp#L716
def process_bound(x, y, side):

  a_vehicle = b_vehicle = c_vehicle = None
  a_bound = b_bound = c_bound = None

  # Idk about math below... just translating from the link above
  if(side == "left" or side == "right"):
    a_vehicle = -65
    b_vehicle = 139
    c_vehicle = a_vehicle*x + b_vehicle*y
    a_bound = -65
    b_bound = 30
  else:
    a_vehicle = 65
    b_vehicle = 30
    c_vehicle = a_vehicle*x + b_vehicle*y
    a_bound = -65
    b_bound = 189
  
  if side == 'left':
    a_bound = UPPER_LEFT_CORNER[1]-LOWER_LEFT_CORNER[1]
    b_bound = -(UPPER_LEFT_CORNER[0]-LOWER_LEFT_CORNER[0])
    c_bound = a_bound*(UPPER_LEFT_CORNER[0])+b_bound*(UPPER_LEFT_CORNER[1])

  elif(side == "up"):
    a_bound = UPPER_LEFT_CORNER[1]-UPPER_RIGHT_CORNER[1]
    b_bound = -(UPPER_LEFT_CORNER[0]-UPPER_RIGHT_CORNER[0])
    c_bound = a_bound*(UPPER_LEFT_CORNER[0])+b_bound*(UPPER_LEFT_CORNER[1])
  elif(side == "right"):
    a_bound = UPPER_RIGHT_CORNER[1]-LOWER_RIGHT_CORNER[1]
    b_bound = -(UPPER_RIGHT_CORNER[0]-LOWER_RIGHT_CORNER[0])
    c_bound = a_bound*(UPPER_RIGHT_CORNER[0])+b_bound*(UPPER_RIGHT_CORNER[1])
  elif(side == "down"):
    a_bound = LOWER_LEFT_CORNER[1]-LOWER_RIGHT_CORNER[1]
    b_bound = -(LOWER_LEFT_CORNER[0]-LOWER_RIGHT_CORNER[0])
    c_bound = a_bound*(LOWER_LEFT_CORNER[0])+b_bound*(LOWER_LEFT_CORNER[1])
  
  determinant = a_vehicle*b_bound-a_bound*b_vehicle

  if determinant == 0:
    return 0
  else:
    x_intercept = (b_bound*c_vehicle - c_bound*b_vehicle)/determinant
    y_intercept = (a_vehicle*c_bound - a_bound*c_vehicle)/determinant

    return process_dist(x_intercept, y_intercept, 1, x, y)
  

def make_state(state_request, num_states, MOOS_STATE):
  state = [0.0]*num_states

  for key in state_request:
    entry = state_request[key]
    
    if entry.type == 'binary':
      if entry.var == 'team':
        state[entry.index] = 0.0 # Only support red team
      elif entry.var == 'tagged':
        state[entry.index] = process_tagged(MOOS_STATE)
      else:
        raise TypeError(f'Unimplemented pLearn state condition')

    elif entry.type == 'distance':
      if entry.vehicle == 'self':
        if entry.var == 'flag':
          if entry.var_mod == 'self':
            state[entry.index] = process_dist(MY_FLAG[0], MY_FLAG[1], entry.bucket, MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'])
          elif entry.var_mod == 'enemy':
            state[entry.index] = process_dist(ENEMY_FLAG[0], ENEMY_FLAG[1], entry.bucket, MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'])
          else:
            raise TypeError(f'Unimplemented pLearn state condition')
        elif entry.var == 'leftBound':
          state[entry.index] = process_bound(MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'], 'left')
        elif entry.var == 'rightBound':
          state[entry.index] = process_bound(MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'], 'right')
        elif entry.var == 'upperBound':
          state[entry.index] = process_bound(MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'], 'up')
        elif entry.var == 'lowerBound':
          state[entry.index] = process_bound(MOOS_STATE['NAV_X'], MOOS_STATE['NAV_Y'], 'down')
        else:
          raise TypeError(f'Unimplemented pLearn state condition')
      else:
        if entry.vehicle not in MOOS_STATE['NODE_REPORTS']:
          raise RuntimeError(f'Vehicle {entry.vehicle} is not in NODE_REPORTS')
        if entry.var == 'player':
          state[entry.index] = process_dist(
            MOOS_STATE['NAV_X'],
            MOOS_STATE['NAV_Y'],
            entry.bucket,
            MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_X'],
            MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_Y']
          )
        else:
          raise TypeError(f'Unimplemented pLearn state condition')

    elif entry.type == 'angle':
      if entry.vehicle == 'self':
        if entry.var == 'flag':
          if entry.var_mod == 'self':
            state[entry.index] = process_angle(
              MY_FLAG[0],
              MY_FLAG[1],
              entry.bucket,
              MOOS_STATE['NAV_X'],
              MOOS_STATE['NAV_Y']
            )
          elif entry.var_mod == 'enemy':
            state[entry.index] = process_angle(
              ENEMY_FLAG[0],
              ENEMY_FLAG[1],
              entry.bucket,
              MOOS_STATE['NAV_X'],
              MOOS_STATE['NAV_Y']
            )
          else:
            raise TypeError(f'Unimplemented pLearn state condition')
        else:
          raise TypeError(f'Unimplemented pLearn state condition')
      else:
        if entry.vehicle not in MOOS_STATE['NODE_REPORTS']:
          raise RuntimeError(f'Vehicle {entry.vehicle} is not in NODE_REPORTS')
        
        if entry.var == 'flag':
          if entry.var_mod == 'self':
            state[entry.index] = process_angle(
              MY_FLAG[0],
              MY_FLAG[1],
              entry.bucket,
              MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_X'],
              MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_Y']
            )
          elif entry.var_mod == 'enemy':
            state[entry.index] = process_angle(
              ENEMY_FLAG[0],
              ENEMY_FLAG[1],
              entry.bucket,
              MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_X'],
              MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_Y']
            )
          else:
            raise TypeError(f'Unimplemented pLearn state condition')
        elif entry.var == 'player':
          state[entry.index] = process_angle(
            MOOS_STATE['NAV_X'],
            MOOS_STATE['NAV_Y'],
            entry.bucket,
            MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_X'],
            MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_Y']
          )
        else:
          raise TypeError(f'Unimplemented pLearn state condition') 
    elif entry.type == 'raw':
      if entry.vehicle == 'self':
        if entry.var == 'x':
          state[entry.index] = MOOS_STATE['NAV_X']/entry.bucket
        elif entry.var == 'y':
          state[entry.index] = MOOS_STATE['NAV_Y']/entry.bucket
        elif entry.var == 'heading':
          state[entry.index] = MOOS_STATE['NAV_HEADING']/entry.bucket
        else:
          raise TypeError(f'Unimplemented pLearn state condition') 
      else:
        if entry.vehicle not in MOOS_STATE['NODE_REPORTS']:
          raise RuntimeError(f'Vehicle {entry.vehicle} is not in NODE_REPORTS')
        
        if entry.var == 'heading':
          state[entry.index] = MOOS_STATE['NODE_REPORTS'][entry.vehicle]['NAV_HEADING']
        else:
          raise TypeError(f'Unimplemented pLearn state condition') 

    else:
        raise TypeError(f'Unimplemented pLearn state condition')
  
  return state
      
