#!/bin/sh
set -e

# Render gives postgresql://user:password@host/database, Spring Boot needs JDBC
address=${DATABASE_URL#*://}
credentials=${address%%@*}

export SPRING_DATASOURCE_URL="jdbc:postgresql://${address#*@}"
export SPRING_DATASOURCE_USERNAME="${credentials%%:*}"
export SPRING_DATASOURCE_PASSWORD="${credentials#*:}"
export SERVER_ADDRESS=0.0.0.0
export SERVER_PORT="${PORT:-8080}"

# The free plan has 512 MB of memory
exec java -Xmx300m -Xss256k -XX:+UseSerialGC -XX:TieredStopAtLevel=1 -jar app.jar
