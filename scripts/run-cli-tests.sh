#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)

choose_python() {
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    command -v python
    return 0
  fi

  return 1
}

if [ -f "$ROOT_DIR/apps/cli/pyproject.toml" ]; then
  if ! PYTHON_BIN=$(choose_python); then
    echo "CLI test target found in apps/cli, but no Python interpreter is available." >&2
    exit 1
  fi

  if ! "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
    echo "CLI test target found in apps/cli, but pytest is not installed for $PYTHON_BIN." >&2
    echo "Install CLI dev dependencies with: cd \"$ROOT_DIR\" && \"$PYTHON_BIN\" -m pip install -e 'apps/cli[dev]'" >&2
    exit 1
  fi

  if ! "$PYTHON_BIN" -c "import typer" >/dev/null 2>&1; then
    echo "CLI test target found in apps/cli, but Typer is not installed for $PYTHON_BIN." >&2
    echo "Install CLI dev dependencies with: cd \"$ROOT_DIR\" && \"$PYTHON_BIN\" -m pip install -e 'apps/cli[dev]'" >&2
    exit 1
  fi

  (
    cd "$ROOT_DIR/apps/cli"
    PYTHONPATH=src "$PYTHON_BIN" -m pytest
  )
  exit 0
fi

echo "No CLI test target found; skipping."
