#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -f package.json ] && is_tracked package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Root end-to-end test target found, but npm is not installed." >&2
    exit 1
  fi

  if npm run | grep -Fq "test:e2e"; then
    npm run test:e2e
    exit 0
  fi
fi

if [ -f apps/web/package.json ] && is_tracked apps/web/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Frontend end-to-end test target found in apps/web, but npm is not installed." >&2
    exit 1
  fi

  (
    cd apps/web
    if npm run | grep -Fq "test:e2e"; then
      npm run test:e2e
      exit 0
    fi
  )
fi

echo "No end-to-end test target found; skipping."
