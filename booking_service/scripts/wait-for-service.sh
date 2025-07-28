#!/usr/bin/env bash
set -e

host="$1"
port="$2"

echo "Waiting for $host:$port..."

until curl -sSf "http://$host:$port" > /dev/null; do
  echo "$host is unavailable - sleeping"
  sleep 2
done

echo "$host is up!"
exit 0
