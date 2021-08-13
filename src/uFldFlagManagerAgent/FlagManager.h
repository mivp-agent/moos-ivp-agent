/************************************************************/
/*   NAME: Mike Benjamin                                    */
/*   ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA */
/*   FILE: FlagManager.h                                    */
/*   DATE: August 18th, 2015                                */
/************************************************************/

#ifndef FLAG_MANAGER_HEADER
#define FLAG_MANAGER_HEADER

#include <string>
#include <vector>
#include <set>
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "NodeRecord.h"
#include "XYMarker.h"
#include "VarDataPair.h"

class FlagManager : public AppCastingMOOSApp
{
 public:
  FlagManager();
  ~FlagManager() {};
  
 protected: // Standard MOOSApp functions to overload
  bool OnNewMail(MOOSMSG_LIST &NewMail);
  bool Iterate();
  bool OnConnectToServer();
  bool OnStartUp();
  
 protected: // Standard AppCastingMOOSApp function to overload
  bool buildReport();
  
 protected:
  void registerVariables();
  
  bool handleConfigFlag(std::string);
  bool handleConfigGrabPost(std::string);
  bool handleConfigLosePost(std::string);
  bool handleConfigNearPost(std::string);
  bool handleConfigAwayPost(std::string);
  bool handleConfigDenyPost(std::string);
  bool handleConfigGoalPost(std::string);
  bool handleConfigHomePost(std::string);
  
  bool handleMailNodeReport(std::string str);
  bool handleMailFlagGrab(std::string, std::string);
  bool handleMailFlagReset(std::string);
  bool handleMailTaggedVehicles(std::string);
  
  void updateVehiclesInFlagRange();
  void updateVehiclesHaveScored();
  void updateVehiclesUntagged();
  void updateVehiclesFlagRender();
  
  bool resetFlagsByLabel(std::string);
  bool resetFlagsByVName(std::string);
  bool resetFlagsAll();
  void postFlagMarkers(bool force=false);
  void postFlagSummary();
  
  bool hasFlag(std::string vname);
  void invokePosts(std::string ptype, std::string vname,
		   std::string vteam, std::string fname,
		   std::string reason="");
  
  void postPolygons();

  void postHeartBeat();
  
 private: // Config variables
  
  // Flag Configurations. Flag ownership is stored in XYMarker.
  // So m_flags is really also a state variable.
  std::vector<XYMarker>  m_flags;
  std::vector<bool>      m_flags_changed;
  
  double      m_default_flag_range;
  double      m_default_flag_width;
  std::string m_default_flag_type;
  bool        m_report_flags_on_start;
  bool        m_flag_follows_vehicle;
  std::string m_grabbed_color;
  std::string m_ungrabbed_color;

  double      m_near_flag_range_buffer;
  bool        m_post_heartbeat;
  
  // Configurable MOOS postings upon defined events
  std::vector<VarDataPair> m_flag_grab_posts;
  std::vector<VarDataPair> m_flag_lose_posts;
  std::vector<VarDataPair> m_flag_near_posts;
  std::vector<VarDataPair> m_flag_away_posts;
  std::vector<VarDataPair> m_flag_deny_posts;
  std::vector<VarDataPair> m_flag_goal_posts;
  std::vector<VarDataPair> m_flag_home_posts;
  
  // Configurable visual Hint Defaults for Polygon around goals                
  double       m_poly_vertex_size;
  double       m_poly_edge_size;
  std::string  m_poly_vertex_color;
  std::string  m_poly_edge_color;
  std::string  m_poly_fill_color;

 private: // State variables
  
  // Vehicle node report state vars. Each map keyed on vname.
  std::map<std::string, NodeRecord>   m_map_record;
  std::map<std::string, double>       m_map_tstamp;
  std::map<std::string, unsigned int> m_map_rcount;
  std::map<std::string, unsigned int> m_map_grab_count;
  std::map<std::string, unsigned int> m_map_flag_count;
  std::map<std::string, bool>         m_map_in_flag_zone;
  std::map<std::string, bool>         m_map_near_flag_zone;
  std::map<std::string, bool>         m_map_in_home_zone;
  
  // Overall Flag/Game Score
  std::map<std::string, unsigned int> m_map_team_score;
  std::map<std::string, unsigned int> m_map_team_grabs;
  
  unsigned int m_total_node_reports_rcvd;
  
  std::set<std::string>  m_tagged_vnames;
  
  // Grab request state vars
  unsigned int m_total_grab_requests_rcvd; 


  // Heartbeat
  unsigned int m_heartbeat_counter;
  double       m_heartbeat_last;
};

#endif
