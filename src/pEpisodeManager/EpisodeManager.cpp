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

    if(key == "TAGGED"){
      string sval = msg.GetString();
      if(sval == "true"){
        m_tagged = true;
        m_tagged_cnt++;

        stopEpisode();
      }
      else
        m_tagged = false;
    }
    else if(key != "APPCAST_REQ") // handled by AppCastingMOOSApp
      reportRunWarning("Unhandled Mail: " + key);
   }
	
   return(true);
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
  // Do your thing here!
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
    if(param == "reset_pos") {
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
  // Register("FOOBAR", 0);

  Register("TAGGED", 0);
}

bool EpisodeManager::resetVarsValid(){
  return m_reset_x != "" && m_reset_y != "" && m_reset_heading != "";
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
  Notify("UNTAG_REQUEST", "vname="+m_vname);

  // Report app casting event
  std::stringstream report;
  report << "Episode #" << m_episode_cnt << " has ended.";
  reportEvent(report.str());

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
  m_msgs << "RESET_HEADING: " << m_reset_heading << endl << endl;

  m_msgs << "State Variables" << endl;
  m_msgs << "----------------------------------" << endl;
  m_msgs << "tagged: " << std::boolalpha << m_tagged << endl;
  m_msgs << "episode_cnt: " << m_episode_cnt << endl;
  m_msgs << "tagged_cnt:  " << m_tagged_cnt << endl;

  return(true);
}




