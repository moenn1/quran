#!/bin/sh

set -eu

is_tracked() {
  git ls-files --error-unmatch "$1" >/dev/null 2>&1
}

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

assert_if_tracked() {
  if is_tracked "$1"; then
    assert_file "$1"
  fi
}

assert_text_if_tracked() {
  file="$1"
  text="$2"

  if is_tracked "$file"; then
    assert_text "$file" "$text"
  fi
}

for file in \
  README.md \
  CHANGELOG.md \
  CONTRIBUTING.md \
  CODE_OF_CONDUCT.md \
  LICENSE \
  compose.yaml \
  .env.example \
  .env.api.example \
  .env.cli.example \
  .env.web.example \
  docs/self-hosting.md \
  docs/testing.md \
  docs/religious-safety.md \
  docs/api.md \
  docs/cli.md \
  docs/release-readiness.md \
  scripts/run-repository-tests.sh \
  docker/api.Dockerfile \
  docker/web.Dockerfile \
  tests/test_self_hosting_baseline.py \
  .github/workflows/quality.yml \
  .github/workflows/release-readiness.yml
do
  assert_file "$file"
done

for file in \
  docs/database.md \
  docs/frontend-architecture.md \
  docs/upstream/quran-database-summary.json \
  scripts/analyze_upstream_quran_sql.py \
  tests/test_analyze_upstream_quran_sql.py
do
  assert_if_tracked "$file"
done

assert_text README.md "I am not an Islamic scholar. This is a personal project with no commercial gain."
assert_text README.md "If I am doing anything wrong Islamically, please DM me directly so I can correct it."
assert_text README.md "Semantic search results are related passages by textual similarity, not tafsir, fatwa, or scholarly interpretation."
assert_text CHANGELOG.md "## [Unreleased]"
assert_text CONTRIBUTING.md "git config user.name \"Mohamed En-Nassibi\""
assert_text CONTRIBUTING.md "git config user.email \"mohamed.enn2001@gmail.com\""
assert_text .env.example "COMPOSE_PROFILES="
assert_text .env.cli.example "QURANKIT_CLI_PRIVACY_MODE=private-by-default"
assert_text docs/self-hosting.md "COMPOSE_PROFILES=semantic-search"
assert_text docs/self-hosting.md ".env.cli.example"
assert_text docs/religious-safety.md "Do not alter Quran text."
assert_text docs/religious-safety.md "Semantic search is textual similarity, not tafsir, fatwa, or religious ruling."
assert_text docs/religious-safety.md "Bookmarks, notes, and reading progress must be private by default."
assert_text docs/testing.md "./scripts/run-repository-tests.sh"
assert_text docs/api.md "without exposing raw database credentials"
assert_text docs/cli.md ".env.cli.example"
assert_text docs/testing.md "./scripts/run-e2e.sh"
assert_text_if_tracked docs/database.md "Attribution Requirements For QuranKit"
assert_text_if_tracked docs/frontend-architecture.md "Semantic results must never be presented as tafsir, fatwa, or rulings."
