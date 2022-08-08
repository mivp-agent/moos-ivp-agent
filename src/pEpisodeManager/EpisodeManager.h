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
#include "VarDataPair.h"

enum ManagerState {RUNNING, STOPPING_HELM, RESETING, PAUSED};

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
   void startEpisode();
   void endEpisode(bool success);
   void resetVehicle();

   bool resetPosValid();
   bool updateInfoBuffer(CMOOSMsg&);
   bool checkConditions(std::vector<LogicCondition> conditions);
   bool debouncedCheckConditions(std::vector<LogicCondition> conditions);
   void postPosts(std::vector<VarDataPair> posts);

 private: // Configuration variables
   //TODO: Move initalization to the constructor
   std::string m_vname = "";

   double m_reset_x;
   double m_reset_y;
   std::string m_reset_heading = "";

   double m_max_duration;
   double m_debounce_period;

  // TODO: m_unpause_conditions, m_unpause_posts, m_continous -> m_paused
  // m_paused set by m_end_posts?? (prob not delay to get new mail?)

   std::vector<LogicCondition> m_end_success_conditions;
   std::vector<LogicCondition> m_end_failure_conditions;
   std::vector<VarDataPair> m_start_posts;
   std::vector<VarDataPair> m_reset_posts;
   std::vector<VarDataPair> m_pause_posts;

 private: // State variables
   ManagerState m_current_state;
   ManagerState m_previous_state;
   bool m_pause_request;
   bool m_run_request;

   int m_episode_cnt;
   int m_success_cnt;
   int m_failure_cnt;

   InfoBuffer *m_info_buffer;
   double m_nav_x;
   double m_nav_y;
   std::string m_helm_state;

   double m_episode_start;
};

#endif 
