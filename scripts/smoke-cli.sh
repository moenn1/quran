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

if [ ! -f "$ROOT_DIR/apps/cli/pyproject.toml" ]; then
  echo "No CLI smoke target found; skipping."
  exit 0
fi

if ! PYTHON_BIN=$(choose_python); then
  echo "CLI smoke target found in apps/cli, but no Python interpreter is available." >&2
  exit 1
fi

if ! "$PYTHON_BIN" -c "import qurankit, typer" >/dev/null 2>&1; then
  echo "CLI smoke target found in apps/cli, but the active Python environment is missing Qurankit or Typer." >&2
  echo "Install CLI dev dependencies with: cd \"$ROOT_DIR\" && \"$PYTHON_BIN\" -m pip install -e 'apps/cli[dev]'" >&2
  exit 1
fi

CLI_BIN="$(dirname "$PYTHON_BIN")/qurankit"
if [ ! -x "$CLI_BIN" ]; then
  echo "CLI smoke target found in apps/cli, but the qurankit console script is not installed for $PYTHON_BIN." >&2
  echo "Install CLI dev dependencies with: cd \"$ROOT_DIR\" && \"$PYTHON_BIN\" -m pip install -e 'apps/cli[dev]'" >&2
  exit 1
fi

SMOKE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/qurankit-cli-smoke.XXXXXX")
cleanup() {
  rm -rf "$SMOKE_DIR"
}
trap cleanup EXIT INT TERM

export QURANKIT_CONFIG_HOME="$SMOKE_DIR/config"
export QURANKIT_DATA_HOME="$SMOKE_DIR/data"

EXPECTED_VERSION=$("$PYTHON_BIN" -c "import qurankit; print(qurankit.__version__)")
ACTUAL_VERSION=$("$CLI_BIN" --version)
if [ "$ACTUAL_VERSION" != "$EXPECTED_VERSION" ]; then
  echo "qurankit --version returned '$ACTUAL_VERSION', expected '$EXPECTED_VERSION'." >&2
  exit 1
fi

REMOTE_PAYLOAD=$("$CLI_BIN" config show --format json)
printf '%s' "$REMOTE_PAYLOAD" | "$PYTHON_BIN" -c '
import json
import os
import sys
from pathlib import Path

payload = json.load(sys.stdin)
expected_db = str(
    (Path(os.environ["QURANKIT_DATA_HOME"]).expanduser() / "qurankit.sqlite3").resolve(
        strict=False
    )
)
assert payload["mode"] == "remote", payload
assert payload["api_url"] == "http://localhost:8000", payload
assert payload["backend_kind"] == "remote", payload
assert str(Path(payload["db_path"]).expanduser().resolve(strict=False)) == expected_db, payload
'

"$CLI_BIN" config set mode local >/dev/null
"$CLI_BIN" config set db-path "$SMOKE_DIR/library.sqlite3" >/dev/null

LOCAL_PAYLOAD=$("$CLI_BIN" config show --format json)
printf '%s' "$LOCAL_PAYLOAD" | "$PYTHON_BIN" -c '
import json
import os
import sys
from pathlib import Path

payload = json.load(sys.stdin)
config_file = str(
    (Path(os.environ["QURANKIT_CONFIG_HOME"]).expanduser() / "config.json").resolve(
        strict=False
    )
)
assert payload["mode"] == "local", payload
assert payload["backend_kind"] == "local", payload
assert payload["db_path"].endswith("library.sqlite3"), payload
assert str(Path(payload["config_file"]).expanduser().resolve(strict=False)) == config_file, payload
assert payload["db_exists"] is False, payload
'
