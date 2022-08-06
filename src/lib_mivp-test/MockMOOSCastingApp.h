#ifndef MockMOOSCastingApp_HEADER
#define MockMOOSCastingApp_HEADER

#include "MockCMOOSApp.h"

class MockMOOSCastingApp : public MockCMOOSApp {
  public:
    MockMOOSCastingApp();
    virtual ~MockMOOSCastingApp() {};

    virtual bool Iterate();
    virtual bool OnNewMail(MOOSMSG_LIST&);
    virtual bool OnStartUp();
    virtual bool buildReport() { return false; };

  // TODO: Mock these?
  protected:
    void RegisterVariables();
    void PostReport(const std::string &directive="");
    void reportEvent(const std::string&){};
    void reportConfigWarning(const std::string&){};
    void reportUnhandledConfigWarning(const std::string&){};
    void reportRunWarning(const std::string&){};
  
  protected:
    std::stringstream m_msgs;
    double m_curr_time;
};
#endif