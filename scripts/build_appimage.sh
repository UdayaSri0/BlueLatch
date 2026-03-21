#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/appimage"
APPDIR="$BUILD_DIR/AppDir"

rm -rf "$BUILD_DIR"
mkdir -p "$APPDIR/usr"

python3 -m pip install --upgrade pip build
python3 -m build
python3 -m pip install --no-deps --prefix "$APPDIR/usr" .

mkdir -p "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp packaging/desktop/io.github.UdayaSri.BlueLatch.desktop "$APPDIR/usr/share/applications/"
cp assets/icons/scalable/apps/io.github.UdayaSri.BlueLatch.svg "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp packaging/appimage/AppRun "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

LINUXDEPLOY="$BUILD_DIR/linuxdeploy-x86_64.AppImage"
GTK_PLUGIN="$BUILD_DIR/linuxdeploy-plugin-gtk.sh"

if [[ ! -f "$LINUXDEPLOY" ]]; then
  curl -L "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" -o "$LINUXDEPLOY"
  chmod +x "$LINUXDEPLOY"
fi

if [[ ! -f "$GTK_PLUGIN" ]]; then
  curl -L "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh" -o "$GTK_PLUGIN"
  chmod +x "$GTK_PLUGIN"
fi

export OUTPUT=appimage
export DEPLOY_GTK_VERSION=4
"$LINUXDEPLOY" \
  --appdir "$APPDIR" \
  --desktop-file packaging/desktop/io.github.UdayaSri.BlueLatch.desktop \
  --icon-file assets/icons/scalable/apps/io.github.UdayaSri.BlueLatch.svg \
  --plugin gtk \
  --output appimage
