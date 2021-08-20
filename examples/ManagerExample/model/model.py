#!/usr/bin/env python3

VEHICLES = ['alder', ]

# Import the MissionManager class from the module
from mivp_agent.manager import MissionManager

# Initalize the MissionManager through python context management
with MissionManager() as mgr:
  print('Waiting for vehicle connection...')
  mgr.wait_for(VEHICLES)

  while True:
    # Get state message from server
    msg = mgr.get_message()

    # Decide on action
    action = None
    if msg.state['NAV_X'] < 100:
      action = {
        'speed': 2.0,
        'course': 90.0
      }
    if msg.state['NAV_X'] > 50:
      action = {
        'speed': 2.0,
        'course': 270.0
      }

    # Respond to BHV_Agent's message with an action
    msg.act(action)