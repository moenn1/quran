#!/bin/sh

set -eu

assert_contains() {
  file="$1"
  text="$2"

  if ! grep -Fq "$text" "$file"; then
    echo "Workflow parity check failed for $file: missing $text" >&2
    exit 1
  fi
}

QUALITY_WORKFLOW=".github/workflows/quality.yml"
RELEASE_WORKFLOW=".github/workflows/release-readiness.yml"

assert_contains "$QUALITY_WORKFLOW" "./scripts/run-data-validation.sh"
assert_contains "$QUALITY_WORKFLOW" "apps/api[dev]"
assert_contains "$QUALITY_WORKFLOW" "./scripts/run-e2e.sh"
assert_contains "$QUALITY_WORKFLOW" "playwright install --with-deps chromium"

assert_contains "$RELEASE_WORKFLOW" "./scripts/release-readiness.sh"
assert_contains "$RELEASE_WORKFLOW" "apps/api[dev]"
assert_contains "$RELEASE_WORKFLOW" "playwright install --with-deps chromium"
