"""
Brain chat validation step approval decision importer.

This module imports a local human reviewer decision for a validation step
approval request packet. It records decision metadata only. It does not
execute tools, collect evidence, send requests, call providers, mutate
targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_validation_step_approval_request import (
    BrainChatValidationStepApprovalRequest,
)


VALID_STEP_APPROVAL_DECISIONS = ("approved", "rejected", "changes-requested")


@dataclass(frozen=True)
class BrainChatValidationStepApprovalDecision:
    decision: str
    reason: str
    reviewer: str
    request_status: str
    gate_status: str
    target_name: str
    focus_endpoint: str | None
    step_review_ready: bool
    validation_allowed: bool
    effective_step_approval_granted: bool
    approved_steps: tuple[str, ...]
    allowed_next_steps: tuple[str, ...]
    rejected_next_steps: tuple[str, ...]
    source_file: str | None = None
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-validation-step-approval-decision"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_validation_step_approval_decision",
            "source": self.source,
            "source_file": self.source_file,
            "decision": self.decision,
            "reason": self.reason,
            "reviewer": self.reviewer,
            "request_status": self.request_status,
            "gate_status": self.gate_status,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "step_review_ready": self.step_review_ready,
            "validation_allowed": self.validation_allowed,
            "effective_step_approval_granted": self.effective_step_approval_granted,
            "approved_steps": list(self.approved_steps),
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
                "validation_execution": False,
                "step_approval_side_effects": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Validation Step Approval Decision") -> str:
        lines = [
            f"# {title}",
            "",
            "## Decision",
            "",
            f"- Decision: `{self.decision}`",
            f"- Effective step approval granted: `{self.effective_step_approval_granted}`",
            f"- Reviewer: `{self.reviewer or 'unspecified'}`",
            f"- Reason: {self.reason or 'none'}",
            "",
            "## Request State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Request status: `{self.request_status}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Step review ready: `{self.step_review_ready}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            "",
            "## Approved Steps",
            "",
        ]

        if self.approved_steps:
            for item in self.approved_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Next Steps", ""])
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
                "- It records step approval metadata only and does not execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def import_validation_step_approval_decision_file(
    approval_request: BrainChatValidationStepApprovalRequest,
    decision_file: Path,
) -> BrainChatValidationStepApprovalDecision:
    if not decision_file.exists():
        raise FileNotFoundError(f"Validation step approval decision JSON not found: {decision_file}")

    data = json.loads(decision_file.read_text(encoding="utf-8"))
    return import_validation_step_approval_decision_data(
        approval_request,
        data,
        source_file=str(decision_file),
    )


def import_validation_step_approval_decision_data(
    approval_request: BrainChatValidationStepApprovalRequest,
    data: dict[str, Any],
    source_file: str | None = None,
) -> BrainChatValidationStepApprovalDecision:
    decision = _normalize_decision(str(data.get("decision", "")))
    reason = str(data.get("reason", "")).strip()
    reviewer = str(data.get("reviewer", "")).strip()

    effective_step_approval_granted = (
        decision == "approved"
        and approval_request.request_status == "ready-for-human-step-approval"
        and approval_request.step_review_ready
        and approval_request.validation_allowed
        and bool(approval_request.steps_for_human_approval)
    )

    approved_steps = (
        tuple(approval_request.steps_for_human_approval)
        if effective_step_approval_granted
        else ()
    )

    return BrainChatValidationStepApprovalDecision(
        decision=decision,
        reason=reason,
        reviewer=reviewer,
        request_status=approval_request.request_status,
        gate_status=approval_request.gate_status,
        target_name=approval_request.target_name,
        focus_endpoint=approval_request.focus_endpoint,
        step_review_ready=approval_request.step_review_ready,
        validation_allowed=approval_request.validation_allowed,
        effective_step_approval_granted=effective_step_approval_granted,
        approved_steps=approved_steps,
        allowed_next_steps=_allowed_next_steps(decision, effective_step_approval_granted),
        rejected_next_steps=_rejected_next_steps(decision, effective_step_approval_granted),
        source_file=source_file,
    )


def _normalize_decision(decision: str) -> str:
    normalized = decision.strip().lower().replace("_", "-")
    if normalized not in VALID_STEP_APPROVAL_DECISIONS:
        raise ValueError(
            f"Invalid validation step approval decision: {decision!r}. "
            f"Expected one of: {', '.join(VALID_STEP_APPROVAL_DECISIONS)}"
        )
    return normalized


def _allowed_next_steps(decision: str, effective_step_approval_granted: bool) -> tuple[str, ...]:
    if effective_step_approval_granted:
        return (
            "Prepare a separate runtime execution gate proposal for the approved manual steps.",
            "Keep runtime tooling disabled until a later explicit execution gate exists.",
            "Record any future validation outputs locally only after separate execution approval.",
        )

    if decision == "changes-requested":
        return (
            "Update validation step review state and reviewer notes.",
            "Resolve requested changes before requesting step approval again.",
        )

    return ()


def _rejected_next_steps(decision: str, effective_step_approval_granted: bool) -> tuple[str, ...]:
    common = (
        "Do not submit a report from step approval metadata alone.",
        "Do not claim vulnerability confirmation from step approval metadata alone.",
    )

    if effective_step_approval_granted:
        return (
            "Do not execute approved steps from this decision import.",
            "Do not collect evidence from this decision import.",
            *common,
        )

    return (
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps.",
        "Do not collect new evidence from a target.",
        "Do not treat this decision as runtime execution approval.",
        *common,
    )
