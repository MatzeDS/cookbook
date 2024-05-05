#!/bin/bash

BASEDIR="$(dirname "$(dirname "$(realpath "$0")")")"
cd "$BASEDIR/scripts"

docker compose down --volumes

./build_backend.sh
./build_frontend.sh

docker compose up -d

docker compose logs -f
