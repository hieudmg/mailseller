#!/bin/sh
set -e

echo "Starting entrypoint: waiting for DB and Redis..."

# Hostnames used inside compose network
DB_HOST=${DB_HOST:-postgres}
DB_PORT=${DB_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

# Maximum wait time in seconds
MAX_WAIT=60
COUNTER=0

# wait for Postgres
echo "Waiting for postgres at $DB_HOST:$DB_PORT..."
until nc -z "$DB_HOST" "$DB_PORT"; do
  echo "Postgres not ready yet - sleeping 1s"
  sleep 1
  COUNTER=$((COUNTER + 1))
  if [ $COUNTER -ge $MAX_WAIT ]; then
    echo "ERROR: Postgres did not become ready within ${MAX_WAIT}s"
    exit 1
  fi
done

echo "Postgres is ready"

# Reset counter for Redis
COUNTER=0

# wait for Redis
echo "Waiting for redis at $REDIS_HOST:$REDIS_PORT..."
until nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  echo "Redis not ready yet - sleeping 1s"
  sleep 1
  COUNTER=$((COUNTER + 1))
  if [ $COUNTER -ge $MAX_WAIT ]; then
    echo "ERROR: Redis did not become ready within ${MAX_WAIT}s"
    exit 1
  fi
done

echo "Redis is ready"

echo "DATABASE_URL is set to: $DATABASE_URL"

# Run alembic migrations
if command -v alembic >/dev/null 2>&1; then
  echo "Running alembic migrations..."
  alembic upgrade head || { echo "ERROR: Alembic migrations failed"; exit 1; }
else
  echo "WARNING: Alembic not installed in container. Skipping migrations."
fi

# Start the app
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
