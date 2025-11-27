#!/usr/bin/env bash
# Create the dtp user and database

source "$(git rev-parse --show-toplevel)/.env"

docker exec postgres-timescaledb psql -U postgres -c \
    "CREATE USER ${PG_USER};" || true
docker exec postgres-timescaledb psql -U postgres -c \
    "ALTER USER ${PG_USER} WITH PASSWORD '${PG_USER_PASSWORD}';"
docker exec postgres-timescaledb psql -U postgres -c \
    "CREATE DATABASE ${PG_DB} WITH OWNER ${PG_USER};" || true
docker exec postgres-timescaledb psql -U postgres -c \
    "GRANT ALL ON DATABASE ${PG_DB} TO $PG_USER;"
