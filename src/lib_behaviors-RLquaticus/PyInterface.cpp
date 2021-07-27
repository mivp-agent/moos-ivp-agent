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
  PyObject* m_bridge_module = PyImport_ImportModule("bridge");

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

bool PyInterface::sendState(double NAV_X, double NAV_Y, std::vector<VarDataPair> vd_pairs){
  if(!isConnected())
    return false;

  // Create the state object
  PyObject* state_dict = constructState(NAV_X, NAV_Y, vd_pairs);

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

bool PyInterface::failureState(){
  return m_bridge_client == NULL;
}


bool PyInterface::isConnected(){
  return m_is_connected;
}

PyObject* PyInterface::constructState(double NAV_X, double NAV_Y, std::vector<VarDataPair> vd_pairs){
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

  PyObject* MOOS_VARS_TMP = PyTuple_New(0); // TODO: Use code above to populate stuff
  PyObject *state_dict = Py_BuildValue("{s:d,s:d,s:()}", // This constructs a python dict
    "NAV_X", NAV_X,
    "NAV_Y", NAV_Y,
    "MOOS_VARS", MOOS_VARS_TMP);

  if (!state_dict){
    PyErr_Print();
    Py_DECREF(MOOS_VARS_TMP);
    return NULL;
  }

  return state_dict;
}

PyInterface::~PyInterface(){
  unloadModule();
  Py_Finalize();
}
 