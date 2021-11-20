#--------------------------------------------------------
# The CMakeLists.txt for:             lib_behaviors-agent
# Author(s):                               Carter Fendley
#--------------------------------------------------------

# Set System Specific Libraries
if (${WIN32})
  # Windows Libraries
  SET(SYSTEM_LIBS
      )
else (${WIN32})
  # Linux and Apple Libraries
  SET(SYSTEM_LIBS
      m )
endif (${WIN32})

#--------------------------------------------------------
#                                               BHV_Agent
#--------------------------------------------------------
add_library(BHV_Agent SHARED
   BHV_Agent.cpp PyInterface.cpp)

TARGET_LINK_LIBRARIES(BHV_Agent
   helmivp
   behaviors 
   ivpbuild 
   logic 
   ivpcore 
   bhvutil 
   mbutil 
   geometry
   ${SYSTEM_LIBS}
   ${Python_LIBRARIES})

# For easy include dirs in testing
target_include_directories(BHV_Agent PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})