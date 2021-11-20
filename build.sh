#!/bin/bash
INVOCATION_ABS_DIR=`pwd`
BUILD_TYPE="None"
TEST="no"
CMD_LINE_ARGS=""

#-------------------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------------------
for ARGI; do
  if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
		printf "%s [SWITCHES]                       \n" $0
		printf "Switches:                           \n" 
		printf "  --help    : -h                    \n" 
		printf "  --debug   : -d                    \n"
		printf "  --release : -r                    \n"
		printf "  --test    : -t                    \n"
		printf "Notes:                              \n"
		printf " (1) All other command line args will be passed as args    \n"
		printf "     to \"make\" when it is eventually invoked.            \n"
		printf " (2) For example -k will continue making when/if a failure \n"
		printf "     is encountered in building one of the subdirectories. \n"
		printf " (3) For example -j2 will utilize a 2nd core in the build  \n"
		printf "     if your machine has two cores. -j4 etc for quad core. \n"
		exit 0;
	elif [[ "${ARGI}" == "--debug" || "${ARGI}" == "-d" ]]; then
		BUILD_TYPE="Debug"
	elif [[ "${ARGI}" == "--release" || "${ARGI}" == "-r" ]]; then
		BUILD_TYPE="Release"
	elif [[ "${ARGI}" == "--test" || "${ARGI}" == "-t" ]]; then
		TEST="yes"
	else
		CMD_LINE_ARGS=$CMD_LINE_ARGS" "$ARGI
	fi
done

set -e # Exit script if sub command fails
trap 'cd ${INVOCATION_ABS_DIR}' EXIT # Clean up

#-------------------------------------------------------------------
#  Part 2: Invoke the call to make in the build directory
#-------------------------------------------------------------------

mkdir -p build
cd build

echo "Configuring moos-ivp-agent..." 
cmake -DCMAKE_BUILD_TYPE=${BUILD_TYPE} ../

echo "Making moos-ivp-agent..."
make ${CMD_LINE_ARGS}

if [ "$TEST" == "yes" ]; then
	ctest --verbose
fi