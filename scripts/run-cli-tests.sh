#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
. "$ROOT_DIR/scripts/lib/cli-python.sh"

if [ -f "$ROOT_DIR/apps/cli/pyproject.toml" ]; then
  if ! PYTHON_BIN=$(choose_python); then
    echo "CLI test target found in apps/cli, but no Python interpreter is available." >&2
    exit 1
  fi

  if ! "$PYTHON_BIN" -c "import pytest" >/dev/null 2>&1; then
    echo "CLI test target found in apps/cli, but pytest is not installed for $PYTHON_BIN." >&2
    print_cli_dev_install_hint "$PYTHON_BIN"
    exit 1
  fi

  if ! "$PYTHON_BIN" -c "import typer" >/dev/null 2>&1; then
    echo "CLI test target found in apps/cli, but Typer is not installed for $PYTHON_BIN." >&2
    print_cli_dev_install_hint "$PYTHON_BIN"
    exit 1
  fi

  (
    cd "$ROOT_DIR/apps/cli"
    PYTHONPATH=src "$PYTHON_BIN" -m pytest
  )
  exit 0
fi

echo "No CLI test target found; skipping."
