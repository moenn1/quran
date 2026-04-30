#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

has_npm_script() {
  package_dir="$1"

  (
    cd "$package_dir"
    node -e '
const fs = require("fs");
const pkg = JSON.parse(fs.readFileSync("package.json", "utf8"));
process.exit(pkg.scripts && pkg.scripts["test:e2e"] ? 0 : 1);
'
  )
}

if [ -f package.json ] && is_tracked package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Root end-to-end test target found, but npm is not installed." >&2
    exit 1
  fi

  if has_npm_script .; then
    npm run test:e2e
    exit 0
  fi
fi

if [ -f apps/web/package.json ] && is_tracked apps/web/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Frontend end-to-end test target found in apps/web, but npm is not installed." >&2
    exit 1
  fi

  if has_npm_script apps/web; then
    (
    cd apps/web
      npm run test:e2e
    )
    exit 0
  fi
fi

echo "No end-to-end test target found; skipping."
