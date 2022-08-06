#include "MockCMOOSApp.h"

MockCMOOSApp::MockCMOOSApp() {}

void MockCMOOSApp::PerformStartUp(const std::string &sName, const std::string &sMissionFile) {
  // Store app name for GetAppName
  m_sAppName = sName;

  m_MissionReader.SetAppName(m_sAppName);
  if(!m_MissionReader.SetFile(sMissionFile.c_str())) {
    throw std::runtime_error("Failed to load mission file.");
  }

  // Fake server connection
  OnConnectToServer();

  // Fake startup
  // TODO: Don't throw runtime error here, allow for testing of failure cases (helper method for allow failure?)
  if(!OnStartUpPrepare()) {
    throw std::runtime_error("OnStartUpPrepare() returned false");
  }

  if(!OnStartUp()) {
    throw std::runtime_error("OnStartUp() returned false");
  }

  if(!OnStartUpComplete()) {
    throw std::runtime_error("OnStartUpComplete() returned false");
  }
}

bool MockCMOOSApp::PerformIterate(int nTimes) {
  // TODO: Implement
  return true;
}

/*
bool MockCMOOSApp::Register(const std::string &sVar, double dfInterval) {
  // TODO: Implement
  return true;
}*/

std::string MockCMOOSApp::GetAppName()
{
  return m_sAppName;
}