/*****************************************************************/
/*    NAME: Michael Benjamin                                     */
/*    ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA     */
/*    FILE: TagManager.h                                         */
/*    DATE: Sep 20th, 2015                                       */
/*                                                               */
/* This program is free software; you can redistribute it and/or */
/* modify it under the terms of the GNU General Public License   */
/* as published by the Free Software Foundation; either version  */
/* 2 of the License, or (at your option) any later version.      */
/*                                                               */
/* This program is distributed in the hope that it will be       */
/* useful, but WITHOUT ANY WARRANTY; without even the implied    */
/* warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR       */
/* PURPOSE. See the GNU General Public License for more details. */
/*                                                               */
/* You should have received a copy of the GNU General Public     */
/* License along with this program; if not, write to the Free    */
/* Software Foundation, Inc., 59 Temple Place - Suite 330,       */
/* Boston, MA 02111-1307, USA.                                   */
/*****************************************************************/

#ifndef UFLD_TAG_MANAGER_HEADER
#define UFLD_TAG_MANAGER_HEADER

#include <vector>
#include <string>
#include <map>
#include <set>
#include "MOOS/libMOOS/Thirdparty/AppCasting/AppCastingMOOSApp.h"
#include "NodeRecord.h"
#include "XYRangePulse.h"
#include "XYPolygon.h"
#include "VTag.h"
#include "VarDataPair.h"

class TagManager : public AppCastingMOOSApp
{
 public:
  TagManager();
  virtual ~TagManager() {};

  bool  OnNewMail(MOOSMSG_LIST &NewMail);
  bool  OnStartUp();
  bool  Iterate();
  bool  OnConnectToServer();

  void  registerVariables();
  bool  buildReport();

 protected: // Config Utilities
  bool    handleConfigVTagRange(std::string);
  bool    handleConfigZone(int, std::string);
  bool    handleConfigTeamName(int, std::string);
  bool    handleConfigRobotTagPost(std::string);
  bool    handleConfigHumanTagPost(std::string);
  bool    handleConfigRobotUnTagPost(std::string);
  bool    handleConfigHumanUnTagPost(std::string);
  bool    handleConfigNoTagPost(std::string);

 protected: // Incoming mail utilities
  bool    handleMailNodeReport(std::string);
  bool    handleMailVTagPost(std::string);
  bool    handleMailVUnTagPost(std::string);

 protected: // Processing Utilities
  double  getTrueNodeRange(double, double, std::string);

  void    processVTags();
  void    processVTag(VTag);
  void    updateCanTagStates();
  void    updateCanTagState(std::string vname);
  void    postTagSummary();
  void    checkForExpiredTags();
  void    checkForOutOfZoneVehicles();
  void    postOnFieldStatus(std::string vname="");
  void    postTagCircles();
    
  void    postHumanTagPairs(std::string src_vname, std::string tar_vname);
  void    postRobotTagPairs(std::string src_vname, std::string tar_vname);
  void    postHumanUnTagPairs(std::string tar_vname);
  void    postRobotUnTagPairs(std::string tar_vname);
  void    postNoTagPairs(std::string src_vname, std::string src_vteam,
			 std::string src_reason);

 protected: // Outgoing mail utilities
  void    postRangePulse(double x, double y, std::string color,
			 std::string label, double dur, double radius);
  void    postCommsPulse(std::string vname1, std::string vname2,
			 std::string color, double duration);

  void    postResult(std::string event, std::string vname,
		     std::string vteam, std::string result,
		     std::string reason);

  void    postResult(std::string event, std::string vname,
		     std::map<std::string, double>);
  void    postZonePolys();

 protected: // State variables

  // Node (position) records: Map keyed on vehicle name
  std::map<std::string, NodeRecord>   m_map_node_records;
  std::map<std::string, unsigned int> m_map_node_reports_rcd;
  std::map<std::string, bool>         m_map_node_onfield;

  // Perspective of vehicles doing tagging: Map keyed on vehicle name
  std::map<std::string, unsigned int> m_map_node_vtags_requested;
  std::map<std::string, unsigned int> m_map_node_vtags_accepted;
  std::map<std::string, unsigned int> m_map_node_vtags_succeeded;
  std::map<std::string, unsigned int> m_map_node_vtags_rejfreq;
  std::map<std::string, unsigned int> m_map_node_vtags_rejzone;
  std::map<std::string, unsigned int> m_map_node_vtags_rejself;
  std::map<std::string, double>       m_map_node_vtags_last_tag;
  std::map<std::string, bool>         m_map_node_vtags_can_tag;
  
  // Perspective of vehicles being tagged: Map keyed on vehicle name
  std::map<std::string, unsigned int> m_map_node_vtags_beentagged;
  std::map<std::string, bool>         m_map_node_vtags_nowtagged;
  std::map<std::string, std::string>  m_map_node_vtags_tagreason;
  std::map<std::string, double>       m_map_node_vtags_timetagged;

  // Other key states
  std::list<VTag>  m_pending_vtags;

  // Map from team name to members of the team (team name == zone name)
  std::map<std::string, std::set<std::string> > m_map_teams;

  // Keep track of notag post times, to limit frequency
  std::map<std::string, double>  m_map_prev_notag_post;

  double        m_time_last_onfield_post;
    
 protected: // Configuration variables
  double        m_tag_range;
  double        m_tag_min_interval;

  double        m_tag_duration;
  double        m_onfield_post_interval;
  
  XYPolygon     m_zone_one;
  XYPolygon     m_zone_two;
  std::string   m_zone_one_color;
  std::string   m_zone_two_color;
  std::string   m_team_one;
  std::string   m_team_two;
  std::string   m_human_platform;

  std::string   m_zone_one_post_var;
  std::string   m_zone_two_post_var;
  
  unsigned int  m_tag_events;
  bool          m_tag_circle;
  std::string   m_tag_circle_color;
  std::string   m_oob_circle_color;
  double        m_tag_circle_range;

  std::vector<VarDataPair> m_robot_tag_posts;
  std::vector<VarDataPair> m_human_tag_posts;
  std::vector<VarDataPair> m_robot_untag_posts;
  std::vector<VarDataPair> m_human_untag_posts;

  std::vector<VarDataPair> m_notag_posts;
  double                   m_notag_gap;
  
  // Visual hints
  std::string   m_post_color;
};

#endif
