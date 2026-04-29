#!/bin/sh

set -eu

PROJECT_NAME="${QURANKIT_SMOKE_PROJECT:-qurankit-smoke}"
POSTGRES_PORT="${QURANKIT_SMOKE_POSTGRES_PORT:-15432}"
API_PORT="${QURANKIT_SMOKE_API_PORT:-18000}"
WEB_PORT="${QURANKIT_SMOKE_WEB_PORT:-13000}"

export POSTGRES_PORT API_PORT WEB_PORT

compose() {
  docker compose -p "$PROJECT_NAME" -f compose.yaml "$@"
}

cleanup() {
  compose down -v >/dev/null 2>&1 || true
}

wait_for_url() {
  url="$1"
  attempts="${2:-30}"
  sleep_seconds="${3:-2}"
  count=0

  while [ "$count" -lt "$attempts" ]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi

    count=$((count + 1))
    sleep "$sleep_seconds"
  done

  echo "Timed out waiting for $url" >&2
  return 1
}

trap cleanup EXIT INT TERM

compose up -d --build

wait_for_url "http://127.0.0.1:${API_PORT}/health"
wait_for_url "http://127.0.0.1:${WEB_PORT}"

curl -fsS "http://127.0.0.1:${API_PORT}/health" | grep -Fq '"status": "ok"'
curl -fsS "http://127.0.0.1:${WEB_PORT}" | grep -Fq "QuranKit Bootstrap"
