#!/usr/bin/env bash

# Cd to dir to make paths uniform
DIRNAME="$(dirname $0)"
cd $DIRNAME

# Test OS type for use letter
OS_TYPE="UNSET"

if [ "$(uname)" == "Linux" ]; then
    OS_TYPE="linux"
elif [ "$(uname)" == "Darwin" ]; then
    OS_TYPE="osx"
else
    printf "ERROR: Unable to determine OS type.\n"
    exit 1
fi

NAME="mivp-agent"
if [[ -n "$2" ]]; then
    printf "Settting name to $2...\n"
    NAME="$2"
fi

# Handle arguments
if [[ -z "$1" ]] || [[ "$1" = "help" ]] || [[ "$1" = "--help" ]] || [[ "$1" = "-h" ]]; then
    printf "Usage: %s <COMMAND>\n" $0
    printf "Commands:\n"
    printf "\t build   - Build docker container and tag as \"mivp-agent\"\n"
    printf "\t run     - Run a docker container from image tagged as \"mivp-agent\"\n"
    printf "\t stop    - Stops a docker container from image tagged as \"mivp-agent\"\n"
    printf "\t rm      - Removes a docker container from image tagged as \"mivp-agent\"\n"
    printf "\t connect - Connect to the docker containertagged ad \"mivp-agent\"\n"
    exit 0;
elif [[ "$1" == "build" ]]; then
    printf "Building mivp_agent container...\n"
    docker build -t "$NAME:1.0" \
	    --build-arg USER_ID=$(id -u) \
	    --build-arg GROUP_ID=$(id -g) .
elif [[ "$1" == "run" ]]; then
    printf "Enabling xhost server...\n"
    xhost +
    printf "Starting docker container...\n"
    printf "\n==========================================\n"
    printf "= To exit and stop: run command \"exit\"   =\n"
    printf "= To detach: CTRL+p CTRL+q               =\n"
    printf "==========================================\n\n"

    if [[ "$OS_TYPE" == "osx" ]]; then
        docker run --env="DISPLAY=host.docker.internal:0" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
            --mount type=bind,source="$(pwd)"/missions,target=/home/moos/moos-ivp-agent/missions \
            --mount type=bind,source="$(pwd)"/src,target=/home/moos/moos-ivp-agent/src \
            --mount type=bind,source="$(pwd)"/examples,target=/home/moos/moos-ivp-agent/examples \
            --workdir="/home/moos/moos-ivp-agent" \
            --name "$NAME" -it "$NAME:1.0" bash
    elif [[ "$OS_TYPE" == "linux" ]]; then
        docker run --env="DISPLAY" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
            --mount type=bind,source="$(pwd)"/missions,target=/home/moos/moos-ivp-agent/missions \
            --mount type=bind,source="$(pwd)"/src,target=/home/moos/moos-ivp-agent/src \
            --mount type=bind,source="$(pwd)"/examples,target=/home/moos/moos-ivp-agent/examples \
            --workdir="/home/moos/moos-ivp-agent" \
	    --user "$(id -u):$(id -g)" \
            --name "$NAME" -it "$NAME:1.0" bash 
    fi
    printf "WARNING: Docker container will run in background unless stopped\n"
elif [[ "$1" == "connect" ]]; then
    printf "Conecting to docker container...\n"
    printf "\n==========================================\n"
    printf "= To detach: CTRL+p CTRL+q               =\n"
    printf "==========================================\n\n"
    docker exec -it "$NAME" bash
elif [[ "$1" == "stop" ]]; then
    printf "Stopping docker container...\n"
    docker stop "$NAME"
elif [[ "$1" == "rm" ]]; then
    printf "Deleting docker container...\n"
    docker rm "$NAME"
else
    printf "Error: Unrecognized argument\n"
    exit;
fi
