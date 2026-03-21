from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

from bluelatch.models import PackageType
from bluelatch.updates.github import GitHubReleaseClient
from bluelatch.updates.models import ReleaseInfo, UpdateCheckResult


class InstallationDetector:
    def __init__(self, executable: Path | None = None) -> None:
        self.executable = executable or Path(sys.argv[0]).resolve()

    def detect(self) -> PackageType:
        if os.environ.get("APPIMAGE"):
            return PackageType.APPIMAGE
        if shutil.which("dpkg-query"):
            result = subprocess.run(
                ["dpkg-query", "-S", str(self.executable)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return PackageType.DEB
        repo_root = Path(__file__).resolve().parents[3]
        if (repo_root / ".git").exists():
            return PackageType.SOURCE
        return PackageType.UNKNOWN


class UpdateService:
    def __init__(
        self,
        owner: str = "UdayaSri0",
        repo: str = "BlueLatch",
        detector: InstallationDetector | None = None,
    ) -> None:
        self.client = GitHubReleaseClient(owner=owner, repo=repo)
        self.detector = detector or InstallationDetector()

    def check_for_updates(self, current_version: str) -> UpdateCheckResult:
        package_type = self.detector.detect()
        try:
            release = self.client.fetch_latest_release()
        except Exception as exc:
            return UpdateCheckResult(
                current_version=current_version,
                latest_version=None,
                update_available=False,
                package_type=package_type,
                guidance="Unable to reach GitHub Releases.",
                error=str(exc),
            )

        update_available = self._is_newer(release, current_version)
        return UpdateCheckResult(
            current_version=current_version,
            latest_version=release.version,
            update_available=update_available,
            package_type=package_type,
            guidance=self._guidance_for(package_type, release),
            release_url=release.html_url,
            notes=release.notes,
        )

    @staticmethod
    def _is_newer(release: ReleaseInfo, current_version: str) -> bool:
        try:
            return Version(release.version) > Version(current_version)
        except InvalidVersion:
            return release.version != current_version

    @staticmethod
    def _guidance_for(package_type: PackageType, release: ReleaseInfo) -> str:
        if package_type is PackageType.APPIMAGE:
            return (
                "Download the new AppImage release and replace the existing file. "
                "If AppImageUpdate metadata is present, use AppImageUpdate for delta updates."
            )
        if package_type is PackageType.DEB:
            return (
                "Update BlueLatch through apt, Software Updater, or by installing the newer .deb package. "
                "BlueLatch will not self-overwrite apt-managed installs."
            )
        return (
            f"Install release {release.version} from GitHub Releases or rebuild from source."
        )
