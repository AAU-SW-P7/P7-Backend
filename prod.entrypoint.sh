#!/bin/sh
set -e

# Create PostgreSQL extensions first
python -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')
    cursor.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto;')
"

# Run migrations and collectstatic
python manage.py makemigrations repository
python manage.py migrate repository --noinput
python manage.py makemigrations
python manage.py migrate --noinput

# Start any background workers (django-q qcluster for example)
# These will be terminated via trap when the container gets a TERM signal
Q_CLUSTER_NAME=high python manage.py qcluster & Q1_PID=$!
Q_CLUSTER_NAME=low python manage.py qcluster & Q2_PID=$!

# Handle signals and forward to background processes
_term() {
  echo "Stopping background processes..."
  kill -TERM "$Q1_PID" "$Q2_PID" 2>/dev/null || true
  exit 0
}
trap _term TERM INT

# Exec the main cmd (gunicorn passed as CMD in Dockerfile)
exec "$@"