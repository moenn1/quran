#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

run_npm_cli_tests() {
  dir="$1"

  (
    cd "$dir"
    npm test
  )
}

run_python_cli_tests() {
  dir="$1"

  (
    cd "$dir"
    pytest
  )
}

for dir in apps/cli packages/cli
do
  if [ -f "$dir/package.json" ] && is_tracked "$dir/package.json"; then
    if ! command -v npm >/dev/null 2>&1; then
      echo "CLI npm test target found in $dir, but npm is not installed." >&2
      exit 1
    fi

    run_npm_cli_tests "$dir"
    exit 0
  fi

  if { [ -f "$dir/pyproject.toml" ] && is_tracked "$dir/pyproject.toml"; } || { [ -f "$dir/requirements.txt" ] && is_tracked "$dir/requirements.txt"; }; then
    if ! command -v pytest >/dev/null 2>&1; then
      echo "CLI test target found in $dir, but pytest is not installed." >&2
      exit 1
    fi

    run_python_cli_tests "$dir"
    exit 0
  fi
done

echo "No CLI test target found; skipping."
