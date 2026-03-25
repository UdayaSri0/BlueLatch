# BlueLatch

BlueLatch is a GNOME-first Linux Bluetooth proximity-lock application for Ubuntu 24.04 and closely related Debian-family desktops.

It watches one trusted phone over BlueZ D-Bus and automatically locks the current desktop session when that phone is no longer nearby. BlueLatch never auto-unlocks the machine.

## Core Rules

BlueLatch preserves these product rules:

1. It auto-locks only. It never auto-unlocks.
2. If BlueLatch locked the session because the phone went away and the user manually unlocks while the phone is still away, BlueLatch does not keep re-locking in a loop.
3. Protection resumes only after the trusted phone returns and presence is stable again.
4. Core Bluetooth and session behavior uses Linux APIs and D-Bus, not `bluetoothctl` scraping.
5. Ubuntu GNOME is the first target, with platform-specific code isolated for future KDE/XFCE backends.

## What BlueLatch Does

- Monitors one trusted Bluetooth phone.
- Uses BlueZ D-Bus for device discovery, pairing, trust actions, connection state, and reconnect attempts.
- Uses a hybrid presence model based on connection state plus smoothed RSSI with hysteresis.
- Applies an explicit protection state machine with `STARTING`, `PRESENT`, `MAYBE_AWAY`, `AWAY_PENDING_LOCK`, `AWAY_LOCKED`, `AWAY_MANUAL_OVERRIDE`, `RETURNING`, and `ERROR`.
- Locks the current session through GNOME or freedesktop D-Bus methods first, then `loginctl` fallback.
- Runs as a background agent so protection continues after the settings window closes.
- Stores per-user config and runtime state under XDG directories with user-only config permissions.
- Checks GitHub Releases and adapts upgrade guidance for AppImage and Debian-based installs.

## Supported Platform

Current release target:

- Ubuntu 24.04 GNOME
- Debian-based desktops with BlueZ, GTK4, libadwaita, and a GNOME-compatible session lock path

Assumptions for the packaged builds:

- `bluetoothd` is available on the system bus.
- The current session supports GNOME ScreenSaver D-Bus or compatible freedesktop locking.
- `loginctl` is available as a fallback lock path.
- Python 3.12 is available on the target system.
- GTK4 and libadwaita are available through PyGObject.

## Quick Start

Choose the install path that matches how you want to run BlueLatch.

### Install from the APT repository

```bash
curl -fsSL https://udayasri0.github.io/BlueLatch/apt/bluelatch-archive-keyring.asc \
  | gpg --dearmor \
  | sudo tee /usr/share/keyrings/bluelatch-archive-keyring.gpg > /dev/null
```

```bash
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bluelatch-archive-keyring.gpg] https://udayasri0.github.io/BlueLatch/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/bluelatch.list > /dev/null
```

```bash
sudo apt update
sudo apt install bluelatch
bluelatch
```

### Install from a standalone Debian package

```bash
sudo apt install ./bluelatch_0.1.1_amd64.deb
bluelatch
```

### Run the AppImage

```bash
chmod +x BlueLatch-0.1.1-x86_64.AppImage
./BlueLatch-0.1.1-x86_64.AppImage
```

### Run from a development checkout

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python3 -m pip install --no-build-isolation -e ".[dev]"
python3 -m bluelatch.main
```

## How to Use BlueLatch

1. Launch BlueLatch. Opening the desktop UI also starts the background agent if it is not already running.
2. Open `Trusted Device`, click `Scan`, and select your phone from the list.
3. Click `Pair` and `Trust` if needed, then click `Use Selected` to save that phone as the one trusted device.
4. Open `Settings`, review `Enable protection`, `Start on login`, `Presence mode`, and the grace-period values, then click `Save Settings`.
5. Open `Status` to confirm the trusted device, Bluetooth availability, connection state, and current protection state.
6. Leave with your phone to test the lock behaviour. If you manually unlock while the phone is still away, BlueLatch enters manual override and waits for the phone to return before normal auto-locking resumes.

## Run Modes

- `bluelatch` launches the GTK desktop UI.
- `bluelatch-agent` runs only the background protection agent.
- `python3 -m bluelatch.main` is the development equivalent of `bluelatch`.
- `python3 -m bluelatch.main --agent` is the development equivalent of `bluelatch-agent`.

## Architecture

BlueLatch is split into two runtime parts.

### Background Agent

Responsible for:

- BlueZ monitoring and reconnect attempts
- Presence estimation
- Explicit lock state machine handling
- Session lock triggering
- Manual unlock detection
- Status and event persistence
- Startup runtime behavior

Key modules:

- `src/bluelatch/agent.py`
- `src/bluelatch/bluetooth/bluez.py`
- `src/bluelatch/presence/estimator.py`
- `src/bluelatch/presence/state_machine.py`
- `src/bluelatch/session/monitor.py`
- `src/bluelatch/session/lock.py`

### GTK4/libadwaita Desktop UI

Responsible for:

- Onboarding guidance
- Trusted device selection
- Settings
- Live status
- Event history
- About dialog
- Update dialog

Key modules:

- `src/bluelatch/ui/window.py`
- `src/bluelatch/ui/devices.py`
- `src/bluelatch/ui/settings.py`
- `src/bluelatch/ui/status.py`
- `src/bluelatch/ui/logs.py`
- `src/bluelatch/ui/updates.py`

## Manual Override Behavior

If all of the following are true:

- the phone is away
- BlueLatch auto-locked the session
- the user manually unlocks anyway

Then BlueLatch enters `AWAY_MANUAL_OVERRIDE`.

While in `AWAY_MANUAL_OVERRIDE`:

- BlueLatch keeps monitoring Bluetooth and session state
- BlueLatch does not auto-lock again repeatedly
- BlueLatch will not clear the override until the phone comes back and presence is stable again

This is the main safeguard against lock storms.

## Security and Privacy

BlueLatch is local-first.

- No cloud service is required.
- No telemetry is enabled by default.
- No phone GPS or location history is stored.
- Only necessary Bluetooth identity and configuration metadata is stored.
- Normal runtime does not require root.

Security limitations:

- Bluetooth proximity is an approximation, not a proof of physical presence.
- RSSI changes with body position, pockets, walls, desk placement, and radio noise.
- A phone can remain connected at longer-than-expected ranges.
- Different Bluetooth chipsets report different RSSI behavior.
- Suspend and resume behavior varies across systems.

BlueLatch should be treated as a convenience security layer, not as a replacement for strong passwords, full-disk encryption, or standard workstation lock policies.

## Development Setup

Install system dependencies on Ubuntu 24.04 or a close Debian-family derivative:

```bash
sudo apt-get update
sudo apt-get install -y \
  appstream \
  bluez \
  curl \
  debhelper \
  desktop-file-utils \
  dh-python \
  fakeroot \
  gir1.2-adw-1 \
  gir1.2-gtk-4.0 \
  gpg \
  libgtk-4-dev \
  pybuild-plugin-pyproject \
  python3-all \
  python3-build \
  python3-gi \
  python3-packaging \
  python3-pip \
  python3-pytest \
  python3-setuptools \
  python3-wheel \
  reprepro \
  rsync
```

Install the Python package in editable mode for development:

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python3 -m pip install --no-build-isolation -e ".[dev]"
```

Run the UI:

```bash
python3 -m bluelatch.main
```

Run the background agent only:

```bash
python3 -m bluelatch.main --agent
```

Run the local verification suite:

```bash
./scripts/check.sh
```

## Local Build Commands

Build wheel and sdist:

```bash
python3 -m build --no-isolation
```

Build the Debian package:

```bash
./scripts/build_deb.sh
```

The Debian package build:

- stages a clean source tree in `build/debian/source/`
- copies `packaging/debian/` into that staging tree
- runs `dpkg-checkbuilddeps`
- runs `dpkg-buildpackage`
- writes artifacts to `dist/debian/`

Expected Debian artifact:

```text
dist/debian/bluelatch_0.1.1_amd64.deb
```

Build the AppImage:

```bash
./scripts/build_appimage.sh
```

The AppImage build:

- builds a wheel into `build/appimage/wheels/`
- installs the package into `build/appimage/AppDir/`
- installs the desktop file, icon, metainfo, and portable launcher wrappers
- downloads `linuxdeploy` and the GTK plugin on first use
- writes the final AppImage to `dist/`

Expected AppImage artifact:

```text
dist/BlueLatch-0.1.1-x86_64.AppImage
```

Collect release-ready assets and checksums after building:

```bash
./scripts/collect_release_assets.sh
```

Expected release asset directory:

```text
dist/release/
```

## Debian Packaging Notes

The Debian package is built from `packaging/debian/` and targets `amd64` first.

What the package installs:

- Python application entry points through the normal Debian Python packaging path
- Desktop launcher in `/usr/share/applications/`
- SVG icon in `/usr/share/icons/hicolor/scalable/apps/`
- AppStream metadata in `/usr/share/metainfo/`
- User service unit in `/usr/lib/systemd/user/bluelatch-agent.service`

What the package does not do:

- It does not enable the background agent for every user automatically.
- It does not run the app as root.
- It does not change BlueLatch locking logic or Bluetooth presence behavior.

BlueLatch still manages startup per user from the settings UI. The installed user unit is there so packaged deployments have a standard systemd user service available.

## AppImage Notes

The AppImage launcher keeps the app entry point portable by replacing build-host-specific console scripts with small shell wrappers that execute `python3 -m bluelatch.main`.

This build currently targets Debian-family systems where Python 3, BlueZ, and the desktop Bluetooth stack are already present. The GTK plugin remains enabled so the AppImage bundles the GTK side of the runtime as far as practical in CI.

Local AppImage builds also require `libgtk-4-dev` so `linuxdeploy-plugin-gtk` can resolve `gtk4.pc` and find the GTK 4 module path through `pkg-config`.

## APT Repository

Tagged releases publish a signed APT repository to GitHub Pages under:

```text
https://udayasri0.github.io/BlueLatch/apt
```

BlueLatch uses a modern `signed-by` setup and does not rely on deprecated `apt-key`.

End-user installation commands:

```bash
curl -fsSL https://udayasri0.github.io/BlueLatch/apt/bluelatch-archive-keyring.asc \
  | gpg --dearmor \
  | sudo tee /usr/share/keyrings/bluelatch-archive-keyring.gpg > /dev/null
```

```bash
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/bluelatch-archive-keyring.gpg] https://udayasri0.github.io/BlueLatch/apt stable main" \
  | sudo tee /etc/apt/sources.list.d/bluelatch.list > /dev/null
```

```bash
sudo apt update
sudo apt install bluelatch
```

## GitHub Release Usage

Each tagged release publishes:

- wheel
- sdist
- Debian package
- AppImage
- `SHA256SUMS.txt`

Download files from the GitHub Releases page:

```text
https://github.com/UdayaSri0/BlueLatch/releases
```

Verify downloaded release assets:

```bash
sha256sum -c SHA256SUMS.txt
```

Install the standalone Debian package directly from a release download:

```bash
sudo apt install ./bluelatch_0.1.1_amd64.deb
```

## Upgrade Guidance

AppImage users:

- Download the new `BlueLatch-0.1.1-x86_64.AppImage` file.
- Replace the old AppImage file.
- Make sure it stays executable with `chmod +x BlueLatch-0.1.1-x86_64.AppImage`.

Debian and APT users:

- If you installed from the GitHub Pages APT repo, run `sudo apt update && sudo apt install --only-upgrade bluelatch`.
- If you installed from a standalone `.deb`, install the newer `.deb` package with `sudo apt install ./bluelatch_0.1.1_amd64.deb`.
- BlueLatch does not self-overwrite APT-managed installs.

## CI and Release Automation

Normal CI lives in `.github/workflows/ci.yml`.

It:

- checks out the repository
- installs packaging and GTK build dependencies
- runs compile checks
- runs the test suite
- verifies release metadata consistency
- builds the wheel and sdist
- builds the Debian package
- builds the AppImage
- uploads release-style artifacts

Tagged releases live in `.github/workflows/release.yml`.

It:

- verifies the tag matches `src/bluelatch/version.py`
- rebuilds and tests the release on Ubuntu 24.04
- renders release notes from `CHANGELOG.md`
- signs and publishes the GitHub Pages APT repository
- uploads GitHub release assets
- deploys the Pages site

Required GitHub repository settings and secrets:

- Enable GitHub Pages and set the source to GitHub Actions.
- Add `BLUELATCH_APT_GPG_PRIVATE_KEY` with the ASCII-armored private signing key.
- Add `BLUELATCH_APT_GPG_PASSPHRASE` with the passphrase for that key.

## Local Release Notes and APT Publishing

Render the release notes for the current version from `CHANGELOG.md`:

```bash
./scripts/render_release_notes.sh
```

Publish a local Pages-style APT repository after importing the signing key into your GPG keyring:

```bash
export BLUELATCH_APT_GPG_FINGERPRINT=YOUR_KEY_FINGERPRINT
export BLUELATCH_APT_BASE_URL=https://udayasri0.github.io/BlueLatch/apt
./scripts/publish_apt_repo.sh
```

That writes the publishable site content to:

```text
dist/pages/
```

## Troubleshooting

### `python3 -m bluelatch.main` fails from a fresh clone

Install the project in editable mode first:

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python3 -m pip install --no-build-isolation -e ".[dev]"
```

### `pip install -e ".[dev]"` or `python3 -m build` tries to download `setuptools` or `wheel`

Local Debian-family development works best with the distro-provided Python packaging tools already installed from `apt`. Recreate the virtualenv with `--system-site-packages`, then use `--no-build-isolation` so `pip` and `build` reuse those local packages instead of creating a temporary download-only environment.

If `.venv` already exists without `--system-site-packages`, remove it and create it again before retrying.

If the error mentions a proxy, clear stale proxy variables such as `http_proxy`, `https_proxy`, `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` before retrying.

### `./scripts/build_deb.sh` reports missing packaging files

The Debian build requires the committed `packaging/debian/` tree. Restore the missing files or start from a clean checkout.

### `./scripts/build_deb.sh` reports unmet build dependencies

Install the Debian build requirements shown in the Development Setup section, then re-run the script. The script calls `dpkg-checkbuilddeps` before building.

### `./scripts/build_appimage.sh` fails while downloading tools

The first AppImage build downloads `linuxdeploy` and the GTK plugin. Confirm outbound network access and re-run the build.

### `./scripts/build_appimage.sh` fails with `gtk4.pc` or `linuxdeploy-plugin-gtk`

Install `libgtk-4-dev` locally and then retry the build. The GTK AppImage plugin reads `gtk4.pc` through `pkg-config` to discover the GTK 4 library and module directories.

### `./scripts/build_appimage.sh` fails validation

Install `desktop-file-utils` and `appstream` so the desktop file and AppStream metadata can be validated locally.

### Release workflow fails while publishing the APT repository

Check all of the following:

- GitHub Pages is enabled for GitHub Actions.
- `BLUELATCH_APT_GPG_PRIVATE_KEY` is a valid ASCII-armored private key.
- `BLUELATCH_APT_GPG_PASSPHRASE` matches the imported key.
- the tag version matches `src/bluelatch/version.py`

## Repository Layout

```text
.
├── assets/
├── packaging/
│   ├── appimage/
│   ├── debian/
│   ├── desktop/
│   └── systemd/
├── scripts/
├── src/bluelatch/
└── tests/
```

## License

MIT. See `LICENSE`.
