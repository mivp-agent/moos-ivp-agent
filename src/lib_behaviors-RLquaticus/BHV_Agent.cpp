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
  addInfoVars("NAV_X, NAV_Y");

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

  if((param == "foo") && isNumber(val)) {
    // Set local member variables here
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
  tickBridge(true);

  // Part 1: Build the IvP function
  IvPFunction *ipf = 0;



  // Part N: Prior to returning the IvP function, apply the priority wt
  // Actual weight applied may be some value different than the configured
  // m_priority_wt, depending on the behavior author's insite.
  if(ipf)
    ipf->setPWT(m_priority_wt);

  return(ipf);
}

void BHV_Agent::postBridgeState(std::string state){
  postRepeatableMessage("AGENT_BRIDGE_STATE", state);
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

    //TODO: Construct actuall VarDataPair vector
    std::vector<VarDataPair> vd_pairs;

    // Send update through bridge
    bridge.sendState(NAV_X, NAV_Y, vd_pairs);
  }
}