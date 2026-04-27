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
from dataclasses import asdict, dataclass
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
        clean_target = self._safe_name(target_name)
        target_dir = self.base_dir / clean_target
        target_dir.mkdir(parents=True, exist_ok=True)

        body_hash = hashlib.sha256(response_body.encode("utf-8", errors="replace")).hexdigest()
        body_preview = redact_text(response_body[:2000])

        record = EvidenceRecord(
            target_name=target_name,
            task_name=task_name,
            url=url,
            method=method.upper(),
            status_code=status_code,
            request=redact_dict(request or {}),
            response_headers=redact_dict(response_headers or {}),
            response_body_preview=body_preview,
            response_body_sha256=body_hash,
            notes=redact_text(notes),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        filename = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{self._safe_name(task_name)}.json"
        path = target_dir / filename

        with path.open("w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2, sort_keys=True)

        return path

    def _safe_name(self, value: str) -> str:
        allowed = []
        for char in value.lower().strip():
            if char.isalnum() or char in {"-", "_"}:
                allowed.append(char)
            elif char in {" ", ".", "/"}:
                allowed.append("-")

        safe = "".join(allowed).strip("-")
        return safe or "untitled"
