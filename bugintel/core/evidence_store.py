"""
Evidence Store for BugIntel AI Workbench.

Stores redacted security-testing evidence as JSON files.

Design goals:
- Never store raw secrets accidentally.
- Save reproducible metadata.
- Hash response bodies for comparison.
- Keep evidence organized by target workspace.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bugintel.analyzers.secret_redactor import redact_dict, redact_text


@dataclass
class EvidenceRecord:
    target_name: str
    task_name: str
    url: str
    method: str
    status_code: int | None
    request: dict[str, Any]
    response_headers: dict[str, Any]
    response_body_preview: str
    response_body_sha256: str
    notes: str
    created_at: str


@dataclass(frozen=True)
class BrowserNetworkEvent:
    method: str
    url: str
    status_code: int | None = None
    resource_type: str = ""
    request_headers: dict[str, Any] = field(default_factory=dict)
    response_headers: dict[str, Any] = field(default_factory=dict)
    request_post_data_preview: str = ""
    response_body_preview: str = ""
    response_body_sha256: str = ""


@dataclass(frozen=True)
class BrowserScreenshotEvidence:
    path: str
    sha256: str = ""
    content_type: str = "image/png"
    notes: str = ""


@dataclass(frozen=True)
class BrowserHTMLSnapshot:
    url: str
    html_preview: str
    html_sha256: str


@dataclass(frozen=True)
class BrowserExecutionOutput:
    runner: str
    status: str
    stdout_preview: str = ""
    stderr_preview: str = ""
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserEvidenceRecord:
    kind: str
    target_name: str
    task_name: str
    start_url: str
    browser: str
    network_events: list[dict[str, Any]]
    screenshots: list[dict[str, Any]]
    html_snapshots: list[dict[str, Any]]
    execution_output: dict[str, Any]
    notes: str
    created_at: str


class EvidenceStore:
    def __init__(self, base_dir: str | Path = "data/evidence"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_http_evidence(
        self,
        target_name: str,
        task_name: str,
        url: str,
        method: str,
        request: dict[str, Any] | None = None,
        response_headers: dict[str, Any] | None = None,
        response_body: str = "",
        status_code: int | None = None,
        notes: str = "",
    ) -> Path:
        target_dir = self._target_dir(target_name)

        body_hash = self._sha256_text(response_body)
        body_preview = redact_text(response_body[:2000])

        record = EvidenceRecord(
            target_name=target_name,
            task_name=task_name,
            url=url,
            method=method.upper(),
            status_code=status_code,
            request=self._redact_value(request or {}),
            response_headers=self._redact_value(response_headers or {}),
            response_body_preview=body_preview,
            response_body_sha256=body_hash,
            notes=redact_text(notes),
            created_at=self._created_at(),
        )

        path = target_dir / self._filename(task_name)

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2, sort_keys=True)

        return path

    def save_browser_evidence(
        self,
        target_name: str,
        task_name: str,
        start_url: str,
        browser: str,
        network_events: list[dict[str, Any]] | None = None,
        screenshots: list[dict[str, Any]] | None = None,
        html_snapshots: list[dict[str, Any]] | None = None,
        execution_output: dict[str, Any] | None = None,
        notes: str = "",
    ) -> Path:
        """
        Save browser automation evidence from HAR/devtools/playwright-style runs.

        This intentionally stores redacted previews and hashes instead of raw
        response bodies or raw page HTML.
        """
        target_dir = self._target_dir(target_name)

        record = BrowserEvidenceRecord(
            kind="browser",
            target_name=target_name,
            task_name=task_name,
            start_url=start_url,
            browser=browser.lower().strip(),
            network_events=[
                self._normalise_network_event(event)
                for event in network_events or []
            ],
            screenshots=[
                self._normalise_screenshot(item)
                for item in screenshots or []
            ],
            html_snapshots=[
                self._normalise_html_snapshot(item, fallback_url=start_url)
                for item in html_snapshots or []
            ],
            execution_output=self._normalise_execution_output(execution_output or {}),
            notes=redact_text(notes),
            created_at=self._created_at(),
        )

        path = target_dir / self._filename(f"browser-{task_name}")

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2, sort_keys=True)

        return path

    def _normalise_network_event(self, event: dict[str, Any]) -> dict[str, Any]:
        clean = self._redact_value(dict(event))

        method = str(clean.get("method", "GET")).upper()
        clean["method"] = method

        response_body = event.get("response_body", "")
        if isinstance(response_body, str) and response_body:
            clean["response_body_preview"] = redact_text(response_body[:2000])
            clean["response_body_sha256"] = self._sha256_text(response_body)

        request_post_data = event.get("request_post_data", "")
        if isinstance(request_post_data, str) and request_post_data:
            clean["request_post_data_preview"] = redact_text(request_post_data[:2000])

        clean.pop("response_body", None)
        clean.pop("request_post_data", None)

        return clean

    def _normalise_screenshot(self, screenshot: dict[str, Any]) -> dict[str, Any]:
        clean = self._redact_value(dict(screenshot))
        clean.setdefault("content_type", "image/png")
        return clean

    def _normalise_html_snapshot(
        self,
        snapshot: dict[str, Any],
        fallback_url: str,
    ) -> dict[str, Any]:
        raw_html = str(
            snapshot.get("html")
            or snapshot.get("content")
            or snapshot.get("html_preview")
            or ""
        )

        clean = self._redact_value(
            {
                key: value
                for key, value in snapshot.items()
                if key not in {"html", "content", "html_preview"}
            }
        )

        clean["url"] = str(clean.get("url") or fallback_url)
        clean["html_preview"] = redact_text(raw_html[:4000])
        clean["html_sha256"] = self._sha256_text(raw_html)

        return clean

    def _normalise_execution_output(self, output: dict[str, Any]) -> dict[str, Any]:
        clean = self._redact_value(dict(output))

        for source_key, preview_key in {
            "stdout": "stdout_preview",
            "stderr": "stderr_preview",
        }.items():
            value = output.get(source_key, "")
            if isinstance(value, str) and value:
                clean[preview_key] = redact_text(value[:4000])
                clean.pop(source_key, None)

        return clean

    def _redact_value(self, value: Any) -> Any:
        if isinstance(value, dict):
            return redact_dict({
                str(key): self._redact_value(inner_value)
                for key, inner_value in value.items()
            })

        if isinstance(value, list):
            return [self._redact_value(item) for item in value]

        if isinstance(value, str):
            return redact_text(value)

        return value

    def _target_dir(self, target_name: str) -> Path:
        target_dir = self.base_dir / self._safe_name(target_name)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def _filename(self, task_name: str) -> str:
        return f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{self._safe_name(task_name)}.json"

    def _created_at(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _sha256_text(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()

    def _safe_name(self, value: str) -> str:
        allowed = []
        for char in value.lower().strip():
            if char.isalnum() or char in {"-", "_"}:
                allowed.append(char)
            elif char in {" ", ".", "/"}:
                allowed.append("-")

        safe = "".join(allowed).strip("-")
        return safe or "untitled"
