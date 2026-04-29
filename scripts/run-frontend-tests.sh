#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -f apps/web/package.json ] && is_tracked apps/web/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Frontend npm test target found in apps/web, but npm is not installed." >&2
    exit 1
  fi

  (
    cd apps/web
    npm test
  )
  exit 0
fi

echo "No frontend test target found; skipping."
