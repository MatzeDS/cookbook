#!/bin/bash

BASEDIR="$(dirname "$(dirname "$(realpath "$0")")")"
cd "$BASEDIR"

docker compose down
docker compose up -d

docker compose logs -f
