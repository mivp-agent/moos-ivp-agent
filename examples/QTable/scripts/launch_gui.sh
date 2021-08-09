#!/usr/bin/env bash
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

cd ../mission
./launch_full.sh 4

cd $PREVIOUS_WD