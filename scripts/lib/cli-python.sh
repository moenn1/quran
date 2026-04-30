#!/bin/sh

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

print_cli_dev_install_hint() {
  python_bin="$1"
  echo "Install CLI dev dependencies with: cd \"$ROOT_DIR\" && \"$python_bin\" -m pip install -e 'apps/cli[dev]'" >&2
}
