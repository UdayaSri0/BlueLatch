from __future__ import annotations

from dataclasses import dataclass

from bluelatch.models import PackageType


@dataclass(slots=True)
class ReleaseInfo:
    version: str
    published_at: str | None
    html_url: str
    notes: str
    draft: bool = False
    prerelease: bool = False


@dataclass(slots=True)
class UpdateCheckResult:
    current_version: str
    latest_version: str | None
    update_available: bool
    package_type: PackageType
    guidance: str
    release_url: str | None = None
    notes: str | None = None
    error: str | None = None
