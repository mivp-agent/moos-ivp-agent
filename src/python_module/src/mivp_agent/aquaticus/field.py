import numpy as np
import matplotlib
import matplotlib.pyplot as plt

from mivp_agent.aquaticus.const import FIELD_CORNERS
from mivp_agent.aquaticus.const import FIELD_UL_NUMPY, FIELD_UR_NUMPY
from mivp_agent.aquaticus.const import FIELD_LL_NUMPY, FIELD_LR_NUMPY
from mivp_agent.aquaticus.const import FIELD_RED_FLAG, FIELD_BLUE_FLAG

FIELD_OUT_BOUNDS_POINT = (30, 10)

def dist_line(l, p):
  return np.cross(l[0]-l[1], p-l[1])/np.linalg.norm(l[0]-l[1])

def in_bounds(p):
  # Check if above the top line
  if dist_line((FIELD_UR_NUMPY, FIELD_UL_NUMPY), p) > 0:
    return False
  # Check if below the bottom line
  if dist_line((FIELD_LR_NUMPY, FIELD_LL_NUMPY), p) < 0:
    return False
  # Check if to left of left line
  if dist_line((FIELD_UL_NUMPY, FIELD_LL_NUMPY), p) > 0:
    return False
  # Check if to right of right line
  if dist_line((FIELD_UR_NUMPY, FIELD_LR_NUMPY), p) < 0:
    return False
  return True

def construct_field_figure(
  corners=FIELD_CORNERS,
  red_flag=FIELD_RED_FLAG,
  blue_flag=FIELD_BLUE_FLAG,
  flag_radius=10,
  useTkAgg=True):

  # TkAgg plays nicely with X server but adds dependencies
  if useTkAgg:
    matplotlib.use('TkAgg')
  
  # Create plot
  fig, ax = plt.subplots()

  # Set stylistic things
  fig.canvas.manager.set_window_title('Aquaticus Field')
  fig.set_size_inches(9, 7)

  # Construct a list of the xs and ys of the corners
  corner_xs = [c[0] for c in corners]
  corner_ys = [c[1] for c in corners]
  # Add the first corner twice so we get a full loop
  corner_xs.append(corners[0][0])
  corner_ys.append(corners[0][1])
  # Plot the outline given these cornerns
  ax.plot(corner_xs, corner_ys, 'y')

  # Plot the flag circles
  circle_red = plt.Circle(red_flag, flag_radius, color='red', fill=False, linewidth=3)
  circle_blue = plt.Circle(blue_flag, flag_radius, color='blue', fill=False, linewidth=3)
  ax.add_artist(circle_red)
  ax.add_artist(circle_blue)

  return fig, ax

class FieldDiscretizer:
  '''
  This utility is used to transform the continuous 2d spaces into a 1d discretized space with variable resolution. The method of doing so was adapted from [this source](https://stackoverflow.com/questions/62778939/python-fastest-way-to-map-continuous-coordinates-to-discrete-grid). By default it used the MIT aquaticus field lines to define the 2d space.

  The discrete space is a 0...n space where 0 represents an input that is **outside** the continuous space.

  See 
  [`to_discrete_idx()`][mivp_agent.aquaticus.field.FieldDiscretizer.to_discrete_idx] for the primary means of translation.
  '''
  def __init__(self, resolution=6):
    '''
    Args:
      resolution (int): This was named **poorly**. It is not the resolution but the opposite. This variable represents the step size used between discrete points. Incresing this parameter will result in a discrete space of smaller size.
    '''
    # Find the min/max x and y in the field
    min = None
    max = None
    for c in FIELD_CORNERS:
      if min is None:
        min = list(c) # Change to list for mutability
      else:
        if min[0] > c[0]:
          min[0] = c[0]
        elif min[1] > c[1]:
          min[1] = c[1]

      if max is None:
        max = list(c)
      else:
        if max[0] < c[0]:
          max[0] = c[0]
        if max[1] < c[1]:
          max[1] = c[1]
    
    # Define the offset (starting point) for our grid
    self._offset = np.array([min[0], min[1]])
    # Define the spacing (resolution) for the grid
    self._spacing = np.array([resolution, resolution])
  
    # Create map between grid points and an index (different than the reference's use of index)
    index = 1
    self._point_idx_map = {
      None: 0 # Used for points off the field
    }
    self._idx_point_map = [None]

    # The below maps the space we are creating to 0...n values for both x and y. This is useful when later binning / counting the occurrences of data in after collected. For example if we have a grid x,y we can create a counter where `count[0][0]` is the count of the first discrete point on our grid. But our discrete grid starts at whatever `min` is no zero. So we must map from the discrete x,y to these indexes in the counter. We do this through `enumerate(range(....))` to map from some x to 0...n.
    # Note: Most times, len(self._xs) and len(self._ys) will not be the same size, and contain values for x & y values which will never be mapped to. This is to make storage in arrays easy too (easy to define a count[n][m]).
    self._xs = {x:i for i, x in enumerate(range(min[0], max[0]+1, resolution))}
    self._ys = {y:i for i, y in enumerate(range(min[1], max[1]+1, resolution))}

    # Interate through the x, y values to find the ones in range
    for x in self._xs:
      for y in self._ys:
        # Add to map if in bounds 
        if in_bounds(np.array([x,y])):
          self._point_idx_map[(x,y)] = index
          index += 1
          self._idx_point_map.append((x,y))
    
    self.space_size = len(self._point_idx_map)
    # Sanity check
    assert self.space_size == len(self._idx_point_map)
  
  def to_discrete_point(self, nav_x, nav_y):
    '''
    This method translates continuous x / y coordinates into discrete x / y coordinates.

    Args:
      nav_x (float): A continuous x coordinate
      nav_y (float): A continuous y coordinate
    
    Returns:
      tuple/None: Will return a `tuple` with (x, y) of type `int` or `None` if the input is outside of the defined space.
    '''
    d = self._offset + np.round((np.array([nav_x, nav_y]) - self._offset) / self._spacing) * self._spacing
    d = tuple(d.astype(int))

    # Handle out of feild positions
    if d not in self._point_idx_map:
      return None

    return d
  
  def to_discrete_idx(self, nav_x, nav_y):
    '''
    This method translates continuous x / y coordinates into discrete 0...n index. 0 indicates that the input was outside of the defined 2d space.

    Args:
      nav_x (float): A continuous x coordinate
      nav_y (float): A continuous y coordinate
    
    Returns:
      int: A discrete index corresponding to a unique point on the 2d discrete field.
    '''
    d = self.to_discrete_point(nav_x, nav_y)
    return self._point_idx_map[d]
  
  def idx_to_discrete_point(self, idx):
    if idx >= self.space_size:
      raise ValueError('Index is outside of discrete space')
    
    return self._idx_point_map[idx]
  
class DiscreteFieldGrapher:
  '''
  This utility uses matplotlib to graph vehicles in descrete positions as defined by an instance of [`FieldDiscretizer`][mivp_agent.aquaticus.field.FieldDiscretizer]

  **WARNING:** This class is *EXTREMELY* ineffecient and should not be used in a loop which timing is important. Its primary use is for debuging.

  You can see a example of how to use this visualizer with the FieldDiscretizer [here](https://github.com/mivp-agent/moos-ivp-agent/blob/main/examples/DiscreteField/run.py).
  '''
  def __init__(self, discretizer):
    '''
    Args:
      discretizer (FieldDiscretizer): Used to plot discrete points and during vehicle initalization.
    '''
    assert isinstance(discretizer, FieldDiscretizer), 'discretizer is of wrong type'

    # Store discretizer
    self._discretizer = discretizer

    # Construct field plot
    plt.ion()
    self._field_fig, self._field_ax = construct_field_figure()

    # Add grid points to field graph
    for p in self._discretizer._point_idx_map:
      # Ignore the entry used for out of field points
      if p is None:
        continue

      self._field_ax.plot([p[0]], [p[1]], marker='.', markersize=3, color='dimgray')
    
    # Draw for first time
    self._field_fig.canvas.draw()

    # Create data structure for storing vehicle's locations
    self._vehicles = {}
 
  def init_vehicle(self, name, color, start_pos=FIELD_OUT_BOUNDS_POINT, plot=True):
    '''
    Initalizes a vehicle specified by `name` in the DiscreteFieldGrapher class and it's matplotlib plot. To update the vehicles initalized by this method see 
    [`update_vehicle()`][mivp_agent.aquaticus.field.DiscreteFieldGrapher.update_vehicle].

    Args:
      name (str): The name (or key) to list the vehicle under.
      color (str): A matplotlib [named color](https://matplotlib.org/stable/gallery/color/named_colors.html).
      start_pos (tuple): A tuple where containing the x / y position to initally render the vehicle.
      plot (bool): A boolean indicating if the the plot should be redrawn after vehicle initalization.
    Raises:
      RuntimeError: If the specified `name` has already been initalized.
    '''
    if name in self._vehicles:
      raise RuntimeError(f'FieldGrapher alread has vehicle named "{name}"')
    
    if start_pos != FIELD_OUT_BOUNDS_POINT:
      start_pos = self._discretizer.to_discrete_point(
        start_pos[0],
        start_pos[1]
      )

    self._vehicles[name] = {
      'circle': plt.Circle(start_pos, 2, color=color),
      'label': self._field_ax.text(start_pos[0] + 3, start_pos[1]+3, name),
      'position': start_pos
    }

    self._field_ax.add_artist(self._vehicles[name]['circle'])

    if plot:
      self._plot()


  def update_vehicle(self, name, discrete_position, plot=True):
    '''
    Used to update the position of a vehicle which has been previously initalized via [`init_vehicle()`][mivp_agent.aquaticus.field.DiscreteFieldGrapher.init_vehicle]

    Args:
      name (str): The name (or key) to list the vehicle under.
      discrete_position (tuple): A tuple where containing the **DISCRETE** x / y position to render the vehicle at. This method **will not** pass the point through the discretizer.
      plot (bool): A boolean indicating if the the plot should be redrawn after vehicle update.
    
    Raises:
      RuntimeError: If the specified `name` has not been initalized previously.
    '''
    if name not in self._vehicles:
      raise RuntimeError(f'FieldGrapher cannot find vehicle with name "{name}"')
    
    if discrete_position is None:
      discrete_position = FIELD_OUT_BOUNDS_POINT

    # Remove old label position
    self._vehicles[name]['label'].set_visible(False)

    # Update graphic
    self._vehicles[name]['circle'].center = discrete_position
    self._vehicles[name]['label'] = self._field_ax.text(discrete_position[0]+3, discrete_position[1]+3, name)
    self._vehicles[name]['position'] = discrete_position

    if plot:
      self._plot()

  def _plot(self):
    # Draw the vehicles
    for v in self._vehicles:
      self._field_ax.draw_artist(self._vehicles[v]['circle'])
    
    self._field_fig.canvas.flush_events()
