import plotly.graph_objects as go

from mivp_agent.log.consumer import Consumer

class PlotlyScalars(Consumer):
  '''
  This abstract class wraps the abstract Consumer to provide ease of creating a plotly scatter plot based on scalars value.
  '''
  
  def _is_data(self):
    try:
      test = self._data
    except AttributeError:
      return False
    return True
  
  def _get_layout(self, name):
    try:
      return self.layout(name)
    except AttributeError:
      return go.Layout(
        title=name,
        xaxis_title='X',
        yaxis_title='Y'
      )

  def plot(self, key, x, y):
    # Create the data storage the first time we use it
    if not self._is_data():
      self._data = {}

    if key not in self._data:
      self._data[key] = {
        'x': [],
        'y': []
      }

    self._data[key]['x'].append(x)
    self._data[key]['y'].append(y)
  
  def _get_fig(self, name):
    if not self._is_data():
      return None
    
    if len(self._data) == 0:
      return None
    
    scatters = []
    for key in self._data:
      s = go.Scatter(
        x=self._data[key]['x'],
        y=self._data[key]['y'],
        mode='markers'
      )
      scatters.append(s)

    fig = go.Figure(
      data=scatters,
      layout=self._get_layout(name)
    )
    
    return fig
