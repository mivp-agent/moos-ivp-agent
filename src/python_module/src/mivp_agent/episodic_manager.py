
from mivp_agent.manager import MissionManager


class AgentData:
  def __init__(self, vname) -> None:
    self.vname = vname

    '''
    Used to recognize if the new episode 'NUM' is a new one. When we have new episodes we must increment the EpisodeManager episode count.
    '''
    self.last_episode = None

    '''
    General idea: only call `rpr_to_act` when we reach a new state. Need to store the first action calculated for the state. 
    '''
    self.current_action = None

    '''
    To identify new states and perform action lookup / calculation from the model.
    '''
    self.last_rpr = None


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
    self.completed_episode = 0

  def _build_report(self):
    report = {
      'completed_episodes': self.completed_episode,
    }

    return report

  def start(self, task, log=True):
    with MissionManager(task, log=log) as mgr:
      mgr.wait_for(self.wait_for)

      while self.completed_episode < self.episodes:
        msg = mgr.get_message()

        # Find agent in list...
        for a in self.agents:
          if msg.vname == a.id():
            data = self.agent_data[a.id()]

            # Probably always
            rpr = a.obs_to_rpr(msg.state) #state nomenclature still lurking
            #rpr = a.obs_to_rpr(msg)  # full msg for console.tick

            if data.last_rpr != rpr:
              msg.mark_transition()
              em_report = self._build_report()
              # still need state here bc rpr_to_act expects obs
              data.current_action = a.rpr_to_act(rpr, msg.state, em_report)

            # Update episode count if applicable
            if data.last_episode != msg.episode_report['NUM']:
              if data.last_episode is not None:
                # update the global episode count # if not first
                self.completed_episode += 1
              data.last_episode = msg.episode_report['NUM']
              em_report = self._build_report()
              em_report['success'] = msg.episode_report['SUCCESS']
              a.episode_end(rpr, msg.state, em_report)


            # track data
            data.last_rpr = rpr

            ################################################
            # Importantly, actually do shit #
            msg.act(data.current_action)
