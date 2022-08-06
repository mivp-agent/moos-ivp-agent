#!/usr/bin/env python3

from mivp_agent.manager import MissionManager
from mivp_agent.aquaticus.field import FieldDiscretizer, DiscreteFieldGrapher

from mivp_agent.util.display import ModelConsole

def run():
  # Create field discretizer and grapher
  d = FieldDiscretizer()
  print(f'Generated discrete field of size: {d.space_size}')
  g = DiscreteFieldGrapher(d)
  g.init_vehicle('felix', 'red')
  g.init_vehicle('evan', 'blue')

  with MissionManager('runner', log=False) as mgr:
    print('Waiting for simulation start...')
    mgr.wait_for(('felix',))

    last_felix_idx = None
    last_evan_idx = None
    console = ModelConsole()

    while True:
      # Get state from server
      msg = mgr.get_message()

      # Get descretized state of evan and felix
      felix_idx = d.to_discrete_idx(
        msg.state['NAV_X'],
        msg.state['NAV_Y']
      )
      evan_idx = d.to_discrete_idx(
        msg.state['NODE_REPORTS']['evan']['NAV_X'],
        msg.state['NODE_REPORTS']['evan']['NAV_Y']
      )

      # Update grapher if we have a state transition
      if felix_idx != last_felix_idx:
        felix_discrete_position = d.idx_to_discrete_point(felix_idx)
        g.update_vehicle('felix', felix_discrete_position)
        last_felix_idx = felix_idx
      if evan_idx != last_evan_idx:
        evan_discrete_position = d.idx_to_discrete_point(evan_idx)
        g.update_vehicle('evan', evan_discrete_position)
        last_evan_idx = evan_idx

      # Tell BHV_Agent to give us another state
      msg.request_new()

      # Update terminal output
      console.tick(msg)


if __name__ == '__main__':
  run()
  input('Press enter to exit...')