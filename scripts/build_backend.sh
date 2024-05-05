#!/bin/bash

BASEDIR="$(dirname "$(dirname "$(realpath "$0")")")"
cd "$BASEDIR/backend"

docker buildx build -t matzeds/cookbook-backend .
