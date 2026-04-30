#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
API_DIR="$ROOT_DIR/apps/api"
DATA_DIR="$API_DIR/.data"

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

if ! PYTHON=$(choose_python); then
  echo "QuranKit data validation requires a Python 3 interpreter." >&2
  exit 1
fi

if [ -f "$API_DIR/pyproject.toml" ]; then
  if ! "$PYTHON" -c "import qurankit_api" >/dev/null 2>&1; then
    echo "apps/api exists, but the active Python environment cannot import qurankit_api." >&2
    print_backend_dev_install_hint "$PYTHON"
    exit 1
  fi

  mkdir -p "$DATA_DIR"

  (
    cd "$API_DIR"
    "$PYTHON" -m qurankit_api.data.pipeline validate "$@"
  )
  exit 0
fi

if [ -f "$ROOT_DIR/tests/test_analyze_upstream_quran_sql.py" ]; then
  if ! "$PYTHON" -c "import pytest" >/dev/null 2>&1; then
    echo "Pytest-based data validation exists, but pytest is not installed for $PYTHON." >&2
    exit 1
  fi

  PYTHONPATH="$ROOT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
    "$PYTHON" -m pytest "$ROOT_DIR/tests/test_analyze_upstream_quran_sql.py" "$@"
  exit 0
fi

echo "No data validation target found; skipping."
