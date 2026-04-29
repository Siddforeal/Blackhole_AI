"""
Scope-guarded Website Fetcher for Blackhole AI Workbench.

Fetches a website page only after Scope Guard approval.

This module is intended for authorized passive website analysis:
- fetch HTML
- preserve status/headers/body
- do not crawl automatically
- do not run destructive actions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from bugintel.core.scope_guard import TargetScope


@dataclass
class WebFetchResult:
    allowed: bool
    reason: str
    url: str
    final_url: str | None
    status_code: int | None
    headers: dict[str, str]
    text: str
    error: str | None = None


def fetch_web_page(
    scope: TargetScope,
    url: str,
    timeout: int = 15,
) -> WebFetchResult:
    """
    Fetch a single web page after Scope Guard approval.

    Only GET is used in this MVP.
    """
    decision = scope.is_url_allowed(url=url, method="GET")

    if not decision.allowed:
        return WebFetchResult(
            allowed=False,
            reason=decision.reason,
            url=url,
            final_url=None,
            status_code=None,
            headers={},
            text="",
            error=None,
        )

    try:
        response = httpx.get(
            url,
            headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Blackhole-AI-Workbench/0.1 authorized-research",
            },
            follow_redirects=True,
            timeout=timeout,
        )

        return WebFetchResult(
            allowed=True,
            reason=decision.reason,
            url=url,
            final_url=str(response.url),
            status_code=response.status_code,
            headers={str(k).lower(): str(v) for k, v in response.headers.items()},
            text=response.text,
            error=None,
        )

    except httpx.HTTPError as exc:
        return WebFetchResult(
            allowed=True,
            reason=decision.reason,
            url=url,
            final_url=None,
            status_code=None,
            headers={},
            text="",
            error=str(exc),
        )
