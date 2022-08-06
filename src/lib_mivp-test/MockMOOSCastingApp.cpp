#include "MockMOOSCastingApp.h"

MockMOOSCastingApp::MockMOOSCastingApp() {
  m_curr_time = 0;
}

bool MockMOOSCastingApp::Iterate() { return true; }
bool MockMOOSCastingApp::OnStartUp() { 
  m_curr_time = MOOSTime();

  return true;
}
bool MockMOOSCastingApp::OnNewMail(MOOSMSG_LIST &NewMail) {
  return true;
}

void MockMOOSCastingApp::RegisterVariables() {}
void MockMOOSCastingApp::PostReport(const std::string &directive) {}