#--------------------------------------------------------
# The CMakeLists.txt for:             lib_mivp-test
# Author(s):                               Carter Fendley
#--------------------------------------------------------

# Set System Specific Libraries
if (${WIN32})
  # Windows Libraries
  SET(SYSTEM_LIBS)
else (${WIN32})
  # Linux and Apple Libraries
  SET(SYSTEM_LIBS m )
endif (${WIN32})

include_directories("${gtest_SOURCE_DIR}/include"
  "${gmock_SOURCE_DIR}/include")

#--------------------------------------------------------
#                                               BHV_Agent
#--------------------------------------------------------
add_library(mivp_test SHARED
   mivptest.h
   MockCMOOSApp.cpp
   MockMOOSCastingApp.cpp)

TARGET_LINK_LIBRARIES(mivp_test
  ${MOOS_LIBRARIES}
  gmock_main
  ${SYSTEM_LIBS}
)



# For easy include dirs in testing
target_include_directories(mivp_test PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

MESSAGE(STATUS "mock_src=${gmock_SOURCE_DIR}")

get_property(dirs DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
foreach(dir ${dirs})
  message(STATUS "dir='${dir}'")
endforeach()
