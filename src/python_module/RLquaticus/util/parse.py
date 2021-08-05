def csp_to_dict(csp_str):
  d = {}
  pairs = csp_str.split(',')
  for p in pairs:
    name, value = p.split('=')
    d[name] = value
  
  return d