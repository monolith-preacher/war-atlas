#!/bin/sh
# Waits for the database, applies migrations, optionally seeds and bootstraps an admin.
set -e
python -m app.cli wait-db --timeout 90
alembic upgrade head
if [ "${SEED_ON_START:-false}" = "true" ]; then
  python -m app.cli seed
fi
python -m app.cli bootstrap
exec "$@"
