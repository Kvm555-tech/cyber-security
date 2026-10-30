#!/bin/sh
set -e

PG_BIN=$(ls -d /usr/lib/postgresql/*/bin)
PG_DATA=/tmp/pgdata
DB_PASSWORD=$(head -c 24 /dev/urandom | od -An -tx1 | tr -d ' \n')

"$PG_BIN/initdb" -D "$PG_DATA" -U postgres --auth-local=trust --auth-host=scram-sha-256 > /dev/null
"$PG_BIN/pg_ctl" -D "$PG_DATA" -w -o "-c listen_addresses=127.0.0.1 -k /tmp" start

"$PG_BIN/psql" -h /tmp -U postgres -q -c "CREATE ROLE cybershield LOGIN PASSWORD '$DB_PASSWORD';"
"$PG_BIN/psql" -h /tmp -U postgres -q -c "CREATE DATABASE cybershield OWNER cybershield;"

cd /app/ml-service
/app/venv/bin/python app.py &

cd /app
export SPRING_DATASOURCE_URL=jdbc:postgresql://127.0.0.1:5432/cybershield
export SPRING_DATASOURCE_PASSWORD="$DB_PASSWORD"
export SERVER_ADDRESS=0.0.0.0
export SERVER_PORT=7860

exec java -Xmx1g -jar app.jar
