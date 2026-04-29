#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

if [ -f "$ROOT_DIR/apps/cli/pyproject.toml" ]; then
  if [ -x "$ROOT_DIR/.venv/bin/pytest" ]; then
    PYTEST_BIN="$ROOT_DIR/.venv/bin/pytest"
  elif command -v pytest >/dev/null 2>&1; then
    PYTEST_BIN=pytest
  else
    echo "CLI test target found in apps/cli, but pytest is not installed." >&2
    exit 1
  fi

  (
    cd "$ROOT_DIR/apps/cli"
    "$PYTEST_BIN"
  )
  exit 0
fi

echo "No CLI test target found; skipping."
