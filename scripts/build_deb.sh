#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

rm -rf debian
cp -r packaging/debian debian
chmod +x debian/rules

dpkg-buildpackage -us -uc -b
