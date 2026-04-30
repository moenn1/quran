#!/bin/sh

set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
SNAPSHOT_DIR="$ROOT_DIR/apps/web/e2e/visual.spec.ts-snapshots"
OUTPUT_DIR="$ROOT_DIR/docs/screenshots"

copy_snapshot() {
  stem="$1"
  target="$2"

  set -- "$SNAPSHOT_DIR"/"$stem"-*.png
  if [ ! -e "$1" ]; then
    echo "Missing Playwright snapshot for $stem in $SNAPSHOT_DIR" >&2
    exit 1
  fi

  cp "$1" "$OUTPUT_DIR/$target"
}

mkdir -p "$OUTPUT_DIR"

copy_snapshot "exact-search-mobile" "release-exact-search-mobile.png"
copy_snapshot "surah-reader-desktop" "release-surah-reader-desktop.png"

echo "Exported release screenshots to $OUTPUT_DIR"
