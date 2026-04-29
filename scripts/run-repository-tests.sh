#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -f tests/test_self_hosting_baseline.py ] && is_tracked tests/test_self_hosting_baseline.py; then
  python3 -m unittest discover -s tests -p 'test_self_hosting_baseline.py'
  exit 0
fi

echo "No repository test target found; skipping."
