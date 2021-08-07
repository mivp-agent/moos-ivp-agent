#!/usr/bin/env python3
import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
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

class TestGrapher:
    def __init__(self, save_dir=None):
      # Parse args
      self.save_dir = save_dir

      # Setup matplotlib
      matplotlib.use('TkAgg')
      plt.ion()

      # Configure axes
      self.fig, self.axs = plt.subplots(2,2)
      self.axs[0, 0].set_title("Success Precent")
      self.success, = self.axs[0,0].plot([], [], '-go')
      self.axs[0,0].set_ylim(-5,100)

      self.axs[0, 1].set_title("Min Dist to Flag")
      self.min_dist, = self.axs[0,1].plot([], [], '-bo')

      self.axs[1, 0].set_title("Avg Durration")
      self.avg_duration, = self.axs[1,0].plot([], [], '-mo')
      self.axs[1,0].set_ylim(0,100)

      self.other, = self.axs[1,1].plot([], [], '-ro')

      # Stylisitic details
      self.fig.tight_layout(pad=2.0)
      self.fig.set_size_inches(8, 7)
      
      # Create data structures
      self.iters = []
      self.success_data = []
      self.min_dist_data = []
      self.avg_duration_data = []
      self.other_data = []
      self.max_iter = -1

      # Show graph just for the nice-ness factor :)
      self._plot()

    
    def add_iteration(self, iter, success_pcnt, min_dist, avg_duration, other, plot=True):
      self.iters.append(iter)
      self.success_data.append(success_pcnt)
      self.min_dist_data.append(min_dist)
      self.avg_duration_data.append(avg_duration)
      self.other_data.append(other)

      if iter > self.max_iter:
        self.max_iter = iter

      if plot:
        self._plot()

    def _plot(self):
      right_bound = max(self.max_iter, 1) # So matplotlib doesn yell about set_xlim(0,0)

      self.success.set_data(self.iters, self.success_data)
      self.axs[0,0].set_xlim(0, right_bound)

      self.min_dist.set_data(self.iters, self.min_dist_data)
      self.axs[0,1].relim()
      self.axs[0,1].set_xlim(0, right_bound)
      self.axs[0,1].autoscale()

      self.avg_duration.set_data(self.iters, self.avg_duration_data)
      self.axs[1,0].set_xlim(0, right_bound)

      self.other.set_data(self.iters, self.other_data)
      self.axs[1,1].relim()
      self.axs[1,1].set_xlim(0, right_bound)
      self.axs[1,1].autoscale()


      self.fig.canvas.draw()
      self.fig.canvas.flush_events()

      if self.save_dir != None:
        plt.savefig(os.path.join(self.save_dir, 'test_graph.png'))


      