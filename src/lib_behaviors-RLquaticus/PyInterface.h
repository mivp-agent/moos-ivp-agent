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
  bool sendState(double helm_time, double NAV_X, double NAV_Y, double NAV_H, std::string VNAME, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs);
  void listen(double &speed, double &course, std::vector<VarDataPair> &posts, std::string &ctrl_msg);

  // State exposure
  bool failureState();
  bool isConnected();

 private:
  // Python functions
  bool loadModule();
  bool unloadModule();
  
  // Helper functions
  bool dictToVarDataPair(PyObject* dict, std::vector<VarDataPair> &vdp);
  PyObject* constructState(double helm_time, double NAV_X, double NAV_Y, double NAV_H, std::string VNAME, std::vector<std::string> node_reports, std::vector<VarDataPair> vd_pairs);
  PyObject* nodeReportToDict(std::string report);
  bool validateAction(PyObject* action);

  // Objects
  PyObject* m_bridge_client;

  bool m_is_connected;
};

#endif 