#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
API_DIR="$ROOT_DIR/apps/api"

choose_python() {
  if [ -x "$ROOT_DIR/.venv/bin/python" ]; then
    printf '%s\n' "$ROOT_DIR/.venv/bin/python"
    return 0
  fi

  if [ -x "$API_DIR/.venv/bin/python" ]; then
    printf '%s\n' "$API_DIR/.venv/bin/python"
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "python3"
    return 0
  fi

  return 1
}

print_backend_dev_install_hint() {
  python_bin="$1"
  echo "Install backend dev dependencies with:" >&2
  echo "  $python_bin -m pip install -e '$API_DIR[dev]'" >&2
}

if [ ! -f "$API_DIR/pyproject.toml" ]; then
  echo "No backend test target found; skipping."
  exit 0
fi

if ! PYTHON=$(choose_python); then
  echo "Backend test target found in apps/api, but no Python interpreter is available." >&2
  exit 1
fi

if ! "$PYTHON" -c "import pytest" >/dev/null 2>&1; then
  echo "Backend test target found in apps/api, but pytest is not installed for $PYTHON." >&2
  print_backend_dev_install_hint "$PYTHON"
  exit 1
fi

cd "$API_DIR"
"$PYTHON" -m pytest "$@"
