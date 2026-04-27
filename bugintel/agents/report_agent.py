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
    if evidence.get("kind") == "browser":
        return generate_browser_evidence_report(evidence)

    return generate_http_evidence_report(evidence)


def generate_http_evidence_report(evidence: dict[str, Any]) -> str:
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

    headers_md = _format_key_values(headers, empty="- No headers captured")

    return f"""# Evidence Report: {task}

## Summary

- Target: {target}
- Task: {task}
- Evidence Type: http
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


def generate_browser_evidence_report(evidence: dict[str, Any]) -> str:
    target = evidence.get("target_name", "unknown-target")
    task = evidence.get("task_name", "unknown-task")
    start_url = evidence.get("start_url", "")
    browser = evidence.get("browser", "unknown-browser")
    created_at = evidence.get("created_at", "unknown")
    notes = evidence.get("notes", "")

    network_events = evidence.get("network_events", [])
    screenshots = evidence.get("screenshots", [])
    html_snapshots = evidence.get("html_snapshots", [])
    execution_output = evidence.get("execution_output", {})

    return f"""# Evidence Report: {task}

## Summary

- Target: {target}
- Task: {task}
- Evidence Type: browser
- Browser: {browser}
- Start URL: {start_url}
- Captured At: {created_at}
- Network Events: {len(network_events) if isinstance(network_events, list) else 0}
- Screenshots: {len(screenshots) if isinstance(screenshots, list) else 0}
- HTML Snapshots: {len(html_snapshots) if isinstance(html_snapshots, list) else 0}

## Browser Network Events

{_format_browser_network_events(network_events)}

## Screenshots

{_format_screenshots(screenshots)}

## HTML Snapshots

{_format_html_snapshots(html_snapshots)}

## Browser Execution Output

{_format_execution_output(execution_output)}

## Notes

{notes}

## Analyst Review Checklist

- [ ] Confirm the browser start URL is in authorized scope.
- [ ] Confirm the browser session/account used for capture.
- [ ] Review browser-observed requests for sensitive endpoints.
- [ ] Compare interesting requests against baseline, blocked, and random-ID responses.
- [ ] Check whether screenshots or HTML previews expose sensitive data.
- [ ] Validate impact manually before writing a final finding.
"""


def save_evidence_report(evidence_path: str | Path, output_path: str | Path) -> Path:
    evidence = load_evidence(evidence_path)
    report = generate_evidence_report(evidence)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")

    return out


def _format_browser_network_events(events: Any) -> str:
    if not isinstance(events, list) or not events:
        return "- No browser network events captured"

    sections = []

    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            continue

        method = event.get("method", "GET")
        url = event.get("url", "")
        status_code = event.get("status_code", "unknown")
        resource_type = event.get("resource_type", "")
        response_hash = event.get("response_body_sha256", "")
        response_preview = event.get("response_body_preview", "")
        request_preview = event.get("request_post_data_preview", "")
        request_headers = event.get("request_headers", {})
        response_headers = event.get("response_headers", {})

        section = f"""### Event {index}: {method} {url}

- Status Code: {status_code}
- Resource Type: {resource_type}
- Response Body SHA256: {response_hash}

Request Headers:

{_format_key_values(request_headers, empty="- No request headers captured")}

Response Headers:

{_format_key_values(response_headers, empty="- No response headers captured")}
"""

        if request_preview:
            section += f"""

Request Body Preview:

    {request_preview}
"""

        if response_preview:
            section += f"""

Response Body Preview:

    {response_preview}
"""

        sections.append(section.rstrip())

    return "\n\n".join(sections) if sections else "- No browser network events captured"


def _format_screenshots(screenshots: Any) -> str:
    if not isinstance(screenshots, list) or not screenshots:
        return "- No screenshots captured"

    lines = []

    for item in screenshots:
        if not isinstance(item, dict):
            continue

        path = item.get("path", "")
        sha256 = item.get("sha256", "")
        content_type = item.get("content_type", "")
        notes = item.get("notes", "")

        lines.append(f"- Path: {path}")
        if sha256:
            lines.append(f"  - SHA256: {sha256}")
        if content_type:
            lines.append(f"  - Content Type: {content_type}")
        if notes:
            lines.append(f"  - Notes: {notes}")

    return "\n".join(lines) if lines else "- No screenshots captured"


def _format_html_snapshots(snapshots: Any) -> str:
    if not isinstance(snapshots, list) or not snapshots:
        return "- No HTML snapshots captured"

    sections = []

    for index, snapshot in enumerate(snapshots, start=1):
        if not isinstance(snapshot, dict):
            continue

        url = snapshot.get("url", "")
        html_hash = snapshot.get("html_sha256", "")
        preview = snapshot.get("html_preview", "")

        section = f"""### Snapshot {index}

- URL: {url}
- HTML SHA256: {html_hash}
"""

        if preview:
            section += f"""

HTML Preview:

    {preview}
"""

        sections.append(section.rstrip())

    return "\n\n".join(sections) if sections else "- No HTML snapshots captured"


def _format_execution_output(output: Any) -> str:
    if not isinstance(output, dict) or not output:
        return "- No browser execution output captured"

    runner = output.get("runner", "")
    status = output.get("status", "")
    reason = output.get("reason", "")
    stdout_preview = output.get("stdout_preview", "")
    stderr_preview = output.get("stderr_preview", "")
    artifacts = output.get("artifacts", {})

    lines = []

    if runner:
        lines.append(f"- Runner: {runner}")
    if status:
        lines.append(f"- Status: {status}")
    if reason:
        lines.append(f"- Reason: {reason}")

    if artifacts:
        lines.append("")
        lines.append("Artifacts:")
        lines.append("")
        lines.append(_format_key_values(artifacts, empty="- No artifacts captured"))

    if stdout_preview:
        lines.append("")
        lines.append("Stdout Preview:")
        lines.append("")
        lines.append(f"    {stdout_preview}")

    if stderr_preview:
        lines.append("")
        lines.append("Stderr Preview:")
        lines.append("")
        lines.append(f"    {stderr_preview}")

    return "\n".join(lines) if lines else "- No browser execution output captured"


def _format_key_values(mapping: Any, empty: str) -> str:
    if not isinstance(mapping, dict) or not mapping:
        return empty

    lines = []
    for key, value in sorted(mapping.items()):
        lines.append(f"- {key}: {_format_value(value)}")

    return "\n".join(lines)


def _format_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)

    return str(value)
