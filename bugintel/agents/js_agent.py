"""
JavaScript Agent for BugIntel AI Workbench.

Collects JavaScript sources discovered in HTML and mines endpoints from them.

Safety:
- Script URLs are discovered from HTML only.
- Each script fetch passes through the Scope Guard.
- This module performs single-file fetches, not crawling.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bugintel.agents.recon_agent import analyze_html
from bugintel.analyzers.endpoint_miner import mine_endpoints
from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.web_fetcher import fetch_web_page


@dataclass
class JSSourceResult:
    url: str
    allowed: bool
    status_code: int | None
    reason: str
    endpoints: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass
class JSCollectionResult:
    page_url: str
    script_count: int
    sources: list[JSSourceResult]

    @property
    def all_endpoints(self) -> list[str]:
        values: set[str] = set()

        for source in self.sources:
            values.update(source.endpoints)

        return sorted(values)


def collect_js_sources(
    scope: TargetScope,
    page_url: str,
    html: str,
    timeout: int = 15,
) -> JSCollectionResult:
    """
    Collect and analyze JavaScript sources referenced by an HTML page.
    """
    recon = analyze_html(base_url=page_url, html=html)
    sources: list[JSSourceResult] = []

    for script_url in recon.scripts:
        fetched = fetch_web_page(scope=scope, url=script_url, timeout=timeout)

        if not fetched.allowed:
            sources.append(
                JSSourceResult(
                    url=script_url,
                    allowed=False,
                    status_code=None,
                    reason=fetched.reason,
                    endpoints=[],
                    error=fetched.error,
                )
            )
            continue

        if fetched.error:
            sources.append(
                JSSourceResult(
                    url=script_url,
                    allowed=True,
                    status_code=fetched.status_code,
                    reason=fetched.reason,
                    endpoints=[],
                    error=fetched.error,
                )
            )
            continue

        endpoints = sorted({endpoint.value for endpoint in mine_endpoints(fetched.text)})

        sources.append(
            JSSourceResult(
                url=script_url,
                allowed=True,
                status_code=fetched.status_code,
                reason=fetched.reason,
                endpoints=endpoints,
                error=None,
            )
        )

    return JSCollectionResult(
        page_url=page_url,
        script_count=len(recon.scripts),
        sources=sources,
    )
