"""
Tool request manifest builder for Blackhole AI Workbench.

This module converts a human approval packet into a planning-only tool request
manifest. It does not execute tools, send requests, run shell commands, launch
browsers, use Kali tools, call LLM providers, mutate targets, or bypass
authorization.

This is the safety bridge before any future human-approved tool loop.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ToolRequest:
    name: str
    tool_family: str
    purpose: str
    requires_human_approval: bool
    execution_allowed: bool
    blocked_by: tuple[str, ...]
    expected_artifact: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocked_by"] = list(self.blocked_by)
        return data


@dataclass(frozen=True)
class ToolRequestManifest:
    target_name: str
    focus_endpoint: str | None
    source_approval_status: str
    execution_allowed: bool
    requests: tuple[ToolRequest, ...]
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "source_approval_status": self.source_approval_status,
            "execution_allowed": self.execution_allowed,
            "requests": [request.to_dict() for request in self.requests],
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_tool_request_manifest_markdown(self),
        }


def build_tool_request_manifest(approval_packet_data: dict[str, Any]) -> ToolRequestManifest:
    """Build a planning-only tool request manifest from a brain-approval JSON object."""
    target_name = str(approval_packet_data.get("target_name") or "unknown-target")
    focus_endpoint_raw = approval_packet_data.get("focus_endpoint")
    focus_endpoint = str(focus_endpoint_raw) if focus_endpoint_raw else None
    approval_status = str(approval_packet_data.get("approval_status") or "unknown")
    approval_required = bool(approval_packet_data.get("approval_required"))
    approval_items = list(approval_packet_data.get("approval_items") or [])
    checklist = [str(item) for item in approval_packet_data.get("checklist") or []]

    requests = tuple(
        _dedupe_requests(
            _base_requests(focus_endpoint)
            + _requests_from_approval_items(approval_items, focus_endpoint)
            + _requests_from_checklist(checklist, focus_endpoint)
        )
    )

    return ToolRequestManifest(
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        source_approval_status=approval_status,
        execution_allowed=False,
        requests=requests,
    )


def render_tool_request_manifest_markdown(manifest: ToolRequestManifest) -> str:
    """Render the tool request manifest as Markdown."""
    lines = [
        f"# Blackhole Tool Request Manifest: {manifest.target_name}",
        "",
        "> Planning-only tool request manifest. No tools are executed.",
        "",
        f"- Target: `{manifest.target_name}`",
        f"- Focus endpoint: `{manifest.focus_endpoint or 'none'}`",
        f"- Source approval status: `{manifest.source_approval_status}`",
        f"- Execution allowed: `{manifest.execution_allowed}`",
        f"- Provider execution enabled: `{manifest.provider_execution_enabled}`",
        f"- Execution state: `{manifest.execution_state}`",
        "",
        "## Tool Requests",
        "",
        "| # | Tool Family | Request | Approval | Execution | Blocked By | Expected Artifact |",
        "|---:|---|---|---|---|---|---|",
    ]

    for index, request in enumerate(manifest.requests, start=1):
        blocked_by = ", ".join(request.blocked_by) or "none"
        lines.append(
            f"| {index} | `{request.tool_family}` | {request.name} | "
            f"{'YES' if request.requires_human_approval else 'NO'} | "
            f"{'YES' if request.execution_allowed else 'NO'} | "
            f"{blocked_by} | `{request.expected_artifact}` |"
        )

    lines.extend(
        [
            "",
            "## Safety Decision",
            "",
            "This manifest is a request plan only.",
            "Do not execute browser actions, curl, shell commands, Kali tools, network requests, or LLM providers from this artifact.",
            "Execution remains disabled until a future explicit human-approved execution gate exists.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _base_requests(focus_endpoint: str | None) -> list[ToolRequest]:
    blocked = ("focus-endpoint-required",) if not focus_endpoint else ("human-approval", "scope-confirmation")

    return [
        ToolRequest(
            name="Prepare scope confirmation request",
            tool_family="scope",
            purpose="Confirm the endpoint and target are authorized before any validation.",
            requires_human_approval=True,
            execution_allowed=False,
            blocked_by=blocked,
            expected_artifact="scope-confirmation-note",
        ),
        ToolRequest(
            name="Prepare redaction review request",
            tool_family="redaction",
            purpose="Review sensitive values that must be redacted from future evidence.",
            requires_human_approval=True,
            execution_allowed=False,
            blocked_by=("redaction-plan",),
            expected_artifact="redaction-review-note",
        ),
        ToolRequest(
            name="Prepare state update request",
            tool_family="state",
            purpose="Plan how research state should be updated after manual validation.",
            requires_human_approval=False,
            execution_allowed=False,
            blocked_by=("manual-validation-result",),
            expected_artifact="state-update-note",
        ),
    ]


def _requests_from_approval_items(
    approval_items: list[dict[str, Any]],
    focus_endpoint: str | None,
) -> list[ToolRequest]:
    requests: list[ToolRequest] = []

    for item in approval_items:
        category = str(item.get("category") or "approval")
        name = str(item.get("name") or "Approval item")
        required = bool(item.get("required", True))
        source = str(item.get("source_blocker") or "human-approval")

        requests.append(
            ToolRequest(
                name=f"Resolve approval item: {name}",
                tool_family=category,
                purpose=str(item.get("reason") or "Resolve approval requirement before validation."),
                requires_human_approval=required,
                execution_allowed=False,
                blocked_by=(source,),
                expected_artifact=f"{_slugify(category)}-{_slugify(name)}-approval-note",
            )
        )

    return requests


def _requests_from_checklist(
    checklist: list[str],
    focus_endpoint: str | None,
) -> list[ToolRequest]:
    requests: list[ToolRequest] = []

    for item in checklist:
        lower = item.lower()

        if "provider execution remains disabled" in lower:
            requests.append(
                ToolRequest(
                    name="Verify provider execution remains disabled",
                    tool_family="provider-safety",
                    purpose="Confirm no LLM provider will be called by the current workflow.",
                    requires_human_approval=False,
                    execution_allowed=False,
                    blocked_by=("no-llm-provider-execution",),
                    expected_artifact="provider-execution-disabled-note",
                )
            )

        if "reportability false" in lower:
            requests.append(
                ToolRequest(
                    name="Verify reportability remains false",
                    tool_family="report-safety",
                    purpose="Confirm the case is not treated as reportable until manually validated evidence exists.",
                    requires_human_approval=False,
                    execution_allowed=False,
                    blocked_by=("manual-validation-result",),
                    expected_artifact="reportability-status-note",
                )
            )

    return requests


def _dedupe_requests(requests: list[ToolRequest]) -> list[ToolRequest]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ToolRequest] = []

    for request in requests:
        key = (request.tool_family, request.name)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(request)

    return deduped


def _slugify(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned.strip("-") or "item"
