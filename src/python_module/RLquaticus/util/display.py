import time

class ModelConsole:
  def __init__(self):
    self._iteration = 0
    self._last_loop_time = None
    self._last_MOOS_time = None
  
  def tick(self, MOOS_STATE):
    loop_delta = None
    MOOS_delta = None

    # Update loop time
    current_perf_time = time.perf_counter()
    if self._last_loop_time is None:
      loop_delta = 'n/a'
    else:
      loop_delta = current_perf_time - self._last_loop_time
    self._last_loop_time = current_perf_time

    # Update MOOS time
    if self._last_MOOS_time is None:
      MOOS_delta = 'n/a'
    else:
      MOOS_delta = MOOS_STATE['HELM_TIME'] - self._last_MOOS_time
    self._last_MOOS_time = MOOS_STATE['HELM_TIME']

    print('\n===========================================')
    print(f' Iteration: {self._iteration}\n')
    print(f' MOOS delta: {MOOS_delta}')
    print(f' Loop delta: {loop_delta}')
    print('===========================================')

    # Updated needed vars 
    self._iteration += 1
