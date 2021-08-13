/************************************************************/
/*   NAME: Mike Benjamin                                    */
/*   ORGN: Dept of Mechanical Eng / CSAIL, MIT Cambridge MA */
/*   FILE: FlagManager.cpp                                  */
/*   DATE: August 18th, 2015                                */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "GeomUtils.h"
#include "ACTable.h"
#include "FlagManager.h"
#include "NodeRecordUtils.h"
#include "XYMarker.h"
#include "XYPolygon.h"
#include "XYFormatUtilsMarker.h"
#include "XYFormatUtilsPoly.h"

using namespace std;

//---------------------------------------------------------
// Constructor

FlagManager::FlagManager()
{
  // Default config values
  m_default_flag_range    = 10; // meters
  m_default_flag_width    = 3;  // meters
  m_default_flag_type     = "circle";
  m_report_flags_on_start = true;

  m_near_flag_range_buffer = 2;

  // Default state values
  m_total_node_reports_rcvd  = 0;
  m_total_grab_requests_rcvd = 0;

  m_flag_follows_vehicle = true;
  
  m_grabbed_color   = "white";
  m_ungrabbed_color = "red";

  m_poly_vertex_size = 0;
  m_poly_edge_size = 1;
  m_poly_vertex_color = "blue";
  m_poly_edge_color = "grey50";
  m_poly_fill_color = "grey90";

  // Heartbeat variables
  m_heartbeat_counter = 0;
  m_heartbeat_last    = 0;
  m_post_heartbeat    = true;
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool FlagManager::OnNewMail(MOOSMSG_LIST &NewMail)
{
  AppCastingMOOSApp::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;
    string key   = msg.GetKey();
    string sval  = msg.GetString();
    string comm  = msg.GetCommunity();

#if 0 // Keep these around just for template
    double dval  = msg.GetDouble();
    string msrc  = msg.GetSource();
    double mtime = msg.GetTime();
    bool   mdbl  = msg.IsDouble();
    bool   mstr  = msg.IsString();
#endif

    bool handled = true;
    if((key == "NODE_REPORT") || (key == "NODE_REPORT_LOCAL"))
      handled = handleMailNodeReport(sval);
    else if(key == "FLAG_RESET")
      handled = handleMailFlagReset(sval);
    else if(key == "FLAG_GRAB_REQUEST")
      handled = handleMailFlagGrab(sval, comm);
    else if(key == "TAGGED_VEHICLES")
      handled = handleMailTaggedVehicles(sval);
    else if(key == "PMV_CONNECT") {
      postFlagMarkers(true);
      postPolygons();
    }
    else
      handled = false;

    if(!handled)
      reportRunWarning("Unhandled Mail: " + key);
  }

  return(true);
}

//---------------------------------------------------------
// Procedure: OnConnectToServer

bool FlagManager::OnConnectToServer()
{
  registerVariables();
  return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()

bool FlagManager::Iterate()
{
  AppCastingMOOSApp::Iterate();

  updateVehiclesInFlagRange();
  updateVehiclesHaveScored();
  updateVehiclesUntagged();

  if(m_flag_follows_vehicle)
    updateVehiclesFlagRender();

  if(m_post_heartbeat)
    postHeartBeat();

  AppCastingMOOSApp::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: postHeartBeat()
//            Post heatbeat message to aid in log file syncing

void FlagManager::postHeartBeat()
{
  double delta_time = m_curr_time - m_heartbeat_last;
  if(delta_time > 15) {
    m_heartbeat_last = m_curr_time;

    // Post a 5-digit index based on time. This should allow
    // the index sequence to pick up where it left off if the
    // flag manager is re-started mid competition.
    long int time_index = (long int)(m_curr_time);
    time_index = time_index % 100000;

    Notify("UFMG_HEARTBEAT", (double)(time_index));
  }
    
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool FlagManager::OnStartUp()
{
  AppCastingMOOSApp::OnStartUp();

  STRING_LIST sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(!m_MissionReader.GetConfigurationAndPreserveSpace(GetAppName(), sParams))
    reportConfigWarning("No config block found for " + GetAppName());

  STRING_LIST pass2params;

  // Perform two passes so we can set the default flag paramaters before
  // handling the flags in the second pass.
  STRING_LIST::iterator p;
  for(p=sParams.begin(); p!=sParams.end(); p++) {
    string orig  = *p;
    string line  = *p;
    string param = tolower(biteStringX(line, '='));
    string value = line;

    bool handled = true;
    if(param == "grabbed_color")
      handled = setColorOnString(m_grabbed_color, value);
    else if(param == "ungrabbed_color")
      handled = setColorOnString(m_ungrabbed_color, value);
    
    else if(param == "default_flag_range")
      handled = setNonNegDoubleOnString(m_default_flag_range, value);
    else if(param == "near_flag_range_buffer")
      handled = setNonNegDoubleOnString(m_near_flag_range_buffer, value);
    else if(param == "default_flag_width")
      handled = setNonNegDoubleOnString(m_default_flag_width, value);
    else if(param == "poly_vertex_size")
      handled = setNonNegDoubleOnString(m_poly_vertex_size, value);
    else if(param == "poly_edge_size")
      handled = setNonNegDoubleOnString(m_poly_edge_size, value);
    else if(param == "poly_vertex_color")
      handled = setColorOnString(m_poly_vertex_color, value);
    else if(param == "poly_edge_color")
      handled = setColorOnString(m_poly_edge_color, value);
    else if(param == "poly_fill_color")
      handled = setColorOnString(m_poly_fill_color, value);
    
    else if(param == "flag_follows_vehicle")
      handled = setBooleanOnString(m_flag_follows_vehicle, value);
    else if(param == "post_heartbeat")
      handled = setBooleanOnString(m_post_heartbeat, value);
    
    else if(param == "default_flag_type") {
      value = tolower(value);
      if((value != "circle")  && (value != "square") &&
         (value != "diamond") && (value != "efield") &&
         (value != "gateway") & (value != "triangle")) 
        handled = false;
      else
        m_default_flag_type = value;
    }
    else
      pass2params.push_back(orig);

    if(!handled)
      reportUnhandledConfigWarning(orig);

  }

  STRING_LIST::iterator p2;
  for(p2=pass2params.begin(); p2!=pass2params.end(); p2++) {
    string orig  = *p2;
    string line  = *p2;
    string param = tolower(biteStringX(line, '='));
    string value = line;

    bool handled = true;
    if(param == "flag")
      handled = handleConfigFlag(value);
    else if(param == "grab_post")
      handled = handleConfigGrabPost(value);
    else if(param == "lose_post")
      handled = handleConfigLosePost(value);
    else if(param == "near_post")
      handled = handleConfigNearPost(value);
    else if(param == "away_post")
      handled = handleConfigAwayPost(value);
    else if(param == "deny_post")
      handled = handleConfigDenyPost(value);
    else if(param == "goal_post")
      handled = handleConfigGoalPost(value);
    else if(param == "home_post")
      handled = handleConfigHomePost(value);
    else
      handled = false;
    
    if(!handled)
      reportUnhandledConfigWarning(orig);
  }

  // Post a bunch of viewable artifacts
  postFlagMarkers();

  // Possibly post a report for all vehicles to know the flags
  if(m_report_flags_on_start)
    postFlagSummary();

  postPolygons();
  
  registerVariables();
  return(true);
}

//---------------------------------------------------------
// Procedure: registerVariables

void FlagManager::registerVariables()
{
  AppCastingMOOSApp::RegisterVariables();
  Register("FLAG_GRAB_REQUEST", 0);
  Register("FLAG_RESET", 0);
  Register("NODE_REPORT", 0);
  Register("NODE_REPORT_LOCAL", 0);
  Register("TAGGED_VEHICLES", 0);
  Register("PMV_CONNECT", 0);
}


//---------------------------------------------------------
// Procedure: handleConfigFlag
//   Example: flag = x=2,y=3,range=10,label=one

bool FlagManager::handleConfigFlag(string str)
{
  XYMarker flag = string2Marker(str);

  if(!flag.is_set_x() || !flag.is_set_y()) {
    reportConfigWarning("Flag with missing x-y position: " + str);
    return(false);
  }
  if(flag.get_label() == "") {
    reportConfigWarning("Flag with missing label: " + str);
    return(false);
  }

  if(!flag.is_set_range())
    flag.set_range(m_default_flag_range);

  if(!flag.is_set_width())
    flag.set_width(m_default_flag_width);

  if(!flag.is_set_type())
    flag.set_type(m_default_flag_type);

  // Ensure that a unique label has been provided
  for(unsigned int i=0; i<m_flags.size(); i++) {
    if(flag.get_label() == m_flags[i].get_label()) {
      reportConfigWarning("Flag with duplicate label: " + str);
      return(false);
    }
  }

  m_flags.push_back(flag);
  m_flags_changed.push_back(true);

  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigGrabPost
//   Example: var=SAY_MOOS, sval={Hello World}
//   Example: var=SAY_MOOS, sval={$[VNAME] has the flag}
//   Example: var=SAY_MOOS_$[VNAME],     \
//            sval={You have the flag}

bool FlagManager::handleConfigGrabPost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);

  m_flag_grab_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigLosePost

bool FlagManager::handleConfigLosePost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);

  m_flag_lose_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigNearPost

bool FlagManager::handleConfigNearPost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);

  m_flag_near_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigAwayPost

bool FlagManager::handleConfigAwayPost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);
  
  m_flag_away_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigDenyPost

bool FlagManager::handleConfigDenyPost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);
  
  m_flag_deny_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigGoalPost

bool FlagManager::handleConfigGoalPost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);
  
  m_flag_goal_posts.push_back(pair);
  return(true);
}

//---------------------------------------------------------
// Procedure: handleConfigHomePost

bool FlagManager::handleConfigHomePost(string str)
{
  VarDataPair pair = stringToVarDataPair(str);
  if(!pair.valid())
    return(false);
  
  m_flag_home_posts.push_back(pair);
  return(true);
}

//------------------------------------------------------------
// Procedure: handleMailTaggedVehicles()
//   Example: TAGGED_VEHICLES = henry,gus,hal

bool FlagManager::handleMailTaggedVehicles(string str)
{
  m_tagged_vnames.clear();

  vector<string> svector = parseString(str, ',');
  for(unsigned int i=0; i<svector.size(); i++) {
    string vname = stripBlankEnds(svector[i]);
    m_tagged_vnames.insert(vname);
  }

  return(true);
}

//------------------------------------------------------------
// Procedure: handleMailNodeReport()

bool FlagManager::handleMailNodeReport(string str)
{
  NodeRecord new_record = string2NodeRecord(str);

  string whynot;
  if(!new_record.valid("x,y,name", whynot)) {
    reportRunWarning("Unhandled NodeReport: " + whynot);
    return(false);
  }

  string vname = toupper(new_record.getName());

  m_map_record[vname] = new_record;
  m_map_tstamp[vname] = m_curr_time;

  if(m_map_rcount.count(vname) == 0)
    m_map_rcount[vname] = 1;
  else
    m_map_rcount[vname]++;

  m_total_node_reports_rcvd++;

  return(true);
}

//------------------------------------------------------------
// Procedure: handleMailFlagReset()
//   Example: FLAG_RESET = vname=henry
//   Example: FLAG_RESET = label=alpha

bool FlagManager::handleMailFlagReset(string str)
{
  bool some_flags_were_reset = false;

  if(tolower(str) == "all") {
    some_flags_were_reset = resetFlagsAll();
  }
  else {
    string vname = tokStringParse(str, "vname", ',', '=');
    if(vname == "")
      vname = tokStringParse(str, "VNAME", ',', '=');
    if(vname != "")
      some_flags_were_reset = resetFlagsByVName(vname);

    string label = tokStringParse(str, "label", ',', '=');
    if(label != "")
      some_flags_were_reset = resetFlagsByLabel(label);

    if((label == "") && (vname == ""))
      return(false);
  }

  if(some_flags_were_reset) {
    postFlagMarkers();
    postFlagSummary();
  }

  return(true);
}

//------------------------------------------------------------
// Procedure: handleMailFlagGrab
//   Example: GRAB_FLAG_REQUEST = "vname=henry"

bool FlagManager::handleMailFlagGrab(string str, string community)
{
  m_total_grab_requests_rcvd++;

  // Part 1: Parse the Grab Request
  string grabbing_vname = tokStringParse(str, "vname", ',', '=');

  // Part 2: Sanity check on the Grab Request
  // Check if grabbing vname is set and matches message community
  if((grabbing_vname == "") || (grabbing_vname != community)) {
    string reason = "invalid_vehicle_name";
    invokePosts("deny", grabbing_vname, "", "", reason);
    reportRunWarning("FLAG_GRAB_REQUEST: " + reason);
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - " + reason);
    return(false);
  }
  
  // If no node records of the grabbing vehicle, return false
  string up_vname = toupper(grabbing_vname);
  if(m_map_record.count(up_vname) == 0) {
    string reason = "name_unknown_to_flag_manager";
    reportRunWarning("FLAG_GRAB_REQUEST: " + reason);
    invokePosts("deny", grabbing_vname, "", "", reason);
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - " + reason);
    return(false);
  }

  // If grabbing vehicle already has a flag, return false
  if(hasFlag(grabbing_vname)) {
    string reason = grabbing_vname + "_already_has_a_flag";
    reportRunWarning("FLAG_GRAB_REQUEST: " + reason);
    invokePosts("deny", grabbing_vname, "", "", reason);
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - " + reason);
    return(false);
  }


  // Part 3: OK grab, so increment counters.
  m_map_grab_count[up_vname]++;

  if(m_tagged_vnames.count(grabbing_vname) ||  m_tagged_vnames.count(up_vname)) {
    string reason = grabbing_vname + "_is_tagged";
    reportRunWarning("FLAG_GRAB_REQUEST: " + reason);
    invokePosts("deny", grabbing_vname, "", "", reason);
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - " + reason);
    return(false);
  }

  if(m_flags.size() == 0) {
    string reason = "no_flags_to_grab";
    invokePosts("deny", grabbing_vname, "", "", reason);
    reportRunWarning("FLAG_GRAB_REQUEST: " + reason);
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - " + reason);
    return(false);
  }
  
  // Part 4: Get the grabbing vehicle's position from the record
  NodeRecord record = m_map_record[up_vname];
  double curr_vx = record.getX();
  double curr_vy = record.getY();
  string group = record.getGroup();


  
  // Part 5: For each flag with the grab_dist of the vehicle, GRAB
  string result;
  for(unsigned int i=0; i<m_flags.size(); i++) {
    if((m_flags[i].get_owner() == "") && (m_flags[i].get_label() != group)) {
      string flag_name = m_flags[i].get_label();
      double x = m_flags[i].get_vx();
      double y = m_flags[i].get_vy();
      double dist = hypot(x-curr_vx, y-curr_vy);

      if(dist <= m_flags[i].get_range()) {
        if(result != "")
          result += ",";
        result += "grabbed=" + m_flags[i].get_label();
        m_flags[i].set_owner(grabbing_vname);
        m_flags_changed[i] = true;
        m_map_flag_count[up_vname]++;

	m_map_team_grabs[group]++;
	
	Notify("HAS_FLAG_"+toupper(grabbing_vname), "true");

	invokePosts("grab", grabbing_vname, group, flag_name);
      }
    }
  }
  if(result == "") {
    invokePosts("deny", grabbing_vname, group, "", "no_one_in_range");
    Notify("FLAG_GRAB_REPORT", "Nothing grabbed - no one in range");
    return(true);
  }
  
  postFlagSummary();
  postFlagMarkers();

  Notify("FLAG_GRAB_REPORT", result);

  return(true);
}


//------------------------------------------------------------
// Procedure: updateVehiclesInFlagRange
//   Purpose: For each vehicle determine if it is within the range
//            of an enemy flag.

void FlagManager::updateVehiclesInFlagRange()
{
  map<string, NodeRecord>::iterator p;
  for(p=m_map_record.begin(); p!=m_map_record.end(); p++) {
    string vname = p->first;
    NodeRecord record = p->second;
    string vteam = record.getGroup();
    double vx = record.getX();
    double vy = record.getY();

    bool vname_in_flag_zone = false;
    bool vname_near_flag_zone = false;

    string flag_name;
    for(unsigned int i=0; i<m_flags.size(); i++) {
      flag_name = m_flags[i].get_label();
      if(flag_name != vteam) {
	double range = m_flags[i].get_range();
	double flagx = m_flags[i].get_vx();
	double flagy = m_flags[i].get_vy();

	double dist = hypot(vx-flagx, vy-flagy);
	if(dist <= range)
	  vname_in_flag_zone = true;
	if(dist <= (range + m_near_flag_range_buffer))
	  vname_near_flag_zone = true;
      }
    }

    //if(!m_map_in_flag_zone[vname] && vname_in_flag_zone)
    //  invokePosts("near", vname, vteam, flag_name);

    if(!m_map_near_flag_zone[vname] && vname_near_flag_zone)
      invokePosts("near", vname, vteam, flag_name);

    if((m_map_in_flag_zone[vname] || (m_map_near_flag_zone[vname]))
	&& !vname_near_flag_zone)
      invokePosts("away", vname, vteam, flag_name);

    m_map_in_flag_zone[vname] = vname_in_flag_zone;
    m_map_near_flag_zone[vname] = vname_near_flag_zone;
  }
}


//------------------------------------------------------------
// Procedure: updateVehiclesHaveScored

void FlagManager::updateVehiclesHaveScored()
{
  // For each vehicle, check if it has scored.
  map<string, NodeRecord>::iterator p;
  for(p=m_map_record.begin(); p!=m_map_record.end(); p++) {
    string vname      = p->first;
    NodeRecord record = p->second;

    // Check, for all flags, if vname owns the flag
    for(unsigned int i=0; i<m_flags.size(); i++) {
      string flag_owner = tolower(m_flags[i].get_owner());
      string flag_label = m_flags[i].get_label();
      if(flag_owner == tolower(vname)) {
	// If it owns the flag, check if vname is home yet
	string vteam = record.getGroup();
	double vx = record.getX();
	double vy = record.getY();

	// home is defined by begin close enough to ownflag
	for(unsigned int j=0; j<m_flags.size(); j++) {
	  if(m_flags[j].get_label() == vteam) {
	    double range = m_flags[j].get_range();
	    double fx = m_flags[j].get_vx();
	    double fy = m_flags[j].get_vy();
	    double dist = hypot((fx-vx), (fy-vy));
	    // If successful
	    if(dist < range) {
	      m_map_team_score[vteam]++;
	      resetFlagsByVName(vname);
	      invokePosts("goal", vname, vteam, flag_label);

	      postFlagMarkers();
	      postFlagSummary();
	    }
	  }
	}
      }
    }
  }
}

//------------------------------------------------------------
// Procedure: updateVehiclesFlagRender

void FlagManager::updateVehiclesFlagRender()
{
  // For each vehicle, check if it has scored.
  map<string, NodeRecord>::iterator p;
  for(p=m_map_record.begin(); p!=m_map_record.end(); p++) {
    string vname      = p->first;
    NodeRecord record = p->second;

    // Check, for all flags, if vname owns the flag
    for(unsigned int i=0; i<m_flags.size(); i++) {
      string flag_owner = tolower(m_flags[i].get_owner());
      string flag_label = m_flags[i].get_label();
      if(flag_owner == tolower(vname)) {

	XYMarker marker = m_flags[i];
	marker.set_color("secondary_color", "black");
	
	double vx = record.getX();
	double vy = record.getY();
	double vh = record.getHeading();
	
	double px, py;
	projectPoint((vh+180), 3, vx, vy, px, py);
	marker.set_vx(px);
	marker.set_vy(py);
	
	string spec = marker.get_spec();
	Notify("VIEW_MARKER", spec);
	
      }
    }
  }
}

//------------------------------------------------------------
// Procedure: updateVehiclesUntagged

void FlagManager::updateVehiclesUntagged()
{
  // For each vehicle, check if it is tagged, and if it is home now.
  map<string, NodeRecord>::iterator p;
  for(p=m_map_record.begin(); p!=m_map_record.end(); p++) {
    string vname      = tolower(p->first);
    NodeRecord record = p->second;

    string vteam = record.getGroup();
    double vx = record.getX();
    double vy = record.getY();

    bool vname_in_home_zone = false;

    // home is defined by begin close enough to ownflag
    string flag_name;
    for(unsigned int i=0; i<m_flags.size(); i++) {
      flag_name = m_flags[i].get_label();
      if(flag_name == vteam) {
	double flag_range = m_flags[i].get_range();
	double fx = m_flags[i].get_vx();
	double fy = m_flags[i].get_vy();
	double dist = hypot((fx-vx), (fy-vy));
	// If successful
	if(dist < flag_range) {
	  vname_in_home_zone = true;
	  if(m_tagged_vnames.count(vname) && !m_map_in_home_zone[vname]) {
	    Notify("UNTAG_REQUEST", "vname="+vname);
	    invokePosts("home", vname, vteam, "");
	  }
	}
      }
    }

    m_map_in_home_zone[vname] = vname_in_home_zone;
  }
}

//------------------------------------------------------------
// Procedure: resetFlagsByLabel
//      Note: Resets any flag with the given label to be not
//            ownedby anyone.
//   Returns: true if a flag was indeed reset, possibly visuals
//            then need updating

bool FlagManager::resetFlagsByLabel(string label)
{
  bool some_flags_were_reset = false;
  
  for(unsigned int i=0; i<m_flags.size(); i++) {
    if(m_flags[i].get_label() == label) {
      if(m_flags[i].get_owner() != "") {
	string flag_owner = m_flags[i].get_owner();
        m_flags[i].set_owner("");
        m_flags_changed[i] = true;
        some_flags_were_reset = true;
	Notify("HAS_FLAG_"+toupper(flag_owner), "false");

	invokePosts("lose", "system", "", label);
      }
    }
  }
  return(some_flags_were_reset);
}

//------------------------------------------------------------
// Procedure: resetFlagsAll
//      Note: Resets all flags regardless of who owned them
//   Returns: true if a flag was indeed reset, possibly visuals
//            then need updating

bool FlagManager::resetFlagsAll()
{
  bool some_flags_were_reset = false;

  for(unsigned int i=0; i<m_flags.size(); i++) {
    if(m_flags[i].get_owner() != "") {
      string flag_name = m_flags[i].get_label();
      m_flags[i].set_owner("");
      m_flags[i].set_owner("");
      m_flags_changed[i] = true;
      some_flags_were_reset = true;
      Notify("HAS_FLAG_ALL", "false");

      invokePosts("lose", "system", "", flag_name);
    }
  }
  return(some_flags_were_reset);
}

//------------------------------------------------------------
// Procedure: resetFlagsByVName
//      Note: Resets any flag presently owned by the given vehicle
//   Returns: true if a flag was indeed reset, possibly visuals
//            then need updating

bool FlagManager::resetFlagsByVName(string vname)
{
  bool some_flags_were_reset = false;
  
  for(unsigned int i=0; i<m_flags.size(); i++) {
    string flag_owner = tolower(m_flags[i].get_owner());
    if(flag_owner == tolower(vname)) {
      string flag_name = m_flags[i].get_label();

      m_flags[i].set_owner("");
      m_flags_changed[i] = true;
      some_flags_were_reset = true;

      Notify("HAS_FLAG_"+toupper(vname), "false");
      invokePosts("lose", "system", "", flag_name);
    }
  }
  return(some_flags_were_reset);
}

//------------------------------------------------------------
// Procedure: postFlagMarkers
//      Note: Typically JUST called on startup unless marker
//            positions or colors are allowed to change.

void FlagManager::postFlagMarkers(bool force)
{
  for(unsigned int i=0; i<m_flags.size(); i++) {
    if(m_flags_changed[i] || force) {
      XYMarker marker = m_flags[i];
      if(m_flags[i].get_owner() == "") {
        if(!m_flags[i].color_set("primary_color"))
          marker.set_color("primary_color", m_ungrabbed_color);
      }
      else
        marker.set_color("primary_color", m_grabbed_color);
      marker.set_color("secondary_color", "black");

      string spec = marker.get_spec();
      Notify("VIEW_MARKER", spec);
      m_flags_changed[i] = false;
    }
  }
}

//------------------------------------------------------------
// Procedure: postPolygons
//      Note: Typically JUST called on startup unless marker
//            positions or colors are allowed to change.

void FlagManager::postPolygons()
{
  for(unsigned int i=0; i<m_flags.size(); i++) {
    string spec = "format=radial";
    spec += ",x=" + doubleToString(m_flags[i].get_vx(),3);
    spec += ",y=" + doubleToString(m_flags[i].get_vy(),3);
    spec += ",radius=" + doubleToString(m_flags[i].get_range(),1);
    spec += ",pts=24";
    spec += ",label=flag_zone_" + m_flags[i].get_label();
    XYPolygon poly = string2Poly(spec);
    poly.set_vertex_size(m_poly_vertex_size);
    poly.set_edge_size(m_poly_edge_size);
    poly.set_vertex_color(m_poly_vertex_color);
    poly.set_edge_color(m_poly_edge_color);
    poly.set_color("fill", m_poly_fill_color);
    string pspec = poly.get_spec();
    Notify("VIEW_POLYGON", pspec);
  }
}

//------------------------------------------------------------
// Procedure: postFlagSummary
//   Example: FLAG_SUMMARY = x=50,y=-24,width=3,range=10,
//            primary_color=red, type=circle,owner=evan,label=red #
//            x=-58,y=-71, width=3,range=10,primary_color=blue,           
//            type=circle,label=blue   

void FlagManager::postFlagSummary()
{
  string summary;
  for(unsigned int i=0; i<m_flags.size(); i++) {
    string spec = m_flags[i].get_spec();
    if(summary != "")
      summary += " # ";
    summary += spec;

    string var_label = toupper(m_flags[i].get_label());
    var_label += "_FLAG_GRABBED";
    if (m_flags[i].get_owner() == "")
      Notify(var_label, "false");
    else
      Notify(var_label, "true");
  }
  Notify("FLAG_SUMMARY", summary);
}

//------------------------------------------------------------
// Procedure: hasFlag()
//   Purpose: Determine if the given vehicle has a flag. No check
//            is made w.r.t. type/color of flag. 

bool FlagManager::hasFlag(string vname)
{
  for(unsigned int i=0; i<m_flags.size(); i++) {
    if(tolower(m_flags[i].get_owner()) == tolower(vname))
      return(true);
  }
  return(false);
}

//------------------------------------------------------------
// Procedure: invokePosts()

void FlagManager::invokePosts(string ptype, string vname, string vteam,
			      string fname, string reason)
{
  vector<VarDataPair> pairs;
  if(ptype == "grab")
    pairs = m_flag_grab_posts;
  else if(ptype == "lose")
    pairs = m_flag_lose_posts;
  else if(ptype == "near")
    pairs = m_flag_near_posts;
  else if(ptype == "away")
    pairs = m_flag_away_posts;
  else if(ptype == "deny")
    pairs = m_flag_deny_posts;
  else if(ptype == "goal")
    pairs = m_flag_goal_posts;
  else if(ptype == "home")
    pairs = m_flag_home_posts;

  for(unsigned int i=0; i<pairs.size(); i++) {
    VarDataPair pair = pairs[i];
    string moosvar = pair.get_var();
    moosvar = findReplace(moosvar, "$VNAME", vname);
    moosvar = findReplace(moosvar, "$VTEAM", vteam);
    moosvar = findReplace(moosvar, "$FLAG", fname);
    moosvar = findReplace(moosvar, "$UP_VNAME", toupper(vname));
    moosvar = findReplace(moosvar, "$UP_VTEAM", toupper(vteam));
    
    if(!pair.is_string()) {
      double dval = pair.get_ddata();
      Notify(moosvar, dval);
    }
    else {
      string sval = pair.get_sdata();
      sval = findReplace(sval, "$VNAME", vname);
      sval = findReplace(sval, "$VTEAM", vteam);
      sval = findReplace(sval, "$FLAG", fname);
      sval = findReplace(sval, "$UP_VNAME", toupper(vname));
      sval = findReplace(sval, "$UP_VTEAM", toupper(vteam));
      sval = findReplace(sval, "$REASON", reason);
      
      if(strContains(sval, "TIME")) {
	string stime = doubleToString(m_curr_time, 2);
	sval = findReplace(sval, "$TIME", stime);
      }
      Notify(moosvar, sval);
    }
  }
}

//------------------------------------------------------------
// Procedure: buildReport()

bool FlagManager::buildReport()
{
  m_msgs << "Configuration Summary: " << endl;
  m_msgs << "======================================" << endl;
  m_msgs << "  default_flag_range: " << m_default_flag_range << endl;
  m_msgs << "  default_flag_width: " << m_default_flag_width << endl;
  m_msgs << "  default_flag_type:  " << m_default_flag_type  << endl;
  m_msgs << endl;

  m_msgs << "Node Report Summary"                    << endl;
  m_msgs << "======================================" << endl;
  m_msgs << "        Total Received: " << m_total_node_reports_rcvd << endl;

  map<string, unsigned int>::iterator p;
  for(p=m_map_rcount.begin(); p!=m_map_rcount.end(); p++) {
    string vname = p->first;
    unsigned int total = p->second;
    string pad_vname  = padString(vname, 20);
    m_msgs << "  " << pad_vname << ": " << total;

    double elapsed_time = m_curr_time - m_map_tstamp[vname];
    string stime = "(" + doubleToString(elapsed_time,1) + ")";
    stime = padString(stime,12);
    m_msgs << stime << endl;
  }

  m_msgs << endl;

  m_msgs << "Team Summary" << endl;
  m_msgs << "======================================" << endl;
  ACTable actab(3);
  actab << "Team | Grabs | Scores";
  actab.addHeaderLines();

  map<string,unsigned int>::iterator p1;
  for(p1=m_map_team_grabs.begin(); p1!=m_map_team_grabs.end(); p1++) {
    string vteam = p1->first;
    unsigned int grabs  = p1->second;
    unsigned int scores = m_map_team_score[vteam];
    string s_scores = uintToString(scores);
    string s_grabs  = uintToString(grabs);
    actab << vteam << s_grabs << s_scores;
  }
  m_msgs << actab.getFormattedString();

 
  m_msgs << endl << endl;;
  m_msgs << "Vehicle Summary" << endl;
  m_msgs << "======================================" << endl;
  actab = ACTable(5);
  actab << "VName | Grabs | Flags | InFlagZone | HasFlag";
  actab.addHeaderLines();

  map<string,unsigned int>::iterator p2;
  for(p2=m_map_rcount.begin(); p2!=m_map_rcount.end(); p2++) {
    string vname = p2->first;
    unsigned int grab_count = 0;
    if(m_map_grab_count.count(vname) != 0)
      grab_count = m_map_grab_count[vname];
    unsigned int flag_count = 0;
    if(m_map_flag_count.count(vname) != 0)
      flag_count = m_map_flag_count[vname];

    bool in_flag_zone = false;
    if(m_map_in_flag_zone.count(vname) != 0)
      in_flag_zone = m_map_in_flag_zone[vname];

    bool has_flag = hasFlag(vname);
    
    string s_grab_count = uintToString(grab_count);
    string s_flag_count = uintToString(flag_count);
    string s_in_flag_zone = boolToString(in_flag_zone);
    string s_has_flag = boolToString(has_flag);

    actab << vname << s_grab_count << s_flag_count << s_in_flag_zone << s_has_flag;
  }
  m_msgs << actab.getFormattedString();
  m_msgs << endl << endl;

  m_msgs << "Flag Summary" << endl;
  m_msgs << "======================================" << endl;
  actab = ACTable(4);
  actab << "Flag | Range | Owner | Spec";
  actab.addHeaderLines();

  for(unsigned int i=0; i<m_flags.size(); i++) {
    string label = m_flags[i].get_label();
    string vname = m_flags[i].get_owner();
    string range = doubleToStringX(m_flags[i].get_range(), 2);
    actab << label << range << vname << m_flags[i].get_spec();
  }
  m_msgs << actab.getFormattedString();

  return(true);
}
