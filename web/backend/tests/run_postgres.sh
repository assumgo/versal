#!/usr/bin/env bash
# Full schema verification against an isolated PostgreSQL, never the app database.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
python_bin="${PYTHON_BIN:-.venv/bin/python}"
container_name="versal-schema-test-$$"
cleanup() { docker rm -f "$container_name" >/dev/null 2>&1 || true; }
trap cleanup EXIT

docker run --detach --name "$container_name" --tmpfs /var/lib/postgresql/data \
    -p 127.0.0.1::5432 -e POSTGRES_PASSWORD=versal-disposable-test \
    postgres:16-alpine >/dev/null
ready=false
for attempt in {1..30}; do
    if docker exec "$container_name" pg_isready -U postgres >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 1
done
if [[ "$ready" != true ]]; then
    docker logs "$container_name"
    exit 1
fi
port=$(docker port "$container_name" 5432/tcp)
export DATABASE_URL="postgresql+psycopg://postgres:versal-disposable-test@${port}/postgres"
export TEST_DATABASE_URL="$DATABASE_URL"
export JWT_SECRET_KEY=test-only-secret-with-at-least-32-characters
"$python_bin" -m alembic upgrade head
"$python_bin" -m pytest -q
"$python_bin" -m alembic check
"$python_bin" -m alembic downgrade base
"$python_bin" -c 'import os; from sqlalchemy import create_engine, inspect; e = create_engine(os.environ["DATABASE_URL"]); assert set(inspect(e).get_table_names()) == {"alembic_version"}; e.dispose()'
"$python_bin" -m alembic upgrade head
"$python_bin" -m alembic check
"$python_bin" -m pytest -q
