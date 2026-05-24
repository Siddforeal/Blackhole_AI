"""
Brain chat evidence approved validation plan builder.

This module turns an evidence approval decision into a local validation-plan
packet. It does not execute tools, collect evidence, send requests, call
providers, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_evidence_approval_decision_importer import (
    BrainChatEvidenceApprovalDecision,
)


@dataclass(frozen=True)
class BrainChatEvidenceApprovedValidationPlan:
    target_name: str
    focus_endpoint: str | None
    plan_status: str
    decision: str
    effective_approval_granted: bool
    validation_allowed: bool
    summary: str
    planned_validation_steps: tuple[str, ...]
    required_runtime_guards: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-evidence-approved-validation-plan"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_approved_validation_plan",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "plan_status": self.plan_status,
            "decision": self.decision,
            "effective_approval_granted": self.effective_approval_granted,
            "validation_allowed": self.validation_allowed,
            "summary": self.summary,
            "planned_validation_steps": list(self.planned_validation_steps),
            "required_runtime_guards": list(self.required_runtime_guards),
            "rejected_actions": list(self.rejected_actions),
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
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Evidence Approved Validation Plan") -> str:
        lines = [
            f"# {title}",
            "",
            "## Plan Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Plan status: `{self.plan_status}`",
            f"- Decision: `{self.decision}`",
            f"- Effective approval granted: `{self.effective_approval_granted}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            "",
            "## Summary",
            "",
            self.summary,
            "",
            "## Planned Validation Steps",
            "",
        ]

        if self.planned_validation_steps:
            for item in self.planned_validation_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Runtime Guards", ""])
        for item in self.required_runtime_guards:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This validation plan is local and planning-only.",
                "- It does not execute tools, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_evidence_approved_validation_plan(
    decision: BrainChatEvidenceApprovalDecision,
    source: str = "brain-chat-evidence-approved-validation-plan",
) -> BrainChatEvidenceApprovedValidationPlan:
    if decision.effective_approval_granted:
        plan_status = "ready-for-manual-validation-planning"
        validation_allowed = True
        summary = (
            "Effective human approval is present. This packet may be used to draft a "
            "manual, non-destructive validation plan, but it still does not execute anything."
        )
        planned_validation_steps = (
            "Review scope and authorization immediately before any validation.",
            "Prepare a minimal non-destructive validation checklist.",
            "Define exact request, browser, or tooling steps for separate human review.",
            "Define redaction and evidence-storage rules before collecting outputs.",
            "Record validation results locally and update evidence checklist state.",
        )
        rejected_actions = (
            "Do not execute this plan automatically.",
            "Do not perform destructive, high-volume, or out-of-scope testing.",
            "Do not submit a report from approval metadata alone.",
            "Do not claim vulnerability confirmation until validation evidence is collected and reviewed.",
        )
    else:
        plan_status = "blocked-pending-effective-approval"
        validation_allowed = False
        summary = (
            "Effective approval is not granted. Validation planning remains blocked until "
            "the approval decision is effective and the review gate is ready."
        )
        planned_validation_steps = ()
        rejected_actions = (
            "Do not execute network, browser, curl, Kali, shell, or target interaction steps.",
            "Do not collect new evidence from a target.",
            "Do not treat a blocked or premature approval decision as validation approval.",
            "Do not submit a report.",
            "Do not claim vulnerability confirmation.",
        )

    return BrainChatEvidenceApprovedValidationPlan(
        target_name=decision.target_name,
        focus_endpoint=decision.focus_endpoint,
        plan_status=plan_status,
        decision=decision.decision,
        effective_approval_granted=decision.effective_approval_granted,
        validation_allowed=validation_allowed,
        summary=summary,
        planned_validation_steps=planned_validation_steps,
        required_runtime_guards=(
            "Human must approve every runtime validation step separately.",
            "Runtime tools must remain disabled unless an explicit execution gate is added later.",
            "Scope, authorization, and controlled test objects must be rechecked before validation.",
            "Evidence redaction must be confirmed before saving or sharing outputs.",
        ),
        rejected_actions=rejected_actions,
        source=source,
    )
