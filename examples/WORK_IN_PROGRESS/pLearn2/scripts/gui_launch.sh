#!/usr/bin/env bash
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

TIME_WARP="4"

cd ../mission/heron
  # Launch a agents
  ./launch_heron.sh red agent 11 --color=orange $TIME_WARP > /dev/null &

  # Launch a blue drone
  ./launch_heron.sh blue drone 21 --behavior=DEFEND --color=orange $TIME_WARP > /dev/null &
cd ..

cd shoreside
  ./launch_shoreside.sh $TIME_WARP >& /dev/null &
  #./launch_shoreside.sh $TIME_WARP >& /dev/null &
  sleep 5
  echo "DEPLOYING"
  uPokeDB targ_shoreside.moos DEPLOY_ALL=true MOOS_MANUAL_OVERRIDE_ALL=false
  sleep 1
  uMAC targ_shoreside.moos
cd $PREVIOUS_WD