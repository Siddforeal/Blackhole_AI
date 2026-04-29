"""
HTTP Parser for Blackhole AI Workbench.

Parses raw curl -i output into:
- status code
- response headers
- response body

Supports basic HTTP/1.x and HTTP/2 response transcripts.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParsedHTTPResponse:
    status_code: int | None
    headers: dict[str, str]
    body: str
    raw: str


def parse_http_response(raw: str) -> ParsedHTTPResponse:
    """Parse raw curl -i output into a structured response."""
    raw = raw or ""
    lines = raw.splitlines()

    response_start_indexes = [
        index for index, line in enumerate(lines)
        if line.startswith("HTTP/")
    ]

    if not response_start_indexes:
        return ParsedHTTPResponse(
            status_code=None,
            headers={},
            body=raw,
            raw=raw,
        )

    start = response_start_indexes[-1]
    status_line = lines[start]

    status_code = _parse_status_code(status_line)

    headers: dict[str, str] = {}
    body_start = len(lines)

    for index in range(start + 1, len(lines)):
        line = lines[index]

        if line.strip() == "":
            body_start = index + 1
            break

        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    body = "\n".join(lines[body_start:])

    return ParsedHTTPResponse(
        status_code=status_code,
        headers=headers,
        body=body,
        raw=raw,
    )


def _parse_status_code(status_line: str) -> int | None:
    parts = status_line.split()

    if len(parts) < 2:
        return None

    try:
        return int(parts[1])
    except ValueError:
        return None
