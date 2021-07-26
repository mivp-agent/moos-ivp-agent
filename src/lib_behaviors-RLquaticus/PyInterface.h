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

 public: // Overloaded virtual functions
  bool failureState();

 private:
  bool loadModule();
  bool unloadModule();

  void printPythonError();

  PyObject* m_bridge_module;
  PyObject* m_bridge_client_attribute;
  PyObject* m_bridge_client;
};

#endif 