#!/bin/sh

set -eu

assert_file() {
  if [ ! -f "$1" ]; then
    echo "Missing required file: $1" >&2
    exit 1
  fi
}

assert_text() {
  file="$1"
  text="$2"

  if ! grep -Fq "$text" "$file"; then
    echo "Missing required text in $file: $text" >&2
    exit 1
  fi
}

for file in \
  README.md \
  CHANGELOG.md \
  CONTRIBUTING.md \
  CODE_OF_CONDUCT.md \
  LICENSE \
  apps/cli/README.md \
  compose.yaml \
  .env.example \
  .env.api.example \
  .env.web.example \
  docs/self-hosting.md \
  docs/testing.md \
  docs/religious-safety.md \
  docs/database.md \
  docs/frontend-architecture.md \
  docs/upstream/quran-database-summary.json \
  docs/api.md \
  docs/cli.md \
  docs/semantic-search.md \
  docs/reading-tracker.md \
  docs/contributing.md \
  docs/release-readiness.md \
  scripts/analyze_upstream_quran_sql.py \
  scripts/lib/cli-python.sh \
  scripts/smoke-cli.sh \
  tests/test_analyze_upstream_quran_sql.py \
  docker/api.Dockerfile \
  docker/web.Dockerfile \
  .github/workflows/quality.yml \
  .github/workflows/release-readiness.yml
do
  assert_file "$file"
done

assert_text README.md "I am not an Islamic scholar. This is a personal project with no commercial gain."
assert_text README.md "If I am doing anything wrong Islamically, please DM me directly so I can correct it."
assert_text README.md "Semantic search results are related passages by textual similarity, not tafsir, fatwa, or scholarly interpretation."
assert_text README.md "python -m pip install -e 'apps/cli[dev]'"
assert_text README.md "./scripts/run-cli-tests.sh"
assert_text CHANGELOG.md "## [Unreleased]"
assert_text CONTRIBUTING.md "git config user.name \"Mohamed En-Nassibi\""
assert_text CONTRIBUTING.md "git config user.email \"mohamed.enn2001@gmail.com\""
assert_text apps/cli/README.md "configuration storage for remote API and local SQLite modes"
assert_text apps/cli/README.md 'initial `config show` and `config set` commands'
assert_text docs/self-hosting.md "qdrant"
assert_text docs/religious-safety.md "Do not alter Quran text."
assert_text docs/religious-safety.md "Semantic search is textual similarity, not tafsir, fatwa, or religious ruling."
assert_text docs/religious-safety.md "Bookmarks, notes, and reading progress must be private by default."
assert_text docs/database.md "Attribution Requirements For QuranKit"
assert_text docs/api.md 'The bootstrap Docker service only exposes `GET /` and `GET /health` today.'
assert_text docs/api.md "/api/v1/search/semantic"
assert_text docs/cli.md "python -m pip install -e 'apps/cli[dev]'"
assert_text docs/cli.md "./scripts/smoke-cli.sh"
assert_text docs/cli.md ".venv/bin/python"
assert_text docs/cli.md "Keep bookmarks, notes, and reading progress private by default"
assert_text docs/cli.md "Describe semantic search as textual similarity only"
assert_text docs/cli.md "The Docker bootstrap API does not implement this contract yet."
assert_text docs/semantic-search.md "textual similarity only"
assert_text docs/semantic-search.md "docker compose --profile semantic-search up --build"
assert_text docs/reading-tracker.md "/api/v1/me/study"
assert_text docs/reading-tracker.md "Private by default does not mean encrypted"
assert_text docs/contributing.md "./scripts/check-docs.sh"
assert_text docs/contributing.md "./scripts/release-readiness.sh"
assert_text docs/release-readiness.md "./scripts/smoke-cli.sh"
assert_text docs/frontend-architecture.md "Semantic results must never be presented as tafsir, fatwa, or rulings."
assert_text docs/testing.md "./scripts/run-e2e.sh"
assert_text docs/testing.md ".venv/bin/python"
assert_text docs/testing.md "./scripts/smoke-cli.sh"
