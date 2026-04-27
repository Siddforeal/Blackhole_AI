"""
Report Agent for BugIntel AI Workbench.

Converts structured evidence JSON into a human-reviewable Markdown evidence report.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_evidence(path: str | Path) -> dict[str, Any]:
    evidence_path = Path(path)

    if not evidence_path.exists():
        raise FileNotFoundError(f"Evidence file not found: {evidence_path}")

    return json.loads(evidence_path.read_text(encoding="utf-8"))


def generate_evidence_report(evidence: dict[str, Any]) -> str:
    target = evidence.get("target_name", "unknown-target")
    task = evidence.get("task_name", "unknown-task")
    method = evidence.get("method", "GET")
    url = evidence.get("url", "")
    status_code = evidence.get("status_code", "unknown")
    created_at = evidence.get("created_at", "unknown")
    body_preview = evidence.get("response_body_preview", "")
    body_hash = evidence.get("response_body_sha256", "")
    notes = evidence.get("notes", "")
    headers = evidence.get("response_headers", {})

    header_lines = []
    for key, value in sorted(headers.items()):
        header_lines.append(f"- {key}: {value}")

    headers_md = "\n".join(header_lines) if header_lines else "- No headers captured"

    return f"""# Evidence Report: {task}

## Summary

- Target: {target}
- Task: {task}
- Method: {method}
- URL: {url}
- Status Code: {status_code}
- Captured At: {created_at}

## Response Headers

{headers_md}

## Response Body Preview

{body_preview}

## Response Body SHA256

{body_hash}

## Notes

{notes}

## Analyst Review Checklist

- [ ] Confirm the endpoint is in authorized scope.
- [ ] Confirm the response was collected from the correct account or session.
- [ ] Compare against baseline, blocked, and random-ID responses.
- [ ] Check whether any sensitive fields are exposed.
- [ ] Validate impact manually before writing a final finding.
"""


def save_evidence_report(evidence_path: str | Path, output_path: str | Path) -> Path:
    evidence = load_evidence(evidence_path)
    report = generate_evidence_report(evidence)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")

    return out
