#!/bin/bash
TIME_WARP=1

VERBOSE=""
CMD_ARGS=""
NO_M200=""
NO_SHORESIDE=""

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
        HELP="yes"
    elif [ "${ARGI}" = "--no_shoreside" -o "${ARGI}" = "-ns" ] ; then
        NO_SHORESIDE="true"
    elif [ "${ARGI}" = "--no_m200" -o "${ARGI}" = "-nm2" ] ; then
        NO_M200="true"
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
        echo "Time warp set up to $TIME_WARP."
    elif [ "${ARGI}" = "--just_build" -o "${ARGI}" = "-j" ] ; then
        JUST_BUILD="-j" 
        # Pass $JUST_BUILD directly to the launch commands, this will be blank if not just building
        echo "Just building files; no vehicle launch."
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ] ; then
        VERBOSE="-v" 
        echo "Excuting launch verbosly."
    else
        CMD_ARGS=$CMD_ARGS" "$ARGI
    fi
done

if [ "${HELP}" = "yes" ]; then
  echo "$0 [SWITCHES]"
  echo "  XX                  : Time warp"
  echo "  --no_shoreside, -ns"
  echo "  --no_mokai, -nm"
  echo "  --no_m200, -nm2"
  echo "  --just_build, -j"
  echo "  --help, -h"
  exit 0;
fi

#-------------------------------------------------------
#  Part 2: Launching M200s
#-------------------------------------------------------
if [[ -z $NO_M200 ]]; then
  echo "Launching vehicles..."
  cd ./m200
  if [[ -z $VERBOSE ]]; then
    # Evan Blue
    ./launch_m200.sh $TIME_WARP $JUST_BUILD -e -b -s --DEFEND >& /dev/null &
    # Felix Red
    ./launch_m200.sh $TIME_WARP $JUST_BUILD -f -r -s >& /dev/null &
  else
    # Evan Blue
    ./launch_m200.sh $TIME_WARP $JUST_BUILD $VERBOSE -e -b -s --DEFEND &
    # Felix Red
    ./launch_m200.sh $TIME_WARP $JUST_BUILD $VERBOSE -f -r -s &
    fi
  cd ..
fi

#-------------------------------------------------------
#  Part 3: Launching shoreside
#-------------------------------------------------------
if [[ -z $NO_SHORESIDE ]]; then
  echo "Lauching shoreside..."
  cd ./shoreside
  if [[ -z $VERBOSE ]]; then
    ./launch_shoreside.sh $TIME_WARP $JUST_BUILD >& /dev/null &
  else
    ./launch_shoreside.sh $TIME_WARP $JUST_BUILD $VERBOSE &
  fi
  cd ..
fi

sleep 3
#-------------------------------------------------------
#  Part 4: Launching uMAC
#-------------------------------------------------------
uMAC shoreside/targ_shoreside.moos
