#!/usr/bin/env bash
# Read-only smoke check; accepts Compose options such as -p and --env-file.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
compose=(docker compose "$@" -f docker-compose.yml)
deadline=$((SECONDS + ${SMOKE_TIMEOUT_SECONDS:-120}))
for service in db backend frontend; do
    while true; do
        container=$("${compose[@]}" ps -q "$service")
        status='missing'
        if [[ -n "$container" ]]; then
            status=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container")
        fi
        [[ "$status" == healthy ]] && break
        if [[ "$status" == unhealthy || "$status" == exited || $SECONDS -ge $deadline ]]; then
            echo "Smoke failed: $service status=$status" >&2
            "${compose[@]}" ps -a
            exit 1
        fi
        sleep 1
    done
done
"${compose[@]}" exec -T backend python -c '
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from app.core.database import get_engine
with get_engine().connect() as connection:
    assert set(MigrationContext.configure(connection).get_current_heads()) == set(ScriptDirectory.from_config(Config("alembic.ini")).get_heads()), "Database migrations are not current"
'
backend_address=$("${compose[@]}" port backend 8000)
frontend_address=$("${compose[@]}" port frontend 5173)
python3 - "$backend_address" "$frontend_address" <<'PY'
import json
import sys
from urllib.request import urlopen
with urlopen(f'http://{sys.argv[1]}/health', timeout=5) as response:
    assert response.status == 200
    assert json.load(response) == {'status': 'ok'}
with urlopen(f'http://{sys.argv[2]}/', timeout=5) as response:
    assert response.status == 200
    assert 'id="root"' in response.read().decode()
print('Compose smoke: database, migrations, API and frontend OK')
PY
