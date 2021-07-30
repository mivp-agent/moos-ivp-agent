/*****************************************************************/
/*    NAME: Carter Fendley                                       */
/*    ORGN: MIT                                                  */
/*    FILE: PyInterface.cpp                                      */
/*    DATE: Jul 22nd 2021                                        */
/*****************************************************************/

#include <cstdlib>
#include <stdexcept>
#include <sstream>
#include "PyInterface.h"
#include "MBUtils.h"

using namespace std;

//---------------------------------------------------------
// Constructor

PyInterface::PyInterface()
{
  m_bridge_client = NULL;

  m_is_connected = false;

  Py_Initialize();
  loadModule();

  setvbuf(stdout, NULL, _IOLBF, 0);
}

//---------------------------------------------------------
// Procedure: loadModule

bool PyInterface::loadModule()
{
  // Check if module has been loaded
  if(m_bridge_client){
    if(!unloadModule())
      return false;
  }
  
  // Load module
  PyObject* m_bridge_module = PyImport_ImportModule("RLquaticus.bridge");

  if(!m_bridge_module){
    fprintf(stderr, "ERROR: Failed to import bridge module\n");
    PyErr_Print();
    return false;
  }

  // Get the reference to the ModelBridgeClient object
  PyObject* m_bridge_client_attribute = PyObject_GetAttrString(m_bridge_module, "ModelBridgeClient");

  if(!m_bridge_client_attribute){
    fprintf(stderr, "ERROR: Failed to get ModelBridgeClient attribute from module\n");
    PyErr_Print();

    // Clean up
    Py_DECREF(m_bridge_module);
    m_bridge_module = NULL;

    return false;
  }

  // Instantiate the object
  PyObject* args = PyTuple_New(0);
  m_bridge_client = PyObject_CallObject(m_bridge_client_attribute, args);
  
  if(!m_bridge_client){
    fprintf(stderr, "ERROR: Failed to create new ModelBridgeClient object\n");
    PyErr_Print();

    // Clean up
    Py_DECREF(m_bridge_module);
    Py_DECREF(m_bridge_client_attribute);
    m_bridge_module = NULL;
    m_bridge_client_attribute = NULL;

    return false;
  }

  // Clean up references
  Py_DECREF(args);
  Py_DECREF(m_bridge_module);
  Py_DECREF(m_bridge_client_attribute);

  // For purposes of keeping state in this class
  m_bridge_module = NULL;
  m_bridge_client_attribute = NULL;

  return true;
}

//---------------------------------------------------------
// Procedure: unloadModule

bool PyInterface::unloadModule()
{
  if (m_bridge_client)
    Py_DECREF(m_bridge_client);
    m_bridge_client = NULL;
}

bool PyInterface::connect(){
  PyObject* result = PyObject_CallMethod(m_bridge_client, "connect", NULL);

  if(result == NULL){
    fprintf(stderr, "ERROR: Failed to call connect function from client object\n\n");
    PyErr_Print();

    return false;
  }

  if(!PyBool_Check(result)){

    //Clean up
    Py_DECREF(result);

    // Not what we are expecting so raise our own error
    throw runtime_error("ModelBridgeClient's call function did not return a boolean");
  }

  if(PyObject_IsTrue(result)){
    m_is_connected = true;
  }else{
    m_is_connected = false;
  }

  // Clean up and return
  Py_DECREF(result);
  
  return m_is_connected;
}

bool PyInterface::sendState(double helm_time, double NAV_X, double NAV_Y, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs){
  if(!isConnected())
    return false;

  // Create the state object
  PyObject* state_dict = constructState(helm_time, NAV_X, NAV_Y, node_reports, vd_pairs);

  if(!state_dict)
    return false; // Error will have been handled by constructState
  
  // Call bridge's send state method
  PyObject* method_name = Py_BuildValue("s", "send_state");
  PyObject* result = PyObject_CallMethodObjArgs(m_bridge_client, method_name, state_dict, NULL);

  // Release our references we just used
  Py_DECREF(method_name);
  Py_DECREF(state_dict);

  // Check if we got an error
  if(result == NULL){
    fprintf(stderr, "ERROR: Failed to call send_state function from client object\n\n");
    PyErr_Print();

    return false;
  }

  if(!PyBool_Check(result)){
    //Clean up
    Py_DECREF(result);

    // Not what we are expecting so raise our own error
    throw runtime_error("ModelBridgeClient's send_state function did not return a boolean");
  }

  // Clean up and return
  bool success = PyObject_IsTrue(result);
  Py_DECREF(result);
  return result;
}

std::vector<VarDataPair> PyInterface::listenAction(){
  std::vector<VarDataPair> action; // Will return with size = 0 on failure

  if(!isConnected())
    return action;

  PyObject* result = PyObject_CallMethod(m_bridge_client, "listen_action", NULL);

  if(result == NULL){
    fprintf(stderr, "ERROR: Failed to call connect function from client object\n\n");
    PyErr_Print();
    return action;
  }

  if(PyBool_Check(result)){
    bool return_bool = PyObject_IsTrue(result);
    //Clean up
    Py_DECREF(result);

    if(return_bool){
      // Not what we are expecting so raise our own error
      throw runtime_error("ModelBridgeClient's listen_state function returned True (invalid protocol)");
    }
    return action; // Fail normally
  }

  if(!PyDict_Check(result)){
    Py_DECREF(result);
    throw runtime_error("Method 'listen_action' did not fail or return dict");
  }

  if(!validateAction(result)){
    Py_DECREF(result);
    throw runtime_error("Unable to unpack dictionary");
  }

  // Parse out speed and course
  double speed, course;
  PyObject* speed_key = Py_BuildValue("s", "speed");
  PyObject* course_key = Py_BuildValue("s", "course");

  // PyDict_GetItem returns borrowed reference so no need to decref
  // Python code should do type checking for us
  speed = PyFloat_AsDouble(PyDict_GetItem(result, speed_key));
  course = PyFloat_AsDouble(PyDict_GetItem(result, course_key));

  Py_DECREF(speed_key);
  Py_DECREF(course_key);

  // Push into return vector
  VarDataPair speed_pair("speed", speed);
  VarDataPair course_pair("course", course);

  action.push_back(speed_pair);
  action.push_back(course_pair);

  // TODO: Parse MOOS_VARS as actions  

  // Clean up and return
  Py_DECREF(result);
  
  return action;
}

bool PyInterface::failureState(){
  return m_bridge_client == NULL;
}


bool PyInterface::isConnected(){
  return m_is_connected;
}

PyObject* PyInterface::constructState(double helm_time, double NAV_X, double NAV_Y, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs){
  // Unpack vd_pairs and translate into python types
  int vsize = vd_pairs.size();
  for(int i=0; i<vsize; i++){
    string var = vd_pairs[i].get_var();
    if(vd_pairs[i].is_string()){
      string sdata = vd_pairs[i].get_sdata();
      //TODO: Handle vd string data
    }else{
      double ddata = vd_pairs[i].get_ddata();
      //TODO: Handle vd double data
    }
  }

  // Build top level state['NODE_REPORTS'] = {} dictionary
  PyObject* node_reports_dict = PyDict_New();

  // Ass all node reports to this dict in the form a a dictionary themselves
  vsize = node_reports.size();
  for(int i=0; i<vsize; i++){
    std::string name = tokStringParse(node_reports[i], "NAME", ',', '=');
    PyObject* report_dict = nodeReportToDict(node_reports[i]);

    

    PyDict_SetItemString(node_reports_dict, name.c_str(), report_dict);
    Py_DECREF(report_dict);
  }

  PyObject* MOOS_VARS_TMP = PyTuple_New(0); // TODO: Use code above to populate stuff
  PyObject *state_dict = Py_BuildValue("{s:d,s:d,s:d,s:O,s:()}", // This constructs a python dict
    "HELM_TIME", helm_time,
    "NAV_X", NAV_X,
    "NAV_Y", NAV_Y,
    "NODE_REPORTS", node_reports_dict, // Using O cause it incref's (for sure)
    "MOOS_VARS", MOOS_VARS_TMP);

  
    Py_DECREF(MOOS_VARS_TMP);
    Py_DECREF(node_reports_dict);

  if (!state_dict){
    PyErr_Print();
    return NULL;
  }

  return state_dict;
}

PyObject* PyInterface::nodeReportToDict(std::string report){
  // Parse node report
  double x = tokDoubleParse(report, "X", ',', '=');
  double y = tokDoubleParse(report, "Y", ',', '=');
  double heading = tokDoubleParse(report, "HDG", ',', '=');

  PyObject* dict = Py_BuildValue("{s:d,s:d,s:d}",
    "NAV_X", x,
    "NAV_Y", y,
    "NAV_HEADING", heading
  );

  return dict;
}

bool PyInterface::validateAction(PyObject* action){
  // NOTE: Most checking will be done python size. This is just for C API errors
  // Define expected keys as python strings
  PyObject* speed = Py_BuildValue("s", "speed");
  PyObject* course = Py_BuildValue("s", "course");
  PyObject* moos_vars = Py_BuildValue("s", "MOOS_VARS");

  int ok = PyDict_Contains(action, speed);

  // This is expanded to not loose an error if two happen at same time
  if(ok > -1){
    ok = PyDict_Contains(action, course);
    if(ok > -1){
      ok = PyDict_Contains(action, moos_vars);
      if(ok > -1){
        return true; // No errors with the dict
      }
    }
  }

  // Print error
  PyErr_Print();

  // Clean up local vars
  Py_DECREF(speed);
  Py_DECREF(course);
  Py_DECREF(moos_vars);

  return false;
}

PyInterface::~PyInterface(){
  unloadModule();
  Py_Finalize();
}
 