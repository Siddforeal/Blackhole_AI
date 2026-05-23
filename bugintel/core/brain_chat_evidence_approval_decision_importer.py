"""
Brain chat evidence approval decision importer.

This module imports a local human reviewer decision for an evidence approval
request packet. It records decision metadata only. It does not execute tools,
collect evidence, send requests, call providers, mutate targets, submit
reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_evidence_approval_request import (
    BrainChatEvidenceApprovalRequest,
)


VALID_APPROVAL_DECISIONS = ("approved", "rejected", "changes-requested")


@dataclass(frozen=True)
class BrainChatEvidenceApprovalDecision:
    decision: str
    reason: str
    reviewer: str
    approval_request_status: str
    gate_status: str
    target_name: str
    focus_endpoint: str | None
    effective_approval_granted: bool
    allowed_next_steps: tuple[str, ...]
    rejected_next_steps: tuple[str, ...]
    source_file: str | None = None
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-evidence-approval-decision"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_approval_decision",
            "source": self.source,
            "source_file": self.source_file,
            "decision": self.decision,
            "reason": self.reason,
            "reviewer": self.reviewer,
            "approval_request_status": self.approval_request_status,
            "gate_status": self.gate_status,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "effective_approval_granted": self.effective_approval_granted,
            "allowed_next_steps": list(self.allowed_next_steps),
            "rejected_next_steps": list(self.rejected_next_steps),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "approval_side_effects": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Evidence Approval Decision") -> str:
        lines = [
            f"# {title}",
            "",
            "## Decision",
            "",
            f"- Decision: `{self.decision}`",
            f"- Effective approval granted: `{self.effective_approval_granted}`",
            f"- Reviewer: `{self.reviewer or 'unspecified'}`",
            f"- Reason: {self.reason or 'none'}",
            "",
            "## Request State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Approval request status: `{self.approval_request_status}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Allowed Next Steps",
            "",
        ]

        if self.allowed_next_steps:
            for item in self.allowed_next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected Next Steps", ""])
        if self.rejected_next_steps:
            for item in self.rejected_next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This decision import is local and planning-only.",
                "- It records approval metadata only and does not execute tools, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def import_evidence_approval_decision_file(
    approval_request: BrainChatEvidenceApprovalRequest,
    decision_file: Path,
) -> BrainChatEvidenceApprovalDecision:
    if not decision_file.exists():
        raise FileNotFoundError(f"Evidence approval decision JSON not found: {decision_file}")

    data = json.loads(decision_file.read_text(encoding="utf-8"))
    return import_evidence_approval_decision_data(
        approval_request,
        data,
        source_file=str(decision_file),
    )


def import_evidence_approval_decision_data(
    approval_request: BrainChatEvidenceApprovalRequest,
    data: dict[str, Any],
    source_file: str | None = None,
) -> BrainChatEvidenceApprovalDecision:
    decision = _normalize_decision(str(data.get("decision", "")))
    reason = str(data.get("reason", "")).strip()
    reviewer = str(data.get("reviewer", "")).strip()

    effective_approval_granted = (
        decision == "approved"
        and approval_request.approval_status == "ready-for-human-approval"
        and approval_request.validation_approval_ready
    )

    return BrainChatEvidenceApprovalDecision(
        decision=decision,
        reason=reason,
        reviewer=reviewer,
        approval_request_status=approval_request.approval_status,
        gate_status=approval_request.gate_status,
        target_name=approval_request.target_name,
        focus_endpoint=approval_request.focus_endpoint,
        effective_approval_granted=effective_approval_granted,
        allowed_next_steps=_allowed_next_steps(decision, effective_approval_granted),
        rejected_next_steps=_rejected_next_steps(decision, effective_approval_granted),
        source_file=source_file,
    )


def _normalize_decision(decision: str) -> str:
    normalized = decision.strip().lower().replace("_", "-")
    if normalized not in VALID_APPROVAL_DECISIONS:
        raise ValueError(
            f"Invalid approval decision: {decision!r}. "
            f"Expected one of: {', '.join(VALID_APPROVAL_DECISIONS)}"
        )
    return normalized


def _allowed_next_steps(decision: str, effective_approval_granted: bool) -> tuple[str, ...]:
    if effective_approval_granted:
        return (
            "Prepare a human-reviewed non-destructive validation plan.",
            "Proceed only with separately approved validation steps.",
            "Record any collected evidence locally and update checklist state.",
        )

    if decision == "changes-requested":
        return (
            "Update checklist evidence statuses and notes.",
            "Resolve reviewer-requested changes before requesting approval again.",
        )

    return ()


def _rejected_next_steps(decision: str, effective_approval_granted: bool) -> tuple[str, ...]:
    common = (
        "Do not submit a report from approval metadata alone.",
        "Do not claim vulnerability confirmation from approval metadata alone.",
    )

    if effective_approval_granted:
        return common

    return (
        "Do not execute network, browser, curl, Kali, shell, or target interaction steps.",
        "Do not collect new evidence from a target.",
        "Do not treat this decision as execution approval.",
        *common,
    )
