#!/bin/bash

# Standard MOOS-IvP vars
TIME_WARP=1
SHORE_IP=localhost
SHORE_LISTEN="9300"
SHARE_LISTEN=""
VPORT=""
VNAME=""

HELP="no"
JUST_BUILD="no"

# Aquaticus specific
START_POS=""
VTEAM=""
OWN_FLAG=""
ENEMY_FLAG=""
GRABR_POS=""
GRABL_POS=""
BEHAVIOR="DEFEND"

# MOOS-IvP-Agent specific
ROLE=""
ID=""
COLOR="green"
LOGGING="no"

function help(){
    echo ""
    echo "USAGE: $0 <team> <role> <id> [SWITCHES]"

    echo ""
    echo "POSSIBLE ROLES:"
    echo "  red,          r  : Red team."
    echo "  blue,         b  : Blue team."

    echo ""
    echo "POSSIBLE ROLES:"
    echo "  agent,        a  : Vehicle running behavior of interest."
    echo "  drone,        d  : Vehicle running supporting behavior."
    echo "                For example, a behavior to train against."

    echo ""
    echo "POSSIBLE IDs: [11,99]"

    echo ""
    echo "POSSIBLE SWITCHES:"
    echo "  --just_build, -J      : Just build targ files."
    echo "  --help,       -H      : Display this message."
    echo "  --behavior=<behavior> : Set the vehicle's color"
    echo "  --color=<some_color>  : Set the vehicle's color"
    exit 0
}

#-------------------------------------------------------
#  Part 1: Check for and handle command-line arguments
#-------------------------------------------------------

# Handle teams
case "$1" in
    red|r)
        VTEAM="red"
        echo "Vehicle added to red team."
        ;;
    blue|b)
        VTEAM="blue"
        echo "Vehicle added to blue team."
        ;;
    *)
        echo "!!! ERROR: expected team assignment got: $1 !!!"
        help
        ;;
esac

if [ "${VTEAM}" = "red" ]; then
    MY_FLAG="50,-24"
    START_POS="50,-24,240"
    ENEMY_FLAG="-52,-70"

    GRABR_POS="-46,-42"
    GRABL_POS="-29,-83"
elif [ "${VTEAM}" = "blue" ]; then
    MY_FLAG="-52,-70"
    START_POS="-52,-70,60"
    ENEMY_FLAG="50,-24"

    GRABR_POS="42,-55"
    GRABL_POS="19,-11"
fi

# Handle role assigment
case "$2" in
    agent|a)
        ROLE="agent"
        BEHAVIOR="AGENT"
        echo "Vehicle set as an agent."
        ;;
    drone|d)
        ROLE="drone"
        echo "Vehicle set as a drone"
        ;;
    *)
        echo "!!! ERROR: expected role assignment got: $2 !!!"
        help
        ;;
esac

if [[ "$3" =~ ^-?[0-9]+$ ]] && [[ "$3" -ge 11 ]] && [[ "$3" -le 99 ]]; then
    ID="$3"
    SHARE_LISTEN="93${ID}"
    VPORT="93${ID}"
else
    help
fi

# Set VNAME based on role and id
VNAME="${ROLE}_${ID}"

echo "hi"

for arg in "${@:4}"; do
    if [ "${arg}" = "--help" -o "${arg}" = "-H" ]; then
        help
    elif [ "${arg//[^0-9]/}" = "$arg" -a "$TIME_WARP" = 1 ]; then
        TIME_WARP=$arg
        echo "Time warp set to: " $arg
    elif [ "${arg}" = "--just_build" -o "${arg}" = "-J" ] ; then
        JUST_BUILD="yes"
        echo "Just building files; no vehicle launch."
    elif [ "${arg}" = "--log" ] ; then
        LOGGING="yes"
    elif [ "${arg:0:8}" = "--color=" ]; then
        COLOR="${arg#--color=*}"
    elif [ "${arg:0:11}" = "--behavior=" ]; then
        BEHAVIOR="${arg#--behavior=*}"
    else
        echo "Undefined switch:" $arg
        help
    fi
done

#-------------------------------------------------------
#  Part 2: Create the .moos and .bhv files.
#-------------------------------------------------------

echo "Assembling MOOS file targ_${VNAME}.moos"
nsplug meta_heron.moos targ_${VNAME}.moos -f \
    SHORE_IP=$SHORE_IP           \
    SHORE_LISTEN=$SHORE_LISTEN   \
    SHARE_LISTEN=$SHARE_LISTEN   \
    VPORT=$VPORT                 \
    VNAME=$VNAME                 \
    WARP=$TIME_WARP              \
    VTYPE="kayak"                \
    VTEAM=$VTEAM                 \
    START_POS=$START_POS         \
    COLOR=$COLOR                 \
    LOGGING=$LOGGING             \
    ROLE=$ROLE                   \

echo "Assembling BHV file targ_${VNAME}.bhv"
nsplug meta_heron.bhv targ_${VNAME}.bhv -f  \
        VTEAM=$VTEAM                        \
        VNAME=$VNAME                        \
        ROLE=$ROLE                          \
        MY_FLAG=$MY_FLAG                    \
        ENEMY_FLAG=$ENEMY_FLAG              \
        GRABR_POS=$GRABR_POS                \
        GRABL_POS=$GRABL_POS                \
	    BEHAVIOR=$BEHAVIOR


if [ ${JUST_BUILD} = "yes" ] ; then
    echo "Files assembled; vehicle not launched; exiting per request."
    exit 0
fi

#-------------------------------------------------------
#  Part 3: Launch the processes
#-------------------------------------------------------

echo "Launching $VNAME MOOS Community "
pAntler targ_${VNAME}.moos >& /dev/null &

uMAC targ_${VNAME}.moos

echo "Killing all processes ..."
kill -- -$$
echo "Done killing processes."
