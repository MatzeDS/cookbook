#!/bin/bash

BASEDIR="$(dirname "$(dirname "$(realpath "$0")")")"
cd "$BASEDIR/frontend"

docker buildx build -t matzeds/cookbook-frontend .
