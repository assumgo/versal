# Repository Guidelines

## Project Structure & Module Organization

Versal Folha TXT is a payroll application being migrated to the web. The current foundation uses FastAPI, React/TypeScript/Vite, and PostgreSQL 16.

- `web/backend/app/`: API entry point, configuration/database helpers in `core/`, and SQLAlchemy models in `models/`.
- `web/backend/alembic/`: versioned database migrations.
- `web/backend/tests/`: pytest suites and legacy SQL fixtures.
- `web/frontend/src/`: React application; `index.html` is the frontend entry document.
- `web/docker-compose.yml`: local development stack.
- `docs/superpowers/`: design specifications and implementation plans. See `web/docs/legacy-schema-compatibility.md` for schema constraints.

## Build, Test, and Development Commands

Use Python 3.12+ and Node.js 24 for local development. Setup details are in `web/README.md`.

- From `web/`: copy `.env.example` to `.env`, configure secrets, then run `docker compose up --build -d` to start the stack. Frontend: port 5173; API: port 8000.
- From `web/backend/`: `.venv/bin/python -m pip install -r requirements.txt` installs dependencies; `.venv/bin/python -m uvicorn app.main:app --reload` runs the API.
- From `web/frontend/`: `npm ci`, then `npm run dev`; `npm run build` checks TypeScript and generates production assets.
- From `web/backend/`: `.venv/bin/python -m alembic upgrade head` applies migrations; `.venv/bin/python -m alembic check` detects model/schema drift.

## Coding Style & Naming Conventions

Follow existing files: Python uses four-space indentation, type annotations, and `snake_case` functions/modules. React/TypeScript uses two-space indentation, single quotes, semicolons, and PascalCase components. No dedicated formatter or linter is currently configured. Preserve legacy database names, identifiers, nullability, and numeric precision when changing models.

## Testing Guidelines

Run `.venv/bin/python -m pytest -q` from `web/backend/`. Use `test_*.py` files and descriptive `test_*` functions; async API tests use pytest-asyncio and HTTPX. PostgreSQL integration tests require `TEST_DATABASE_URL`; otherwise they skip. From the repository root, `bash web/backend/tests/run_postgres.sh` verifies migrations and tests against disposable PostgreSQL using Docker. Never target the operational database. No coverage threshold is configured.

## Commit & Pull Request Guidelines

History uses conventional prefixes: `feat:`, `fix:`, `docs:`, and `chore:` with concise imperative descriptions. PRs should explain behavior changes, link relevant issues or plans, and report validation commands/results. Include screenshots for UI changes and migration/compatibility details for schema changes.

## Security & Configuration

Keep `.env` files and credentials untracked. Use distinct database and JWT secrets; `JWT_SECRET_KEY` requires at least 32 characters. Treat all `VITE_*` variables as public.
