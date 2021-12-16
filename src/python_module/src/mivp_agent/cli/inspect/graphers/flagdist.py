import plotly.graph_objects as go

from mivp_agent.cli.inspect.consumers import PlotlyScalars

from mivp_agent.util.math import dist
from mivp_agent.aquaticus.const import FIELD_BLUE_FLAG

class FlagDist(PlotlyScalars):
  def layout(self, name):
    title = go.layout.Title(
        text=f"<b>Distance to Flag</b><br><sup>{name}</sup>",
        xref="paper",
        x=0
    )
    return go.Layout(
      title=title,
      xaxis_title='Episode',
      yaxis_title='Distance to Flag'
    )
  
  def setup(self, *args, **kwargs):
    self.min_dist = None
    self.last_episode = None

  def pb2_data(self, data):
    x1 = data.s1.vinfo.NAV_X
    y1 = data.s1.vinfo.NAV_Y

    # Track the distance to the blue flag from s1
    d_to_red = abs(dist((x1, y1), FIELD_BLUE_FLAG))
    if self.min_dist is None or self.min_dist > d_to_red:
      self.min_dist = d_to_red

    # When we transition to a new episode plot the last one
    if data.s2.HasField('episode_report'):
      num = data.s2.episode_report.NUM
      
      if num != self.last_episode:
        self.plot('distance', num, self.min_dist)

        # Reset parameters
        self.min_dist = None
        self.last_episode = num