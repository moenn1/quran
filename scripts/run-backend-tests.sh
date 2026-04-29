#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -f apps/api/package.json ] && is_tracked apps/api/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Backend npm test target found in apps/api, but npm is not installed." >&2
    exit 1
  fi

  (
    cd apps/api
    npm test
  )
  exit 0
fi

if { [ -f apps/api/pyproject.toml ] && is_tracked apps/api/pyproject.toml; } || { [ -f apps/api/requirements.txt ] && is_tracked apps/api/requirements.txt; }; then
  if ! command -v pytest >/dev/null 2>&1; then
    echo "Backend test target found in apps/api, but pytest is not installed." >&2
    exit 1
  fi

  (
    cd apps/api
    pytest
  )
  exit 0
fi

echo "No backend test target found; skipping."
