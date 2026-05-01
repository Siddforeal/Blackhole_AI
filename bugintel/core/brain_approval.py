"""
Human approval packet builder for Blackhole AI Workbench.

This module converts a brain-decision JSON artifact into a planning-only
human approval packet. It does not call LLM providers, send requests,
execute shell commands, launch browsers, use Kali tools, mutate targets,
or bypass authorization.

The approval packet is the safety bridge before any future human-approved
tool loop.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ApprovalItem:
    name: str
    category: str
    required: bool
    reason: str
    source_blocker: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainApprovalPacket:
    target_name: str
    focus_endpoint: str | None
    source_decision: str
    approval_status: str
    approval_required: bool
    approval_items: tuple[ApprovalItem, ...]
    checklist: tuple[str, ...]
    reportable: bool = False
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "source_decision": self.source_decision,
            "approval_status": self.approval_status,
            "approval_required": self.approval_required,
            "approval_items": [item.to_dict() for item in self.approval_items],
            "checklist": list(self.checklist),
            "reportable": self.reportable,
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_brain_approval_packet_markdown(self),
        }


def build_brain_approval_packet(brain_decision_data: dict[str, Any]) -> BrainApprovalPacket:
    """Build a planning-only human approval packet from brain-decision JSON."""
    target_name = str(brain_decision_data.get("target_name") or "unknown-target")
    focus_endpoint = brain_decision_data.get("focus_endpoint")
    focus_endpoint = str(focus_endpoint) if focus_endpoint else None
    decision = str(brain_decision_data.get("decision") or "unknown")
    blockers = list(brain_decision_data.get("blockers") or [])
    next_steps = tuple(str(item) for item in brain_decision_data.get("required_next_steps") or [])

    approval_items = tuple(_approval_items_from_decision(focus_endpoint, decision, blockers))
    checklist = tuple(_build_checklist(next_steps, approval_items))
    approval_required = any(item.required for item in approval_items)

    return BrainApprovalPacket(
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        source_decision=decision,
        approval_status=_approval_status(decision, approval_required),
        approval_required=approval_required,
        approval_items=approval_items,
        checklist=checklist,
        reportable=False,
    )


def render_brain_approval_packet_markdown(packet: BrainApprovalPacket) -> str:
    """Render the human approval packet as Markdown."""
    lines = [
        f"# Blackhole Human Approval Packet: {packet.target_name}",
        "",
        "> Planning-only approval packet. This does not execute validation or confirm a vulnerability.",
        "",
        f"- Target: `{packet.target_name}`",
        f"- Focus endpoint: `{packet.focus_endpoint or 'none'}`",
        f"- Source decision: `{packet.source_decision}`",
        f"- Approval status: `{packet.approval_status}`",
        f"- Approval required: `{packet.approval_required}`",
        f"- Reportable: `{packet.reportable}`",
        f"- Provider execution enabled: `{packet.provider_execution_enabled}`",
        f"- Execution state: `{packet.execution_state}`",
        "",
        "## Approval Items",
        "",
    ]

    for item in packet.approval_items:
        source = f", source=`{item.source_blocker}`" if item.source_blocker else ""
        lines.append(
            f"- [{'x' if not item.required else ' '}] `{item.category}` / `{item.name}` "
            f"(required={item.required}{source}) — {item.reason}"
        )

    lines.extend(["", "## Human Checklist", ""])

    for step in packet.checklist:
        lines.append(f"- [ ] {step}")

    lines.extend(
        [
            "",
            "## Safety Decision",
            "",
            "This packet only prepares a human approval review.",
            "Do not execute curl, browser actions, shell commands, Kali tools, LLM providers, or target requests from this packet.",
            "Keep the finding unconfirmed and non-reportable until manually validated evidence exists.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _approval_items_from_decision(
    focus_endpoint: str | None,
    decision: str,
    blockers: list[dict[str, Any]],
) -> list[ApprovalItem]:
    items: list[ApprovalItem] = []

    if not focus_endpoint:
        items.append(
            ApprovalItem(
                name="Select focus endpoint",
                category="planning",
                required=True,
                reason="No focus endpoint is available for approval.",
                source_blocker="missing-focus-endpoint",
            )
        )

    blocker_names = {str(blocker.get("name")) for blocker in blockers}

    for blocker in blockers:
        name = str(blocker.get("name") or "unknown-blocker")
        reason = str(blocker.get("reason") or "Approval required due to decision blocker.")

        if name == "scope-confirmation-required":
            items.append(
                ApprovalItem(
                    name="Confirm program scope and authorization",
                    category="scope",
                    required=True,
                    reason=reason,
                    source_blocker=name,
                )
            )
        elif name == "controlled-accounts-required":
            items.append(
                ApprovalItem(
                    name="Confirm controlled test accounts and objects",
                    category="test-controls",
                    required=True,
                    reason=reason,
                    source_blocker=name,
                )
            )
        elif name == "human-approval-required":
            items.append(
                ApprovalItem(
                    name="Approve evidence collection",
                    category="evidence",
                    required=True,
                    reason=reason,
                    source_blocker=name,
                )
            )
        elif name == "missing-evidence-plan":
            items.append(
                ApprovalItem(
                    name="Create evidence plan before validation",
                    category="evidence",
                    required=True,
                    reason=reason,
                    source_blocker=name,
                )
            )
        elif name == "missing-stop-conditions":
            items.append(
                ApprovalItem(
                    name="Define stop conditions",
                    category="safety",
                    required=True,
                    reason=reason,
                    source_blocker=name,
                )
            )

    if "scope-confirmation-required" not in blocker_names:
        items.append(
            ApprovalItem(
                name="Reconfirm scope before validation",
                category="scope",
                required=True,
                reason="Scope should be reconfirmed before any future active validation.",
            )
        )

    items.append(
        ApprovalItem(
            name="Confirm redaction plan",
            category="redaction",
            required=True,
            reason="Cookies, tokens, API keys, emails, identifiers, screenshots, and private data must be redacted.",
        )
    )

    items.append(
        ApprovalItem(
            name="Confirm non-destructive validation",
            category="safety",
            required=True,
            reason="Future validation must not mutate real data, affect users, trigger payments, or bypass authorization.",
        )
    )

    if decision == "ready-for-manual-validation":
        items.append(
            ApprovalItem(
                name="Approve manual validation start",
                category="manual-validation",
                required=True,
                reason="Decision gate indicates manual validation may be next after approval.",
            )
        )

    return _dedupe_items(items)


def _build_checklist(next_steps: tuple[str, ...], approval_items: tuple[ApprovalItem, ...]) -> list[str]:
    checklist = list(next_steps)

    checklist.extend(
        [
            "Review every approval item in this packet.",
            "Confirm provider execution remains disabled.",
            "Confirm no target interaction happens from this approval packet.",
            "Confirm evidence will remain minimal, relevant, and redacted.",
            "Keep reportability false until manually validated evidence exists.",
        ]
    )

    for item in approval_items:
        if item.required:
            checklist.append(f"Approve or resolve: {item.name}")

    return _dedupe_strings(checklist)


def _approval_status(decision: str, approval_required: bool) -> str:
    if decision in {"blocked", "blocked-pending-scope-and-controls"}:
        return "blocked-pending-approval"
    if decision == "ready-for-human-approval":
        return "approval-required"
    if decision == "ready-for-manual-validation" and approval_required:
        return "approval-required-before-validation"
    if decision == "ready-for-manual-validation":
        return "approval-ready"
    return "needs-planning"


def _dedupe_items(items: list[ApprovalItem]) -> list[ApprovalItem]:
    seen: set[tuple[str, str]] = set()
    deduped: list[ApprovalItem] = []

    for item in items:
        key = (item.category, item.name)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)

    return deduped
