/************************************************************/
/*    NAME: Carter Fendley                                              */
/*    ORGN: MIT                                             */
/*    FILE: BHV_Agent.cpp                                    */
/*    DATE: 2021/07/22                                      */
/************************************************************/

#include <iterator>
#include <cstdlib>
#include "MBUtils.h"
#include "BuildUtils.h"
#include "BHV_Agent.h"
#include "VarDataPair.h"
#include "ZAIC_PEAK.h"
#include "OF_Coupler.h"

using namespace std;

//---------------------------------------------------------------
// Constructor

BHV_Agent::BHV_Agent(IvPDomain domain) :
  IvPBehavior(domain)
{
  // Provide a default behavior name
  IvPBehavior::setParam("name", "rl_agent");

  // Declare the behavior decision space
  m_domain = subDomain(m_domain, "course,speed");

  // Add any variables this behavior needs to subscribe for
  addInfoVars("NAV_X, NAV_Y", "NAV_HEADING");

  if(true)
    setbuf(stdout, NULL);
}

//---------------------------------------------------------------
// Procedure: setParam()

bool BHV_Agent::setParam(string param, string val)
{
  // Convert the parameter to lower case for more general matching
  param = tolower(param);

  // Get the numerical value of the param argument for convenience once
  double double_val = atof(val.c_str());

  if((param == "sub_vehicle")) {
    m_sub_vehicles.push_back(toupper(stripBlankEnds(val)));
    return(true);
  }
  else if (param == "bar") {
    // return(setBooleanOnString(m_my_bool, val));
  }

  // If not handled above, then just return false;
  return(false);
}

//---------------------------------------------------------------
// Procedure: onSetParamComplete()
//   Purpose: Invoked once after all parameters have been handled.
//            Good place to ensure all required params have are set.
//            Or any inter-param relationships like a<b.

void BHV_Agent::onSetParamComplete()
{
  unsigned int i, vsize = m_sub_vehicles.size();
  for(i=0; i<vsize; i++){
    addInfoVars("NODE_REPORT_"+m_sub_vehicles[i]);
  }
}

//---------------------------------------------------------------
// Procedure: onHelmStart()
//   Purpose: Invoked once upon helm start, even if this behavior
//            is a template and not spawned at startup

void BHV_Agent::onHelmStart()
{
}

//---------------------------------------------------------------
// Procedure: onIdleState()
//   Purpose: Invoked on each helm iteration if conditions not met.

void BHV_Agent::onIdleState()
{
  tickBridge(false);
}

//---------------------------------------------------------------
// Procedure: onCompleteState()

void BHV_Agent::onCompleteState()
{
  tickBridge(false);
}

//---------------------------------------------------------------
// Procedure: postConfigStatus()
//   Purpose: Invoked each time a param is dynamically changed

void BHV_Agent::postConfigStatus()
{
}

//---------------------------------------------------------------
// Procedure: onIdleToRunState()
//   Purpose: Invoked once upon each transition from idle to run state

void BHV_Agent::onIdleToRunState()
{
}

//---------------------------------------------------------------
// Procedure: onRunToIdleState()
//   Purpose: Invoked once upon each transition from run to idle state

void BHV_Agent::onRunToIdleState()
{
}

//---------------------------------------------------------------
// Procedure: onRunState()
//   Purpose: Invoked each iteration when run conditions have been met.

IvPFunction* BHV_Agent::onRunState()
{
  IvPFunction *ipf = 0;
  tickBridge(true);

  // Listen for action from bridge
  std::vector<VarDataPair> action = bridge.listenAction();
  
  int vsize = action.size();
  if(vsize > 0){
    // We got an action
    for(int i=0; i<vsize; i++){
      string var = action[i].get_var();

      if (var == "speed"){
        m_current_speed = action[i].get_ddata();
      }else if (var == "course"){
        m_current_course = action[i].get_ddata();
      }else if (var == "othervar"){
        // Do something
      }
    }
  }else{
    // Bridge didn't get an action but failed nicely (timeout)
  }

  // Build a new IvP function
  ZAIC_PEAK spd_zaic(m_domain, "speed");
  spd_zaic.setSummit(m_current_speed);
  spd_zaic.setBaseWidth(0.3);
  spd_zaic.setPeakWidth(0.0);
  spd_zaic.setSummitDelta(0.0);
  IvPFunction *spd_of = spd_zaic.extractIvPFunction();

  ZAIC_PEAK crs_zaic(m_domain, "course");
  crs_zaic.setSummit(m_current_course);
  crs_zaic.setBaseWidth(180.0);
  crs_zaic.setValueWrap(true);
  IvPFunction *crs_of = crs_zaic.extractIvPFunction();

  OF_Coupler coupler;
  ipf = coupler.couple(crs_of, spd_of);

  // Part N: Prior to returning the IvP function, apply the priority wt
  // Actual weight applied may be some value different than the configured
  // m_priority_wt, depending on the behavior author's insite.
  if(ipf)
    ipf->setPWT(m_priority_wt);

  return(ipf);
}

void BHV_Agent::postBridgeState(std::string state){
  postRepeatableMessage("AGENT_BRIDGE_STATE", state);
  postRepeatableMessage("AGENT_CURRENT_ACTION", "speed="+doubleToString(m_current_speed)+",course="+doubleToString(m_current_course));
}

//---------------------------------------------------------------
// Procedure: tickBridge()
//   Purpose: Used to tick the bridge
void BHV_Agent::tickBridge(bool running){
  // Post status if failed
  if(bridge.failureState()){
    postBridgeState("Failed");
    return;
  }

  // Post status if connected
  if(!bridge.isConnected()){
    bridge.connect();
    postBridgeState("Not Connected");
    return; // Nothing else to do
  }
  
  postBridgeState("Connected");
  // Send the current state
  if(running){
    // Pull NAV_X and NAV_Y from the Helm info buffer
    bool x_ok, y_ok;
    double NAV_X = getBufferDoubleVal("NAV_X", x_ok);
    if(!x_ok){
      postWMessage("NAV_X not found in info buffer. Can't send state update.");
      return;
    }
    double NAV_Y = getBufferDoubleVal("NAV_Y", y_ok);
    if(!y_ok){
      postWMessage("NAV_Y not found in info buffer. Can't send state update.");
      return;
    }

    // Post other node reports
    std::vector<std::string> node_reports;
    unsigned int i, vsize = m_sub_vehicles.size();
    for(i=0; i<vsize; i++){
      bool ok;
      std::string result = getBufferStringVal("NODE_REPORT_"+m_sub_vehicles[i], ok);
      if(ok){
        node_reports.push_back(result);
      }
    }

    //TODO: Construct actuall VarDataPair vector
    std::vector<VarDataPair> vd_pairs;

    // Send update through bridge
    bool ok = bridge.sendState(getBufferCurrTime(), NAV_X, NAV_Y, node_reports, vd_pairs);
    if (!ok){
      postWMessage("Bridge says connected but failed to send state.");
    }
  }
}