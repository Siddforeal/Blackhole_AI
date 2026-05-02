"""
Tool execution gate for Blackhole AI Workbench.

This module converts a planning-only tool request manifest into a conservative
execution gate decision. It does not execute tools, send requests, run shell
commands, launch browsers, use Kali tools, call LLM providers, mutate targets,
or bypass authorization.

The gate fails closed by default and is designed as the final safety checkpoint
before any future human-approved execution layer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionGateItem:
    request_name: str
    tool_family: str
    gate_status: str
    reason: str
    required_confirmations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["required_confirmations"] = list(self.required_confirmations)
        return data


@dataclass(frozen=True)
class ToolExecutionGate:
    target_name: str
    focus_endpoint: str | None
    gate_decision: str
    execution_allowed: bool
    gate_items: tuple[ExecutionGateItem, ...]
    required_global_confirmations: tuple[str, ...]
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "gate_decision": self.gate_decision,
            "execution_allowed": self.execution_allowed,
            "gate_items": [item.to_dict() for item in self.gate_items],
            "required_global_confirmations": list(self.required_global_confirmations),
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_tool_execution_gate_markdown(self),
        }


def build_tool_execution_gate(tool_request_manifest_data: dict[str, Any]) -> ToolExecutionGate:
    """Build a conservative planning-only execution gate from a tool request manifest."""
    target_name = str(tool_request_manifest_data.get("target_name") or "unknown-target")
    focus_endpoint_raw = tool_request_manifest_data.get("focus_endpoint")
    focus_endpoint = str(focus_endpoint_raw) if focus_endpoint_raw else None
    manifest_execution_allowed = bool(tool_request_manifest_data.get("execution_allowed"))
    requests = list(tool_request_manifest_data.get("requests") or [])

    gate_items = tuple(_build_gate_item(request, focus_endpoint) for request in requests)
    global_confirmations = tuple(_global_confirmations(focus_endpoint))

    gate_decision = _gate_decision(
        focus_endpoint=focus_endpoint,
        manifest_execution_allowed=manifest_execution_allowed,
        gate_items=gate_items,
    )

    return ToolExecutionGate(
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        gate_decision=gate_decision,
        execution_allowed=False,
        gate_items=gate_items,
        required_global_confirmations=global_confirmations,
    )


def render_tool_execution_gate_markdown(gate: ToolExecutionGate) -> str:
    """Render the tool execution gate as Markdown."""
    lines = [
        f"# Blackhole Tool Execution Gate: {gate.target_name}",
        "",
        "> Planning-only execution gate. No tools are executed.",
        "",
        f"- Target: `{gate.target_name}`",
        f"- Focus endpoint: `{gate.focus_endpoint or 'none'}`",
        f"- Gate decision: `{gate.gate_decision}`",
        f"- Execution allowed: `{gate.execution_allowed}`",
        f"- Provider execution enabled: `{gate.provider_execution_enabled}`",
        f"- Execution state: `{gate.execution_state}`",
        "",
        "## Required Global Confirmations",
        "",
    ]

    for confirmation in gate.required_global_confirmations:
        lines.append(f"- [ ] {confirmation}")

    lines.extend(
        [
            "",
            "## Gate Items",
            "",
            "| # | Tool Family | Request | Gate Status | Required Confirmations |",
            "|---:|---|---|---|---|",
        ]
    )

    for index, item in enumerate(gate.gate_items, start=1):
        confirmations = ", ".join(item.required_confirmations) or "none"
        lines.append(
            f"| {index} | `{item.tool_family}` | {item.request_name} | "
            f"`{item.gate_status}` | {confirmations} |"
        )

    lines.extend(
        [
            "",
            "## Safety Decision",
            "",
            "This gate intentionally keeps execution disabled.",
            "Do not run browser actions, curl, shell commands, Kali tools, network requests, or LLM providers from this artifact.",
            "A future execution layer must require explicit human approval, confirmed scope, controlled assets, redaction, and non-destructive mode.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _build_gate_item(request: dict[str, Any], focus_endpoint: str | None) -> ExecutionGateItem:
    name = str(request.get("name") or "unknown-request")
    tool_family = str(request.get("tool_family") or "unknown")
    request_execution_allowed = bool(request.get("execution_allowed"))
    requires_human_approval = bool(request.get("requires_human_approval"))
    blocked_by = tuple(str(item) for item in request.get("blocked_by") or [])

    confirmations = list(_confirmations_for_request(
        focus_endpoint=focus_endpoint,
        requires_human_approval=requires_human_approval,
        blocked_by=blocked_by,
    ))

    if not focus_endpoint:
        status = "blocked-missing-focus-endpoint"
        reason = "No focus endpoint is available for this tool request."
    elif not request_execution_allowed:
        status = "blocked-request-execution-disabled"
        reason = "The source tool request explicitly disables execution."
    elif requires_human_approval:
        status = "blocked-human-approval-required"
        reason = "The tool request requires human approval before any future execution."
    elif blocked_by:
        status = "blocked-by-safety-gates"
        reason = "The tool request still has unresolved safety blockers."
    else:
        status = "eligible-for-future-review"
        reason = "The request has no local blockers, but execution remains disabled by the global gate."

    return ExecutionGateItem(
        request_name=name,
        tool_family=tool_family,
        gate_status=status,
        reason=reason,
        required_confirmations=tuple(_dedupe(confirmations)),
    )


def _confirmations_for_request(
    focus_endpoint: str | None,
    requires_human_approval: bool,
    blocked_by: tuple[str, ...],
) -> list[str]:
    confirmations = [
        "confirm-scope",
        "confirm-controlled-assets",
        "confirm-redaction",
        "confirm-non-destructive-mode",
    ]

    if not focus_endpoint:
        confirmations.append("select-focus-endpoint")

    if requires_human_approval:
        confirmations.append("obtain-human-approval")

    for blocker in blocked_by:
        if blocker:
            confirmations.append(f"resolve-{blocker}")

    return confirmations


def _global_confirmations(focus_endpoint: str | None) -> list[str]:
    confirmations = [
        "Confirm program scope and authorization.",
        "Confirm controlled accounts, objects, tenants, projects, or files.",
        "Confirm redaction plan for tokens, cookies, IDs, emails, screenshots, and private data.",
        "Confirm non-destructive mode.",
        "Confirm provider execution remains disabled unless separately approved.",
        "Confirm no finding is treated as reportable without manually validated evidence.",
    ]

    if not focus_endpoint:
        confirmations.insert(0, "Select a focus endpoint before any execution review.")

    return confirmations


def _gate_decision(
    focus_endpoint: str | None,
    manifest_execution_allowed: bool,
    gate_items: tuple[ExecutionGateItem, ...],
) -> str:
    if not focus_endpoint:
        return "blocked-missing-focus-endpoint"

    if not manifest_execution_allowed:
        return "blocked-manifest-execution-disabled"

    if any(item.gate_status.startswith("blocked") for item in gate_items):
        return "blocked-by-request-gates"

    return "eligible-for-future-human-approved-execution-review"


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    return deduped
