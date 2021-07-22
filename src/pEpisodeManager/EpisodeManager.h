/************************************************************/
/*    NAME: Carter Fendley                                              */
/*    ORGN: MIT                                             */
/*    FILE: EpisodeManager.h                                          */
/*    DATE: December 29th, 1963                             */
/************************************************************/

#ifndef EpisodeManager_HEADER
#define EpisodeManager_HEADER

#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "LogicCondition.h"
#include "InfoBuffer.h"

class EpisodeManager : public AppCastingMOOSApp
{
 public:
   EpisodeManager();
   ~EpisodeManager();

 protected: // Standard MOOSApp functions to overload  
   bool OnNewMail(MOOSMSG_LIST &NewMail);
   bool Iterate();
   bool OnConnectToServer();
   bool OnStartUp();

 protected: // Standard AppCastingMOOSApp function to overload 
   bool buildReport();

 protected:
   void registerVariables();
   bool stopEpisode();

   bool resetVarsValid();
   bool updateInfoBuffer(CMOOSMsg&);
   bool checkConditions();

 private: // Configuration variables
   //TODO: Move initalization to the constructor
   std::string m_vname = "";

   std::string m_reset_x = "";
   std::string m_reset_y = "";
   std::string m_reset_heading = "";

   bool m_episode_running;
   bool m_continuous;

   std::vector<LogicCondition> m_end_conditions;

 private: // State variables
   InfoBuffer *m_info_buffer;
   int m_episode_cnt;
};

#endif 
