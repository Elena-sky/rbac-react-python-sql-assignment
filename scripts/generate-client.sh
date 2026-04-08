#! /usr/bin/env bash

set -euo pipefail
set -x

# OpenAPI generation imports the backend app; backend settings require env vars.
# Provide safe defaults only for this script when env is missing (CI-friendly).
export PROJECT_NAME="${PROJECT_NAME:-RBAC Test App}"
export POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
export POSTGRES_PORT="${POSTGRES_PORT:-5432}"
export POSTGRES_DB="${POSTGRES_DB:-app}"
export POSTGRES_USER="${POSTGRES_USER:-postgres}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
export FIRST_SUPERUSER="${FIRST_SUPERUSER:-admin@example.com}"
export FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-changeme}"
export SECRET_KEY="${SECRET_KEY:-dev-secret-key}"

cd backend
uv run python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
bun run --filter frontend generate-client
bun run lint
