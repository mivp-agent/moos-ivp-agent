#--------------------------------------------------------
# The CMakeLists.txt for:                 pEpisodeManager
# Author(s):                              Carter Fendley
#--------------------------------------------------------

SET(SRC
  EpisodeManager.cpp
  EpisodeManager_Info.cpp
  RandomPair.cpp
  RandPairPoly.cpp
  main.cpp
)

ADD_EXECUTABLE(pEpisodeManager ${SRC})

TARGET_LINK_LIBRARIES(pEpisodeManager
   ${MOOS_LIBRARIES}
   geometry
   apputil
   mbutil
   m
   pthread
   logic
   mivp_test)

ADD_EXECUTABLE(test_pEpisodeManager
  EpisodeManager.cpp
  EpisodeManager_test.cpp
)

TARGET_LINK_LIBRARIES(test_pEpisodeManager
   ${MOOS_LIBRARIES}
   geometry
   apputil
   mbutil
   m
   pthread
   logic
   mivp_test)

include(GoogleTest)
gtest_discover_tests(test_pEpisodeManager)
