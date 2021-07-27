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
#include "VarDataPair.h"

class PyInterface
{
 public:
  PyInterface();
  ~PyInterface();

 public: 
  // Do things functions TODO: name?
  bool connect();
  bool sendState(double NAV_X, double NAV_Y, std::vector<VarDataPair> vd_pairs);

  // State exposure
  bool failureState();
  bool isConnected();


 private:
  // Python functions
  bool loadModule();
  bool unloadModule();
  
  // Helper functions
  PyObject* constructState(double NAV_X, double NAV_Y, std::vector<VarDataPair> vd_pairs);


  // Objects
  PyObject* m_bridge_client;

  bool m_is_connected;
};

#endif 