#!/bin/bash
TIME_WARP=1

CMD_ARGS=""
NO_HERON=""
NO_MOKAI=""
NO_SHORESIDE=""

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
        HELP="yes"
    elif [ "${ARGI}" = "--no_shoreside" -o "${ARGI}" = "-ns" ] ; then
        NO_SHORESIDE="true"
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
        echo "Time warp set up to $TIME_WARP."
    elif [ "${ARGI}" = "--just_build" -o "${ARGI}" = "-j" ] ; then
        JUST_BUILD="yes"
        echo "Just building files; no vehicle launch."
    else
        CMD_ARGS=$CMD_ARGS" "$ARGI
    fi
done


if [ "${HELP}" = "yes" ]; then
  echo "$0 [SWITCHES]"
  echo "  XX                  : Time warp"
  echo "  --no_shoreside, -ns"
  echo "  --just_build, -j"
  echo "  --help, -h"
  exit 0;
fi

#-------------------------------------------------------
#  Part 2: Launching herons
#-------------------------------------------------------
if [[ -z $NO_HERON ]]; then
  cd ./heron
  # Gus Red
  ./launch_heron.sh g r1 r3 $TIME_WARP -s --start-x=50 --start-y=-50 --start-a=240 > /dev/null &
  sleep 1
  # Luke Red
  ./launch_heron.sh l r2 r4 $TIME_WARP -s --start-x=50 --start-y=-45 --start-a=240 > /dev/null &
  sleep 1
  # Kirk Blue
  ./launch_heron.sh k b1 b3 $TIME_WARP -s --start-x=-52 --start-y=-55 --start-a=60 > /dev/null &
  sleep 1
  # Jing Blue
  ./launch_heron.sh j b2 b4 $TIME_WARP -s --start-x=-52 --start-y=-70 --start-a=60 > /dev/null &
  sleep 1
  # Evan Red
  ./launch_heron.sh e r3 r4 $TIME_WARP -s --start-x=50 --start-y=-18 --start-a=240 > /dev/null &
  sleep 1
  # Felix Blue
  ./launch_heron.sh f b3 b4 $TIME_WARP -s --start-x=-52 --start-y=-50 --start-a=60 > /dev/null &
  sleep 1
  # Hal Red
  ./launch_heron.sh h r4 r3 $TIME_WARP -s --start-x=50 --start-y=-40 --start-a=240 > /dev/null &
  sleep 1
  # Ida Blue
  ./launch_heron.sh i b4 b3 $TIME_WARP -s --start-x=-52 --start-y=-75 --start-a=60 > /dev/null &
  sleep 1
  cd ..
fi



#-------------------------------------------------------
#  Part 3: Launching shoreside
#-------------------------------------------------------
if [[ -z $NO_SHORESIDE ]]; then
  cd ./shoreside
  ./launch_shoreside.sh $TIME_WARP >& /dev/null &
  cd ..
fi

#-------------------------------------------------------
#  Part 4: Launching uMAC
#-------------------------------------------------------
uMAC shoreside/targ_shoreside.moos

#-------------------------------------------------------
#  Part 5: Killing all processes launched from script
#-------------------------------------------------------
echo "Killing Simulation..."
kill -- -$$
# sleep is to give enough time to all processes to die
sleep 3
echo "All processes killed"
