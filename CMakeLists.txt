#=======================================================================
# FILE:  moos-ivp-agent/CMakeLists.txt
# DATE:  2020/10/25
# INFO:  Top-level CMakeLists.txt file for the moos-ivp-agent
# NAME:  Maintained by Carter Fendley - Original setup by Christian Convey
#        Chris Gagner, Mike Benjamin and tips borrowed from Dave Billin
#=======================================================================
CMAKE_MINIMUM_REQUIRED(VERSION 3.0)

# Use cmake 3.0+ versioning
CMAKE_POLICY(SET CMP0048 NEW)

PROJECT(IVP_AGENT VERSION 0.1)

set (CMAKE_CXX_STANDARD 11)

#=======================================================================
# Find python libraries
#=======================================================================

# NOTE: There is some interaction going on between this find_package for
# python and the one inside gtest. It seems that I need to find the
# Interpeter component here or any re-build of the project will fail. Not
# 100% sure why or if the order of these two matter.

if(${CMAKE_VERSION} VERSION_LESS "3.12")
  message("Using legacy FindPythonLibs due to cmake ${CMAKE_VERSION}")
  find_package(PythonLibs 3.7 EXACT REQUIRED)
  
  # Rename
  set(Python_INCLUDE_DIRS ${PYTHON_INCLUDE_DIRS})
  set(Python_LIBRARIES ${PYTHON_LIBRARIES})
else()
  find_package(Python 3.7 EXACT COMPONENTS Interpreter Development REQUIRED)
endif()

include_directories(${Python_INCLUDE_DIRS})

message("Python include dirs: ${Python_INCLUDE_DIRS}")
message("Python libraries: ${Python_LIBRARIES}")

#=======================================================================
# Enable Google Testing
#=======================================================================
add_subdirectory(thirdparty/gtest)
enable_testing()

#=======================================================================
# Set the output directories for the binary and library files
#=======================================================================
GET_FILENAME_COMPONENT(IVP_EXTEND_BIN_DIR "${CMAKE_SOURCE_DIR}/bin"  ABSOLUTE )
GET_FILENAME_COMPONENT(IVP_EXTEND_LIB_DIR "${CMAKE_SOURCE_DIR}/lib"  ABSOLUTE )

SET( LIBRARY_OUTPUT_PATH      "${IVP_EXTEND_LIB_DIR}" CACHE PATH "" )
SET( ARCHIVE_OUTPUT_DIRECTORY "${IVP_EXTEND_LIB_DIR}" CACHE PATH "" )
SET( LIBRARY_OUTPUT_DIRECTORY "${IVP_EXTEND_LIB_DIR}" CACHE PATH "" )

SET( EXECUTABLE_OUTPUT_PATH    "${IVP_EXTEND_BIN_DIR}" CACHE PATH "" )
SET( RUNTIME_OUTPUT_DIRECTORY "${IVP_EXTEND_BIN_DIR}"  CACHE PATH "" )

#=======================================================================
# Find MOOS
#=======================================================================
find_package(MOOS 10.0 REQUIRED)
INCLUDE_DIRECTORIES(${MOOS_INCLUDE_DIRS})

#=======================================================================
# Find the "moos-ivp" base directory
#=======================================================================

# Search for the moos-ivp folder
find_path( MOOSIVP_SOURCE_TREE_BASE
           NAMES build-ivp.sh build-moos.sh configure-ivp.sh
           PATHS "./moos-ivp" "../moos-ivp" "../../moos-ivp" "../../moos-ivp/trunk/" "../moos-ivp/trunk/"
           DOC "Base directory of the MOOS-IvP source tree"
           NO_DEFAULT_PATH
)

if (NOT MOOSIVP_SOURCE_TREE_BASE)
    message(FATAL_ERROR "Please set MOOSIVP_SOURCE_TREE_BASE to  the location of the \"moos-ivp\" folder ")
endif()

#======================================================================
# Specify where to find IvP's headers and libraries...
#======================================================================

FILE(GLOB IVP_INCLUDE_DIRS ${MOOSIVP_SOURCE_TREE_BASE}/ivp/src/lib_* )
INCLUDE_DIRECTORIES(${IVP_INCLUDE_DIRS})

FILE(GLOB IVP_LIBRARY_DIRS ${MOOSIVP_SOURCE_TREE_BASE}/lib )
LINK_DIRECTORIES(${IVP_LIBRARY_DIRS})

#======================================================================
# Specify Compiler Flags
#======================================================================
IF( ${WIN32} )
   #---------------------------------------------
   # Windows Compiler Flags
   #---------------------------------------------
   IF(MSVC)
      # Flags for Microsoft Visual Studio
      SET( WALL_ON OFF CACHE BOOL 
         "tell me about all compiler warnings (-Wall) ")
      IF(WALL_ON)
         SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall")
      ENDIF(WALL_ON)
   ELSE(MSVC)
      # Other Windows compilers go here
   ENDIF(MSVC)

ELSE( ${WIN32} )
   #---------------------------------------------
   # Linux and Apple Compiler Flags
   #---------------------------------------------
   # Force -fPIC because gcc complains when we don't use it with x86_64 code.
   # Note sure why: -fPIC should only be needed for shared objects, and
   # AFAIK, CMake gets that right when building shared objects. -CJC
   SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fPIC -g -Wdeprecated-declarations")
   IF(CMAKE_COMPILER_IS_GNUCXX)
      # Flags for the GNU C++ Compiler
      SET( WALL_ON OFF CACHE BOOL 
         "tell me about all compiler warnings (-Wall) ")
      IF(WALL_ON)
         SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall" -C++11)
      ENDIF( WALL_ON)
   ELSE(CMAKE_COMPILER_IS_GNUCXX)
    
   ENDIF(CMAKE_COMPILER_IS_GNUCXX)

ENDIF( ${WIN32} )

#=======================================================================
# Add Subdirectories
#=======================================================================
ADD_SUBDIRECTORY(src)
ADD_SUBDIRECTORY(test/cpp)
