#!/bin/sh

set -eu

sh -n scripts/*.sh
if [ -d scripts/lib ]; then
  sh -n scripts/lib/*.sh
fi
python3 -m py_compile docker/api/bootstrap-api.py
if [ -f scripts/analyze_upstream_quran_sql.py ]; then
  python3 -m py_compile scripts/analyze_upstream_quran_sql.py
fi
if [ -d apps/cli/src/qurankit ]; then
  python3 -m py_compile apps/cli/src/qurankit/*.py
fi
