add_executable(test_pyinterface
  PyInterface_test.cpp
)

message("Include dirs: ${Python_INCLUDE_DIRS}")

target_link_libraries(test_pyinterface
  gtest_main
  BHV_Agent
)

include(GoogleTest)
gtest_discover_tests(test_pyinterface)