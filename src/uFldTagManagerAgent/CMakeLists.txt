#--------------------------------------------------------
# The CMakeLists.txt for:             uFldTagManagerAgent
# Author(s):                Mike Benjamin, Carter Fendley
#--------------------------------------------------------

# Set System Specific Libraries
SET(SYSTEM_LIBS m pthread)

SET(SRC
   TagManager.cpp
   TagManager_Info.cpp
   VTag.cpp
   main.cpp
)

ADD_EXECUTABLE(uFldTagManagerAgent ${SRC})

TARGET_LINK_LIBRARIES(uFldTagManagerAgent
  ${MOOS_LIBRARIES}
  apputil
  geometry 
  mbutil
  contacts
  ${SYSTEM_LIBS}
)

