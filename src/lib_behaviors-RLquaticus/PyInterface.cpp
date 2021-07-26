/*****************************************************************/
/*    NAME: Carter Fendley                                       */
/*    ORGN: MIT                                                  */
/*    FILE: PyInterface.cpp                                      */
/*    DATE: Jul 22nd 2021                                        */
/*****************************************************************/

#include <cstdlib>
#include "PyInterface.h"
#include "MBUtils.h"

using namespace std;

//---------------------------------------------------------
// Constructor

PyInterface::PyInterface()
{
  Py_Initialize();

  loadModule();

  m_bridge_module = NULL;
  m_bridge_client_attribute;
  m_bridge_client = NULL;
}

bool PyInterface::failureState(){
  return m_bridge_module == NULL;
}

void PyInterface::printPythonError(){
  // Print error to console
  PyObject *ptype, *pvalue, *ptraceback;
  PyErr_Fetch(&ptype, &pvalue, &ptraceback);
  printf("ERROR: PyInterface.cpp failed to load module in specified path\n");
  PyErr_Print();
}

//---------------------------------------------------------
// Procedure: loadModule

bool PyInterface::loadModule()
{
  // Check if module has been loaded
  if(m_bridge_module){
    if(!unloadModule())
      return false;
  }
  
  // Load module
  m_bridge_module = PyImport_ImportModule("RLAgent_interface");

  if(!m_bridge_module){
    printPythonError();
    return false;
  }

  // Get the reference to the ModelBridgeClient object
  m_bridge_client_attribute = PyObject_GetAttrString(m_bridge_module, "ModelBridgeClient");

  if(!m_bridge_client_attribute){
    printPythonError();
    return false;
  }

  // Instantiate the object
  PyObject* args = PyTuple_New(0);
  m_bridge_client = PyObject_CallObject(m_bridge_client_attribute, args);

  return true;
}

//---------------------------------------------------------
// Procedure: unloadModule

bool PyInterface::unloadModule()
{
  if (m_bridge_module)
    Py_DECREF(m_bridge_module);
  
  Py_Finalize();
}


PyInterface::~PyInterface(){
  unloadModule();
}
 