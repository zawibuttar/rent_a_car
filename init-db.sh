#!/bin/bash
set -e

# Only create the rentacar database if it does not already exist.
# POSTGRES_DB=rentacar already creates the database during init.
if [ "$(psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='rentacar'")" != "1" ]; then
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
        CREATE DATABASE rentacar;
        GRANT ALL PRIVILEGES ON DATABASE rentacar TO $POSTGRES_USER;
EOSQL
fi
