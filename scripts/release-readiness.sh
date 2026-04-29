#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

./scripts/lint-repo.sh
./scripts/check-docs.sh
./scripts/run-repository-tests.sh

if [ -f package.json ] && is_tracked package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Tracked JavaScript workspace detected, but npm is not installed." >&2
    exit 1
  fi

  npm run lint
  npm run build
fi

./scripts/run-backend-tests.sh
./scripts/run-frontend-tests.sh
./scripts/run-cli-tests.sh
./scripts/run-data-validation.sh
./scripts/run-e2e.sh

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is not installed; skipping Docker Compose and image validation."
  exit 0
fi

docker compose -f compose.yaml config >/dev/null
docker build -f docker/api.Dockerfile . >/dev/null
docker build -f docker/web.Dockerfile . >/dev/null
./scripts/smoke-compose.sh
