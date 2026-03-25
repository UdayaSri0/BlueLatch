#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
OUTPUT_FILE="$DIST_DIR/release-notes.md"
VERSION="${1:-$(PYTHONPATH="$ROOT_DIR/src" python3 -c 'from bluelatch.version import __version__; print(__version__)')}"

fail() {
  echo "render_release_notes.sh: $*" >&2
  exit 1
}

mkdir -p "$DIST_DIR"

awk -v version="$VERSION" '
  $0 ~ "^## \\[" version "\\]" { capture = 1; next }
  capture && $0 ~ "^## \\[" { exit }
  capture { print }
' "$ROOT_DIR/CHANGELOG.md" > "$OUTPUT_FILE"

[[ -s "$OUTPUT_FILE" ]] || fail "no release notes found for version $VERSION"

echo "Release notes written to $OUTPUT_FILE"
