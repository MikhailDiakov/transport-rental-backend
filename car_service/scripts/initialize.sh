#!/usr/bin/env bash

set -e
set -x

python app/db/backend_pre_start.py
alembic upgrade head