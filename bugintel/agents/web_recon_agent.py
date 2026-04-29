"""
Website Recon Agent for Blackhole AI Workbench.

This is the first Website Mode pipeline.

Flow:
- Scope-guarded page fetch
- Passive HTML analysis
- JavaScript source collection
- Endpoint merging
- Multi-agent orchestration plan generation

This module does not perform crawling or destructive testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from bugintel.agents.js_agent import JSCollectionResult, collect_js_sources
from bugintel.agents.recon_agent import WebReconResult, analyze_html
from bugintel.core.orchestrator import OrchestrationPlan, create_orchestration_plan
from bugintel.core.scope_guard import TargetScope
from bugintel.integrations.web_fetcher import WebFetchResult, fetch_web_page


@dataclass
class WebsiteReconPipelineResult:
    target_name: str
    page_url: str
    fetch: WebFetchResult
    html_recon: WebReconResult | None
    js_recon: JSCollectionResult | None
    endpoints: list[str] = field(default_factory=list)
    orchestration_plan: OrchestrationPlan | None = None

    @property
    def allowed(self) -> bool:
        return self.fetch.allowed

    @property
    def successful(self) -> bool:
        return self.fetch.allowed and self.fetch.error is None and self.fetch.status_code is not None


def run_website_recon(
    scope: TargetScope,
    page_url: str,
    timeout: int = 15,
) -> WebsiteReconPipelineResult:
    """
    Run the website recon pipeline for a single in-scope page.
    """
    fetched = fetch_web_page(scope=scope, url=page_url, timeout=timeout)

    if not fetched.allowed or fetched.error or fetched.text == "":
        return WebsiteReconPipelineResult(
            target_name=scope.target_name,
            page_url=page_url,
            fetch=fetched,
            html_recon=None,
            js_recon=None,
            endpoints=[],
            orchestration_plan=None,
        )

    final_url = fetched.final_url or page_url

    html_recon = analyze_html(
        base_url=final_url,
        html=fetched.text,
    )

    js_recon = collect_js_sources(
        scope=scope,
        page_url=final_url,
        html=fetched.text,
        timeout=timeout,
    )

    endpoints = sorted(set(html_recon.endpoints) | set(js_recon.all_endpoints))

    plan = create_orchestration_plan(
        target_name=scope.target_name,
        endpoints=endpoints,
    )

    return WebsiteReconPipelineResult(
        target_name=scope.target_name,
        page_url=page_url,
        fetch=fetched,
        html_recon=html_recon,
        js_recon=js_recon,
        endpoints=endpoints,
        orchestration_plan=plan,
    )
