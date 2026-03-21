# BlueLatch

BlueLatch is a Linux Bluetooth proximity-lock application for Ubuntu 24.04 GNOME.

It watches one trusted phone over BlueZ D-Bus and automatically locks the current desktop session when that phone is no longer nearby. BlueLatch never auto-unlocks the machine.

## Core Rules

BlueLatch enforces these product rules:

1. It auto-locks only. It never auto-unlocks.
2. If BlueLatch locked the session because the phone went away and the user manually unlocks while the phone is still away, BlueLatch does not keep re-locking in a loop.
3. Protection resumes only after the trusted phone returns and presence is stable again.
4. Core Bluetooth and session behavior uses Linux APIs and D-Bus, not `bluetoothctl` scraping.
5. Ubuntu GNOME is the first target, with platform-specific code isolated for future KDE/XFCE backends.

## What It Does

- Monitors one trusted Bluetooth phone.
- Uses BlueZ D-Bus for device discovery, pairing/trust actions, connection state, and reconnect attempts.
- Uses a hybrid presence model based on connection state plus smoothed RSSI with hysteresis.
- Applies an explicit protection state machine:
  - `STARTING`
  - `PRESENT`
  - `MAYBE_AWAY`
  - `AWAY_PENDING_LOCK`
  - `AWAY_LOCKED`
  - `AWAY_MANUAL_OVERRIDE`
  - `RETURNING`
  - `ERROR`
- Locks the current session through GNOME/freedesktop D-Bus methods first, then `loginctl` fallback.
- Runs as a background agent so protection continues after the settings window closes.
- Stores per-user config and runtime state under XDG directories with user-only config permissions.
- Checks GitHub Releases for updates and adapts guidance for AppImage vs Debian installs.

## Supported Platform

Current first-release target:

- Ubuntu 24.04 GNOME

Tested and designed assumptions:

- BlueZ available on the system bus
- GNOME session lock support via `org.gnome.ScreenSaver` or compatible freedesktop fallback
- `loginctl` available for session fallback handling
- Python 3.12 runtime target
- GTK4 + libadwaita available through PyGObject

Future desktop environments can add session lock and session monitor backends without rewriting the core presence logic.

## Architecture

BlueLatch is split into two runtime parts.

### 1. Background agent

Responsible for:

- BlueZ monitoring and reconnect attempts
- presence estimation
- explicit lock state machine
- session lock triggering
- manual unlock detection
- status/event persistence
- startup runtime behavior

Important modules:

- `src/bluelatch/agent.py`
- `src/bluelatch/bluetooth/bluez.py`
- `src/bluelatch/presence/estimator.py`
- `src/bluelatch/presence/state_machine.py`
- `src/bluelatch/session/monitor.py`
- `src/bluelatch/session/lock.py`

### 2. GTK4/libadwaita desktop UI

Responsible for:

- onboarding guidance
- trusted device selection
- settings
- live status
- event history
- about dialog
- update dialog

Important modules:

- `src/bluelatch/ui/window.py`
- `src/bluelatch/ui/devices.py`
- `src/bluelatch/ui/settings.py`
- `src/bluelatch/ui/status.py`
- `src/bluelatch/ui/logs.py`
- `src/bluelatch/ui/updates.py`

### Shared storage model

The UI and agent stay decoupled. The agent writes runtime status and event history to XDG state files. The UI reads those files and writes config changes that the agent reloads automatically.

This keeps the architecture simple, local-first, and resilient when the main window closes.

## Presence and Locking Model

BlueLatch does not treat Bluetooth RSSI as literal distance.

Instead it uses:

- smoothed RSSI samples
- near/far thresholds
- hysteresis
- debounce timers
- away grace periods
- explicit reconnect backoff

Modes currently exposed:

- `disconnect_only`
- `weak_signal_or_disconnect`
- `hybrid`

The hybrid mode is the default and is intended to absorb short disconnects while still reacting to sustained absence.

## Manual Override Behavior

This is the most important behavioral rule in the project.

If all of the following are true:

- the phone is away
- BlueLatch auto-locked the session
- the user manually unlocks anyway

Then BlueLatch enters `AWAY_MANUAL_OVERRIDE`.

While in `AWAY_MANUAL_OVERRIDE`:

- BlueLatch keeps monitoring Bluetooth and session state
- BlueLatch does not auto-lock again repeatedly
- BlueLatch will not clear the override until the phone comes back and presence is stable again

This prevents lock storms.

## Security and Privacy

BlueLatch is local-first.

- No cloud service is required.
- No telemetry is enabled by default.
- No phone GPS or phone location history is stored.
- Only necessary Bluetooth identity/config metadata is stored.
- Normal runtime does not require root.

### Security limitations

Bluetooth proximity is an approximation, not a secure proof of physical presence.

Limitations include:

- RSSI changes with body position, pockets, walls, desk placement, and radio noise.
- A phone can remain connected at longer-than-expected ranges.
- Different Bluetooth chipsets report different RSSI behavior.
- Suspend/resume, adapter resets, and GNOME lock backends vary across systems.

BlueLatch should be treated as a convenience security layer, not as a replacement for strong passwords, full-disk encryption, or standard workstation lock policies.

## First-Run Setup

1. Open BlueLatch.
2. Go to `Trusted Device`.
3. Start a scan and select your phone.
4. Pair and trust the device if required by BlueZ.
5. Choose `Use Selected`.
6. Open `Settings`.
7. Confirm the away grace period, lock method, reconnect behavior, and startup behavior.
8. Enable start-on-login if desired.

BlueLatch stores the trusted device:

- MAC address
- BlueZ object path
- alias/friendly name
- pair/trust flags

## Startup Behavior

BlueLatch supports per-user startup management.

- Preferred path: user-level systemd service
- Fallback path: XDG autostart desktop entry

The settings UI exposes `Start on login`. When enabled, BlueLatch installs or updates the per-user startup mechanism cleanly and reversibly.

The background agent is intended to run even when the main UI is not open.

## Update Behavior

BlueLatch checks GitHub Releases for updates.

- `Check for updates on startup` can be disabled in settings.
- The UI provides a manual `Updates` action.
- The result includes current version, latest version, release notes snippet, and package-aware guidance.

Package-specific behavior:

- AppImage:
  - preferred flow is download-and-replace
  - AppImage delta update support can be added later when release metadata is wired for it
- Debian / apt installs:
  - BlueLatch does not self-overwrite apt-managed installs
  - the app shows update guidance instead

## Screenshots

Placeholders live in `assets/screenshots/`.

Recommended captures for the first release:

- onboarding page
- trusted device selection page
- protection settings page
- live status page
- update dialog

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
│   ├── bluetooth/
│   ├── config/
│   ├── presence/
│   ├── session/
│   ├── startup/
│   ├── ui/
│   ├── updates/
│   └── util/
└── tests/
```

## Development Setup

Ubuntu 24.04 development dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
  bluez \
  gir1.2-adw-1 \
  gir1.2-gtk-4.0 \
  libnotify-bin \
  python3-gi \
  python3-gi-cairo \
  python3-packaging \
  python3-pip \
  python3-pytest
```

Optional Python build tooling:

```bash
python3 -m pip install --user build
```

Run the UI:

```bash
python3 -m bluelatch.main
```

Run the background agent only:

```bash
python3 -m bluelatch.main --agent
```

Run checks:

```bash
./scripts/check.sh
```

## Testing

The test suite covers:

- presence estimator behavior
- manual override state machine behavior
- reconnect backoff
- config persistence
- lock-method model stability
- integration-style manual override flow simulation

## Packaging

Build Debian package:

```bash
./scripts/build_deb.sh
```

Build AppImage:

```bash
./scripts/build_appimage.sh
```

Packaging assets live under:

- `packaging/debian/`
- `packaging/appimage/`
- `packaging/desktop/`
- `packaging/systemd/`

## CI and Releases

GitHub Actions workflow:

- installs system dependencies
- runs compile and pytest checks
- builds wheel and sdist
- builds `.deb`
- builds AppImage
- uploads artifacts
- publishes release assets on version tags

Release notes template:

- `.github/RELEASE_TEMPLATE.md`

Version source of truth:

- `src/bluelatch/version.py`

## Troubleshooting

### Bluetooth is off or no adapter is found

- Turn Bluetooth on in GNOME Settings.
- Confirm `bluetoothd` is running.
- Verify the current user can access BlueZ D-Bus.

### The trusted phone never reconnects

- Re-pair the phone if BlueZ lost trust/pairing metadata.
- Check whether the phone allows reconnect from the laptop side.
- Review `Logs` for reconnect backoff and BlueZ errors.

### The desktop does not lock

- Verify GNOME screen lock works manually.
- Confirm `loginctl lock-session` works for the current session.
- Try forcing the lock method to `GNOME` or `loginctl` in settings.

### The app keeps saying the phone is away

- Increase `Away grace`.
- Switch to `disconnect_only` mode.
- Lower sensitivity by adjusting RSSI thresholds and smoothing window.

### Startup does not stick

- Check whether `systemctl --user` is available and working.
- If a user service cannot be enabled, BlueLatch falls back to XDG autostart.

## Known Limitations

- The first release is GNOME-first and not yet tuned for KDE/XFCE session APIs.
- The UI currently reads runtime status/history from state files rather than a dedicated IPC bus.
- AppImage updating is guidance-first until release metadata is finalized for delta updates.
- Bluetooth behavior depends on the adapter, phone stack, and BlueZ behavior on the host.

## License

MIT. See `LICENSE`.
