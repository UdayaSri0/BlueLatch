#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PACKAGING_DIR="$ROOT_DIR/packaging/debian"
BUILD_ROOT="$ROOT_DIR/build/debian"
STAGING_DIR="$BUILD_ROOT/source"
OUTPUT_DIR="$ROOT_DIR/dist/debian"
SYSTEM_BUILD_PATH="/usr/sbin:/usr/bin:/sbin:/bin"

fail() {
  echo "build_deb.sh: $*" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "required command not found: $command_name"
}

require_file() {
  local file_path="$1"
  [[ -f "$file_path" ]] || fail "required packaging file is missing: $file_path"
}

run_with_system_python() {
  env \
    -u VIRTUAL_ENV \
    -u PYTHONHOME \
    -u PYTHONPATH \
    PATH="$SYSTEM_BUILD_PATH" \
    "$@"
}

require_command dpkg-buildpackage
require_command dpkg-checkbuilddeps
require_command fakeroot
require_command rsync

require_file "$PACKAGING_DIR/control"
require_file "$PACKAGING_DIR/rules"
require_file "$PACKAGING_DIR/changelog"
require_file "$PACKAGING_DIR/copyright"
require_file "$PACKAGING_DIR/bluelatch.install"
require_file "$PACKAGING_DIR/source/format"

mkdir -p "$BUILD_ROOT" "$OUTPUT_DIR"
rm -rf "$STAGING_DIR"
find "$BUILD_ROOT" -maxdepth 1 -type f \
  \( -name 'bluelatch_*.deb' -o -name 'bluelatch_*.buildinfo' -o -name 'bluelatch_*.changes' \) \
  -delete
find "$OUTPUT_DIR" -maxdepth 1 -type f \
  \( -name 'bluelatch_*.deb' -o -name 'bluelatch_*.buildinfo' -o -name 'bluelatch_*.changes' \) \
  -delete

rsync -a \
  --delete \
  --exclude='.git/' \
  --exclude='.github/' \
  --exclude='.pytest_cache/' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  --exclude='build/' \
  --exclude='dist/' \
  --exclude='debian/' \
  "$ROOT_DIR/" "$STAGING_DIR/"

cp -a "$PACKAGING_DIR" "$STAGING_DIR/debian"
chmod 0755 "$STAGING_DIR/debian/rules"

cd "$STAGING_DIR"
if ! run_with_system_python dpkg-checkbuilddeps; then
  cat >&2 <<'EOF'
build_deb.sh: install the Debian packaging prerequisites before retrying, for example:
  sudo apt-get update
  sudo apt-get install -y debhelper dh-python fakeroot pybuild-plugin-pyproject python3-all python3-build python3-packaging python3-pytest python3-setuptools python3-wheel rsync
EOF
  exit 1
fi
run_with_system_python dpkg-buildpackage -rfakeroot -us -uc -b

find "$BUILD_ROOT" -maxdepth 1 -type f \
  \( -name 'bluelatch_*.deb' -o -name 'bluelatch_*.buildinfo' -o -name 'bluelatch_*.changes' \) \
  -exec mv -f {} "$OUTPUT_DIR/" \;

echo "Debian artifacts are available in $OUTPUT_DIR"
