/************************************************************/
/*    NAME: Carter Fendley                                              */
/*    ORGN: MIT                                             */
/*    FILE: EpisodeManager.h                                          */
/*    DATE: December 29th, 1963                             */
/************************************************************/

#ifndef EpisodeManager_HEADER
#define EpisodeManager_HEADER

#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"

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

 private: // Configuration variables
   std::string m_vname = "";

   std::string m_reset_x = "";
   std::string m_reset_y = "";
   std::string m_reset_heading = "";


 private: // State variables
   bool m_tagged;

   int m_episode_cnt = 0;
   int m_tagged_cnt = 0;
   int m_capture_cnt = 0;
};

#endif 
