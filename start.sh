#!/bin/bash
set -e

echo "Starting Inventory Service"

APP_DIR="/app"
cd "$APP_DIR"

if [ -f .env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" =~ ^[[:space:]]*$ ]] && continue
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
      key="${BASH_REMATCH[1]}"
      value="${BASH_REMATCH[2]}"
      value="${value#\'}"; value="${value%\'}"
      value="${value#\"}"; value="${value%\"}"
      if [[ -z "${!key:-}" ]]; then
        export "$key=$value"
      fi
    fi
  done < .env
fi

PYTHON=$(command -v python3 || command -v python)

echo "Checking migration state..."
$PYTHON check_and_fix_migrations.py || echo "Migration check skipped"

echo "Running migrations..."
if ! $PYTHON manage.py migrate --noinput; then
  echo "ERROR: Migration failed! Check logs above for details."
  echo "Container will exit to prevent restart loop."
  echo "Fix the migration issues in the code and redeploy."
  exit 1
fi

echo "Collecting static files..."
$PYTHON manage.py collectstatic --noinput

echo "Creating superuser..."
if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_EMAIL:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
  $PYTHON manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" || echo "Superuser already exists or creation failed"
else
  echo "Skipping superuser creation - environment variables not set (DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL, DJANGO_SUPERUSER_PASSWORD)"
fi

echo "Starting Gunicorn..."
exec gunicorn inventory_service.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${WORKERS:-2} \
    --timeout 120
