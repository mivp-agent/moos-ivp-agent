#--------------------------------------------------------
# The CMakeLists.txt for:              lib_behaviors-test
# Author(s):                                
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


MACRO(ADD_BHV BHV_NAME)
  ADD_LIBRARY(${BHV_NAME} SHARED ${BHV_NAME}.cpp)
  TARGET_LINK_LIBRARIES(${BHV_NAME} 
    helmivp
    behaviors 
    ivpbuild 
    logic 
    ivpcore 
    bhvutil 
    mbutil 
    geometry 
    ${SYSTEM_LIBS} )
ENDMACRO(ADD_BHV)


#--------------------------------------------------------
#                                               BHV_Agent
#--------------------------------------------------------
add_library(BHV_Agent SHARED 
   BHV_Agent.cpp PyInterface.cpp)

if(${CMAKE_VERSION} VERSION_LESS "3.12")
  message("Using legacy FindPythonLibs due to cmake ${CMAKE_VERSION}")
  find_package(PythonLibs 3.7 EXACT REQUIRED)
  include_directories(${PYTHON_INCLUDE_DIRS})
  target_link_libraries(BHV_Agent ${PYTHON_LIBRARIES})
else()
  find_package(Python 3.7 EXACT COMPONENTS Development REQUIRED)
  include_directories(${Python_INCLUDE_DIRS})
  target_link_libraries(BHV_Agent ${Python_LIBRARIES})
endif()

TARGET_LINK_LIBRARIES(BHV_Agent
   helmivp
   behaviors 
   ivpbuild 
   logic 
   ivpcore 
   bhvutil 
   mbutil 
   geometry
   ${SYSTEM_LIBS})

