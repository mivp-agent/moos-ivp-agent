import time

class ModelConsole:
  def __init__(self):
    self.iteration = 0
    self._last_loop_time = None

    self.vehicles = {}

    self.last_MOOS_delta = 0

    self._last_loop_time = None
    self._last_MOOS_time = None
  
  def tick(self, msg):
    if msg.vname not in self.vehicles:
      self.vehicles[msg.vname] = {}
      self.vehicles[msg.vname]['last_MOOS_delta'] = 'n/a'
      self.vehicles[msg.vname]['last_loop_delta'] = 'n/a'
      self.vehicles[msg.vname]['last_MOOS_time'] = msg.state['MOOS_TIME']
      self.vehicles[msg.vname]['last_loop_time'] = time.perf_counter()
    else:
      self.vehicles[msg.vname]['last_MOOS_delta'] = msg.state['MOOS_TIME']-self.vehicles[msg.vname]['last_MOOS_time']
      self.vehicles[msg.vname]['last_MOOS_time'] = msg.state['MOOS_TIME']
      loop_time = time.perf_counter()
      self.vehicles[msg.vname]['last_loop_delta'] = loop_time - self.vehicles[msg.vname]['last_loop_time']
      self.vehicles[msg.vname]['last_loop_time'] = loop_time
    

    print('\n===========================================')
    print(f' Iteration: {self.iteration}')
    print(f' MOOS_TIME: {msg.state["MOOS_TIME"]}\n')
    for v in self.vehicles:
      print(f' Vehicle: {v}')
      print(f'   MOOS delta: {self.vehicles[v]["last_MOOS_delta"]}')
      print(f'   Loop delta: {self.vehicles[v]["last_loop_delta"]}')
    print('===========================================')

    # Updated needed vars 
    self.iteration += 1
