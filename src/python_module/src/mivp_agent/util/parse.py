def csp_to_dict(csp_str):
  d = {}
  pairs = csp_str.split(',')
  for p in pairs:
    name, value = p.split('=')
    d[name] = value
  
  return d

def parse_boolstr(boolstr):
  if boolstr.lower() == 'true':
    return True
  elif boolstr.lower() == 'false':
    return False
  else:
    raise RuntimeError(f'Unexpected non boolean value: {boolstr}')

# For parsing pEpisodeManager reports
def parse_report(report):
  if report is None:
    return None
  report = csp_to_dict(report)

  report['NUM'] = int(report['NUM'])
  report['DURATION'] = float(report['DURATION'])
  report['SUCCESS'] = parse_boolstr(report['SUCCESS'])
  report['WILL_PAUSE'] = parse_boolstr(report['WILL_PAUSE'])

  return report