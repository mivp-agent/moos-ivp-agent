#!/usr/bin/env bash

printf "Killing XQuartz...\n"
killall Xquartz

set -e

printf "\nRestarting XQuartz...\n"
xhost +
printf "\nDone."