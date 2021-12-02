from mivp_agent.util import validate
from mivp_agent.const import KEY_ID, KEY_EPISODE_MGR_STATE, KEY_EPISODE_MGR_REPORT
from mivp_agent.proto.moos_pb2 import MOOSVar, NodeReport
from mivp_agent.proto.mivp_agent_pb2 import State, EpisodeReport

core_keys = (
  KEY_ID,
  KEY_EPISODE_MGR_REPORT,
  KEY_EPISODE_MGR_STATE,
  "NAV_X",
  "NAV_Y",
  "NAV_HEADING",
  "MOOS_TIME",
  "NODE_REPORTS"
)

def node_report_from_dict(report, vname):
  assert isinstance(report, dict), "Report must be dict"

  proto_report = NodeReport()
  proto_report.vname = vname
  proto_report.NAV_X = report['NAV_X']
  proto_report.NAV_Y = report['NAV_Y']
  proto_report.NAV_HEADING = report['NAV_HEADING']
  proto_report.MOOS_TIME = report['MOOS_TIME']

  return proto_report

def episode_report_from_dict(report):
  assert isinstance(report, dict), "Report must be dict"
  
  proto_report = EpisodeReport()
  proto_report.NUM = report['NUM']
  proto_report.SUCCESS = report['SUCCESS']
  proto_report.DURATION = report['DURATION']
  proto_report.WILL_PAUSE = report['WILL_PAUSE']

  return proto_report

def state_from_dict(state):
  validate.validateState(state)
  
  # Create new protobuf to store information
  proto_state = State()

  # Parse own report / info 
  vinfo = node_report_from_dict(state, state[KEY_ID])
  proto_state.vinfo.CopyFrom(vinfo)

  # Parse other reports
  if 'NODE_REPORTS' in state:
    for vname in state['NODE_REPORTS']:
      report = node_report_from_dict(state['NODE_REPORTS'][vname], vname)
      proto_state.node_reports.add().CopyFrom(report)

  # Find other vars
  for key in state:
    if key not in core_keys:
      var = MOOSVar()
      var.key = key

      if isinstance(state[key], float):
        var.dval = state[key]
      elif isinstance(state[key], str):
        var.sval = state[key]
      elif isinstance(state[key], bool):
        var.bval = state[key]
      else:
        raise TypeError(f"Unexpected type when parsing moos var {key}:{state[key]}")

      proto_state.vars.add().CopyFrom(var)

  if state[KEY_EPISODE_MGR_REPORT] is not None:
    proto_state.episode_report.CopyFrom(episode_report_from_dict(state[KEY_EPISODE_MGR_REPORT]))

  return proto_state

def node_report_to_dict(report):
  assert isinstance(report, NodeReport), "Input report is not of known NodeReport prototype"

  dict_report = {}

  dict_report['vname'] = report.vname
  dict_report['NAV_X'] = report.NAV_X
  dict_report['NAV_Y'] = report.NAV_Y
  dict_report['NAV_HEADING'] = report.NAV_HEADING
  dict_report['MOOS_TIME'] = report.MOOS_TIME

  return dict_report

def episode_report_to_dict(report):
  assert isinstance(report, EpisodeReport), "Input report is not of known EpisodeReport prototype"

  dict_report = {}
  
  dict_report['NUM'] = report.NUM
  dict_report['SUCCESS'] = report.SUCCESS
  dict_report['DURATION'] = report.DURATION
  dict_report['WILL_PAUSE'] = report.WILL_PAUSE

  return dict_report

def state_to_dict(state):
  assert isinstance(state, State), "Input state is not of known State prototype"

  dict_state = {}

  # Parse own info
  dict_vinfo = node_report_to_dict(state.vinfo)
  for key in dict_vinfo:
    if key == 'vname':
      dict_state[KEY_ID] = dict_vinfo[key]
    else:
      dict_state[key] = dict_vinfo[key]
  
  # Parse other reports
  for report in state.node_reports:
    if 'NODE_REPORTS' not in dict_state:
      dict_state['NODE_REPORTS'] = {}
    dict_state['NODE_REPORTS'][report.vname] = node_report_to_dict(report)
  
  # Parse other vars
  for var in state.vars:
    if var.HasField('sval'):
      dict_state[var.key] = var.sval
    elif var.HasField('dval'):
      dict_state[var.key] = var.dval
    elif var.HasField('bval'):
      dict_state[var.key] = var.bval
    else:
      raise TypeError("Could not find valid type in MOOSVar message")
  
  # Parse episode report
  if state.HasField('episode_report'):
    dict_state[KEY_EPISODE_MGR_REPORT] = episode_report_to_dict(state.episode_report)
  else:
    dict_state[KEY_EPISODE_MGR_REPORT] = None
  
  return dict_state