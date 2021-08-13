#--------------------------------------------------------
# The CMakeLists.txt for:                 uFldFlagManager
# Author(s):                                Mike Benjamin
#--------------------------------------------------------

SET(SRC
  FlagManager.cpp
  FlagManager_Info.cpp
  main.cpp
)

ADD_EXECUTABLE(uFldFlagManagerAgent ${SRC})

TARGET_LINK_LIBRARIES(uFldFlagManagerAgent
   ${MOOS_LIBRARIES}
   apputil
   contacts
   geometry
   mbutil
   m
   pthread)

