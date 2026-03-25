# Changelog

All notable changes to BlueLatch are tracked here.

The project follows Semantic Versioning.

## [0.1.1] - 2026-03-25

### Summary

- This release finishes the Linux desktop distribution story for Debian-family systems without changing BlueLatch core behavior.

### Highlights

- BlueLatch still auto-locks only, never auto-unlocks, and preserves the manual unlock override behavior.
- Debian packaging is now complete and builds a real `bluelatch_0.1.1_amd64.deb` package from `packaging/debian/`.
- AppImage packaging now emits a stable `BlueLatch-0.1.1-x86_64.AppImage` artifact with a portable launcher path.

### Packaging and Distribution

- Added a full Debian packaging tree under `packaging/debian/` using `pybuild` and pyproject-aware tooling.
- Installed the desktop launcher, SVG icon, AppStream metadata, and packaged user service unit through Debian packaging.
- Rewrote `scripts/build_deb.sh` to validate packaging inputs, stage a clean build tree, and place artifacts in `dist/debian/`.
- Reworked `scripts/build_appimage.sh` to validate metadata, stage a clean AppDir, and place the final AppImage in `dist/`.
- Added portable AppImage launcher wrappers so the packaged app no longer depends on a build-host-specific Python shebang.
- Added release asset collection and checksum generation for wheel, sdist, Debian package, and AppImage outputs.
- Added a signed GitHub Pages APT repository publishing flow using `reprepro` and GPG.
- Split GitHub Actions into separate CI and tagged release workflows with explicit artifact paths and release publishing.

### Fixes

- Fixed the failing Debian build path caused by the missing `packaging/debian/` directory.
- Fixed inconsistent version reporting between package metadata and release artifacts by aligning all release-facing version references to `0.1.1`.
- Fixed release-note publishing so tag builds use generated notes from the current changelog entry instead of a placeholder template.
- Corrected the documented local development flow to use an editable install before running the app from source.

### Upgrade Notes

- AppImage users should replace their existing AppImage with `BlueLatch-0.1.1-x86_64.AppImage` and keep it executable.
- Debian and APT users can update through `apt`, Software Updater, or by installing the newer `.deb`.
- The GitHub Pages APT repository uses a `signed-by` keyring setup and does not use `apt-key`.

### Known Issues

- BlueLatch remains GNOME-first and is not yet tuned for every non-GNOME session-lock backend.
- The AppImage flow is intended for Debian-family systems with the expected desktop Bluetooth stack available.

## [0.1.0] - 2026-03-21

### Added

- Initial Ubuntu GNOME focused release.
- BlueZ D-Bus monitoring for a single trusted device.
- Explicit presence state machine with manual unlock override protection.
- GTK4 + libadwaita settings UI, device picker, status page, logs page, and update dialog.
- User startup management, Debian packaging assets, AppImage packaging assets, and GitHub Actions workflow groundwork.
