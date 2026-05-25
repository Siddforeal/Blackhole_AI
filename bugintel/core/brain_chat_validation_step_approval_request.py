"""
Brain chat validation step approval request packet.

This module turns a validation plan step review gate into a local human
approval-request packet for reviewed validation steps. It does not grant
approval, execute tools, collect evidence, send requests, call providers,
mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_validation_plan_step_review_gate import (
    BrainChatValidationPlanStepReviewGate,
)


@dataclass(frozen=True)
class BrainChatValidationStepApprovalRequest:
    target_name: str
    focus_endpoint: str | None
    request_status: str
    gate_status: str
    step_review_ready: bool
    validation_allowed: bool
    requested_action: str
    summary: str
    reviewed_step_count: int
    blockers: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    steps_for_human_approval: tuple[str, ...]
    rejected_without_approval: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-validation-step-approval-request"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_validation_step_approval_request",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "request_status": self.request_status,
            "gate_status": self.gate_status,
            "step_review_ready": self.step_review_ready,
            "validation_allowed": self.validation_allowed,
            "requested_action": self.requested_action,
            "summary": self.summary,
            "reviewed_step_count": self.reviewed_step_count,
            "blockers": list(self.blockers),
            "required_human_checks": list(self.required_human_checks),
            "steps_for_human_approval": list(self.steps_for_human_approval),
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
                "validation_execution": False,
                "step_approval_granted": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Validation Step Approval Request") -> str:
        lines = [
            f"# {title}",
            "",
            "## Request Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Request status: `{self.request_status}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Step review ready: `{self.step_review_ready}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Reviewed step count: `{self.reviewed_step_count}`",
            f"- Requested action: {self.requested_action}",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Blockers",
            "",
        ]

        if self.blockers:
            for blocker in self.blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- none")

        lines.extend(["", "## Steps For Human Approval", ""])
        if self.steps_for_human_approval:
            for step in self.steps_for_human_approval:
                lines.append(f"- {step}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Human Checks", ""])
        for check in self.required_human_checks:
            lines.append(f"- {check}")

        lines.extend(["", "## Rejected Without Approval", ""])
        for item in self.rejected_without_approval:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This approval request is local and planning-only.",
                "- It does not grant approval, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_validation_step_approval_request(
    step_gate: BrainChatValidationPlanStepReviewGate,
    source: str = "brain-chat-validation-step-approval-request",
) -> BrainChatValidationStepApprovalRequest:
    blockers = _blockers(step_gate)

    if step_gate.step_review_ready and step_gate.validation_allowed and not blockers:
        request_status = "ready-for-human-step-approval"
        requested_action = "Request human approval for reviewed manual validation steps."
        summary = (
            "The validation step review gate is ready. This packet can be used to ask "
            "a human reviewer to approve the reviewed manual validation steps. It does "
            "not grant approval or execute anything."
        )
        steps_for_human_approval = tuple(item.step for item in step_gate.reviewed_steps)
    else:
        request_status = "blocked-pending-step-review-gate"
        requested_action = "Do not request validation step approval yet."
        summary = (
            "The validation step review gate is not ready. Resolve blockers, scope checks, "
            "or unsafe validation language before requesting human step approval."
        )
        steps_for_human_approval = ()

    return BrainChatValidationStepApprovalRequest(
        target_name=step_gate.target_name,
        focus_endpoint=step_gate.focus_endpoint,
        request_status=request_status,
        gate_status=step_gate.gate_status,
        step_review_ready=step_gate.step_review_ready,
        validation_allowed=step_gate.validation_allowed,
        requested_action=requested_action,
        summary=summary,
        reviewed_step_count=step_gate.total_steps,
        blockers=tuple(blockers),
        required_human_checks=(
            "Confirm every validation step is explicitly in authorized scope.",
            "Confirm every validation step is non-destructive and minimally invasive.",
            "Confirm accounts, roles, identifiers, and objects are controlled or explicitly permitted.",
            "Confirm runtime tooling remains disabled unless a separate execution gate is built later.",
            "Confirm evidence redaction and storage rules before collecting any output.",
        ),
        steps_for_human_approval=steps_for_human_approval,
        rejected_without_approval=(
            "Do not execute validation steps from this packet.",
            "Do not run browser, curl, Kali, shell, scanner, or target interaction from this packet.",
            "Do not collect evidence from a target from this packet.",
            "Do not submit a report from step approval request state alone.",
            "Do not claim vulnerability confirmation from step approval request state alone.",
        ),
        source=source,
    )


def _blockers(step_gate: BrainChatValidationPlanStepReviewGate) -> list[str]:
    blockers: list[str] = list(step_gate.blocking_reasons)

    if not step_gate.step_review_ready and not step_gate.blocking_reasons:
        blockers.append("Validation step review gate is not ready.")

    if not step_gate.validation_allowed:
        blockers.append("Validation is not allowed by the current plan.")

    if step_gate.needs_scope_check_count:
        blockers.append(f"{step_gate.needs_scope_check_count} validation step(s) need scope check.")

    if step_gate.rejected_unsafe_count:
        blockers.append(f"{step_gate.rejected_unsafe_count} validation step(s) were rejected as unsafe.")

    if not step_gate.reviewed_steps:
        blockers.append("No reviewed validation steps are available for approval.")

    # Preserve order while removing duplicates.
    return list(dict.fromkeys(blockers))
