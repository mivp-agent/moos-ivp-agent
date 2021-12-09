#include "PyInterface.h"
#include <gtest/gtest.h>
#include <string.h>

using namespace std;

#define MODULE_PATH strcat(__FILE__, "/../src/python_module")

string file = __FILE__;
string test_dir = file.substr(0, file.find_last_of('/'));
string src_dir = test_dir.substr(0, test_dir.find_last_of('/'))+"/src";
string module_dir = src_dir + "/python_module";

//fprintf(stderr, "%s\n", src_dir.c_str());
//fprintf(stderr, "Current path: %ls\n", Py_GetPath());

TEST(TestInitalization, TestFailure){
  Py_Initialize();

  // Remove any existing moos-ivp-agent from PYTHONPATH
  PyRun_SimpleString("import sys");
  PyRun_SimpleString("sys.path = [p for p in sys.path if \"moos-ivp-agent\" not in p]");

  fprintf(stderr, "Current path: %ls\n", Py_GetPath());

  PyInterface bridge("mivp_agent.bridge");

  EXPECT_TRUE(bridge.failureState());
}

TEST(TestInitalization, TestSuccess){
  Py_Initialize();

  // Add the correct path for the module
  PyRun_SimpleString("import sys");
  string cmd_string = "sys.path.append(\"" + module_dir + "\")";
  PyRun_SimpleString(cmd_string.c_str());

  fprintf(stderr, "Current path: %ls\n", Py_GetPath());

  PyInterface bridge("mivp_agent.bridge");

  EXPECT_FALSE(bridge.failureState());
}