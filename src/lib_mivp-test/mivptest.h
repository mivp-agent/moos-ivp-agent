#define USING_MOOSApp(template_param)                 \
  /* CMOOSApp functions */                            \
  using template_param::Notify;                       \
  using template_param::Register;                     \
  using template_param::GetAppName;                   \
  /* CMOOSApp member vars */                          \
  using template_param::m_MissionReader;

#define USING_MOOSCastingApp(template_param)          \
  USING_MOOSApp(template_param)                       \
  /* AppCastingMOOSApp functions */                   \
  using template_param::reportEvent;                  \
  using template_param::reportRunWarning;             \
  using template_param::reportConfigWarning;          \
  using template_param::reportUnhandledConfigWarning; \
  /* AppCastingMOOSApp member vars */                 \
  using template_param::m_msgs;

#define SPECIALIZE_MOOSCastingApp(class_name)   \
  template class class_name<AppCastingMOOSApp>; \
  template class class_name<MockMOOSCastingApp>;