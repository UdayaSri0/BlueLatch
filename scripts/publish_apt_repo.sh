#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PAGES_DIR="${1:-$ROOT_DIR/dist/pages}"
DEB_PATH="${2:-}"

fail() {
  echo "publish_apt_repo.sh: $*" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "required command not found: $command_name"
}

require_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || fail "required file is missing: $file_path"
}

require_command dpkg-deb
require_command gpg
require_command reprepro

if [[ -z "$DEB_PATH" ]]; then
  DEB_PATH="$(find "$ROOT_DIR/dist/debian" -maxdepth 1 -type f -name 'bluelatch_*.deb' | sort | head -n 1)"
fi

[[ -n "$DEB_PATH" ]] || fail "no Debian package provided and none found in dist/debian"
require_file "$DEB_PATH"

KEY_FINGERPRINT="${BLUELATCH_APT_GPG_FINGERPRINT:-}"
REPO_BASE_URL="${BLUELATCH_APT_BASE_URL:-}"

[[ -n "$KEY_FINGERPRINT" ]] || fail "BLUELATCH_APT_GPG_FINGERPRINT is required"
[[ -n "$REPO_BASE_URL" ]] || fail "BLUELATCH_APT_BASE_URL is required"

PACKAGE_NAME="$(dpkg-deb -f "$DEB_PATH" Package)"
PACKAGE_VERSION="$(dpkg-deb -f "$DEB_PATH" Version)"
PACKAGE_ARCH="$(dpkg-deb -f "$DEB_PATH" Architecture)"

[[ "$PACKAGE_NAME" == "bluelatch" ]] || fail "expected package name bluelatch, got $PACKAGE_NAME"
[[ "$PACKAGE_ARCH" == "amd64" ]] || fail "expected package architecture amd64, got $PACKAGE_ARCH"

APT_DIR="$PAGES_DIR/apt"
CONF_DIR="$APT_DIR/conf"

rm -rf "$APT_DIR"
mkdir -p "$CONF_DIR"

cat > "$CONF_DIR/distributions" <<EOF
Origin: BlueLatch
Label: BlueLatch
Suite: stable
Codename: stable
Version: $PACKAGE_VERSION
Architectures: $PACKAGE_ARCH
Components: main
Description: BlueLatch stable APT repository
SignWith: $KEY_FINGERPRINT
EOF

cat > "$CONF_DIR/options" <<'EOF'
verbose
basedir .
outdir .
distdir dists
dbdir db
pooldir pool
EOF

reprepro --basedir "$APT_DIR" includedeb stable "$DEB_PATH"

gpg --batch --yes --armor --output "$APT_DIR/bluelatch-archive-keyring.asc" --export "$KEY_FINGERPRINT"
gpg --batch --yes --output "$APT_DIR/bluelatch-archive-keyring.gpg" --export "$KEY_FINGERPRINT"

cat > "$PAGES_DIR/index.html" <<EOF
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>BlueLatch Downloads</title>
</head>
<body>
  <h1>BlueLatch Downloads</h1>
  <p>APT repository: <a href="$REPO_BASE_URL">$REPO_BASE_URL</a></p>
  <p>Public key: <a href="$REPO_BASE_URL/bluelatch-archive-keyring.asc">$REPO_BASE_URL/bluelatch-archive-keyring.asc</a></p>
</body>
</html>
EOF

require_file "$APT_DIR/dists/stable/InRelease"
require_file "$APT_DIR/dists/stable/Release"
require_file "$APT_DIR/dists/stable/Release.gpg"

echo "APT repository content is available in $APT_DIR"
