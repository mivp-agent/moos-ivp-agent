#!/usr/bin/env bash

# Move to this director (for relative paths)
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

# Make sure that ktm is run on EXIT of this script
trap "echo \"Killing MOOS...\" && ktm && ktm && ktm" EXIT

# Launch MOOS-IvP simulation
cd mission_alder
./launch.sh &> /dev/null &
cd ..

# Launch the python model
cd model
./model.py
cd
