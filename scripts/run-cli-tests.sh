#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -f packages/cli/package.json ] && is_tracked packages/cli/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "CLI npm test target found in packages/cli, but npm is not installed." >&2
    exit 1
  fi

  (
    cd packages/cli
    npm test
  )
  exit 0
fi

if { [ -f packages/cli/pyproject.toml ] && is_tracked packages/cli/pyproject.toml; } || { [ -f packages/cli/requirements.txt ] && is_tracked packages/cli/requirements.txt; }; then
  if ! command -v pytest >/dev/null 2>&1; then
    echo "CLI test target found in packages/cli, but pytest is not installed." >&2
    exit 1
  fi

  (
    cd packages/cli
    pytest
  )
  exit 0
fi

echo "No CLI test target found; skipping."
