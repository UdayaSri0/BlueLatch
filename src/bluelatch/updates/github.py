from __future__ import annotations

import json
import urllib.request

from bluelatch.updates.models import ReleaseInfo


class GitHubReleaseClient:
    def __init__(self, owner: str, repo: str) -> None:
        self.owner = owner
        self.repo = repo

    @property
    def latest_release_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/releases/latest"

    def fetch_latest_release(self, timeout: int = 10) -> ReleaseInfo:
        request = urllib.request.Request(
            self.latest_release_url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "BlueLatch Update Checker",
            },
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        notes = str(payload.get("body") or "").strip()
        snippet = notes[:500].strip()
        return ReleaseInfo(
            version=str(payload.get("tag_name", "")).lstrip("v"),
            published_at=payload.get("published_at"),
            html_url=str(payload.get("html_url", "")),
            notes=snippet,
            draft=bool(payload.get("draft", False)),
            prerelease=bool(payload.get("prerelease", False)),
        )
