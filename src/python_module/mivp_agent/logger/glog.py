import os
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from tqdm import tqdm

from mivp_agent.aquaticus.const import FIELD_CORNERS
from mivp_agent.aquaticus.field import FieldDiscretizer
from mivp_agent.proto.mivp_agent_pb2 import Transition
from mivp_agent.proto.proto_logger import ProtoLogger

def ani_surface(x_bounds, y_bounds, step, ax=None, figsize=(12,10)):
  assert isinstance(x_bounds, tuple), "x_bounds must be tuple of len 2"
  assert len(x_bounds), "x_bounds must be tuple of len 2"
  assert isinstance(y_bounds, tuple), "y_bounds must be tuple of len 2"
  assert len(y_bounds), "y_bounds must be tuple of len 2"
  assert isinstance(step, float) or isinstance(step, int), "Step must be int or float"

  # Create plot if we were not given one
  if ax is not None:
    ax = plt.figure(figsize=(12,10)).gca(projection='3d')
  
  # Create indexes based on bounds and spacing
  x = np.arange(x_bounds[0], x_bounds[1], step)
  y = np.arange(y_bounds[0], y_bounds[1], step)

  # Create a "Mesh grid" the purpose is to at every point on a 2d plane, tell the graphing library what x,y to draw the point at. This cannot be done by simple python lists. See more info in this stack overflow answer: https://stackoverflow.com/a/49439331/11325551.
  XX, YY = np.meshgrid(x, y)

  def callback(z_vals):
    ax.clear()

    ax.plot_surface(XX, YY, z_vals, cmap=cm.RdYlGn)

    plt.draw()
    plt.show(block=False)

  return callback


def glog(path, discretizer=None):
  assert os.path.isdir(path), "Must point inspect to a path"

  

  log = ProtoLogger(path, Transition, mode='r')

def do_glog(transitions, discretizer=None, only=False):
  if discretizer is None:
      discretizer = FieldDiscretizer(resolution=10)

  # Create a matrix to store the counts at each x / y position 
  bins = np.zeros((len(discretizer._ys), len(discretizer._xs)))

  for i in tqdm(range(len(transitions))):
    t = transitions[i]
    #print(transitions)

    dis_point = discretizer.to_discrete_point(t.s1.vinfo.NAV_X, t.s1.vinfo.NAV_Y)

    # Make sure that point wasn't out of bounds
    if dis_point is not None:
      bin_x = discretizer._xs[dis_point[0]]
      bin_y = discretizer._ys[dis_point[1]]

      # Increase the count plotly takes the column (first index) as the y values
      bins[bin_y][bin_x] += 1

  #data = go.Bar(x=[1, 2, 3], y=[1, 3, 2])
  data = go.Surface(
    x=[x for x in discretizer._xs],
    y=[y for y in discretizer._ys],
    z=bins / np.max(bins)
  )

  # Below is to mark out the corners and put lines between them. The extra +'s are to add the first point twice otherwise there will not be a line from the last corner to the first.
  field_lines = go.Scatter3d(
    x=[c[0] for c in FIELD_CORNERS]+[FIELD_CORNERS[0][0]],
    y=[c[1] for c in FIELD_CORNERS]+[FIELD_CORNERS[0][1]],
    z=[0.3]*(len(FIELD_CORNERS)+1),
    line={
      'color': 'red',
      'width': 15
    }
  )
  fig = go.Figure(
    data=[data, field_lines],
    layout=go.Layout(
        title=go.layout.Title(text="Surface test"),
        xaxis_title="X Position",
        yaxis_title="Y Position",
    )
  )
  fig.show()