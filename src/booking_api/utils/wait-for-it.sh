#!/bin/bash

echo "trying to connect to db"

while ! nc -z postgres 5432; do
    sleep 5
    echo "still waiting for db ..."
done

echo "db launched"

# Apply database migrations
echo "Apply database migrations"
cd db/migrator && alembic upgrade head
cd ../..

exec "$@"
