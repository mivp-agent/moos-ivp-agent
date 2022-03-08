#
# ----------------------------------------------
#
# - wait_for might not be needed as a param to Episodic init


class AgentData:
  def __init__(self, vname) -> None:
    self.vname = vname
    self.last_episode = None
    self.last_state = None

    self.current_action = None

class EpisodicManager:
  def __init__(self, agents, episodes, wait_for=None) -> None:
    '''
    SETUP AGENTS
    '''
    self.agents = agents
    self.agent_data = {}
    
    # Combine the agent's id and any additional wait fors
    self.wait_for = wait_for

    if self.wait_for is None:
      self.wait_for = []
    
    # Setup things specific to each agent
    for a in self.agents:
      # Make sure they are waited for
      self.wait_for.append(a.id())

      # Make a agent state for them
      self.agent_data[a.id()] = AgentData(a.id())
    
    '''
    SETUP EPISODE TRACKING
    '''
    self.episodes = episodes
    self.current_episode = 0


  def run(self, task, log=True):
    with MissionManager(task, log=log) as mgr:
      mgr.wait_for(self.wait_for)

      while self.current_episode < self.episodes:
        msg = msg.get_message()

        # Find agent in list...
        for a in self.agents:
          if msg.vname == a.id():
            data = self.agent_data[a.id()]

            # Probably always 
            state = a.obs_to_state(msg.state)

            if data.last_state != state:
              msg.transition()
              data.current_action = a.state_to_act(state)

            # Update episode count if applicable
            if data.last_episode != msg.episode_report['NUM']:
              data.last_episode = msg.episode_report['NUM']
              
              ################################################
              # Importantly, update the global episode count #
              self.episodes += 1

            # track data
            data.last_state = state

            ################################################
              # Importantly, actually do shit #
            msg.act(data.current_action)


class Agent:
  def __init__(self, own_id, opponent_id) -> None:
    self.own_id = own_id
    self.opponent_id = opponent_id

  def id(self):
    return self.own_id

  def obs_to_state(self, observation):
    # obs -> state
    state = observation + 1

    return state
  
  def state_to_act(self, state):
    act = my_model(state)

    return act

if __name__ == '__main__':
  # Create agents required

  agents = []
  wait_for = []
  for i in [1,2,3,4,5]:
    agents.append(Agent(f'agent_1{i}', f'drone_2{i}'))
    wait_for.append(f'drone_2')
  
  mgr = EpisodicManager(agents, 1000, wait_for=wait_for)
  mgr.run()