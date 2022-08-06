/************************************************************/
/*    NAME: Carter Fendley                                              */
/*    ORGN: MIT                                             */
/*    FILE: EpisodeManager.cpp                                        */
/*    DATE:                                                 */
/************************************************************/

#include <iterator>
#include "MBUtils.h"
#include "ACTable.h"
#include "EpisodeManager.h"
#include <cmath>

using namespace std;

//---------------------------------------------------------
// Constructor

template<typename T>
EpisodeManager<T>::EpisodeManager()
{
  m_current_state = RUNNING;
  m_previous_state = PAUSED; // So start vars get posted
  m_pause_request = false;
  m_run_request = false;

  m_info_buffer = new InfoBuffer;
  m_nav_x = 0;
  m_nav_y = 0;
  m_helm_state = "uninitalized";

  m_episode_cnt = 0;
  m_success_cnt = 0;
  m_failure_cnt = 0;

  m_max_duration = -1;
}

//---------------------------------------------------------
// Destructor

template<typename T>
EpisodeManager<T>::~EpisodeManager() {}

//---------------------------------------------------------
// Procedure: OnNewMail

template<typename T>
bool EpisodeManager<T>::OnNewMail(MOOSMSG_LIST &NewMail)
{
  T::OnNewMail(NewMail);

  MOOSMSG_LIST::iterator p;
  for(p=NewMail.begin(); p!=NewMail.end(); p++) {
    CMOOSMsg &msg = *p;
    string key    = msg.GetKey();

#if 0 // Keep these around just for template
    string comm  = msg.GetCommunity();
    double dval  = msg.GetDouble();
    string sval  = msg.GetString(); 
    string msrc  = msg.GetSource();
    double mtime = msg.GetTime();
    bool   mdbl  = msg.IsDouble();
    bool   mstr  = msg.IsString();
#endif

    if(key == "EPISODE_MGR_CTRL"){
      string sval = msg.GetString();
      reportEvent("Got control message: "+sval);
      string type = tokStringParse(sval, "type", ',', '=');
      if(type == "pause"){
        if(m_current_state == PAUSED)
          reportRunWarning("Got pause signal while in PAUSED state. Ignoring.");
        else
          m_pause_request = true;
      }else if(type == "start"){
        if(m_current_state == RUNNING){
          reportRunWarning("Got run signal while in RUNNING state. Ignoring");
        }else{
          m_run_request = true;
        }
      }else if(type == "hardstop"){
        if(m_current_state == PAUSED){
          reportRunWarning("Got hardstop singal in state PAUSED state. Ignoring");
        }else{
          // End episode immediatly and go to stop state
          if(m_current_state == RUNNING)
            endEpisode(false);
          m_pause_request = true;
        }
      }else if(type == "reset"){
        if(m_current_state == PAUSED){
          reportRunWarning("Got reset singal in state PAUSED state. Ignoring");
        }else if (m_current_state != RUNNING){
          reportRunWarning("Got reset singal while reseting. Ignoring");
        }else{
          string success = tolower(tokStringParse(sval, "success", ',', '='));
          if(success == "true"){
            endEpisode(true);
          }else{
            if(success != "false")
              reportRunWarning("Got reset signal with non-boolean success value: '"+success+"'. Assuming false");
            endEpisode(false);
          }
        }
      }else{
        reportRunWarning("Unimplemented control message: "+type);
      }
    }else if(key == "NAV_X"){
      m_nav_x = msg.GetDouble();
    }else if(key == "NAV_Y"){
      m_nav_y = msg.GetDouble();
    }else if(key == "IVPHELM_STATE"){
      m_helm_state = msg.GetString();
    }
    else{
      updateInfoBuffer(msg);
    }
  }
	
   return(true);
}

//------------------------------------------------------------
// Procedure: updateInfoBuffer()

template<typename T>
bool EpisodeManager<T>::updateInfoBuffer(CMOOSMsg &msg)
{
  string key = msg.GetKey();
  string sdata = msg.GetString();
  double ddata = msg.GetDouble();

  if(msg.IsDouble()) {
    return(m_info_buffer->setValue(key, ddata));
  }
  else if(msg.IsString()) {
    return(m_info_buffer->setValue(key, sdata));
  }
  return(false);
}


//---------------------------------------------------------
// Procedure: OnConnectToServer

template<typename T>
bool EpisodeManager<T>::OnConnectToServer()
{
   registerVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

template<typename T>
bool EpisodeManager<T>::Iterate()
{
  T::Iterate();
  
  if(m_current_state == PAUSED){
    Notify("EPISODE_MGR_STATE", "PAUSED");
    if(m_run_request){
      m_run_request = false;
      startEpisode(); // Transition to RUNNING and other init stuff
    }
  }else if(m_current_state == RUNNING){
    Notify("EPISODE_MGR_STATE", "RUNNING");
    bool end, success;
    end = success = checkConditions(m_end_success_conditions);
    if(!end)
      end = checkConditions(m_end_failure_conditions);
    if(!end && m_max_duration != -1 && (MOOSTime()-m_episode_start) >= m_max_duration)
      end = true;

    if(end)
      endEpisode(success);
  }else if(m_current_state == STOPPING_HELM){
    Notify("EPISODE_MGR_STATE", "STOPPING_HELM");
    if(m_helm_state == "PARK"){
      resetVehicle();
    }
  }else if(m_current_state == RESETING){
    Notify("EPISODE_MGR_STATE", "RESETING");
    if(std::abs(m_nav_x-m_reset_x) < 1 && std::abs(m_nav_y-m_reset_y) < 1){
      postPosts(m_reset_posts);
      Notify("MOOS_MANUAL_OVERRIDE", "false");

      m_previous_state = m_current_state;
      if(m_pause_request){
        m_pause_request = false;

        postPosts(m_pause_posts);

        m_current_state = PAUSED;
      }else{
        startEpisode(); // Transition to RUNNING and other init stuff
      }
    }
  }

  T::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

template<typename T>
bool EpisodeManager<T>::OnStartUp()
{
  T::OnStartUp();

  STRING_LIST sParams;
  m_MissionReader.EnableVerbatimQuoting(false);
  if(!m_MissionReader.GetConfiguration(GetAppName(), sParams))
    reportConfigWarning("No config block found for " + GetAppName());

  STRING_LIST::iterator p;
  for(p=sParams.begin(); p!=sParams.end(); p++) {
    string orig  = *p;
    string line  = *p;
    string param = tolower(biteStringX(line, '='));
    string value = line;

    bool handled = false;
    if(param == "end_success_condition"){
      // Following example from TS_MOOSApp
      LogicCondition new_condition;
      bool ok = new_condition.setCondition(value);
      if(ok)
        m_end_success_conditions.push_back(new_condition);
      else
        reportConfigWarning("Invalid logic condition: " + value);
      
      handled = true;
    }else if(param == "end_failure_condition"){
      // Following example from TS_MOOSApp
      LogicCondition new_condition;
      bool ok = new_condition.setCondition(value);
      if(ok)
        m_end_failure_conditions.push_back(new_condition);
      else
        reportConfigWarning("Invalid logic condition: " + value);
      
      handled = true;
    }else if(param == "reset_post" || param == "pause_post" || param == "start_post"){
      // Add a new end post
      string new_var;
      string new_val;

      // Loop through the comma seperated pairs to find the key and value to post
      vector<string> svector = parseStringQ(value, ',');
      unsigned int i, vsize = svector.size();
      if(vsize == 2){
        for(i=0; i<vsize; i++){
          string k = tolower(biteStringX(svector[i], '='));
          string v = svector[i];

          if(k == "var") {
            new_var = v;
            if(strContainsWhite(v))
              reportConfigWarning("End post variable has white-space: " + v);
          }else if(k == "val") {
            new_val = v;
          }else{
            reportConfigWarning("Invalid end post: "+ value);
          }
        }
      }else{
        reportConfigWarning("Invalid end post: "+ value);
      }

      if(new_var != "" && new_val != ""){
        VarDataPair new_pair(new_var, new_val, "auto");
        if(param == "reset_post")
          m_reset_posts.push_back(new_pair);
        else if (param == "start_post")
          m_start_posts.push_back(new_pair);
        else if (param == "pause_post")
          m_pause_posts.push_back(new_pair);
      }else{
        // TODO: Will double post with first one of these in some conditions
        reportConfigWarning("Invalid end post: "+ value);
      }

      handled = true;
    }else if(param == "reset_pos") {
      m_reset_x = std::atof(biteStringX(value, ',').c_str());
      m_reset_y = std::atof(biteStringX(value, ',').c_str());
      m_reset_heading = biteStringX(value, ',');

      if(!resetPosValid()){
        reportConfigWarning("Invalid START_POS config");
      }

      handled = true;
    }
    else if (param == "vname"){
      m_vname = value;
      handled = true;
    }else if(param == "paused"){
      value = tolower(stripBlankEnds(value));
      if(value == "true"){
        m_current_state = PAUSED;
      }
      else if(value == "false")
       m_current_state = RUNNING;
      else
        reportConfigWarning("paused parameter should be boolean");
      handled = true;
    }else if(param == "max_duration"){
      m_max_duration = std::atof(stripBlankEnds(value).c_str());
      handled = true;
    }

    if(!handled)
      reportUnhandledConfigWarning(orig);
  }
  
  registerVariables();	
  return(true);
}

//---------------------------------------------------------
// Procedure: registerVariables

template<typename T>
void EpisodeManager<T>::registerVariables()
{
  T::RegisterVariables();
  // Register vars needed for state machine
  fprintf(stderr, "Yo man -------------\n");
  Register("IVPHELM_STATE");
  Register("NAV_X", 0);
  Register("NAV_Y", 0);

  // Register for control var
  Register("EPISODE_MGR_CTRL", 0);


  // Again following TS_MOOSApp example
  vector<string> all_vars;
  unsigned int i, vsize = m_end_success_conditions.size();
  for(i=0; i<vsize; i++) {
    vector<string> svector = m_end_success_conditions[i].getVarNames();
    all_vars = mergeVectors(all_vars, svector);
  }
  vsize = m_end_failure_conditions.size();
  for(i=0; i<vsize; i++) {
    vector<string> svector = m_end_failure_conditions[i].getVarNames();
    all_vars = mergeVectors(all_vars, svector);
  }
  all_vars = removeDuplicates(all_vars);

  // Register for all variables found in all conditions.
  unsigned int all_size = all_vars.size();
  for(i=0; i<all_size; i++){
    Register(all_vars[i], 0);
    reportEvent("Regested for end condition var: "+all_vars[i]);
  }
}

template<typename T>
bool EpisodeManager<T>::resetPosValid(){
  //TODO: Fix this
  return m_reset_heading != "";
}

//-----------------------------------------------------------
// Procedure: checkConditions()
//   Purpose: Determine if all the logic conditions in the vector
//            of conditions is met, given the snapshot of variable
//            values in the info_buffer.

template<typename T>
bool EpisodeManager<T>::checkConditions(std::vector<LogicCondition> conditions)
{
  // If no conditions exist, assume false
  if(conditions.size() == 0)
    return false;

  // Reject if info buffer is NULL
  if(!m_info_buffer) 
    return(false);

  unsigned int i, j, vsize, csize;

  // Phase 1: get all the variable names from all present conditions.
  vector<string> all_vars;
  csize = conditions.size();
  for(i=0; i<csize; i++) {
    vector<string> svector = conditions[i].getVarNames();
    all_vars = mergeVectors(all_vars, svector);
  }
  all_vars = removeDuplicates(all_vars);

  // Phase 2: get values of all variables from the info_buffer and 
  // propogate these values down to all the logic conditions.
  vsize = all_vars.size();
  for(i=0; i<vsize; i++) {
    string varname = all_vars[i];
    bool   ok_s, ok_d;
    string s_result = m_info_buffer->sQuery(varname, ok_s);
    double d_result = m_info_buffer->dQuery(varname, ok_d);

    for(j=0; (j<csize)&&(ok_s); j++)
      conditions[j].setVarVal(varname, s_result);
    for(j=0; (j<csize)&&(ok_d); j++)
      conditions[j].setVarVal(varname, d_result);
  }

  // Phase 3: evaluate all logic conditions. Return true only if all
  // conditions evaluate to be true.
  for(i=0; i<csize; i++) {
    bool satisfied = conditions[i].eval();
    if(!satisfied)
      return(false);
  }
  return(true);
}

template<typename T>
void EpisodeManager<T>::startEpisode(){
  // Change state to running
  m_previous_state = m_current_state;
  m_current_state = RUNNING;

  if(m_previous_state == PAUSED){
    postPosts(m_start_posts);
  }

  m_episode_cnt += 1;
  m_episode_start = MOOSTime();  
}

template<typename T>
void EpisodeManager<T>::endEpisode(bool success){
  if(success)
    m_success_cnt += 1;
  else
    m_failure_cnt += 1;

  std::string report = "NUM="+intToString(m_episode_cnt);
  report += ",SUCCESS="+boolToString(success);
  report += ",DURATION="+doubleToString(MOOSTime()-m_episode_start);
  report += ",WILL_PAUSE="+boolToString(m_pause_request);
  Notify("EPISODE_MGR_REPORT", report);
  reportEvent("Episode over: "+report);

  // Stop helm and transition state
  Notify("MOOS_MANUAL_OVERRIDE", "true");
  m_previous_state = m_current_state;
  m_current_state = STOPPING_HELM;
}

template<typename T>
void EpisodeManager<T>::resetVehicle(){
  if(!resetPosValid()){
    reportRunWarning("Cannot reset vehicle due to invalid reset position.");
    return;
  }

  m_previous_state = m_current_state;
  m_current_state = RESETING;

  std::string reset_string = "x="+doubleToString(m_reset_x);
  reset_string += ",y="+doubleToString(m_reset_y);
  reset_string += ",heading="+m_reset_heading;
  reset_string += ",speed=0,depth=0";

  Notify("USM_RESET", reset_string);
}

template<typename T>
void EpisodeManager<T>::postPosts(std::vector<VarDataPair> posts){
  // Notify end posts
  unsigned int i, vsize = posts.size();
  for(i=0; i<vsize; i++){
    string var = posts[i].get_var();

    if(!posts[i].is_string()){
      double dval = posts[i].get_ddata();
      Notify(var, dval);
      // TODO: Booleans do not get printed nicely here
      reportEvent("Posted float "+var+"="+doubleToString(dval));
    }else{
      string sval = posts[i].get_sdata();

      // Notify vars & add to local info buffer
      if(isNumber(sval) && !posts[i].is_quoted()){
        double dval = atof(sval.c_str());
        m_info_buffer->setValue(var, dval);
        Notify(var, dval);
        reportEvent("Posted \""+sval+"\" as float "+var+"="+doubleToString(dval));
      }else{
        m_info_buffer->setValue(var, sval);
        Notify(var, sval);
        reportEvent("Posted string "+var+"="+sval);
      }
    }
  }
}

//------------------------------------------------------------
// Procedure: buildReport()

template<typename T>
bool EpisodeManager<T>::buildReport() 
{
  m_msgs << "Config Variables" << endl;
  m_msgs << "----------------------------------" << endl;
  m_msgs << "VNAME: " << m_vname << endl;
  m_msgs << "RESET_X:       " << m_reset_x << endl;
  m_msgs << "RESET_Y:       " << m_reset_y << endl;
  m_msgs << "RESET_HEADING: " << m_reset_heading << endl;
  if(m_max_duration != -1)
    m_msgs << "MAX_DURATION:  " << m_max_duration << endl;

  m_msgs << "State Variables" << endl;
  m_msgs << "----------------------------------" << endl;
  m_msgs << "state:           "; 
  if(m_current_state == RUNNING)
    m_msgs << "RUNNING" << endl;
  else if(m_current_state == STOPPING_HELM)
    m_msgs << "STOPPING_HELM (reset loop)" << endl;
  else if(m_current_state == RESETING)
    m_msgs << "RESETING (reset loop)" << endl;
  else if(m_current_state == PAUSED)
    m_msgs << "PAUSED" << endl;
  
  m_msgs << "pause_request:   " << std::boolalpha << m_pause_request << endl;
  m_msgs << "run_request:     " << std::boolalpha << m_run_request << endl;

  m_msgs << "episode_cnt:     " << m_episode_cnt << endl;
  m_msgs << "success_cnt:     " << m_success_cnt << endl;
  m_msgs << "failure_cnt:     " << m_failure_cnt << endl;

  return(true);
}

SPECIALIZE_MOOSCastingApp(EpisodeManager)