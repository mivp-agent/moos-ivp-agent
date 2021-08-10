/*****************************************************************/
/*    NAME: Michael Benjamin                                     */
/*    ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA     */
/*    FILE: TagManager.cpp                                       */
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

#include <cstdlib>
#include <iostream>
#include <cmath>
#include "AngleUtils.h"
#include "ColorParse.h"
#include "TagManager.h"
#include "MBUtils.h"
#include "ACTable.h"
#include "NodeRecordUtils.h"
#include "XYCircle.h"
#include "XYFormatUtilsPoly.h"
#include "XYCommsPulse.h"

using namespace std;

//------------------------------------------------------------
// Constructor

TagManager::TagManager()
{
  // Initialize config variables
  m_post_color = "white";
  m_tag_range  = 25;
  m_tag_min_interval = 10;
  m_human_platform = "mokai";

  m_tag_duration = 30; // seconds
  m_tag_circle   = true;
  m_tag_circle_color = "green";
  m_oob_circle_color = "yellow";
  m_tag_circle_range = 5;

  m_zone_one_color = "pink";
  m_zone_two_color = "light_blue";

  m_team_one = "red";
  m_team_two = "blue";

  m_zone_one_post_var = "UTM_ZONE_ONE";
  m_zone_two_post_var = "UTM_ZONE_TWO";
  
  m_notag_gap = 5;

  m_onfield_post_interval = 10; // seconds
  
  // Initialize state variables
  m_tag_events = 0;       // Counter for tag events

  m_time_last_onfield_post = 0;
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool TagManager::OnNewMail(MOOSMSG_LIST &NewMail)
{
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;

    string key  = msg.GetKey();
    string sval = msg.GetString();

    bool handled = true;
    if((key == "NODE_REPORT") || (key == "NODE_REPORT_LOCAL"))
      handled = handleMailNodeReport(sval);
    else if(key == "TAG_REQUEST")
      handled = handleMailVTagPost(sval);
    else if(key == "UNTAG_REQUEST")
      handled = handleMailVUnTagPost(sval);
    else if(key == "APPCAST_REQ")
      handled = true;
    else if(key == "PMV_CONNECT") 
      postZonePolys();
    else
      handled = false;
    
    if(!handled)
      reportRunWarning("Unhandled Mail: " + key);
  }
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()

bool TagManager::OnStartUp()
{
  AppCastingMOOSApp::OnStartUp();

  STRING_LIST sParams;
  if(!m_MissionReader.GetConfigurationAndPreserveSpace(GetAppName(), sParams))
    reportConfigWarning("No config block found for " + GetAppName());
  
  STRING_LIST::iterator p;
  for(p = sParams.begin(); p!=sParams.end(); p++) {
    string line  = *p;
    string orig  = line;
    string param = tolower(biteStringX(line, '='));
    string value = line;

    bool handled = true;
    if(param == "tag_range")
      handled = setNonNegDoubleOnString(m_tag_range, value);
    else if(param == "tag_min_interval")
      handled = setNonNegDoubleOnString(m_tag_min_interval, value);
    else if(param == "notag_gap")
      handled = setNonNegDoubleOnString(m_notag_gap, value);
    else if(param == "post_color")
      handled = setColorOnString(m_post_color, value);
    else if(param == "zone_one")
      handled = handleConfigZone(1, value);
    else if(param == "zone_two")
      handled = handleConfigZone(2, value);
    else if(param == "zone_one_post_var")
      handled = setNonWhiteVarOnString(m_zone_one_post_var, value);
    else if(param == "zone_two_post_var")
      handled = setNonWhiteVarOnString(m_zone_two_post_var, value);
    else if(param == "team_one")
      handled = handleConfigTeamName(1, value);
    else if(param == "team_two")
      handled = handleConfigTeamName(2, value);
    else if(param == "tag_duration")
      handled = setNonNegDoubleOnString(m_tag_duration, value);
    else if(param == "human_tag_post")
      handled = handleConfigHumanTagPost(value);
    else if(param == "robot_tag_post")
      handled = handleConfigRobotTagPost(value);
    else if(param == "human_untag_post")
      handled = handleConfigHumanUnTagPost(value);
    else if(param == "robot_untag_post")
      handled = handleConfigRobotUnTagPost(value);
    else if(param == "notag_post")
      handled = handleConfigNoTagPost(value);

    else if(param == "tag_circle_color")
      handled = setColorOnString(m_tag_circle_color, value);
    else if(param == "oob_circle_color")
      handled = setColorOnString(m_oob_circle_color, value);
    else if(param == "tag_circle")
      handled = setBooleanOnString(m_tag_circle, value);
    else if(param == "zone_one_color")
      handled = setColorOnString(m_zone_one_color, value);
    else if(param == "zone_two_color")
      handled = setColorOnString(m_zone_two_color, value);
    else if(param == "tag_circle_range")
      handled = setNonNegDoubleOnString(m_tag_circle_range, value);
    else if(param == "onfield_post_interval")
      handled = setNonNegDoubleOnString(m_onfield_post_interval, value);
    else if((param == "human_platform") && isKnownVehicleType(value))
      m_human_platform = value;
    else
      handled = false;

    if(!handled)
      reportUnhandledConfigWarning(orig);
  }

  postZonePolys();
  registerVariables();
  return(true);
}

//------------------------------------------------------------
// Procedure: Iterate()

bool TagManager::Iterate()
{
  AppCastingMOOSApp::Iterate();
  updateCanTagStates();
  processVTags();
  checkForExpiredTags();
  checkForOutOfZoneVehicles();
  postOnFieldStatus();
  
  postTagSummary();
  
  if(m_tag_circle)
    postTagCircles();

  AppCastingMOOSApp::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: OnConnectToServer

bool TagManager::OnConnectToServer()
{
  registerVariables();
  return(true);
}

//------------------------------------------------------------
// Procedure: registerVariables

void TagManager::registerVariables()
{
  AppCastingMOOSApp::RegisterVariables();
  Register("NODE_REPORT", 0);
  Register("NODE_REPORT_LOCAL", 0);
  Register("TAG_REQUEST", 0);
  Register("UNTAG_REQUEST", 0);
  Register("PMV_CONNECT", 0);
}

//------------------------------------------------------------
// Procedure: postTagSummary()

void TagManager::postTagSummary()
{
  string tagged_vnames;
  map<string,bool>::iterator p;
  for(p=m_map_node_vtags_nowtagged.begin();
      p!=m_map_node_vtags_nowtagged.end(); p++) {
    string vname = p->first;
    bool   tagged = p->second;
    if(tagged) {
      if(tagged_vnames != "")
	tagged_vnames += ",";
      tagged_vnames += vname;
    }
  }
  Notify("TAGGED_VEHICLES", tagged_vnames);
}
  
  
//---------------------------------------------------------
// Procedure: handleMailNodeReport
//   Example: NAME=alpha,TYPE=KAYAK,UTC_TIME=1267294386.51,X=29.66,Y=3.9,
//            LAT=43.825089, LON=-70.330030,SPD=2.0, HDG=119.06,
//            YAW=119.05677,DEPTH=0, LENGTH=4.0,MODE=ENGAGED

bool TagManager::handleMailNodeReport(string node_report_str)
{
  // Step 1: Deserialize the node record and check validity
  NodeRecord new_node_record = string2NodeRecord(node_report_str);
  if(!new_node_record.valid())
    return(false);

  // Step 2: Add/Update the node record and increment the counter
  string vname = new_node_record.getName();
  m_map_node_records[vname] = new_node_record;
  m_map_node_reports_rcd[vname]++;

  // Step 3: Get the Group/Team name and make sure we know this
  // vehicle and associate it with the proper team.
  string vteam = new_node_record.getGroup();
  if(vteam == "") {
    string msg = "Node report for " + vname + " with no group.";
    reportRunWarning(msg);
    return(false);
  }
  if((vteam != m_team_one) && (vteam != m_team_two)) {
    string msg = "Node report for " + vname + " w/ unknown team: " + vteam;
    reportRunWarning(msg);
    return(false);
  }

  m_map_teams[vteam].insert(vname);

  return(true);
}

//---------------------------------------------------------
// Procedure: handleMailVTagPost
//   Example: vname=alpha

bool TagManager::handleMailVTagPost(string launch_str)
{
  // Part 1: Confirm request is coming from a known vehicle.
  string vname = tokStringParse(launch_str, "vname",  ',', '=');
  if((vname == "") || (m_map_node_records.count(vname) == 0)) {
    string msg = "Failed VTag Post: Unknown vehicle [" + vname + "]";
    Notify("TAG_RESULT_VERBOSE", msg);
    reportRunWarning(msg);
    reportEvent(msg);
    return(false);
  }

  // Part 2: Legal tag request, so increment key counters
  m_tag_events++;
  m_map_node_vtags_requested[vname]++;


  // Part 3: Tag is accepted. Add an appcasting event.
  stringstream ss;
  ss << "Tag requested by " << vname << "[" << m_tag_events << "]";
  reportEvent(ss.str());

  // Part 4: Create a VTag and push it on the list of pending vtags
  // for subsequent processing.
  NodeRecord record = m_map_node_records[vname];
  double     vx = record.getX();
  double     vy = record.getY();
  string     group = record.getGroup();
  VTag vtag(vname, vx, vy, m_curr_time);
  vtag.setEvent(m_tag_events);
  vtag.setVTeam(group);
  m_pending_vtags.push_back(vtag);

#if 0
  // Disabled by mikerb, moved to be in processVTag() after criteria met
  // Part 5: Post the RangePulse for the requesting vehicle. This is
  // purely a visual artifact.
  double pulse_duration = 2;
  postRangePulse(vx, vy, m_post_color, vname+"_vtag",
		 pulse_duration, m_tag_range);
#endif

  return(true);
}

//------------------------------------------------------------
// Procedure: postRangePulse

void TagManager::postRangePulse(double x, double y, string color,
                                string label, double duration, double radius)
{
  XYRangePulse pulse;
  pulse.set_x(x);
  pulse.set_y(y);
  pulse.set_label(label);
  pulse.set_rad(radius);
  pulse.set_fill(0.60);
  pulse.set_fill_invariant(true);
  pulse.set_duration(duration);
  pulse.set_linger(2);
  pulse.set_time(m_curr_time);
  if(color != "") {
    pulse.set_color("edge", color);
    pulse.set_color("fill", color);
  }
  string spec = pulse.get_spec();
  Notify("VIEW_RANGE_PULSE", spec);
}

//------------------------------------------------------------
// Procedure: postCommsPulse
 
void TagManager::postCommsPulse(string vname1, string vname2,
				string color, double duration)
{
  // Sanity check: make sure we know about both vehicles.
  if((m_map_node_records.count(vname1) == 0) ||
     (m_map_node_records.count(vname2) == 0))
    return;

  // Get each vehicle's record and position
  NodeRecord record1 = m_map_node_records[vname1];
  NodeRecord record2 = m_map_node_records[vname2];
  double osx = record1.getX();
  double osy = record1.getY();
  double cnx = record2.getX();
  double cny = record2.getY();
  
  XYCommsPulse pulse(osx, osy, cnx, cny);
  pulse.set_label(vname1 + "2" + vname2);
  pulse.set_duration(duration);
  pulse.set_beam_width(7);
  pulse.set_fill(0.6);
  pulse.set_time(m_curr_time);
  pulse.set_color("fill", color);
  
  string spec = pulse.get_spec();
  Notify("VIEW_COMMS_PULSE", spec);
}


//------------------------------------------------------------
// Procedure: getTrueNodeRange()

double TagManager::getTrueNodeRange(double x, double y, string node)
{
  if(m_map_node_records.count(node) == 0)
    return(-1);

  double node_x = m_map_node_records[node].getX();
  double node_y = m_map_node_records[node].getY();
  double range  = hypot((x-node_x), (y-node_y));

  return(range);
}


//------------------------------------------------------------
// Procedure: handleConfigZone()
//      Note: Zone number must be 1 or 2. Polygon must be convex
//   Example: pts={0,-20:120,-20:120,-160:0,-160}

bool TagManager::handleConfigZone(int zone_number, string str)
{
  if((zone_number != 1) && (zone_number != 2))
    return(false);

  XYPolygon poly = string2Poly(str);
  if(poly.size() == 0)
    return(false);

  poly.set_edge_size(1);
  poly.set_vertex_size(1);
  poly.set_transparency(0.1);

  if(zone_number == 1) {
    poly.set_color("vertex", "gray50");
    poly.set_color("edge", "gray50");
    poly.set_color("fill", m_zone_one_color);
    if(m_team_one != "")
      poly.set_label(m_team_one);
    else
      poly.set_label("zone_one");
    m_zone_one = poly;
  }
  else {
    poly.set_color("vertex", "gray50");
    poly.set_color("edge", "gray50");
    poly.set_color("fill", m_zone_two_color);
    if(m_team_two != "")
      poly.set_label(m_team_two);
    else
      poly.set_label("zone_two");
    m_zone_two = poly;
  }

  return(true);
}


//------------------------------------------------------------
// Procedure: handleConfigTeamName()

bool TagManager::handleConfigTeamName(int zone_number, string team_name)
{
  // Sanity check - this app only handles TWO zones
  if((zone_number != 1) && (zone_number != 2))
    return(false);
  if(team_name == "")
    return(false);

  // Set the m_team_one member variable and apply the label to the
  // polygon representing the zone. Even if the polygon has not been
  // set yet. Now that m_team_one is set, it will be applied when/if
  // the polygon/zone is later configured.
  if((zone_number == 1) && ((m_team_one=="") || (m_team_one=="red"))) {
    m_team_one = team_name;
    m_zone_one.set_label(team_name);
  }
  else if((zone_number == 2) && ((m_team_two=="") || (m_team_two=="blue"))) {
    m_team_two = team_name;
    m_zone_two.set_label(team_name);
  }
  else
    return(false);

  return(true);
}


//------------------------------------------------------------
// Procedure: handleConfigHumanTagPost

bool TagManager::handleConfigHumanTagPost(string str)
{
  string moosvar = biteStringX(str, '=');
  string moosval = str;

  if((moosvar == "") || (moosval == ""))
    return(false);

  VarDataPair pair(moosvar, moosval, "auto");
  m_human_tag_posts.push_back(pair);
  return(true);
}

//------------------------------------------------------------
// Procedure: handleConfigRobotTagPost

bool TagManager::handleConfigRobotTagPost(string str)
{
  string moosvar = biteStringX(str, '=');
  string moosval = str;

  if((moosvar == "") || (moosval == ""))
    return(false);

  VarDataPair pair(moosvar, moosval, "auto");
  m_robot_tag_posts.push_back(pair);
  return(true);
}


//------------------------------------------------------------
// Procedure: handleConfigHumanUnTagPost

bool TagManager::handleConfigHumanUnTagPost(string str)
{
  string moosvar = biteStringX(str, '=');
  string moosval = str;

  if((moosvar == "") || (moosval == ""))
    return(false);

  VarDataPair pair(moosvar, moosval, "auto");
  m_human_untag_posts.push_back(pair);
  return(true);
}

//------------------------------------------------------------
// Procedure: handleConfigNoTagPost
//   Purpose: A "NoTag" post is made when tag has been denied to a
//            human platform requesting a tag

bool TagManager::handleConfigNoTagPost(string str)
{
  string moosvar = biteStringX(str, '=');
  string moosval = str;

  if((moosvar == "") || (moosval == ""))
    return(false);

  VarDataPair pair(moosvar, moosval, "auto");
  m_notag_posts.push_back(pair);
  return(true);
}

//------------------------------------------------------------
// Procedure: handleConfigRobotUnTagPost

bool TagManager::handleConfigRobotUnTagPost(string str)
{
  string moosvar = biteStringX(str, '=');
  string moosval = str;

  if((moosvar == "") || (moosval == ""))
    return(false);

  VarDataPair pair(moosvar, moosval, "auto");
  m_robot_untag_posts.push_back(pair);
  return(true);
}



//------------------------------------------------------------
// Procedure: updateCanTagStates()

void TagManager::updateCanTagStates()
{
  map<string, NodeRecord>::iterator p;
  for(p=m_map_node_records.begin(); p!=m_map_node_records.end(); p++) {
    string vname = p->first;
    updateCanTagState(vname);
  }
}

//------------------------------------------------------------
// Procedure: updateCanTagState()

void TagManager::updateCanTagState(string vname)
{
  if(m_map_node_records.count(vname) == 0)
    return;

  NodeRecord record = m_map_node_records[vname];
  double vx = record.getX();
  double vy = record.getY();
  string vteam = record.getGroup();

  bool first_look = (m_map_node_vtags_can_tag.count(vname) == 0);
  bool can_tag_prev = m_map_node_vtags_can_tag[vname];
  bool can_tag = true;
  
  // Part 1A: Check if this/tagging vehicle is currently itself tagged
  if(m_map_node_vtags_nowtagged[vname])
    can_tag = false;
  
  // Part 1B: Check if tag allowed based on freq and last tag
  double elapsed = m_curr_time - m_map_node_vtags_last_tag[vname];
  if(elapsed < m_tag_min_interval) 
    can_tag = false;


  // Part 2: Check if tag-target vehicle in zone for tagging
  bool in_own_zone = false;
  if((vteam == m_team_one) && (m_zone_one.contains(vx, vy)))
    in_own_zone = true;
  else if((vteam == m_team_two) && (m_zone_two.contains(vx, vy)))
    in_own_zone = true;
  if(!in_own_zone)
    can_tag = false;


  // Part 3: Measure and collect the range to each non-team member
  //         Taking note of the closest target.
  string taggable_node;
  map<string, NodeRecord>::iterator p;
  for(p=m_map_node_records.begin(); p!=m_map_node_records.end(); p++) {
    string targ_name = p->first;
    string targ_team = p->second.getGroup();
    if((vname != targ_name) && (vteam != targ_team)) {
      double targ_x    = p->second.getX();
      double targ_y    = p->second.getY();

      // Check if target is currently untagged
      bool targ_currently_tagged = m_map_node_vtags_nowtagged[targ_name]; 
    
      // Check if target is in enemy territory
      bool targ_in_enemy_zone = false;
      if((vteam == m_team_one) && (m_zone_one.contains(targ_x, targ_y)))
	targ_in_enemy_zone = true;
      if((vteam == m_team_two) && (m_zone_two.contains(targ_x, targ_y)))
	targ_in_enemy_zone = true;
      
      // Check the target range
      if(targ_in_enemy_zone && !targ_currently_tagged) {
	double targ_range = getTrueNodeRange(vx, vy, targ_name);
	if(targ_range <= m_tag_range)
	  taggable_node = targ_name;
      }
    }
  }
  if(taggable_node == "")
    can_tag = false;

  // Part 4: Update can_tag status and post a message if changed.
  bool changed = false;
  if(can_tag_prev != can_tag)
    changed = true;

  if(!changed && !first_look)
    return;
  
  m_map_node_vtags_can_tag[vname] = can_tag;
  
  Notify("CANTAG_"+toupper(vname), boolToString(can_tag));
  
}

//------------------------------------------------------------
// Procedure: processVTags

void TagManager::processVTags()
{
  list<VTag>::iterator p;
  for(p=m_pending_vtags.begin(); p!=m_pending_vtags.end(); p++) {
    VTag vtag = *p;
    if(vtag.valid())
      processVTag(vtag);
    else
      reportEvent("Invalid vtag: " + vtag.str());
  }
  m_pending_vtags.clear();
}

//------------------------------------------------------------
// Procedure: processVTag()

void TagManager::processVTag(VTag vtag)
{
  // Part 0: Pull out the fields from vtag data structure
  double vx = vtag.getX();
  double vy = vtag.getY();
  string vname = vtag.getVName();
  string vteam = vtag.getVTeam();
  string event = uintToString(vtag.getEvent());

  // Part 1A: Check if the tagging vehicle is currently itself tagged
  bool self_currently_tagged = m_map_node_vtags_nowtagged[vname]; 
  if(self_currently_tagged) {
    m_map_node_vtags_rejself[vname]++;
    string result = "rejected";
    string reason = "selftagged";
    postResult(event, vname, vteam, result, reason);
    return;
  }

  
  // Part 1B: Check if tag allowed based on frequency based on the last
  // time it posted a vtag.
  double elapsed = m_curr_time - m_map_node_vtags_last_tag[vname];
  if(elapsed < m_tag_min_interval) {
    m_map_node_vtags_rejfreq[vname]++;
    string result = "rejected";
    string reason = "freq";
    postResult(event, vname, vteam, result, reason);
    return;
  }

  // Part 2: Check if tag-target vehicle in zone for tagging
  bool in_own_zone = false;
  if((vteam == m_team_one) && (m_zone_one.contains(vx, vy)))
    in_own_zone = true;
  else if((vteam == m_team_two) && (m_zone_two.contains(vx, vy)))
    in_own_zone = true;

  if(!in_own_zone) {
    m_map_node_vtags_rejzone[vname]++;
    string result = "rejected";
    string reason = "zone";
    postResult(event, vname, vteam, result, reason);
    return;
  }

  // Tag request ok in terms of frequency, zone etc, so declare the
  // tag to be accepted and increment the counter.
  m_map_node_vtags_accepted[vname]++;
  // old location mikerb
  
  // Part 3: Measure and collect the range to each non-team member
  //         Taking note of the closest target.
  string node_closest;
  string node_closest_type;
  map<string, double> map_node_range;
  map<string, NodeRecord>::iterator p;
  for(p=m_map_node_records.begin(); p!=m_map_node_records.end(); p++) {
    string targ_name = p->first;
    string targ_team = p->second.getGroup();
    string targ_type = tolower(p->second.getType());
    double targ_x    = p->second.getX();
    double targ_y    = p->second.getY();

    // Check if target is currently untagged
    bool targ_currently_tagged = m_map_node_vtags_nowtagged[targ_name]; 
    
    // Check if target is in enemy territory
    bool targ_in_enemy_zone = false;
    if((vteam == m_team_one) && (m_zone_one.contains(targ_x, targ_y)))
      targ_in_enemy_zone = true;
    if((vteam == m_team_two) && (m_zone_two.contains(targ_x, targ_y)))
      targ_in_enemy_zone = true;
      
    // Disregard members of the same team
    if((targ_team != vteam) && targ_in_enemy_zone && !targ_currently_tagged) {
      double targ_range = getTrueNodeRange(vx, vy, targ_name);
      map_node_range[targ_name] = targ_range;
      if((node_closest == "") || (targ_range < map_node_range[node_closest])) {
	node_closest = targ_name;
	node_closest_type = targ_type;
      }
    }
  }
  // Always post the full range results to the verbose variable
  postResult(event, vname, map_node_range);

  double pulse_duration = 4;
  string result = "tagged";
  string reason = "none";
  
  // Part 4: Sanity checks.
  if(map_node_range.size() == 0) {
    //postRangePulse(vx, vy, m_post_color, vname+"_vtag", pulse_duration, m_tag_range);
    postResult(event, vname, vteam, result, reason);
    return;
  }
  if(node_closest == "") {
    postRangePulse(vx, vy, m_post_color, vname+"_vtag", pulse_duration, m_tag_range);
    postResult(event, vname, vteam, result, reason);
    return;
  }
  if(map_node_range.count(node_closest) == 0) {
    postResult(event, vname, vteam, result, reason);
    return;
  }

  // Part 5: Examine the closest target, declare it tagged if in range
  double node_closest_dist = map_node_range[node_closest];
  if(node_closest_dist <= m_tag_range) {
    result = "tagged";
    reason = node_closest;
    m_map_node_vtags_succeeded[vname]++;
    m_map_node_vtags_beentagged[node_closest]++;
    m_map_node_vtags_nowtagged[node_closest] = true;
    m_map_node_vtags_tagreason[node_closest] = "enemy";
    m_map_node_vtags_timetagged[node_closest] = m_curr_time;

    m_map_node_vtags_last_tag[vname] = m_curr_time;  // new location mikerb

    if(node_closest_type != m_human_platform)
      postRobotTagPairs(vname, node_closest);
    else
      postHumanTagPairs(vname, node_closest);
    postCommsPulse(vname, node_closest, "white", pulse_duration);
  }
  else
    postRangePulse(vx, vy, m_post_color, vname+"_vtag", pulse_duration, m_tag_range);
  
  postResult(event, vname, vteam, result, reason);
}


//------------------------------------------------------------
// Procedure: checkForExpiredTags()

void TagManager::checkForExpiredTags()
{
  map<string, bool>::iterator p;
  for(p=m_map_node_vtags_nowtagged.begin();
      p!=m_map_node_vtags_nowtagged.end(); p++) {
    string vname = p->first;
    bool   now_tagged = p->second;
    if(now_tagged) {
      double time_tagged = m_map_node_vtags_timetagged[vname];
      double elapsed = m_curr_time - time_tagged;
      double remaining = m_tag_duration - elapsed;
      if(remaining <= 0) {
        m_map_node_vtags_nowtagged[vname]  = false;
        m_map_node_vtags_tagreason[vname]  = "";
        m_map_node_vtags_timetagged[vname] = 0;

        string vtype = tolower(m_map_node_records[vname].getType());
        if(vtype == m_human_platform)
          postHumanUnTagPairs(vname);
        else
          postRobotUnTagPairs(vname);

        XYCircle circle;
        circle.set_label(vname);
        circle.set_active(false);
        string spec = circle.get_spec();
        Notify("VIEW_CIRCLE", spec);

        string time_str = doubleToString(m_curr_time - m_start_time);
        string msg = "vname=" + vname + ",time=" + time_str;
        Notify("TAG_RELEASE_VERBOSE", msg);
      }
    }
  }
}

//------------------------------------------------------------
// Procedure: postOnFieldStatus()

void TagManager::postOnFieldStatus(string vname)
{
  if(vname != "") {
    string msg_var = "ONFIELD_" + toupper(vname);
    string msg_val = boolToString(m_map_node_onfield[vname]);
    Notify(msg_var, msg_val);
    return;
  }

  double curr_time = MOOSTime();
  if((curr_time - m_time_last_onfield_post) > m_onfield_post_interval) {
    m_time_last_onfield_post = curr_time;
    
    map<string, bool>::iterator p;
    for(p=m_map_node_onfield.begin(); p!=m_map_node_onfield.end(); p++) {
      string vname = p->first;
      string msg_var = "ONFIELD_" + toupper(vname);
      string msg_val = boolToString(m_map_node_onfield[vname]);
      Notify(msg_var, msg_val);
    }
  }
}

//------------------------------------------------------------
// Procedure: checkForOutOfZoneVehicles()

void TagManager::checkForOutOfZoneVehicles()
{
  map<string, NodeRecord>::iterator p;
  for(p=m_map_node_records.begin(); p!=m_map_node_records.end(); p++) {
    string vname = p->first;
    NodeRecord record = p->second;

    double vx = record.getX();
    double vy = record.getY();

    bool onfield_status_change = false;
    
    if(!m_zone_one.contains(vx, vy) && !m_zone_two.contains(vx, vy)) {
      if(!m_map_node_onfield.count(vname) || m_map_node_onfield[vname])
	onfield_status_change = true;
      m_map_node_onfield[vname] = false;

      if(!m_map_node_vtags_nowtagged.count(vname) || !m_map_node_vtags_nowtagged[vname]) {
	m_map_node_vtags_beentagged[vname]++;
	m_map_node_vtags_nowtagged[vname] = true;
	m_map_node_vtags_tagreason[vname] = "boundary";
	m_map_node_vtags_timetagged[vname] = m_curr_time;
	
	string targ_type = tolower(record.getType());
	if(targ_type == m_human_platform)
	  postHumanTagPairs("tag_manager", vname);
	else
	  postRobotTagPairs("tag_manager", vname);
      }
    }
    else {
      if(!m_map_node_onfield.count(vname) || !m_map_node_onfield[vname])
	onfield_status_change = true;
      m_map_node_onfield[vname] = true;
    }

    if(onfield_status_change)
      postOnFieldStatus(vname);
    
  }
}

//------------------------------------------------------------
// Procedure: handleMailVUnTagPost()

bool TagManager::handleMailVUnTagPost(string launch_str)
{
    // Part 1: Confirm request is coming from a known vehicle.
  string vname = tokStringParse(launch_str, "vname",  ',', '=');
  if((vname == "") || (m_map_node_records.count(vname) == 0)) {
    string msg = "Failed VUntag Post: Unknown vehicle [" + vname + "]";
    Notify("TAG_RELEASE_VERBOSE", msg);
    reportRunWarning(msg);
    reportEvent(msg);
    return(false);
  }

  // If the requesting vehicle is not currently tagged, just ignore
  if(!m_map_node_vtags_nowtagged.count(vname) ||
     !m_map_node_vtags_nowtagged[vname]) {
    return(true);
  }
  
  stringstream ss;
  ss << "Untag requested for " << vname ;
  reportEvent(ss.str());

  m_map_node_vtags_nowtagged[vname]  = false;
  m_map_node_vtags_tagreason[vname]  = "";
  m_map_node_vtags_timetagged[vname] = 0;

  string vtype = tolower(m_map_node_records[vname].getType());
  if(vtype == m_human_platform)
    postHumanUnTagPairs(vname);
  else
    postRobotUnTagPairs(vname);

  string time_str = doubleToString(m_curr_time - m_start_time);
  string msg = "vname=" + vname + ",time=" + time_str;
  Notify("TAG_RELEASE_VERBOSE", msg);
  Notify("TAG_RELEASE_"+toupper(vname), msg);
  Notify("TAGGED_"+toupper(vname), "false");

  // Part 3: Post an inactive circle for this vehicle to erase
  XYCircle circle;
  circle.set_label(vname);
  circle.set_active(false);
  string spec = circle.get_spec();
  Notify("VIEW_CIRCLE", spec);


  return(true);
}

//------------------------------------------------------------
// Procedure: postTagCircles()
//      Note: Called on every iteration since the circles for tagged
//            vehicles may need to move with the vehicle.

void TagManager::postTagCircles()
{
  map<string, bool>::iterator p;
  for(p=m_map_node_vtags_nowtagged.begin();
      p!=m_map_node_vtags_nowtagged.end(); p++) {
    string vname = p->first;
    bool   now_tagged = p->second;
    if(now_tagged) {
      double x = m_map_node_records[vname].getX();
      double y = m_map_node_records[vname].getY();

      XYCircle circle(x, y, m_tag_circle_range);
      circle.set_label(vname);
      if(m_map_node_vtags_tagreason[vname] == "boundary") {
	circle.set_color("fill", m_oob_circle_color);
	circle.set_color("edge", m_oob_circle_color);
      }
      else {
	circle.set_color("fill", m_tag_circle_color);
	circle.set_color("edge", m_tag_circle_color);
      }
      circle.set_transparency(0.2);
      string spec = circle.get_spec();
      Notify("VIEW_CIRCLE", spec);
    }
  }
}


//------------------------------------------------------------
// Procedure: postHumanTagPairs
//      Note: Called on only when a tag has been made.

void TagManager::postHumanTagPairs(string src_vname, string tar_vname)
{
  for(unsigned int i=0; i<m_human_tag_posts.size(); i++) {
    VarDataPair pair = m_human_tag_posts[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$SOURCE", src_vname);
    moosvar = findReplace(moosvar, "$TARGET", tar_vname);
    moosvar = findReplace(moosvar, "$UP_SOURCE", toupper(src_vname));
    moosvar = findReplace(moosvar, "$UP_TARGET", toupper(tar_vname));

    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$SOURCE", src_vname);
      sval = findReplace(sval, "$TARGET", tar_vname);
      sval = findReplace(sval, "$UP_SOURCE", toupper(src_vname));
      sval = findReplace(sval, "$UP_TARGET", toupper(tar_vname));

      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}

//------------------------------------------------------------
// Procedure: postRobotTagPairs
//      Note: Called on only when a tag has been made.

void TagManager::postRobotTagPairs(string src_vname, string tar_vname)
{
  for(unsigned int i=0; i<m_robot_tag_posts.size(); i++) {
    VarDataPair pair = m_robot_tag_posts[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$SOURCE", src_vname);
    moosvar = findReplace(moosvar, "$TARGET", tar_vname);
    moosvar = findReplace(moosvar, "$UP_SOURCE", toupper(src_vname));
    moosvar = findReplace(moosvar, "$UP_TARGET", toupper(tar_vname));

    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$SOURCE", src_vname);
      sval = findReplace(sval, "$TARGET", tar_vname);
      sval = findReplace(sval, "$UP_SOURCE", toupper(src_vname));
      sval = findReplace(sval, "$UP_TARGET", toupper(tar_vname));

      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}

//------------------------------------------------------------
// Procedure: postHumanUnTagPairs()
//      Note: Called on only when a tag has expired

void TagManager::postHumanUnTagPairs(string tar_vname)
{
  for(unsigned int i=0; i<m_human_untag_posts.size(); i++) {
    VarDataPair pair = m_human_untag_posts[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$TARGET", tar_vname);
    moosvar = findReplace(moosvar, "$UP_TARGET", toupper(tar_vname));

    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$TARGET", tar_vname);
      sval = findReplace(sval, "$UP_TARGET", toupper(tar_vname));
      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}

//------------------------------------------------------------
// Procedure: postRobotUnTagPairs()
//      Note: Called on only when a tag has expired

void TagManager::postRobotUnTagPairs(string tar_vname)
{
  for(unsigned int i=0; i<m_robot_untag_posts.size(); i++) {
    VarDataPair pair = m_robot_untag_posts[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$TARGET", tar_vname);
    moosvar = findReplace(moosvar, "$UP_TARGET", toupper(tar_vname));

    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$TARGET", tar_vname);
      sval = findReplace(sval, "$UP_TARGET", toupper(tar_vname));
      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}

//------------------------------------------------------------
// Procedure: postNoTagPairs
//      Note: Called on only when a tag has been unsuccessful

void TagManager::postNoTagPairs(string src_vname, string src_vteam,
				string src_reason)
{
  // First ensure that this post is happening with reasonable frequency
  // based on when the last time this vehicle involved in a notag post.
  if(m_map_prev_notag_post.count(src_vname)) {
    double time_gap = m_curr_time - m_map_prev_notag_post[src_vname];
    if(time_gap < m_notag_gap)
      return;
  }
  m_map_prev_notag_post[src_vname] = m_curr_time;
  
  
  for(unsigned int i=0; i<m_notag_posts.size(); i++) {
    VarDataPair pair = m_notag_posts[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$SOURCE", src_vname);
    moosvar = findReplace(moosvar, "$SRC_TEAM", src_vteam);
    moosvar = findReplace(moosvar, "$UP_SOURCE", toupper(src_vname));
    moosvar = findReplace(moosvar, "$UP_SRC_TEAM", toupper(src_vteam));

    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$SOURCE", src_vname);
      sval = findReplace(sval, "$SRC_TEAM", src_vteam);
      sval = findReplace(sval, "$UP_SOURCE", toupper(src_vname));
      sval = findReplace(sval, "$UP_SRC_TEAM", toupper(src_vteam));
      sval = findReplace(sval, "$REASON", src_reason);

      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}


//------------------------------------------------------------
// Procedure: postResult
//   Example: TAG_RESULT_ABE = "event=23,src=abe,team=red,rejected=selftagged"
//   Example: TAG_RESULT_ABE = "event=23,src=abe,team=red,rejected=freq"
//   Example: TAG_RESULT_ABE = "event=23,src=abe,team=red,rejected=zone"
//   Example: TAG_RESULT_ABE = "event=23,src=abe,team=red,tagged=none"
//   Example: TAG_RESULT_ABE = "event=23,src=abe,team=red,tagged=gilda"
//
//   Possible results: rejected or tagged
//   Possible reasons: rejected
//                        - selftagged or freq or zone
//                     tagged
//                        - none or vname 


void TagManager::postResult(string event, string vname, string vteam,
			    string result, string reason)
{
  string msg = "event=" + event;
  msg += ",src=" + vname;
  msg += ",team=" + vteam;
  msg += "," + result + "=" + reason;

  reportEvent(msg);
  Notify("TAG_RESULT_"+toupper(vname), msg);

  if((result == "rejected") || (reason == "none")) {
    if(reason == "selftagged") 
      postNoTagPairs(vname, vteam, "Tagger is tagged");
    else if(reason == "freq") 
      postNoTagPairs(vname, vteam, "Tagger is fast");
    else if(reason == "zone") 
      postNoTagPairs(vname, vteam, "Tagger is not home");
    else if(reason == "none") 
      postNoTagPairs(vname, vteam, "Nobody in range");
  }
}


//------------------------------------------------------------
// Procedure: postResult
//   Example: TAG_RESULT_VERBOSE = "event=23,src=abe,ranges=hal:2.1#jeb:19

void TagManager::postResult(string event, string vname,
			    map<string, double> map_node_range)
{
  string msg = "event=" + event;
  msg += ",src=" + vname;
  msg += ",ranges=";

  map<string,double>::iterator p;
  for(p=map_node_range.begin(); p!=map_node_range.end(); p++) {
    string targ = p->first;
    double dist = p->second;
    if(p != map_node_range.begin())
      msg += "#";
    msg += targ + ":" + doubleToString(dist,1);
  }
  Notify("TAG_RESULT_VERBOSE", msg);
}

//------------------------------------------------------------
// Procedure: postZonePolys

void TagManager::postZonePolys()
{
  string spec_one = m_zone_one.get_spec();
  string spec_two = m_zone_two.get_spec();

  Notify("VIEW_POLYGON", spec_one);
  Notify("VIEW_POLYGON", spec_two);

  if(m_zone_one_post_var != "")
    Notify(m_zone_one_post_var, spec_one);
  if(m_zone_two_post_var != "")
    Notify(m_zone_two_post_var, spec_two);
}



//------------------------------------------------------------
// Procedure: buildReport()
//
//   Global Settings
//   ======================================================
//   Tag Range: 35
//   Tag Interval: 10
//   Team [red]: lou, mal, ned, opi (4)
//   Team [blue]: lima, mesa, nuuk, oslo (4)
//
//   Tag Application Stats
//   ======================================================
//             ReQ   Rejec  Rejec            Applied  Time
//   Name      Tags  Zone   Freq   Accepted     Tags  Next
//   --------  ----  -----  -----  --------   ------   ----
//   lou        5        1      3        1         1   n/a
//   mal        8        2      1        5         0    23
//   ned        23      11      2       10         4     4
//   opi        18      2       9        7         1   n/a
//   --------  ----   ----  -----  --------   ------   ----
//   lima       2        0      1        1         1   n/a
//   mesa       4        2      1        1         0    23
//   nuuk       11      11      0        0         0   n/a
//   oslo       1        0      0        1         1    44
//
//   Tag Receiver Stats
//   ======================================================
//             Times   Currently  Time
//   Name      Tagged  Tagged     Remain   Taggable
//   --------  ------  ---------  ------   ---------
//   lou            2         no     n/a       no
//   mal            1        YES      14      YES
//   ned            1         no     n/a      YES
//   opi            0         no     n/a      YES
//   --------  ------  ---------  ------   ---------
//   lima           0         no     n/a       no
//   mesa           1        YES      58      YES
//   nuuk           1        YES       7      YES
//   oslo           2         no     n/a      YES
//
//   Events (Last 8):
//   ====================================================
//   201.0   Tag Attempt by HENRY [27]
//   201.0   Tag Attempt by HENRY [27]
//   201.0       BETTY tagged by ARCHIE
//   201.0   Tag Attempt by ARCHIE [23]
//   .....
//   198.2   Failed VTag Post: Unknown vehicle [jake]

bool TagManager::buildReport()
{
  // Part 1: Build the easy global settings output
  m_msgs << "Global Settings            " << endl;
  m_msgs << "===========================" << endl;
  m_msgs << "Tag Range    :      " << doubleToStringX(m_tag_range,1)   << endl;
  m_msgs << "Tag Min Interval:   " << doubleToStringX(m_tag_min_interval,1) << endl;
  m_msgs << "Tag Duration:       " << doubleToStringX(m_tag_duration,1) << endl;
  m_msgs << "Tag Circle Enabled: " << boolToString(m_tag_circle) << endl;

  // Part 2: Produce the team structure
  map<string, set<string> >::iterator pp;
  for(pp=m_map_teams.begin(); pp!=m_map_teams.end(); pp++) {
    string team_name = pp->first;
    set<string> team = pp->second;
    m_msgs << "Team [" << team_name << "]: ";
    set<string>::iterator qq;
    for(qq=team.begin(); qq!=team.end(); qq++) {
      if(qq!=team.begin())
	m_msgs << ", ";
      m_msgs << *qq;
    }
    m_msgs << " (" << team.size() << ")" << endl;
  }
  m_msgs << endl;

  // Part 3: Build report from perspective of tagging vehicles
  m_msgs << "Tag Application Stats:         " << endl;
  m_msgs << "=================================================" << endl;
  ACTable actab(8);
  actab << "     | ReQ  | Rejec | Rejec | Rejec |          | Applied | Time ";
  actab << "Name | Tags | Zone  | Freq  | Self  | Accepted |    Tags | Next";
  actab.addHeaderLines();

  map<string, NodeRecord>::iterator p1;
  for(p1=m_map_node_records.begin(); p1!=m_map_node_records.end(); p1++) {
    string vname = p1->first;  // col1
    string tags = uintToString(m_map_node_vtags_requested[vname]);   // col2
    string zone = uintToString(m_map_node_vtags_rejzone[vname]);     // col3
    string freq = uintToString(m_map_node_vtags_rejfreq[vname]);     // col4
    string self = uintToString(m_map_node_vtags_rejself[vname]);     // col5
    string accp = uintToString(m_map_node_vtags_accepted[vname]);    // col6
    string hits = uintToString(m_map_node_vtags_succeeded[vname]);   // col7
    string next = "n/a";  // col7

    actab << vname << tags << zone << freq << self << accp << hits << next;
  }
  m_msgs << actab.getFormattedString();
  m_msgs << endl << endl;

  // Part 4: Build report from perspective of vehicles being tagged.
  m_msgs << "Tag Receiver Stats:         " << endl;
  m_msgs << "=================================================" << endl;
  ACTable actabb(6);
  actabb << "     | Times  | Currently | Time   |          | On ";
  actabb << "Name | Tagged | Tagged    | Remain | Taggable | Field ";
  actabb.addHeaderLines();

  for(pp=m_map_teams.begin(); pp!=m_map_teams.end(); pp++) {
    if(pp!=m_map_teams.begin())
      actabb.addHeaderLines();
    set<string> team = pp->second;
    set<string>::iterator qq;
    for(qq=team.begin(); qq!=team.end(); qq++) {
      string vname = *qq;

      bool now_tagged = false;
      if(m_map_node_vtags_nowtagged.count(vname))
	now_tagged = m_map_node_vtags_nowtagged[vname];

      bool now_onfield = false;
      if(m_map_node_onfield.count(vname))
	now_onfield = m_map_node_onfield[vname];

      double time_remaining = 0;
      if(m_map_node_vtags_timetagged.count(vname)) {
	double elapsed = (m_curr_time - m_map_node_vtags_timetagged[vname]);
	time_remaining = m_tag_duration - elapsed;
	if(time_remaining < 0)
	  time_remaining = 0;
      }

      string times = uintToString(m_map_node_vtags_beentagged[vname]);   // col2
      string now_tagged_s  = boolToString(now_tagged);
      string trem  = doubleToString(time_remaining,2);
      string tgabl = boolToString(!now_tagged);
      string onfld = boolToString(now_onfield);
      actabb << vname << times << now_tagged_s << trem << tgabl << onfld;
    }
  }

  m_msgs << actabb.getFormattedString();
  return(true);
}
