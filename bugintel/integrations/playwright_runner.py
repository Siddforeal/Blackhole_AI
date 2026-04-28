"""
Browser Action Planner for BugIntel AI Workbench.

v0.3.0 foundation for browser automation.

This module does not launch a browser yet. It creates safe, reviewable browser
action plans and capture result models that future Playwright/Chrome/Firefox
runners can execute only after Scope Guard approval and human approval.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
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


@dataclass(frozen=True)
class PlaywrightAvailability:
    available: bool
    reason: str
    package_name: str = "playwright"


@dataclass(frozen=True)
class BrowserExecutionConfig:
    """
    Safe execution configuration for future Playwright runs.

    Live execution is intentionally disabled by default. This lets BugIntel
    build reviewable execution previews without launching a browser.
    """

    headless: bool = True
    timeout_ms: int = 15000
    wait_until: str = "load"
    capture_network: bool = True
    capture_screenshot: bool = True
    capture_html: bool = True
    screenshot_path: str = "artifacts/browser-screenshot.png"
    allow_live_execution: bool = False




@dataclass(frozen=True)
class PlaywrightArtifactPlan:
    """
    Planned artifact paths for future Playwright execution.

    These are only paths. Creating this object does not create files, launch a
    browser, save screenshots, or capture network traffic.
    """

    artifact_dir: str
    screenshot_path: str
    html_snapshot_path: str
    network_log_path: str
    trace_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "artifact_dir": self.artifact_dir,
            "screenshot_path": self.screenshot_path,
            "html_snapshot_path": self.html_snapshot_path,
            "network_log_path": self.network_log_path,
            "trace_path": self.trace_path,
        }


@dataclass(frozen=True)
class PlaywrightExecutionRequest:
    """
    Reviewable request object for a future Playwright execution adapter.

    This is the job ticket the real adapter will consume later. It is safe to
    build because it does not launch a browser.
    """

    target_name: str
    task_name: str
    start_url: str
    browser: str
    config: BrowserExecutionConfig
    artifacts: PlaywrightArtifactPlan
    planned_actions: list[dict[str, str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "task_name": self.task_name,
            "start_url": self.start_url,
            "browser": self.browser,
            "config": {
                "headless": self.config.headless,
                "timeout_ms": self.config.timeout_ms,
                "wait_until": self.config.wait_until,
                "capture_network": self.config.capture_network,
                "capture_screenshot": self.config.capture_screenshot,
                "capture_html": self.config.capture_html,
                "screenshot_path": self.config.screenshot_path,
                "allow_live_execution": self.config.allow_live_execution,
            },
            "artifacts": self.artifacts.to_dict(),
            "planned_actions": self.planned_actions,
        }




@dataclass(frozen=True)
class PlaywrightAdapterContext:
    """
    Internal context object for the future Playwright adapter.

    Human meaning: this is the safe engine-connector package. It carries the
    request and artifact paths to the future adapter, but it does not launch a
    browser by itself.
    """

    request: PlaywrightExecutionRequest
    artifact_dir_created: bool = False
    browser_launch_implemented: bool = False
    safety_notes: tuple[str, ...] = (
        "Adapter context prepared only.",
        "No browser launched.",
        "No network captured.",
        "No screenshots captured.",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request": self.request.to_dict(),
            "artifact_dir_created": self.artifact_dir_created,
            "browser_launch_implemented": self.browser_launch_implemented,
            "safety_notes": list(self.safety_notes),
        }


def build_playwright_adapter_context(
    request: PlaywrightExecutionRequest,
    create_artifact_dir: bool = False,
) -> PlaywrightAdapterContext:
    """
    Build internal context for the future Playwright adapter.

    This function does not launch a browser. By default, it also does not create
    directories. When create_artifact_dir=True, it creates only the planned
    artifact directory so future execution can write files there.
    """
    artifact_dir_created = False

    if create_artifact_dir:
        Path(request.artifacts.artifact_dir).mkdir(parents=True, exist_ok=True)
        artifact_dir_created = True

    return PlaywrightAdapterContext(
        request=request,
        artifact_dir_created=artifact_dir_created,
    )


def build_playwright_artifact_plan(
    target_name: str,
    task_name: str,
    base_dir: str | Path = "artifacts/browser",
) -> PlaywrightArtifactPlan:
    """
    Plan artifact paths for future Playwright execution.

    This does not create directories or files. It only returns deterministic
    safe paths that later execution can use.
    """
    base = Path(base_dir)
    artifact_dir = base / _safe_artifact_name(target_name) / _safe_artifact_name(task_name)

    return PlaywrightArtifactPlan(
        artifact_dir=str(artifact_dir),
        screenshot_path=str(artifact_dir / "screenshot.png"),
        html_snapshot_path=str(artifact_dir / "page.html"),
        network_log_path=str(artifact_dir / "network.json"),
        trace_path=str(artifact_dir / "trace.zip"),
    )


def build_playwright_execution_request(
    plan: BrowserPlan,
    task_name: str,
    config: BrowserExecutionConfig | None = None,
    base_artifact_dir: str | Path = "artifacts/browser",
) -> PlaywrightExecutionRequest:
    """
    Build a future Playwright execution request from an approved BrowserPlan.

    This is still pre-execution. It does not launch a browser.
    """
    if not plan.allowed:
        raise ValueError(f"Cannot build Playwright execution request from blocked browser plan: {plan.reason}")

    config = config or BrowserExecutionConfig()
    artifacts = build_playwright_artifact_plan(
        target_name=plan.target_name,
        task_name=task_name,
        base_dir=base_artifact_dir,
    )

    return PlaywrightExecutionRequest(
        target_name=plan.target_name,
        task_name=task_name,
        start_url=plan.start_url,
        browser=plan.browser,
        config=config,
        artifacts=artifacts,
        planned_actions=[
            {
                "action_type": action.action_type,
                "value": action.value,
                "description": action.description,
            }
            for action in plan.actions
        ],
    )


def _safe_artifact_name(value: str) -> str:
    allowed = []

    for char in value.lower().strip():
        if char.isalnum() or char in {"-", "_"}:
            allowed.append(char)
        elif char in {" ", ".", "/"}:
            allowed.append("-")

    safe = "".join(allowed).strip("-")
    return safe or "untitled"




def run_playwright_adapter_stub(
    context: PlaywrightAdapterContext,
    notes: str = "",
    availability: PlaywrightAvailability | None = None,
) -> BrowserCaptureResult:
    """
    Stub runner for the future Playwright adapter.

    Human meaning: this is the future engine entry point, but the engine is not
    installed yet. It converts an adapter context into a BrowserCaptureResult
    with status "not_implemented" and does not launch a browser.
    """
    request = context.request

    execution_output = {
        "runner": "playwright",
        "status": "not_implemented",
        "reason": "Playwright adapter stub reached; live browser launch is not implemented yet.",
        "browser_launch_implemented": context.browser_launch_implemented,
        "artifact_dir_created": context.artifact_dir_created,
        "live_execution_allowed": request.config.allow_live_execution,
        "artifacts": request.artifacts.to_dict(),
        "safety_notes": list(context.safety_notes),
    }

    if availability is not None:
        execution_output["playwright_available"] = availability.available
        execution_output["playwright_availability_reason"] = availability.reason

    return BrowserCaptureResult(
        target_name=request.target_name,
        task_name=request.task_name,
        start_url=request.start_url,
        browser=request.browser,
        network_events=[],
        screenshots=[],
        html_snapshots=[],
        execution_output=execution_output,
        notes=notes or "Playwright adapter stub only; browser not launched.",
    )


def check_playwright_available() -> PlaywrightAvailability:
    """
    Check whether the optional Playwright Python package is importable.

    This does not install packages, download browsers, or launch a browser.
    """
    if importlib.util.find_spec("playwright") is None:
        return PlaywrightAvailability(
            available=False,
            reason="Python package 'playwright' is not installed.",
        )

    if importlib.util.find_spec("playwright.sync_api") is None:
        return PlaywrightAvailability(
            available=False,
            reason="Python package 'playwright.sync_api' is not available.",
        )

    return PlaywrightAvailability(
        available=True,
        reason="Playwright Python package is available.",
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
    Build a BrowserCaptureResult from an approved browser plan.

    This normalizes future Playwright adapter output into the evidence-store
    shape. It does not launch a browser by itself.
    """
    if not plan.allowed:
        raise ValueError(f"Cannot build capture result from blocked browser plan: {plan.reason}")

    return BrowserCaptureResult(
        target_name=plan.target_name,
        task_name=task_name,
        start_url=plan.start_url,
        browser=plan.browser,
        network_events=network_events or [],
        screenshots=screenshots or [],
        html_snapshots=html_snapshots or [],
        execution_output=execution_output or {},
        notes=notes,
    )


def build_playwright_execution_preview(
    plan: BrowserPlan,
    config: BrowserExecutionConfig | None = None,
) -> dict[str, Any]:
    """
    Build a safe, reviewable Playwright execution preview.

    This does not launch a browser. It records whether live execution would be
    allowed and whether the optional Playwright package is available.
    """
    if not plan.allowed:
        raise ValueError(f"Cannot build Playwright execution preview from blocked browser plan: {plan.reason}")

    config = config or BrowserExecutionConfig()
    availability = check_playwright_available()

    if not config.allow_live_execution:
        status = "preview"
    elif availability.available:
        status = "ready"
    else:
        status = "unavailable"

    return {
        "runner": "playwright",
        "status": status,
        "live_execution_allowed": config.allow_live_execution,
        "playwright_available": availability.available,
        "reason": availability.reason,
        "browser": plan.browser,
        "start_url": plan.start_url,
        "headless": config.headless,
        "timeout_ms": config.timeout_ms,
        "wait_until": config.wait_until,
        "capture_network": config.capture_network,
        "capture_screenshot": config.capture_screenshot,
        "capture_html": config.capture_html,
        "screenshot_path": config.screenshot_path,
        "planned_actions": [
            {
                "action_type": action.action_type,
                "value": action.value,
                "description": action.description,
            }
            for action in plan.actions
        ],
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



class PlaywrightExecutionSafetyError(RuntimeError):
    """Raised when live Playwright execution is blocked by the safety gate."""


def execute_playwright_plan(
    plan: BrowserPlan,
    task_name: str,
    config: BrowserExecutionConfig | None = None,
    notes: str = "",
) -> BrowserCaptureResult:
    """
    Safety-gated skeleton for future live Playwright execution.

    This function intentionally does not launch a browser yet. It enforces the
    checks that must pass before a future live adapter is allowed to run:

    - BrowserPlan must be allowed by Scope Guard.
    - BrowserExecutionConfig.allow_live_execution must be True.
    - Optional Playwright package must be importable.

    Once those gates pass, this function now routes through the internal
    Playwright adapter context and adapter stub runner. The stub still returns
    execution_output status "not_implemented" so real browser launch can be
    added behind the same safety gate later.
    """
    if not plan.allowed:
        raise PlaywrightExecutionSafetyError(f"Cannot execute blocked browser plan: {plan.reason}")

    config = config or BrowserExecutionConfig()

    if not config.allow_live_execution:
        raise PlaywrightExecutionSafetyError(
            "Live Playwright execution is disabled. Set allow_live_execution=True only after human approval."
        )

    availability = check_playwright_available()

    if not availability.available:
        raise PlaywrightExecutionSafetyError(availability.reason)

    request = build_playwright_execution_request(
        plan=plan,
        task_name=task_name,
        config=config,
    )

    context = build_playwright_adapter_context(request)

    return run_playwright_adapter_stub(
        context=context,
        notes=notes,
        availability=availability,
    )
