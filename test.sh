#!/usr/bin/env bash

echo "Passing the following to ctest: $@"

cd "build" && ctest "$@"