"""
HAR Importer for BugIntel AI Workbench.

Parses HAR files exported from browser DevTools, proxy tools, or compatible
traffic capture utilities.

This module does not send network requests. It only parses provided HAR data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from bugintel.analyzers.endpoint_miner import categorize_endpoint


@dataclass(frozen=True)
class HAREntry:
    method: str
    url: str
    endpoint: str
    status_code: int | None
    mime_type: str
    category: str


@dataclass(frozen=True)
class HARImportResult:
    entries: list[HAREntry]

    @property
    def endpoints(self) -> list[str]:
        return sorted({entry.endpoint for entry in self.entries if entry.endpoint})

    @property
    def api_entries(self) -> list[HAREntry]:
        return [
            entry for entry in self.entries
            if entry.category not in {"unknown"} or entry.endpoint.startswith("/api")
        ]


def load_har(path: str | Path) -> HARImportResult:
    har_path = Path(path)

    if not har_path.exists():
        raise FileNotFoundError(f"HAR file not found: {har_path}")

    data = json.loads(har_path.read_text(encoding="utf-8"))
    return import_har_from_dict(data)


def import_har_from_dict(data: dict) -> HARImportResult:
    log = data.get("log", {})
    raw_entries = log.get("entries", [])

    entries: list[HAREntry] = []

    for item in raw_entries:
        request = item.get("request", {})
        response = item.get("response", {})

        method = str(request.get("method", "GET")).upper()
        url = str(request.get("url", ""))
        endpoint = endpoint_from_url(url)

        status_code = response.get("status")
        if not isinstance(status_code, int):
            status_code = None

        content = response.get("content", {})
        mime_type = str(content.get("mimeType", ""))

        entries.append(
            HAREntry(
                method=method,
                url=url,
                endpoint=endpoint,
                status_code=status_code,
                mime_type=mime_type,
                category=categorize_endpoint(endpoint),
            )
        )

    return HARImportResult(entries=entries)


def endpoint_from_url(url: str) -> str:
    parsed = urlparse(url)

    if not parsed.scheme or not parsed.netloc:
        return url

    endpoint = parsed.path or "/"

    if parsed.query:
        endpoint += "?" + parsed.query

    return endpoint
