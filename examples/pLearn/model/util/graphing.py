#!/usr/bin/env python3
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

from tqdm import tqdm
from util.constants import PLEARN_ACTIONS

def plot_rewards(reward_function, defender=False):
  # Init lists to graph
  x_pos = []
  y_pos = []
  v_pos = []

  for x in tqdm(range(-85, 85, 4)):
    for y in range(-115, 20, 4):
      # Find the max value across all headings
      max_value = None 
      for action in PLEARN_ACTIONS:
        fake_state = {
          'NAV_X': x,
          'NAV_Y': y,
          'NAV_HEADING': PLEARN_ACTIONS[action]['course'],
          'TAGGED': False,
          'NODE_REPORTS': {
            'evan': {
              'NAV_X': 200,
              'NAV_Y': 200,
              'NAV_HEADING': 200,
            }
          }
        }

        value = reward_function(fake_state)

        if max_value is None or value > max_value:
          max_value = value
      
      v_pos.append(max_value.item(0))
      x_pos.append(x)
      y_pos.append(y)

  fig = plt.figure()
  ax = plt.axes(projection='3d')

  # Do the plotting
  ax.plot([56,-83,-53,82,56], [16,-49,-114,-56,16], 'red', linewidth=4)
  ax.plot_trisurf(x_pos, y_pos, v_pos)

  plt.show()



      