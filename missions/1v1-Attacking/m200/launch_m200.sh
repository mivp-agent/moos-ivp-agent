#!/bin/bash
TIME_WARP=1

SHORE_IP="192.168.1.226" #155 for normal shoreside
SHORE_LISTEN="9300"

VERBOSE=""
HELP="no"
JUST_BUILD="no"
VTEAM=""
VNAME=""
VMODEL="M200"

START_POS="56,16,240"
GRAB_POS=""
GRABR_POS=""
GRABL_POS=""
UNTAG_POS=""
BEH="ATTACK"

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------
for ARGI; do
    if [ "${ARGI}" = "--help" -o "${ARGI}" = "-h" ] ; then
        HELP="yes"
    elif [ "${ARGI//[^0-9]/}" = "$ARGI" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$ARGI
    elif [ "${ARGI}" = "--evan" -o "${ARGI}" = "-e" ] ; then
        M200_IP=192.168.5.1 #evan
        VNAME="evan"
        VPORT="9005"
        SHARE_LISTEN="9305"
        echo "EVAN vehicle selected."
    elif [ "${ARGI}" = "--felix" -o "${ARGI}" = "-f" ] ; then
        M200_IP=192.168.6.1 #felix
        VNAME="felix"
        VPORT="9006"
        SHARE_LISTEN="9306"
        echo "FELIX vehicle selected."
    elif [ "${ARGI}" = "--gus" -o "${ARGI}" = "-g" ] ; then
        M200_IP=192.168.7.1 #gus
        VNAME="gus"
        VPORT="9007"
        SHARE_LISTEN="9307"
        echo "GUS vehicle selected as HUNTER."
    elif [ "${ARGI}" = "--hal" -o "${ARGI}" = "-H" ] ; then
        M200_IP=192.168.8.1 #hal
        VNAME="hal"
	    VMODEL="M300"
        VPORT="9008"
        SHARE_LISTEN="9308"
        echo "HAL vehicle selected."
    elif [ "${ARGI}" = "--ida" -o "${ARGI}" = "-i" ] ; then
        M200_IP=192.168.9.1 #ida
        VNAME="ida"
	    VMODEL="M300"
        VPORT="9009"
        SHARE_LISTEN="9309"
        echo "IDA vehicle selected."
    elif [ "${ARGI}" = "--jing" -o "${ARGI}" = "-J" ] ; then
        M200_IP=192.168.10.1 #jing
        VNAME="jing"
	    VMODEL="M300"
        VPORT="9010"
        SHARE_LISTEN="9310"
        echo "JING vehicle selected."
    elif [ "${ARGI}" = "--just_build" -o "${ARGI}" = "-j" ] ; then
        JUST_BUILD="yes"
        echo "Just building files; no vehicle launch."
    elif [ "${ARGI}" = "--verbose" -o "${ARGI}" = "-v" ] ; then
        VERBOSE="-v" 
        echo "Excuting launch verbosly."
    elif [ "${ARGI}" = "--sim" -o "${ARGI}" = "-s" ] ; then
        SIM="SIM"
        echo "Simulation mode ON."
    elif [ "${ARGI}" = "--red" -o "${ARGI}" = "-r" ] ; then
        VTEAM="red"
        GRAB_POS="-58,-71"
        GRABR_POS="-46,-42"
        GRABL_POS="-29,-83"
        UNTAG_POS="50,-24"
        RETURN_POS="5,0"
        START_POS="50,-24,240"
        echo "Red team selected."
    elif [ "${ARGI}" = "--blue" -o "${ARGI}" = "-b" ] ; then
        VTEAM="blue"
        GRAB_POS="50,-24"
	    GRABR_POS="42,-55"
        GRABL_POS="19,-11"
        UNTAG_POS="-58,-71"
        RETURN_POS="5,0"
        START_POS="-58,-71,60"
        echo "Blue team selected."
    elif [ "${ARGI}" = "--DEFEND" ] ; then
        BEH="DEFEND"
    elif [ "${ARGI:0:10}" = "--start-x=" ] ; then
        START_POS_X="${ARGI#--start-x=*}"
    elif [ "${ARGI:0:10}" = "--start-y=" ] ; then
        START_POS_Y="${ARGI#--start-y=*}"
    elif [ "${ARGI:0:10}" = "--start-a=" ] ; then
        START_POS_A="${ARGI#--start-a=*}"
    else
        echo "Undefined argument:" $ARGI
        echo "Please use -h for help."
        exit 1
    fi
done

#-------------------------------------------------------
#  Part 2: Handle Ill-formed command-line arguments
#-------------------------------------------------------

if [ "${HELP}" = "yes" ]; then
    echo "$0 [SWITCHES]"
    echo "  --evan,       -e  : Evan vehicle."
    echo "  --felix,      -f  : Felix vehicle."
    echo "  --gus,        -g  : Gus vehicle."
    echo "  --hal,        -H  : Hal vehicle."
    echo "  --ida,        -i  : Ida vehicle."
    echo "  --jing,       -J  : Jing vehicle."
    echo "  --blue,       -b  : Blue team."
    echo "  --red,        -r  : Red team."
    echo "  --sim,        -s  : Simulation mode."
    echo "  --start-x=        : Start from x position (requires x y a)."
    echo "  --start-y=        : Start from y position (requires x y a)."
    echo "  --start-a=        : Start from angle (requires x y a)."
    echo "  --just_build, -j"
    echo "  --help, -h"
    exit 0;
fi

if [ -z $VNAME ]; then
    echo "No vehicle has been selected..."
    echo "Exiting."
    exit 2
fi

if [ -z $VTEAM ]; then
    echo "No team has been selected..."
    echo "Exiting."
    exit 3
fi

#-------------------------------------------------------
#  Part 3: Create the .moos and .bhv files.
#-------------------------------------------------------

if [[ -n $START_POS_X && (-n $START_POS_Y && -n $START_POS_A)]]; then
  START_POS="$START_POS_X,$START_POS_Y,$START_POS_A"
  echo "Starting from " $START_POS
elif [[ -z $START_POS_X && (-z $START_POS_Y && -z $START_POS_A) ]]; then
  echo "Starting from default postion: " $START_POS
else [[ -z $START_POS_X || (-z $START_POS_Y || -z $START_POS_A) ]]
  echo "When specifing a strating coordinate, all 3 should be specified (x,y,a)."
  echo "See help (-h)."
  exit 1
fi

echo "Assembling MOOS file targ_${VNAME}.moos"


nsplug meta_m200.moos targ_${VNAME}.moos -f \
    VNAME=$VNAME                 \
    VPORT=$VPORT                 \
    WARP=$TIME_WARP              \
    SHARE_LISTEN=$SHARE_LISTEN   \
    SHORE_LISTEN=$SHORE_LISTEN   \
    SHORE_IP=$SHORE_IP           \
    M200_IP=$M200_IP             \
    VMODEL=$VMODEL               \
    VTYPE="kayak"                \
    VTEAM=$VTEAM                 \
    START_POS=$START_POS         \
    $SIM

echo "Assembling BHV file targ_${VNAME}.bhv"
nsplug meta_m200.bhv targ_${VNAME}.bhv -f  \
    RETURN_POS=${RETURN_POS}    \
    VTEAM=$VTEAM                \
    VNAME=$VNAME                \
    GRAB_POS=$GRAB_POS          \
    GRABR_POS=$GRABR_POS        \
    GRABL_POS=$GRABL_POS        \
    UNTAG_POS=$UNTAG_POS        \
	FLAG=$START_POS             \
	BEH=$BEH


if [ ${JUST_BUILD} = "yes" ] ; then
    echo "Files assembled; vehicle not launched; exiting per request."
    exit 0
fi

#-------------------------------------------------------
#  Part 4: Launch the processes
#-------------------------------------------------------

echo "Launching $VNAME MOOS Community "
pAntler targ_${VNAME}.moos >& /dev/null &
uMAC targ_${VNAME}.moos

echo "Killing all processes ..."
kill -- -$$
echo "Done killing processes."
