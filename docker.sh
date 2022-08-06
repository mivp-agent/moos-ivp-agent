#!/usr/bin/env bash

# Cd to dir to make paths uniform
DIRNAME="$(dirname $0)"
cd $DIRNAME

# Make sure script exits if sub commands fail
set -e

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

# Define names or tags to use when testing / normal operation
NAME="mivp-agent"
if [[ -n "$2" ]]; then
    printf "Settting name to $2...\n"
    NAME="$2"
fi
TEST_NAME="$NAME-testing"

function prompt(){
    if [[ "$1" == "" ]]; then
        echo "Echo: prompt function reruires a prompt provided as the first argument"
    fi
    
    if [[ "$2" == "0" || "$2" == "" ]]; then
        printf "$1 [Y/n]: "
    elif [[ "$2" == "1" ]]; then
        printf "$1 [y/N]: "
    else
        echo "Error: prompt function requires either '0', '1', or '' as the second argument"
        exit 1
    fi

    read response

    case $response in
        "Y"|"y"|"yes")
            return 0
            ;;
        "N"|"n"|"no")
            return 1
            ;;
        "")
            return $2
            ;;
        *)
            echo "You must respond with either Y or N" >&2
            prompt "$1" "$2"
            return $?
            ;;
       esac
}

require_image(){
    if [[ "$(docker images -q $NAME)" == "" ]]; then
        printf "Error: Unable to find docker image with tag \"$NAME\".\n\n"
        printf "Maybe run ./docker.sh build to build it?\n"
        exit 1;
    fi
}

require_no_container(){
    if [[ "$(docker ps -a | grep $1)" != "" ]]; then
        printf "Error: Existing container with name \"$1\".\n"
        exit 1;
    fi
}

do_run(){
    if [[ "$1" == "" || "$2" == "" ]]; then
        printf "Error: do_run should be called with two arguments\n"
        exit 1
    fi
    if [[ "$OS_TYPE" == "osx" ]]; then
        docker run --env="DISPLAY=host.docker.internal:0" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
            --mount type=bind,source="$(pwd)"/missions,target=/home/moos/moos-ivp-agent/missions \
            --mount type=bind,source="$(pwd)"/src,target=/home/moos/moos-ivp-agent/src \
            --mount type=bind,source="$(pwd)"/examples,target=/home/moos/moos-ivp-agent/examples \
            --workdir="/home/moos/moos-ivp-agent" \
            --name "$2" "-it$3" "$1:1.0" bash
    elif [[ "$OS_TYPE" == "linux" ]]; then
        docker run --env="DISPLAY" \
            --volume="/tmp/.X11-unix:/tmp/.X11-unix" \
            --mount type=bind,source="$(pwd)"/missions,target=/home/moos/moos-ivp-agent/missions \
            --mount type=bind,source="$(pwd)"/src,target=/home/moos/moos-ivp-agent/src \
            --mount type=bind,source="$(pwd)"/examples,target=/home/moos/moos-ivp-agent/examples \
            --workdir="/home/moos/moos-ivp-agent" \
	        --user "$(id -u):$(id -g)" \
            --name "$2" "-it$3" "$1:1.0" bash 
    fi

    # Return status from `docker run` command
    return $?
}

count_running(){
    if [[ "$1" == "" ]]; then
        printf "Error: count_running should be called with one argument\n"
        exit 1
    fi
    
    ps_line_count=$(docker ps --no-trunc --filter "name=$1" | wc -l)
    
    # The number of containers is the line count minus one (for the header line)
    echo $(($ps_line_count-1))
}

count_all(){
    if [[ "$1" == "" ]]; then
        printf "Error: count_all should be called with one argument\n"
        exit 1
    fi
    
    ps_line_count=$(docker ps -a --no-trunc --filter "name=$1" | wc -l)
    
    # The number of containers is the line count minus one (for the header line)
    echo $(($ps_line_count-1))
}

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
    if [[ "$OS_TYPE" == "osx" ]]; then
        docker build -t "$NAME:1.0" \
            --build-arg USER_ID=1001 \
            --build-arg GROUP_ID=1001 .
    elif [[ "$OS_TYPE" == "linux" ]]; then
        docker build -t "$NAME:1.0" \
            --build-arg USER_ID=$(id -u) \
            --build-arg GROUP_ID=$(id -g) .
    fi
elif [[ "$1" == "run" ]]; then
    # Make sure an image has been build
    require_image

    # Check for running containers and prompt for removal
    running=$(count_running $NAME)
    if [[ "$running" -gt "0" ]]; then
        pmpt="Found running containers named $NAME!\n"
        pmpt+="\nTo start a new container there must be no existing containers with the same name.\n"
        pmpt+="\nWARNING: Stopping containers while running is dangerous. Make sure you have all process stopped and data saved.\n"
        pmpt+="\nWould you like you to stop the running container AND remove it?"

        # Allow prompt to return non zero response
        set +e
        prompt "$pmpt" 1
        rsp=$?
        set -e

        if [[ "$rsp" == "1" ]]; then
            echo "Exiting..."
            exit 1
        else
            docker stop "$NAME"
            docker rm "$NAME"
        fi
    else
        # Check for stopped containers and prompt for removal
        stopped="$(count_all $NAME)"

        if [[ "$stopped" -gt "0" ]]; then
            set +e
            prompt "Remove stopped container named $NAME?" 0
            rsp=$?

            if [[ "$rsp" == "1" ]]; then
                echo "Exiting..."
                exit 1
            else
                docker rm "$NAME"
            fi
        fi
    fi

    printf "Enabling xhost server...\n"
    xhost +
    printf "Starting docker container...\n"
    printf "\n==========================================\n"
    printf "= To exit and stop: run command \"exit\"   =\n"
    printf "= To detach: CTRL+p CTRL+q               =\n"
    printf "==========================================\n\n"

    do_run $NAME $NAME
    
    printf "WARNING: Docker container can run in background unless stopped\n"
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
elif [[ "$1" == "test" ]]; then
    require_image
    require_no_container $TEST_NAME

    printf "Starting container for testing...\n"
    do_run $NAME $TEST_NAME "d" > /dev/null
    printf "Running tests with docker container...\n"
    # Prevent failure for exiting script
    set +e

    test_clean_up(){
        # Reset -e
        set -e
 
        printf "Cleaning up test container...\n"
        docker stop "$TEST_NAME" > /dev/null
        docker rm "$TEST_NAME" > /dev/null
    }

    fail_test(){
        printf "====================================\n"
        printf " Failed \"$1\" tests\n"
        printf "====================================\n"
        test_clean_up
        exit 1
    }

    # Run environment tests
    printf "====================================\n"
    printf "             Environment            \n"
    printf "====================================\n"
    docker exec -i $TEST_NAME bash -c "./test/test_environment.sh" || fail_test "Environment"
    
    # Run C++ tests
    printf "====================================\n"
    printf "                C++                 \n"
    printf "====================================\n"
    docker exec -i $TEST_NAME bash -c "cd build && ctest --verbose; exit $?" || fail_test "C++"

    # Run python tests
    printf "====================================\n"
    printf "               Python               \n"
    printf "====================================\n"
    docker exec -i $TEST_NAME bash -c "cd src/python_module/test && ./test_all.py" || fail_test "Python"

    # Function for testing linkings
    printf "====================================\n"
    printf "            File Stystem            \n"
    printf "====================================\n"
    test_links(){
        echo "Testing links between docker files and host machine files in directory $1..."
        [[ "$1" == "" ]] && printf "Internal error!" && fail_test "File System" 

        testing_file="__docker_script_testing__"
        [[ -f "$1/$testing_file" ]] && echo "Internal Error! Testing file already exists in $1." && fail_test "File System";

        # Create file in docker container make sure it shows on host machine
        docker exec -i $TEST_NAME bash -c "touch $1/$testing_file"
        if [[ "$?" != "0" ]]; then
            echo "Failed to create testing file named $testing_file in path $1. This can indicate improper permissions for the default docker user"
            fail_test "File System" 
        fi

        if [[ ! -f "$1/$testing_file" ]]; then
            echo "Testing file in directory $1 failed to show up on the host machine. Check the volume mounting of the docker container."
            # Don't need to cleanup $testing_file here b/c it won't have made it to the host machine so wont persist
            fail_test "File System" 
        fi

        docker exec -i $TEST_NAME bash -c "rm $1/$testing_file"
        if [[ "$?" != "0" ]]; then
            echo "Failed to remove testing file named $testing_file in path $1. This can indicate improper permissions for the default docker user"
            fail_test "File System" 
        fi
    }

    test_links "examples"
    test_links "src"
    test_links "missions"

    # Still need to clean up if no failures
    test_clean_up

    # Display results and exit
    EXIT="0"
elif [[ "$1" == "clean" ]]; then
    # Following run in sub shell so -e doesn't catch it
    NO_FAIL="$(docker stop $NAME)"
    NO_FAIL="$(docker rm $NAME)"
else
    printf "Error: Unrecognized argument\n"
    exit;
fi
