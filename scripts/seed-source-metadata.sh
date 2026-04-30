#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
API_DIR="$ROOT_DIR/apps/api"
DATA_DIR="$API_DIR/.data"

if [ ! -d "$API_DIR" ]; then
  echo "apps/api is missing." >&2
  exit 1
fi

if [ -x "$API_DIR/.venv/bin/python" ]; then
  PYTHON="$API_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  echo "python3 is required to seed source metadata." >&2
  exit 1
fi

if [ -z "${QURANKIT_DATABASE_URL:-}" ]; then
  mkdir -p "$DATA_DIR"
  export QURANKIT_DATABASE_URL="sqlite+pysqlite:///$DATA_DIR/qurankit.db"
fi

cd "$API_DIR"
"$PYTHON" -m qurankit_api.db.seed "$@"
