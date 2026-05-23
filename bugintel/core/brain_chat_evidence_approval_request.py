"""
Brain chat evidence approval request packet.

This module turns an evidence checklist review gate into a local human
approval-request packet. It does not collect evidence, execute tools, send
requests, call providers, mutate targets, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_evidence_checklist_review_gate import (
    BrainChatEvidenceChecklistReviewGate,
)


@dataclass(frozen=True)
class BrainChatEvidenceApprovalRequest:
    target_name: str
    focus_endpoint: str | None
    approval_status: str
    gate_status: str
    validation_approval_ready: bool
    requested_action: str
    approval_summary: str
    blockers: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    allowed_after_approval: tuple[str, ...]
    rejected_without_approval: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-evidence-approval-request"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_approval_request",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "approval_status": self.approval_status,
            "gate_status": self.gate_status,
            "validation_approval_ready": self.validation_approval_ready,
            "requested_action": self.requested_action,
            "approval_summary": self.approval_summary,
            "blockers": list(self.blockers),
            "required_human_checks": list(self.required_human_checks),
            "allowed_after_approval": list(self.allowed_after_approval),
            "rejected_without_approval": list(self.rejected_without_approval),
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
                "approval_granted": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Evidence Approval Request") -> str:
        lines = [
            f"# {title}",
            "",
            "## Approval Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Approval status: `{self.approval_status}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Validation approval ready: `{self.validation_approval_ready}`",
            f"- Requested action: {self.requested_action}",
            "",
            "## Summary",
            "",
            self.approval_summary,
            "",
            "## Blockers",
            "",
        ]

        if self.blockers:
            for blocker in self.blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Human Checks", ""])
        for check in self.required_human_checks:
            lines.append(f"- {check}")

        lines.extend(["", "## Allowed After Approval", ""])
        for item in self.allowed_after_approval:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Without Approval", ""])
        for item in self.rejected_without_approval:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This approval request is local and planning-only.",
                "- It does not grant approval, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_evidence_approval_request(
    gate: BrainChatEvidenceChecklistReviewGate,
    source: str = "brain-chat-evidence-approval-request",
) -> BrainChatEvidenceApprovalRequest:
    if gate.gate_status == "ready-for-validation-approval":
        approval_status = "ready-for-human-approval"
        requested_action = "Request human approval for non-destructive validation planning."
        approval_summary = (
            "The evidence checklist is complete and the review gate is ready for "
            "human validation approval. This packet does not approve or execute anything."
        )
        blockers: tuple[str, ...] = ()
    else:
        approval_status = "blocked-pending-review-gate"
        requested_action = "Do not request validation approval yet."
        approval_summary = (
            "The evidence checklist review gate is not ready. Resolve blockers or "
            "review-needed evidence before preparing a human validation approval request."
        )
        blockers = tuple(gate.blocking_reasons + gate.review_reasons)

    return BrainChatEvidenceApprovalRequest(
        target_name=gate.target_name,
        focus_endpoint=gate.focus_endpoint,
        approval_status=approval_status,
        gate_status=gate.gate_status,
        validation_approval_ready=gate.validation_approval_ready,
        requested_action=requested_action,
        approval_summary=approval_summary,
        blockers=blockers,
        required_human_checks=(
            "Confirm the target and endpoint are in authorized scope.",
            "Confirm test accounts, roles, and objects are controlled or explicitly permitted.",
            "Confirm validation steps are non-destructive and minimally invasive.",
            "Confirm evidence redaction requirements before saving or sharing outputs.",
            "Confirm no report or vulnerability claim is made before validation evidence exists.",
        ),
        allowed_after_approval=(
            "Prepare a human-reviewed validation plan.",
            "Collect only approved local evidence artifacts.",
            "Update checklist statuses after evidence is reviewed.",
        ),
        rejected_without_approval=(
            "Do not execute network, browser, curl, Kali, shell, or target interaction steps.",
            "Do not collect new evidence from a target.",
            "Do not submit a report.",
            "Do not claim vulnerability confirmation.",
        ),
        source=source,
    )
