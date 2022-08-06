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

PyInterface::PyInterface(string module_name)
{
  m_module_name = module_name;
  m_bridge_client = NULL;

  m_is_connected = false;

  // Below will fatal error on failure, no-op on second call
  Py_Initialize();

  // Attempt to load the module
  loadModule();
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
  PyObject* m_bridge_module = PyImport_ImportModule(m_module_name.c_str());

  if(!m_bridge_module){
    fprintf(stderr, "ERROR: Failed to import bridge module \"%s\"\n", m_module_name.c_str());
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
  if (m_bridge_client){
    Py_DECREF(m_bridge_client);
    m_bridge_client = NULL;
    return true;
  }
  return false;
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

bool PyInterface::sendState(double helm_time, double NAV_X, double NAV_Y, double NAV_H, std::string VNAME, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs){
  if(!isConnected())
    return false;
  // Create the state object
  PyObject* state_dict = constructState(helm_time, NAV_X, NAV_Y, NAV_H, VNAME, node_reports, vd_pairs);

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
  return success;
}

void PyInterface::listen(double &speed, double &course, std::vector<VarDataPair> &posts, std::string &ctrl_msg){
  if(!isConnected())
    return;

  PyObject* result = PyObject_CallMethod(m_bridge_client, "listen", NULL);

  if(result == NULL){
    fprintf(stderr, "ERROR: Failed to call listen function from client object\n\n");
    PyErr_Print();
    return;
  }

  if(PyBool_Check(result)){
    bool return_bool = PyObject_IsTrue(result);
    //Clean up
    Py_DECREF(result);

    if(return_bool){
      // Not what we are expecting so raise our own error
      throw runtime_error("ModelBridgeClient's listen_state function returned True (invalid protocol)");
    }
    return; // TODO: Propogate failure up to IvP BHV for warnings
  }

  if(!PyDict_Check(result)){
    Py_DECREF(result);
    throw runtime_error("Method 'listen_action' did not fail or return dict");
  }
  
  // PyDict_GetItemString returns borrowed references so no need to DECREF
  speed = PyFloat_AsDouble(PyDict_GetItemString(result, "speed"));
  course = PyFloat_AsDouble(PyDict_GetItemString(result, "course"));
  ctrl_msg = PyUnicode_AsUTF8(PyDict_GetItemString(result, "ctrl_msg"));
  bool ok = dictToVarDataPair(PyDict_GetItemString(result, "posts"), posts);
  if(!ok){
    // Clean up and throw
    Py_DECREF(result);
    throw runtime_error("Error translating python dict to std::vector<VarDataPair>");
  }

  // Clean up an return normally
  Py_DECREF(result);
  return;
}

bool PyInterface::failureState(){
  return m_bridge_client == NULL;
}


bool PyInterface::isConnected(){
  return m_is_connected;
}

bool PyInterface::dictToVarDataPair(PyObject* dict, std::vector<VarDataPair> &vdp){
  PyObject *key, *value;
  Py_ssize_t pos = 0;
  while (PyDict_Next(dict, &pos, &key, &value)){
    std::string sname = PyUnicode_AsUTF8(key);


    if(PyObject_TypeCheck(value, &PyUnicode_Type)){
      std::string svalue = PyUnicode_AsUTF8(value);

      VarDataPair pair(sname, svalue);
      vdp.push_back(pair);
    }else if(PyBool_Check(value)){
      if(PyObject_IsTrue(value)){
        VarDataPair pair(sname, "true", "auto");
        vdp.push_back(pair);
      }else{
        VarDataPair pair(sname, "false", "auto");
        vdp.push_back(pair);
      }
    }else{
      return false;
    }
  }
  return true;
}

PyObject* PyInterface::constructState(double helm_time, double NAV_X, double NAV_Y, double NAV_H, std::string VNAME, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs){
  // Build top level state['NODE_REPORTS'] = {} dictionary
  PyObject* node_reports_dict = PyDict_New();

  // Ass all node reports to this dict in the form a a dictionary themselves
  int vsize = node_reports.size();
  for(int i=0; i<vsize; i++){
    std::string name = tokStringParse(node_reports[i], "NAME", ',', '=');
    PyObject* report_dict = nodeReportToDict(node_reports[i]);

    PyDict_SetItemString(node_reports_dict, name.c_str(), report_dict);
    Py_DECREF(report_dict);
  }

  PyObject *state_dict = Py_BuildValue("{s:s,s:d,s:d,s:d,s:d,s:O}", // This constructs a python dict
    "_ID_", VNAME.c_str(),
    "MOOS_TIME", helm_time,
    "NAV_X", NAV_X,
    "NAV_Y", NAV_Y,
    "NAV_HEADING", NAV_H,
    "NODE_REPORTS", node_reports_dict // Using O cause it incref's (for sure)
  );
  
  Py_DECREF(node_reports_dict);

  if (!state_dict){
    PyErr_Print();
    return NULL;
  }

  // Unpack vd_pairs and translate into python types
  vsize = vd_pairs.size();
  for(int i=0; i<vsize; i++){
    string var = vd_pairs[i].get_var();
    PyObject* pydata;

    if(vd_pairs[i].is_string()){
      string sdata = vd_pairs[i].get_sdata();

      // Convert python land and True / False if applicable
      if(tolower(sdata) == "false"){
        Py_INCREF(Py_False);
        pydata = Py_False;
      }else if(tolower(sdata) == "true"){
        Py_INCREF(Py_True);
        pydata = Py_True;
      }else if(tolower(sdata) == "null"){
        Py_INCREF(Py_None);
        pydata = Py_None;
      }else{
        pydata = Py_BuildValue("s", sdata.c_str());
      }
    }else{
      double ddata = vd_pairs[i].get_ddata();
      pydata = PyFloat_FromDouble(ddata);
    }

    // Add to state dict and release our hold
    PyDict_SetItemString(state_dict, var.c_str(), pydata);
    Py_DECREF(pydata);
  }
  return state_dict;
}

PyObject* PyInterface::nodeReportToDict(std::string report){
  // Parse node report
  double x = tokDoubleParse(report, "X", ',', '=');
  double y = tokDoubleParse(report, "Y", ',', '=');
  double heading = tokDoubleParse(report, "HDG", ',', '=');
  double time = tokDoubleParse(report, "TIME", ',', '=');

  PyObject* dict = Py_BuildValue("{s:d,s:d,s:d,s:d}",
    "NAV_X", x,
    "NAV_Y", y,
    "NAV_HEADING", heading,
    "MOOS_TIME", time
  );

  return dict;
}

PyInterface::~PyInterface(){
  unloadModule();
  Py_Finalize();
}
 