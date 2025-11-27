#!/usr/bin/env bash
# Create the dtp user and database

source "$(git rev-parse --show-toplevel)/env/timescaledb.env"

docker exec postgres-timescaledb psql -U postgres -c \
    "CREATE USER ${USER_NAME};" || true
docker exec postgres-timescaledb psql -U postgres -c \
    "ALTER USER ${USER_NAME} WITH PASSWORD '${USER_PASSWORD}';"
docker exec postgres-timescaledb psql -U postgres -c \
    "CREATE DATABASE ${USER_DB} WITH OWNER ${USER_NAME};" || true
docker exec postgres-timescaledb psql -U postgres -c \
    "GRANT ALL ON DATABASE ${USER_DB} TO $USER_NAME;"
