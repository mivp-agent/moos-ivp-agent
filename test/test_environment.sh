#!/usr/bin/env bash

help(){
  printf "Usage: $0 <python_executable>\n"
}

PYTHON="python3"
if [[ "$1" != "" ]]; then
  if [[ "$(which $1)" == "" ]]; then
    printf "Error: Could not verify python executable\n"
    printf "\n"
    help
    exit 1
  fi
  PYTHON="$1"
fi 

require_exe(){
  printf "Looking for a executable named \"$1\"..."
  if [[ "$(which $1)" == "" ]]; then
    printf "Error: Unable to find executable \"$1\"\n"

    if [[ "$2" != "" ]]; then
      printf "\n$2\n"
    fi
    exit 1
  fi
}

require_module(){
  printf "Looking for a module named \"$1\"..."
  $PYTHON -c "import $1" 2>&1 /dev/null
  if [[ "$?" != "0" ]]; then
    printf "Error: Unable to find python module \"$1\"\n"
    
    if [[ "$2" != "" ]]; then
      printf "\n$2\n\n"
    fi

    printf "This could be an issue with the python interpreter version see below the usage.\n"
    help
    exit 1
  fi
}

# Check for executables from each package
require_exe pAntler "Please check your MOOS installation and that the MOOS/bin paths have been added to your \$PATH variable"
require_exe pMarineViewer "Please check your MOOS-IvP installation and that the moos-ivp/bin directory has been added to your \$PATH variable"

require_exe pNodeReportParse "Please check your moos-ivp-aquaticus installation and that the moos-ivp-aquaticus/bin directory has been added to your \$PATH variable"

require_exe pEpisodeManager "Please make sure you have built moos-ivp-agent and added the moos-ivp-agent/bin directory to your \$PATH variable"

require_exe agnt "Please make sure you have installed the mivp_agent python package."

require_module mivp_agent "Please make sure you have installed the mivp_agent for the current python interpreter $(which $PYTHON)."