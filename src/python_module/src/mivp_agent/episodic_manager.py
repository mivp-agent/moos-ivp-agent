import time
from threading import Event, Lock

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
    self.current_episode = 0

    # Control signals
    self._run_lock = Lock()
    self._stop_signal = Event()

  '''
  Perform non blocking acquire on the run lock to test if the lock is acquired by the run method. The lock will be released right after acquisition.
  '''
  def is_running(self):
    if self._run_lock.acquire(False):
      self._run_lock.release()
      return False
    return True

  def _should_stop(self):
    return self.current_episode >= self.episodes or \
    self._stop_signal.is_set()

  def stop(self):
    if not self.is_running():
      RuntimeError('Stop called before start.')
    self._stop_signal.set()

  def start(self, task, log=True):
    if not self._run_lock.acquire(False):
      raise RuntimeError('Start should only be called once.')

    with MissionManager(task, log=log) as mgr:
      # Below is similar to `mgr.wait_for(...)` but respects out stop signal
      while not mgr.are_present(self.wait_for) and \
        not self._should_stop():
        time.sleep(0.1)

      while not self._should_stop():
        # Non blocking so `stop()` method will work immediately
        msg = mgr.get_message(block=False)

        # If we didn't get a message sleep and then loop
        if msg is None:
          time.sleep(0.1)
          continue

        # Find agent in list...
        for a in self.agents:
          if msg.vname == a.id():
            data = self.agent_data[a.id()]

            # Probably always
            rpr = a.obs_to_rpr(msg.state) #state nomenclature still lurking
            #rpr = a.obs_to_rpr(msg)  # full msg for console.tick

            if data.last_rpr != rpr:
              msg.mark_transition()
              # still need state here bc rpr_to_act expects obs
              data.current_action = a.rpr_to_act(rpr, msg.state)

            # Update episode count if applicable
            if data.last_episode != msg.episode_report['NUM']:
              data.last_episode = msg.episode_report['NUM']

              ################################################
              # Importantly, update the global episode count #
              self.current_episode += 1

            # track data
            data.last_rpr = rpr

            # If we have an action send that, otherwise mark message as handled and request new one.
            if data.current_action is None:
              msg.request_new()
            else:
              msg.act(data.current_action)

    self._run_lock.release()
