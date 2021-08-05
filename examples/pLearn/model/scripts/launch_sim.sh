#!/usr/bin/env bash
PREVIOUS_WD="$(pwd)"
DIRNAME="$(dirname $0)"
cd $DIRNAME

cd ../../mission
./launch_full.sh --no_gui --deploy 15

cd $PREVIOUS_WD