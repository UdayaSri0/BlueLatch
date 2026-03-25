#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

fail() {
  echo "check_release_metadata.sh: $*" >&2
  exit 1
}

VERSION="$(PYTHONPATH="$ROOT_DIR/src" python3 -c 'from bluelatch.version import __version__; print(__version__)')"
CHANGELOG_VERSION="$(sed -n 's/^## \[\([^]]*\)\].*/\1/p' "$ROOT_DIR/CHANGELOG.md" | head -n 1)"
DEBIAN_VERSION="$(sed -n '1s/^bluelatch (\([^)]*\)).*/\1/p' "$ROOT_DIR/packaging/debian/changelog")"
APPDATA_VERSION="$(sed -n 's/.*<release version="\([^"]*\)".*/\1/p' "$ROOT_DIR/packaging/appimage/io.github.UdayaSri.BlueLatch.appdata.xml" | head -n 1)"

[[ -n "$VERSION" ]] || fail "failed to read application version"
[[ "$CHANGELOG_VERSION" == "$VERSION" ]] || fail "CHANGELOG.md version $CHANGELOG_VERSION does not match $VERSION"
[[ "$DEBIAN_VERSION" == "$VERSION" ]] || fail "packaging/debian/changelog version $DEBIAN_VERSION does not match $VERSION"
[[ "$APPDATA_VERSION" == "$VERSION" ]] || fail "AppStream release version $APPDATA_VERSION does not match $VERSION"

echo "Release metadata is consistent at version $VERSION"
