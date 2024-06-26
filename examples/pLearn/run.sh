#!/usr/bin/env bash

# Move to this director (for relative paths)
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

# Ktm 3 times on exit to kill all running MOOS processes
function cleanup {
  echo "==============================="
  echo "=    Dont ^C any futher       ="
  echo "==============================="
  printf "Killing MOOS..."
  ktm &> /dev/null
  printf " 1"
  ktm &> /dev/null
  printf " 2"
  ktm &> /dev/null
  printf " 3\n"
}

# Make sure that ktm is run on EXIT of this script
# ^C / Error / Normal exit
trap cleanup EXIT

# Launch MOOS-IvP simulation
echo "Launching simulation..."
cd mission
./launch_full.sh 6 &> /dev/null &
cd ..

# Start trainer with any arguments passed to this script
echo "Launching runner..."
./model/run.py "$@"

cd $PREVIOUS_WD