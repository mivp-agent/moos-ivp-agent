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
}

//---------------------------------------------------------
// Procedure: loadModule

bool PyInterface::loadModule(string path)
{
  if(m_module){
    if(!unloadModule())
      return false;
  }
  m_module = PyImport_ImportModule("RLAgent_interface");

  if(!m_module){
    // Print error to console
    PyObject *ptype, *pvalue, *ptraceback;
    PyErr_Fetch(&ptype, &pvalue, &ptraceback);
    printf("ERROR: PyInterface.cpp failed to load module in specified path\n");
    PyErr_Print();
  }
}

//---------------------------------------------------------
// Procedure: unloadModule

bool PyInterface::unloadModule()
{
  
}


PyInterface::~PyInterface(){
  unloadModule();
}
 