#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$ROOT_DIR/dist"
RELEASE_DIR="$DIST_DIR/release"

fail() {
  echo "collect_release_assets.sh: $*" >&2
  exit 1
}

require_match() {
  local pattern="$1"
  local match
  match="$(find "$DIST_DIR" -maxdepth 1 -type f -name "$pattern" | sort | head -n 1)"
  [[ -n "$match" ]] || fail "expected artifact matching $pattern in $DIST_DIR"
  printf '%s\n' "$match"
}

require_deb() {
  local match
  match="$(find "$DIST_DIR/debian" -maxdepth 1 -type f -name 'bluelatch_*.deb' | sort | head -n 1)"
  [[ -n "$match" ]] || fail "expected Debian package in $DIST_DIR/debian"
  printf '%s\n' "$match"
}

mkdir -p "$DIST_DIR"
rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

cp -f "$(require_match 'bluelatch-*.whl')" "$RELEASE_DIR/"
cp -f "$(require_match 'bluelatch-*.tar.gz')" "$RELEASE_DIR/"
cp -f "$(require_match 'BlueLatch-*.AppImage')" "$RELEASE_DIR/"
cp -f "$(require_deb)" "$RELEASE_DIR/"

if [[ -f "$DIST_DIR/pages/apt/bluelatch-archive-keyring.asc" ]]; then
  cp -f "$DIST_DIR/pages/apt/bluelatch-archive-keyring.asc" "$RELEASE_DIR/"
fi

(
  cd "$RELEASE_DIR"
  find . -maxdepth 1 -type f ! -name 'SHA256SUMS.txt' -printf '%P\n' | sort | xargs sha256sum > SHA256SUMS.txt
)

echo "Release assets are available in $RELEASE_DIR"
