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

using namespace std;

//---------------------------------------------------------
// Constructor

EpisodeManager::EpisodeManager()
{
  m_info_buffer = new InfoBuffer;

  m_episode_cnt = 0;
  m_episode_running = true;
  m_continuous = true;
}

//---------------------------------------------------------
// Destructor

EpisodeManager::~EpisodeManager()
{
}

//---------------------------------------------------------
// Procedure: OnNewMail

bool EpisodeManager::OnNewMail(MOOSMSG_LIST &NewMail)
{
  AppCastingMOOSApp::OnNewMail(NewMail);

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

    if(key == "SOME_KEY_HERE"){
      // TODO: Other stuff?
    }else{
      updateInfoBuffer(msg);
    }
  }
	
   return(true);
}

//------------------------------------------------------------
// Procedure: updateInfoBuffer()

bool EpisodeManager::updateInfoBuffer(CMOOSMsg &msg)
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

bool EpisodeManager::OnConnectToServer()
{
   registerVariables();
   return(true);
}

//---------------------------------------------------------
// Procedure: Iterate()
//            happens AppTick times per second

bool EpisodeManager::Iterate()
{
  AppCastingMOOSApp::Iterate();

  if(m_episode_running){
    
    bool end = checkConditions();

    // Handle episode ending 
    if (end)
      stopEpisode();
  }

  AppCastingMOOSApp::PostReport();
  return(true);
}

//---------------------------------------------------------
// Procedure: OnStartUp()
//            happens before connection is open

bool EpisodeManager::OnStartUp()
{
  AppCastingMOOSApp::OnStartUp();

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
    if(param == "end_condition"){
      // Following example from TS_MOOSApp
      LogicCondition new_condition;
      bool ok = new_condition.setCondition(value);
      if(ok)
        m_end_conditions.push_back(new_condition);
      else
        reportConfigWarning("Invalid logic condition:" + value);
      
      handled = true;
    }else if(param == "reset_pos") {
      m_reset_x = biteStringX(value, ',');
      m_reset_y = biteStringX(value, ',');
      m_reset_heading = biteStringX(value, ',');

      if(!resetVarsValid()){
        reportConfigWarning("Invalid START_POS config");
      }

      handled = true;
    }
    else if (param == "vname"){
      m_vname = value;
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

void EpisodeManager::registerVariables()
{
  AppCastingMOOSApp::RegisterVariables();

  // Again following TS_MOOSApp example
  vector<string> all_vars;
  unsigned int i, vsize = m_end_conditions.size();
  for(i=0; i<vsize; i++) {
    vector<string> svector = m_end_conditions[i].getVarNames();
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

bool EpisodeManager::resetVarsValid(){
  return m_reset_x != "" && m_reset_y != "" && m_reset_heading != "";
}

//-----------------------------------------------------------
// Procedure: checkConditions()
//   Purpose: Determine if all the logic conditions in the vector
//            of conditions is met, given the snapshot of variable
//            values in the info_buffer.

bool EpisodeManager::checkConditions()
{
  if(!m_info_buffer) 
    return(false);

  unsigned int i, j, vsize, csize;

  // Phase 1: get all the variable names from all present conditions.
  vector<string> all_vars;
  csize = m_end_conditions.size();
  for(i=0; i<csize; i++) {
    vector<string> svector = m_end_conditions[i].getVarNames();
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
      m_end_conditions[j].setVarVal(varname, s_result);
    for(j=0; (j<csize)&&(ok_d); j++)
      m_end_conditions[j].setVarVal(varname, d_result);
  }

  // Phase 3: evaluate all logic conditions. Return true only if all
  // conditions evaluate to be true.
  for(i=0; i<csize; i++) {
    bool satisfied = m_end_conditions[i].eval();
    if(!satisfied)
      return(false);
  }
  return(true);
}

//---------------------------------------------------------
// Procedure: registerVariables

bool EpisodeManager::stopEpisode(){
  if(!resetVarsValid()){
    reportRunWarning("Cannot stop episode due to invalid reset point.");
    return false;
  }
  
  Notify("USM_RESET", "x="+m_reset_x+",y="+m_reset_y+",speed=0,heading="+m_reset_heading+"depth=0");
  Notify("TAGGED", false);

  // Report app casting event
  if(!m_continuous){
    m_episode_running = false;
    reportEvent("Episode #"+ intToString(m_episode_cnt) + " has_ended.");
  }else{
    reportEvent("Episode #"+ intToString(m_episode_cnt) + " has_ended. Starting next...");
  }

  // Update state vars
  m_episode_cnt++;

  return true;
}

//------------------------------------------------------------
// Procedure: buildReport()

bool EpisodeManager::buildReport() 
{
  m_msgs << "Config Variables" << endl;
  m_msgs << "----------------------------------" << endl;
  m_msgs << "VNAME: " << m_vname << endl;
  m_msgs << "RESET_X:       " << m_reset_x << endl;
  m_msgs << "RESET_Y:       " << m_reset_y << endl;
  m_msgs << "RESET_HEADING: " << m_reset_heading << endl;
  m_msgs << "Continous:     " << std::boolalpha << m_continuous << endl << endl;

  m_msgs << "State Variables" << endl;
  m_msgs << "----------------------------------" << endl;
  m_msgs << "episode_cnt: " << m_episode_cnt << endl;

  return(true);
}




