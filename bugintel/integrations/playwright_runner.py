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


@dataclass(frozen=True)
class BrowserNetworkEvent:
    """Typed browser network evidence item."""

    method: str
    url: str
    status_code: int | None = None
    resource_type: str = ""
    request_headers: dict[str, Any] = field(default_factory=dict)
    response_headers: dict[str, Any] = field(default_factory=dict)
    request_post_data: str = ""
    response_body: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: "BrowserNetworkEvent | dict[str, Any]") -> "BrowserNetworkEvent":
        if isinstance(value, cls):
            return value

        data = dict(value)
        known_keys = {
            "method",
            "url",
            "status_code",
            "resource_type",
            "request_headers",
            "response_headers",
            "request_post_data",
            "response_body",
        }

        return cls(
            method=str(data.get("method", "GET")).upper(),
            url=str(data.get("url", "")),
            status_code=data.get("status_code"),
            resource_type=str(data.get("resource_type", "")),
            request_headers=dict(data.get("request_headers") or {}),
            response_headers=dict(data.get("response_headers") or {}),
            request_post_data=str(data.get("request_post_data") or ""),
            response_body=str(data.get("response_body") or ""),
            extra={key: value for key, value in data.items() if key not in known_keys},
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "method": self.method.upper(),
            "url": self.url,
        }

        if self.status_code is not None:
            data["status_code"] = self.status_code
        if self.resource_type:
            data["resource_type"] = self.resource_type
        if self.request_headers:
            data["request_headers"] = self.request_headers
        if self.response_headers:
            data["response_headers"] = self.response_headers
        if self.request_post_data:
            data["request_post_data"] = self.request_post_data
        if self.response_body:
            data["response_body"] = self.response_body

        data.update(self.extra)
        return data


@dataclass(frozen=True)
class BrowserScreenshot:
    """Typed browser screenshot evidence item."""

    path: str
    sha256: str = ""
    content_type: str = "image/png"
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: "BrowserScreenshot | dict[str, Any]") -> "BrowserScreenshot":
        if isinstance(value, cls):
            return value

        data = dict(value)
        known_keys = {"path", "sha256", "content_type"}

        return cls(
            path=str(data.get("path", "")),
            sha256=str(data.get("sha256", "")),
            content_type=str(data.get("content_type") or "image/png"),
            extra={key: value for key, value in data.items() if key not in known_keys},
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "path": self.path,
            "content_type": self.content_type,
        }

        if self.sha256:
            data["sha256"] = self.sha256

        data.update(self.extra)
        return data


@dataclass(frozen=True)
class BrowserHtmlSnapshot:
    """Typed browser HTML snapshot evidence item."""

    url: str
    html: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_value(cls, value: "BrowserHtmlSnapshot | dict[str, Any]") -> "BrowserHtmlSnapshot":
        if isinstance(value, cls):
            return value

        data = dict(value)
        raw_html = data.get("html") or data.get("content") or data.get("html_preview") or ""
        known_keys = {"url", "html", "content", "html_preview"}

        return cls(
            url=str(data.get("url", "")),
            html=str(raw_html),
            extra={key: value for key, value in data.items() if key not in known_keys},
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "url": self.url,
        }

        if self.html:
            data["html"] = self.html

        data.update(self.extra)
        return data


@dataclass(frozen=True)
class BrowserCaptureResult:
    """Normalized browser capture result."""

    target_name: str
    task_name: str
    start_url: str
    browser: str
    network_events: list[BrowserNetworkEvent] = field(default_factory=list)
    screenshots: list[BrowserScreenshot] = field(default_factory=list)
    html_snapshots: list[BrowserHtmlSnapshot] = field(default_factory=list)
    execution_output: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        """Normalize dictionary evidence items into typed browser evidence models."""
        object.__setattr__(
            self,
            "network_events",
            [BrowserNetworkEvent.from_value(event) for event in self.network_events],
        )
        object.__setattr__(
            self,
            "screenshots",
            [BrowserScreenshot.from_value(screenshot) for screenshot in self.screenshots],
        )
        object.__setattr__(
            self,
            "html_snapshots",
            [BrowserHtmlSnapshot.from_value(snapshot) for snapshot in self.html_snapshots],
        )

    def to_evidence_kwargs(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "task_name": self.task_name,
            "start_url": self.start_url,
            "browser": self.browser,
            "network_events": [event.to_dict() for event in self.network_events],
            "screenshots": [screenshot.to_dict() for screenshot in self.screenshots],
            "html_snapshots": [snapshot.to_dict() for snapshot in self.html_snapshots],
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
    """Safe execution configuration for Playwright runs."""

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
    """Planned artifact paths for Playwright execution."""

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
    """Request object for the Playwright execution adapter."""

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
    """Internal context object for the Playwright adapter."""

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
    """Build internal context for the Playwright adapter."""
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
    """Plan artifact paths for Playwright execution."""
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
    """Build a Playwright execution request from an approved BrowserPlan."""
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
    """Return a BrowserCaptureResult from the Playwright adapter stub."""
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
    """Check whether the optional Playwright Python package is importable."""
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
    network_events: list[BrowserNetworkEvent | dict[str, Any]] | None = None,
    screenshots: list[BrowserScreenshot | dict[str, Any]] | None = None,
    html_snapshots: list[BrowserHtmlSnapshot | dict[str, Any]] | None = None,
    execution_output: dict[str, Any] | None = None,
    notes: str = "",
) -> BrowserCaptureResult:
    """Build a BrowserCaptureResult from an approved browser plan."""
    if not plan.allowed:
        raise ValueError(f"Cannot build capture result from blocked browser plan: {plan.reason}")

    return BrowserCaptureResult(
        target_name=plan.target_name,
        task_name=task_name,
        start_url=plan.start_url,
        browser=plan.browser,
        network_events=[BrowserNetworkEvent.from_value(event) for event in network_events or []],
        screenshots=[BrowserScreenshot.from_value(screenshot) for screenshot in screenshots or []],
        html_snapshots=[BrowserHtmlSnapshot.from_value(snapshot) for snapshot in html_snapshots or []],
        execution_output=execution_output or {},
        notes=notes,
    )


def build_playwright_execution_preview(
    plan: BrowserPlan,
    config: BrowserExecutionConfig | None = None,
) -> dict[str, Any]:
    """Build a Playwright execution preview."""
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
    """Run the safety-gated Playwright execution handoff."""
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
