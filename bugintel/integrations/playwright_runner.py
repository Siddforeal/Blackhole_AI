"""
Browser Action Planner for BugIntel AI Workbench.

v0.3.0 foundation for browser automation.

This module does not launch a browser yet. It creates safe, reviewable browser
action plans and capture result models that future Playwright/Chrome/Firefox
runners can execute only after Scope Guard approval and human approval.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.core.scope_guard import TargetScope


@dataclass(frozen=True)
class BrowserAction:
    action_type: str
    value: str
    description: str


@dataclass
class BrowserPlan:
    allowed: bool
    reason: str
    target_name: str
    start_url: str
    browser: str
    actions: list[BrowserAction] = field(default_factory=list)
    requires_human_approval: bool = True


@dataclass
class BrowserCaptureResult:
    """
    Normalized result shape for future browser execution.

    This is intentionally execution-engine neutral. A future Playwright runner,
    Chrome runner, Firefox runner, or imported DevTools capture can populate the
    same shape before handing it to EvidenceStore.save_browser_evidence().
    """

    target_name: str
    task_name: str
    start_url: str
    browser: str
    network_events: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[dict[str, Any]] = field(default_factory=list)
    html_snapshots: list[dict[str, Any]] = field(default_factory=list)
    execution_output: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_evidence_kwargs(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "task_name": self.task_name,
            "start_url": self.start_url,
            "browser": self.browser,
            "network_events": self.network_events,
            "screenshots": self.screenshots,
            "html_snapshots": self.html_snapshots,
            "execution_output": self.execution_output,
            "notes": self.notes,
        }


def build_browser_plan(
    scope: TargetScope,
    start_url: str,
    browser: str = "chromium",
    capture_network: bool = True,
    capture_screenshot: bool = True,
) -> BrowserPlan:
    """
    Build a browser automation plan after Scope Guard approval.

    Supported browser labels:
    - chromium
    - chrome
    - firefox
    """
    browser = browser.lower().strip()

    if browser not in {"chromium", "chrome", "firefox"}:
        return BrowserPlan(
            allowed=False,
            reason=f"Unsupported browser: {browser}",
            target_name=scope.target_name,
            start_url=start_url,
            browser=browser,
            actions=[],
            requires_human_approval=True,
        )

    decision = scope.is_url_allowed(url=start_url, method="GET")

    if not decision.allowed:
        return BrowserPlan(
            allowed=False,
            reason=decision.reason,
            target_name=scope.target_name,
            start_url=start_url,
            browser=browser,
            actions=[],
            requires_human_approval=True,
        )

    actions = [
        BrowserAction(
            action_type="navigate",
            value=start_url,
            description="Navigate to the approved start URL.",
        )
    ]

    if capture_network:
        actions.append(
            BrowserAction(
                action_type="capture_network",
                value="enabled",
                description="Capture browser-observed requests and responses for analysis.",
            )
        )

    if capture_screenshot:
        actions.append(
            BrowserAction(
                action_type="capture_screenshot",
                value="enabled",
                description="Capture screenshot evidence after page load.",
            )
        )

    actions.append(
        BrowserAction(
            action_type="extract_html",
            value="document",
            description="Extract page HTML for passive endpoint, link, script, and form analysis.",
        )
    )

    return BrowserPlan(
        allowed=True,
        reason=decision.reason,
        target_name=scope.target_name,
        start_url=start_url,
        browser=browser,
        actions=actions,
        requires_human_approval=scope.human_approval_required,
    )


def build_browser_capture_result(
    plan: BrowserPlan,
    task_name: str,
    network_events: list[dict[str, Any]] | None = None,
    screenshots: list[dict[str, Any]] | None = None,
    html_snapshots: list[dict[str, Any]] | None = None,
    execution_output: dict[str, Any] | None = None,
    notes: str = "",
) -> BrowserCaptureResult:
    """
    Build a normalized browser capture result from an approved BrowserPlan.

    This does not execute a browser. It creates the handoff object that future
    Playwright execution can populate and then save as browser evidence.
    """
    if not plan.allowed:
        raise ValueError(f"Cannot build capture result from blocked browser plan: {plan.reason}")

    return BrowserCaptureResult(
        target_name=plan.target_name,
        task_name=task_name,
        start_url=plan.start_url,
        browser=plan.browser,
        network_events=list(network_events or []),
        screenshots=list(screenshots or []),
        html_snapshots=list(html_snapshots or []),
        execution_output=dict(execution_output or {}),
        notes=notes,
    )
