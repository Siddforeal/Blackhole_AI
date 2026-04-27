"""
Endpoint Miner for BugIntel AI Workbench.

Extracts API-like endpoints from JavaScript, HTML, HAR text, Burp exports,
curl logs, and general text.

This module does not send network requests. It only parses provided text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse


ABSOLUTE_URL_RE = re.compile(
    r"https?://[A-Za-z0-9.-]+(?::\d+)?/[^\s\"'<>`)]*",
    re.IGNORECASE,
)

QUOTED_PATH_RE = re.compile(
    r"""["'`](?P<path>/(?:api|v[0-9]+|graphql|auth|oauth|admin|user|users|account|accounts|project|projects|export|exports|integration|integrations|webhook|webhooks|upload|uploads|file|files|setting|settings|billing|payment|payments)[^"'`\s<>]*)["'`]""",
    re.IGNORECASE,
)

METHOD_PATH_RE = re.compile(
    r"\b(GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD)\s+(/[^\s\"'<>]+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Endpoint:
    value: str
    category: str
    source: str


def mine_endpoints(text: str) -> list[Endpoint]:
    """Extract and categorize endpoints from raw text."""
    if not text:
        return []

    found: dict[str, Endpoint] = {}

    for match in ABSOLUTE_URL_RE.finditer(text):
        raw = _clean(match.group(0))
        parsed = urlparse(raw)
        value = parsed.path or "/"
        if parsed.query:
            value += "?" + parsed.query

        found[value] = Endpoint(
            value=value,
            category=categorize_endpoint(value),
            source="absolute_url",
        )

    for match in QUOTED_PATH_RE.finditer(text):
        value = _clean(match.group("path"))
        found[value] = Endpoint(
            value=value,
            category=categorize_endpoint(value),
            source="quoted_path",
        )

    for match in METHOD_PATH_RE.finditer(text):
        value = _clean(match.group(2))
        found[value] = Endpoint(
            value=value,
            category=categorize_endpoint(value),
            source="method_path",
        )

    return sorted(found.values(), key=lambda item: item.value)


def categorize_endpoint(endpoint: str) -> str:
    """Assign a rough category to an endpoint path."""
    value = endpoint.lower()

    if "graphql" in value:
        return "graphql"

    if any(x in value for x in ["auth", "oauth", "login", "logout", "session", "token"]):
        return "auth"

    if "admin" in value:
        return "admin"

    if any(x in value for x in ["user", "users", "me", "profile"]):
        return "user"

    if any(x in value for x in ["account", "accounts", "tenant", "organization", "org"]):
        return "account"

    if any(x in value for x in ["project", "projects", "workspace"]):
        return "project"

    if any(x in value for x in ["export", "download", "report"]):
        return "export"

    if any(x in value for x in ["integration", "integrations", "webhook", "webhooks"]):
        return "integration"

    if any(x in value for x in ["upload", "uploads", "file", "files", "attachment"]):
        return "file"

    if any(x in value for x in ["billing", "payment", "invoice", "subscription"]):
        return "billing"

    if value.startswith("/api") or re.match(r"^/v[0-9]+/", value):
        return "api"

    return "unknown"


def _clean(value: str) -> str:
    """Remove common trailing characters from extracted endpoints."""
    return value.strip().rstrip(".,;)")
