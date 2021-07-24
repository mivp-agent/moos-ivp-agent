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
  bool loadModule(std::string path);

 private:
  bool unloadModule();

  PyObject *m_module;
};

#endif 