#!/bin/bash

docker exec -w /app -it cookbook-backend-1 python scripts/admin.py "$@"
