#!/bin/sh

set -eu

sh -n scripts/*.sh
python3 -m py_compile docker/api/bootstrap-api.py
if [ -f scripts/analyze_upstream_quran_sql.py ]; then
  python3 -m py_compile scripts/analyze_upstream_quran_sql.py
fi
