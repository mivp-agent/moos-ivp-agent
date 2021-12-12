import plotly.graph_objects as go
from .consumers import PlotlyScalars

from mivp_agent.util.math import dist

class TransitionDist(PlotlyScalars):
  def layout(self):
    return go.Layout(
      title='Transition Distance vs Time',
      xaxis_title='Episode',
      yaxis_title='Transition Distance'
    )
  
  def pb2_data(self, data):
    x1 = data.s1.vinfo.NAV_X
    y1 = data.s1.vinfo.NAV_Y
    x2 = data.s2.vinfo.NAV_X
    y2 = data.s2.vinfo.NAV_Y

    num = 0
    if data.s2.HasField('episode_report'):
      num = data.s2.episode_report.NUM

    d = dist((x1, y1), (x2, y2))
    #self.plot('Transition Distance', data.s1.vinfo.MOOS_TIME, d)
    self.plot('Transition Distance', num, d)