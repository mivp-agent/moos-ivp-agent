#!/usr/bin/env python3

from mivp_agent.bridge import ModelBridgeServer
from mivp_agent.aquaticus.field import FieldDiscretizer, DiscreteFieldGrapher

from mivp_agent.util.display import ModelConsole

INSTR = {
  'speed': 0.0,
  'course': 0.0,
  'posts': {},
  'ctrl_msg': 'SEND_STATE'
}

def run():
  # Create field discretizer and grapher
  d = FieldDiscretizer()
  print(f'Generated discrete field of size: {d.space_size}')
  g = DiscreteFieldGrapher(d)
  g.init_vehicle('felix', 'red')
  g.init_vehicle('evan', 'blue')

  with ModelBridgeServer() as server:
    print('Waiting for simulation start...')
    server.accept()

    MOOS_STATE = None
    last_felix_idx = None
    last_evan_idx = None
    console = ModelConsole()

    server.send_instr(INSTR)
    while True:
      MOOS_STATE = server.listen_state()

      # Get descretized state of evan and felix
      felix_idx = d.to_discrete_idx(
        MOOS_STATE['NAV_X'],
        MOOS_STATE['NAV_Y']
      )
      evan_idx = d.to_discrete_idx(
        MOOS_STATE['NODE_REPORTS']['evan']['NAV_X'],
        MOOS_STATE['NODE_REPORTS']['evan']['NAV_Y']
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
      server.send_instr(INSTR)

      # Update terminal output
      console.tick(MOOS_STATE)


if __name__ == '__main__':
  run()
  input('Press enter to exit...')