#ifndef MockCMOOSApp_HEADER
#define MockCMOOSApp_HEADER

#include "MOOS/libMOOS/Comms/CommsTypes.h"
#include "MOOS/libMOOS/Utils/MOOSUtilityFunctions.h"
#include "MOOS/libMOOS/Utils/ProcessConfigReader.h"

//#include "gmock/gmock.h"
#include <gmock/gmock.h>
//#include "<gtest/>"
//#include "gtest/googlemock/include/gmock/gmock.h"

class MockCMOOSApp {
  // TODO: Where was the article about virtual deconstructors?
  public:
    MockCMOOSApp();
    virtual ~MockCMOOSApp() {};

  /**
   * Mocked Methods
   */
  public: 
    MOCK_METHOD(
      bool,
      Notify,
      (const std::string &sVar, const std::string &sVal)
    );

    MOCK_METHOD(
      bool,
      Notify,
      (const std::string &sVar, double dfVal)
    );

    MOCK_METHOD(
      void,
      Register,
      (const std::string &sVar)
    );

    MOCK_METHOD(
      void,
      Register,
      (const std::string &sVar, double dfInterval)
    );

    // TODO: Mock register
  
  
  /**
   * Helper Methods
   */
  public:
    void PerformStartUp(const std::string &sName, const std::string &sMissionFile);

    bool InjectMail(CMOOSMsg msg);
    bool InjectMail(MOOSMSG_LIST &NewMail);

    bool PerformIterate(int nTimes = 1);

    // TODO: Re-org this header file this is not a helper method
    //bool Register(const std::string &sVar, double dfInterval=0.0);

    // TODO: Disconnect?

  /**
   * MOOS Compatibility method
   */
  protected:
    std::string m_sAppName;
    std::string GetAppName();

  /**
   * MOOS Compatibility / Mock implementation
   */
  protected:
    // Startup
    CProcessConfigReader m_MissionReader;
    virtual bool OnConnectToServer(){ return true; };
    virtual bool OnStartUp() { return true; };
    virtual bool OnStartUpPrepare(){ return true; };
    virtual bool OnStartUpComplete(){ return true; };

    // Iterate Methods
    virtual bool Iterate() { return true; };
    virtual bool OnIterateComplete(){ return true; };
    virtual bool OnIteratePrepare(){ return true; };

    virtual bool OnNewMail(MOOSMSG_LIST &NewMail) { return true; };
};
#endif