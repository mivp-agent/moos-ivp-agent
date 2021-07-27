/*****************************************************************/
/*    NAME: Carter Fendley                                       */
/*    ORGN: MIT                                                  */
/*    FILE: PyInterface.h                                        */
/*    DATE: Jul 22nd 2021                                        */
/*****************************************************************/

#ifndef PY_INTERFACE_HEADER
#define PY_INTERFACE_HEADER

#include <string>
#include <Python.h>

class PyInterface
{
 public:
  PyInterface();
  ~PyInterface();

 public: 
  // Do things functions TODO: name?
  bool connect();

  // State exposure
  bool failureState();
  bool isConnected(); 

 private:
  // Python functions
  bool loadModule();
  bool unloadModule();
  
  // Helper functions

  // Objects
  PyObject* m_bridge_client;

  bool m_is_connected;
};

#endif 