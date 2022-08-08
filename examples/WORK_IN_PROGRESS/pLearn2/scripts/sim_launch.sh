#!/usr/bin/env bash
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

TIME_WARP="10"
# Change below to --log for logging
LOGGING=""

cd "../mission/heron"
  # Launch a agents
  ./launch_heron.sh red agent 11 --color=orange $LOGGING $TIME_WARP > /dev/null &
  ./launch_heron.sh red agent 12 --color=green $LOGGING $TIME_WARP > /dev/null &
  ./launch_heron.sh red agent 13 --color=purple $LOGGING $TIME_WARP > /dev/null &
  #./launch_heron.sh red agent 14 --color=gray $LOGGING $TIME_WARP > /dev/null &
  #./launch_heron.sh red agent 15 --color=yellow $LOGGING $TIME_WARP > /dev/null &


  # Launch a blue drone
  ./launch_heron.sh blue drone 21 --behavior=DEFEND --color=orange $LOGGING $TIME_WARP > /dev/null &
  ./launch_heron.sh blue drone 22 --behavior=DEFEND --color=green $LOGGING $TIME_WARP > /dev/null &
  ./launch_heron.sh blue drone 23 --behavior=DEFEND --color=purple $LOGGING $TIME_WARP > /dev/null &
  #./launch_heron.sh blue drone 24 --behavior=DEFEND --color=gray $LOGGING $TIME_WARP > /dev/null &
  #./launch_heron.sh blue drone 25 --behavior=DEFEND --color=yellow $LOGGING $TIME_WARP > /dev/null &
cd ..

cd shoreside
  ./launch_shoreside.sh --no_gui $LOGGING $TIME_WARP >& /dev/null &
  #./launch_shoreside.sh $LOGGING 4 >& /dev/null &
  sleep 5
  echo "DEPLOYING"
  uPokeDB targ_shoreside.moos DEPLOY_ALL=true MOOS_MANUAL_OVERRIDE_ALL=false
  sleep 1
  uMAC targ_shoreside.moos
cd $PREVIOUS_WD