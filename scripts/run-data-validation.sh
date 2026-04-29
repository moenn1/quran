#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

if [ -x data/validate.sh ] && is_tracked data/validate.sh; then
  data/validate.sh
  exit 0
fi

if [ -f tests/test_analyze_upstream_quran_sql.py ] && is_tracked tests/test_analyze_upstream_quran_sql.py; then
  if ! command -v pytest >/dev/null 2>&1; then
    echo "Pytest-based data validation exists, but pytest is not installed." >&2
    exit 1
  fi

  PYTHONPATH="${PWD}${PYTHONPATH:+:${PYTHONPATH}}" pytest tests/test_analyze_upstream_quran_sql.py
  exit 0
fi

if [ -f data/package.json ] && is_tracked data/package.json; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "Data npm validation target found in data, but npm is not installed." >&2
    exit 1
  fi

  (
    cd data
    npm test
  )
  exit 0
fi

if { [ -f data/pyproject.toml ] && is_tracked data/pyproject.toml; } || { [ -f data/requirements.txt ] && is_tracked data/requirements.txt; }; then
  if ! command -v pytest >/dev/null 2>&1; then
    echo "Data validation target found in data, but pytest is not installed." >&2
    exit 1
  fi

  (
    cd data
    pytest
  )
  exit 0
fi

echo "No data validation target found; skipping."
