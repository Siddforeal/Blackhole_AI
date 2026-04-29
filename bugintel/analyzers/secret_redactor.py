"""
Secret Redactor for Blackhole AI Workbench.

Redacts sensitive values from logs, HTTP evidence, reports, and command output.
This helps prevent accidental exposure of tokens, cookies, emails, API keys,
and authorization headers.
"""

from __future__ import annotations

import re


REDACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Emails
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "<email>",
    ),

    # Bearer tokens
    (
        re.compile(r"(?i)\bAuthorization:\s*Bearer\s+[A-Za-z0-9._~+/=-]+"),
        "Authorization: Bearer <redacted>",
    ),

    # Raw bearer token fragments
    (
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
        "Bearer <redacted>",
    ),

    # JWT-like values
    (
        re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b"),
        "<jwt>",
    ),

    # Common API key patterns
    (
        re.compile(r"(?i)\b(api[_-]?key|x-api-key|access[_-]?token|secret)\s*[:=]\s*[A-Za-z0-9._~+/=-]{8,}"),
        r"\1=<redacted>",
    ),

    # Cookie header
    (
        re.compile(r"(?i)\bCookie:\s*.+"),
        "Cookie: <redacted>",
    ),

    # Set-Cookie header
    (
        re.compile(r"(?i)\bSet-Cookie:\s*.+"),
        "Set-Cookie: <redacted>",
    ),
]


def redact_text(text: str) -> str:
    """Return text with sensitive values redacted."""
    if not text:
        return text

    redacted = text

    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)

    return redacted


def redact_dict(data: dict) -> dict:
    """Recursively redact strings inside a dictionary."""
    clean = {}

    for key, value in data.items():
        if isinstance(value, str):
            clean[key] = redact_text(value)
        elif isinstance(value, dict):
            clean[key] = redact_dict(value)
        elif isinstance(value, list):
            clean[key] = [
                redact_dict(item) if isinstance(item, dict)
                else redact_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            clean[key] = value

    return clean
