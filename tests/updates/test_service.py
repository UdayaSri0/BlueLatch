from __future__ import annotations

from bluelatch.updates.models import ReleaseInfo
from bluelatch.updates.service import UpdateService


def test_version_comparison_detects_newer_release() -> None:
    release = ReleaseInfo(
        version="1.2.0",
        published_at="2026-03-21T00:00:00Z",
        html_url="https://example.invalid/release",
        notes="",
    )
    assert UpdateService._is_newer(release, "1.1.9") is True
    assert UpdateService._is_newer(release, "1.2.0") is False
