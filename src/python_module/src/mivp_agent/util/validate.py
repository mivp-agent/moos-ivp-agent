from mivp_agent.const import KEY_ID

def checkFloat(var, error_string):
  try:
    return float(var)
  except ValueError:
    raise ValueError(error_string)

def validateAction(action):
  assert isinstance(action, dict), "Action must be a dict"

  assert "speed" in action, "Action must have key 'speed'"
  action['speed'] = checkFloat(action['speed'], "Action['speed'] must be a float")
  
  assert "course" in action, "Action must have key 'course'"
  action['course'] = checkFloat(action['course'], "Action['course'] must be a float")

  assert "posts" in action, "Action must have key 'posts'"
  assert isinstance(action["posts"], dict), "posts must be a dict"

def validateInstruction(instr):
  validateAction(instr)

  assert "ctrl_msg" in instr, "Instruction must have key 'ctrl_msg'"
  assert isinstance(instr['ctrl_msg'], str), 'ctrl_msg must be string'

def validateState(state):
  assert isinstance(state, dict), 'State must be a dictonary'

  assert 'MOOS_TIME' in state, 'State must have key: MOOS_TIME'
  assert 'NAV_X' in state, 'State must have key: NAV_X'
  assert 'NAV_Y' in state, 'State must have key: NAV_Y'
  assert 'NAV_HEADING' in state, 'State must have key, NAV_HEADING'

  assert KEY_ID in state, f'State must have key: {KEY_ID}'
  assert isinstance(state[KEY_ID], str), f'Value at {KEY_ID} must be a string'