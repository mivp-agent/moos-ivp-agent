#--------------------------------------------------------
# The CMakeLists.txt for:                       pEpisodeManager
# Author(s):                              Carter Fendley
#--------------------------------------------------------

SET(SRC
  EpisodeManager.cpp
  EpisodeManager_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(pEpisodeManager ${SRC})

TARGET_LINK_LIBRARIES(pEpisodeManager
   ${MOOS_LIBRARIES}
   apputil
   mbutil
   m
   pthread
   logic)

