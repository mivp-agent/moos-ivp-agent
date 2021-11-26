#!/usr/bin/env bash
DIRNAME="$(dirname $0)"
cd $DIRNAME

TIME_WARP="4"

cd vehicle
  # Launch a agents
  ./launch_vehicle.sh red agent 11 --color=orange $TIME_WARP > /dev/null &
cd ..

cd shoreside
  ./launch_shoreside.sh $TIME_WARP >& /dev/null &
  sleep 1
  uMAC targ_shoreside.moos