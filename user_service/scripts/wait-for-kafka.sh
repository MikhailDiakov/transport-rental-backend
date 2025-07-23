#!/usr/bin/env bash
set -e

host="$1"
port="$2"

echo "Waiting for $host:$port..."

while ! (exec 3<>/dev/tcp/$host/$port) 2>/dev/null; do
  echo "$host:$port is unavailable - sleeping"
  sleep 2
done

echo "$host:$port is up!"
