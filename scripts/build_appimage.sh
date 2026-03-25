#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="$ROOT_DIR/build/appimage"
DOWNLOAD_DIR="$BUILD_DIR/downloads"
WHEEL_DIR="$BUILD_DIR/wheels"
APPDIR="$BUILD_DIR/AppDir"
DIST_DIR="$ROOT_DIR/dist"
DESKTOP_FILE="$ROOT_DIR/packaging/desktop/io.github.UdayaSri.BlueLatch.desktop"
ICON_FILE="$ROOT_DIR/assets/icons/scalable/apps/io.github.UdayaSri.BlueLatch.svg"
APPDATA_FILE="$ROOT_DIR/packaging/appimage/io.github.UdayaSri.BlueLatch.appdata.xml"
APP_RUN_FILE="$ROOT_DIR/packaging/appimage/AppRun"

fail() {
  echo "build_appimage.sh: $*" >&2
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

resolve_pkg_config_command() {
  if command -v pkgconf >/dev/null 2>&1; then
    printf '%s\n' pkgconf
    return 0
  fi

  if command -v pkg-config >/dev/null 2>&1; then
    printf '%s\n' pkg-config
    return 0
  fi

  fail "pkg-config/pkgconf is required for linuxdeploy-plugin-gtk; install libgtk-4-dev or pkg-config before building the AppImage"
}

ensure_build_backend_available() {
  "$PYTHON_BIN" -c 'import setuptools, wheel' >/dev/null 2>&1 || fail \
    "$PYTHON_BIN needs setuptools and wheel in the active environment; run '$PYTHON_BIN -m pip install --upgrade pip setuptools wheel build' before building the AppImage"
}

resolve_python_command() {
  if [[ -n "${PYTHON_BIN:-}" ]]; then
    printf '%s\n' "$PYTHON_BIN"
    return 0
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' python3
    return 0
  fi

  fail "required command not found: python or python3"
}

require_command bash
require_command curl
PYTHON_BIN="$(resolve_python_command)"
PKG_CONFIG_BIN="$(resolve_pkg_config_command)"
require_command "$PYTHON_BIN"

"$PYTHON_BIN" -m pip --version >/dev/null 2>&1 || fail "$PYTHON_BIN pip support is required"
"$PYTHON_BIN" -m build --version >/dev/null 2>&1 || fail \
  "$PYTHON_BIN -m build is required; run '$PYTHON_BIN -m pip install --upgrade pip setuptools wheel build' before building the AppImage"
ensure_build_backend_available

"$PKG_CONFIG_BIN" --exists gtk4 || fail \
  "$PKG_CONFIG_BIN could not find gtk4.pc; install libgtk-4-dev so linuxdeploy-plugin-gtk can discover GTK 4 paths"
GTK4_LIBDIR="$("$PKG_CONFIG_BIN" --variable=libdir gtk4 2>/dev/null)"
[[ -n "$GTK4_LIBDIR" ]] || fail \
  "$PKG_CONFIG_BIN found gtk4 but did not report a libdir; check the libgtk-4-dev installation on this runner"

echo "build_appimage.sh: using Python interpreter $("$PYTHON_BIN" -c 'import sys; print(sys.executable)')"
echo "build_appimage.sh: $("$PYTHON_BIN" --version 2>&1)"
echo "build_appimage.sh: using pkg-config tool $(command -v "$PKG_CONFIG_BIN")"
echo "build_appimage.sh: gtk4 libdir $GTK4_LIBDIR"

require_file "$DESKTOP_FILE"
require_file "$ICON_FILE"
require_file "$APPDATA_FILE"
require_file "$APP_RUN_FILE"
require_file "$ROOT_DIR/packaging/appimage/bluelatch"
require_file "$ROOT_DIR/packaging/appimage/bluelatch-agent"

if command -v desktop-file-validate >/dev/null 2>&1; then
  desktop-file-validate "$DESKTOP_FILE"
fi
if command -v appstreamcli >/dev/null 2>&1; then
  appstreamcli validate --no-net "$APPDATA_FILE"
fi

VERSION="$(PYTHONPATH="$ROOT_DIR/src" "$PYTHON_BIN" -c 'from bluelatch.version import __version__; print(__version__)')"
ARCH="$(uname -m)"
ARTIFACT_NAME="BlueLatch-$VERSION-$ARCH.AppImage"
FINAL_ARTIFACT="$DIST_DIR/$ARTIFACT_NAME"

mkdir -p "$DOWNLOAD_DIR" "$WHEEL_DIR" "$DIST_DIR"
rm -rf "$APPDIR"
find "$BUILD_DIR" -maxdepth 1 -type f \( -name '*.AppImage' -o -name 'appimage' \) -delete
find "$DIST_DIR" -maxdepth 1 -type f -name 'BlueLatch-*.AppImage' -delete
find "$WHEEL_DIR" -maxdepth 1 -type f -name 'bluelatch-*.whl' -delete

if command -v git >/dev/null 2>&1 && git -C "$ROOT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  export SOURCE_DATE_EPOCH
  SOURCE_DATE_EPOCH="$(git -C "$ROOT_DIR" log -1 --pretty=%ct)"
fi

"$PYTHON_BIN" -m build --wheel --no-isolation --outdir "$WHEEL_DIR" "$ROOT_DIR"
WHEEL_PATH="$(find "$WHEEL_DIR" -maxdepth 1 -type f -name 'bluelatch-*.whl' | head -n 1)"
[[ -n "$WHEEL_PATH" ]] || fail "wheel build did not produce a bluelatch wheel"
echo "build_appimage.sh: built wheel $WHEEL_PATH"

mkdir -p \
  "$APPDIR/usr/bin" \
  "$APPDIR/usr/share/applications" \
  "$APPDIR/usr/share/icons/hicolor/scalable/apps" \
  "$APPDIR/usr/share/metainfo"

echo "build_appimage.sh: installing wheel into $APPDIR/usr"
"$PYTHON_BIN" -m pip install --no-compile --no-deps --prefix "$APPDIR/usr" "$WHEEL_PATH"
install -m 0755 "$ROOT_DIR/packaging/appimage/bluelatch" "$APPDIR/usr/bin/bluelatch"
install -m 0755 "$ROOT_DIR/packaging/appimage/bluelatch-agent" "$APPDIR/usr/bin/bluelatch-agent"
install -m 0644 "$DESKTOP_FILE" "$APPDIR/usr/share/applications/io.github.UdayaSri.BlueLatch.desktop"
install -m 0644 "$ICON_FILE" "$APPDIR/usr/share/icons/hicolor/scalable/apps/io.github.UdayaSri.BlueLatch.svg"
install -m 0644 "$APPDATA_FILE" "$APPDIR/usr/share/metainfo/io.github.UdayaSri.BlueLatch.appdata.xml"
install -m 0755 "$APP_RUN_FILE" "$APPDIR/AppRun"

LINUXDEPLOY="$DOWNLOAD_DIR/linuxdeploy-x86_64.AppImage"
GTK_PLUGIN="$DOWNLOAD_DIR/linuxdeploy-plugin-gtk.sh"

if [[ ! -f "$LINUXDEPLOY" ]]; then
  curl -L "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage" -o "$LINUXDEPLOY"
  chmod +x "$LINUXDEPLOY"
fi

if [[ ! -f "$GTK_PLUGIN" ]]; then
  curl -L "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh" -o "$GTK_PLUGIN"
  chmod +x "$GTK_PLUGIN"
fi

pushd "$BUILD_DIR" >/dev/null
export DEPLOY_GTK_VERSION=4
export LDAI_OUTPUT="$ARTIFACT_NAME"
export LDAI_NO_APPSTREAM=1
"$LINUXDEPLOY" \
  --appdir "$APPDIR" \
  --desktop-file "$DESKTOP_FILE" \
  --icon-file "$ICON_FILE" \
  --plugin gtk \
  --output appimage
RAW_APPIMAGE="$(find "$BUILD_DIR" -maxdepth 1 -type f \( -name '*.AppImage' -o -name 'appimage' \) | head -n 1)"
[[ -n "$RAW_APPIMAGE" ]] || fail "linuxdeploy did not produce an AppImage"
mv -f "$RAW_APPIMAGE" "$FINAL_ARTIFACT"
popd >/dev/null

echo "AppImage artifact is available at $FINAL_ARTIFACT"
