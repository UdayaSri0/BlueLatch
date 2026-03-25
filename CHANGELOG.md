# Changelog

All notable changes to BlueLatch are tracked here.

The project follows Semantic Versioning.

## [0.1.1] - 2026-03-25

### Summary

- This release prepares BlueLatch for real-world distribution on Debian-based Linux systems and adds clearer install, run, and first-use guidance.

### Highlights

- Added proper Debian packaging for BlueLatch.
- Improved AppImage build and release artifact naming.
- Added release automation for `.deb`, AppImage, wheel, and source tarball.
- Added APT repository publishing support for Ubuntu, Linux Mint, and Debian-based systems.
- Hardened Debian and AppImage GitHub Actions packaging on Ubuntu 24.04.
- Improved packaging, installation, run, and usage documentation.

### Packaging and Distribution

- Users can now install BlueLatch using a Debian package.
- AppImage releases are easier to download and run.
- APT repository support has been prepared for simpler future upgrades.
- Release artifacts now use cleaner naming and checksum support.
- AppImage builds now use a consistent `setup-python` packaging toolchain in CI.

### Fixes

- Fixed the Debian build failure caused by the missing `packaging/debian` structure.
- Fixed Debian CI build failures caused by missing `dpkg-checkbuilddeps` prerequisites on the GitHub Actions runner.
- Fixed AppImage CI wheel builds by using the `setup-python` environment consistently instead of falling back to Ubuntu dist-packages.
- Fixed the AppImage GTK plugin failure on Ubuntu 24.04 runners by installing `libgtk-4-dev` so `gtk4.pc` is available.
- Improved build script reliability, artifact collection, and troubleshooting guidance.
- Cleaned up release workflow expectations.

### Upgrade Notes

- AppImage users should replace the previous AppImage with the new release file.
- Debian and APT users should install or upgrade through the package manager once the repository is published.
- BlueLatch remains GNOME-first and keeps the same core auto-lock-only behaviour.

### Known Issues

- BlueLatch is still primarily tuned for Ubuntu GNOME.
- Behaviour may vary slightly across Bluetooth adapters and desktop environments.

## [0.1.0] - 2026-03-21

### Added

- Initial Ubuntu GNOME focused release.
- BlueZ D-Bus monitoring for a single trusted device.
- Explicit presence state machine with manual unlock override protection.
- GTK4 + libadwaita settings UI, device picker, status page, logs page, and update dialog.
- User startup management, Debian packaging assets, AppImage packaging assets, and GitHub Actions workflow groundwork.
