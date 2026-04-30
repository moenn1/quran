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
  echo "python3 is required to build QuranKit data artifacts." >&2
  exit 1
fi

mkdir -p "$DATA_DIR"

cd "$API_DIR"
"$PYTHON" -m qurankit_api.data.pipeline build "$@"
