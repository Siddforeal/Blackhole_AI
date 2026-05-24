"""
Brain chat validation plan step review gate.

This module reviews local validation-plan steps before any future execution
layer exists. It classifies steps for human review only. It does not execute
tools, collect evidence, send requests, call providers, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_evidence_approved_validation_plan import (
    BrainChatEvidenceApprovedValidationPlan,
)


STEP_STATUSES = (
    "allowed-for-manual-review",
    "needs-scope-check",
    "rejected-unsafe",
)


@dataclass(frozen=True)
class ValidationPlanStepReview:
    step: str
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "status": self.status,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class BrainChatValidationPlanStepReviewGate:
    target_name: str
    focus_endpoint: str | None
    gate_status: str
    plan_status: str
    validation_allowed: bool
    step_review_ready: bool
    reviewed_steps: tuple[ValidationPlanStepReview, ...]
    blocking_reasons: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-validation-plan-step-review-gate"

    @property
    def total_steps(self) -> int:
        return len(self.reviewed_steps)

    @property
    def allowed_count(self) -> int:
        return self._count("allowed-for-manual-review")

    @property
    def needs_scope_check_count(self) -> int:
        return self._count("needs-scope-check")

    @property
    def rejected_unsafe_count(self) -> int:
        return self._count("rejected-unsafe")

    def _count(self, status: str) -> int:
        return sum(1 for item in self.reviewed_steps if item.status == status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_validation_plan_step_review_gate",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "gate_status": self.gate_status,
            "plan_status": self.plan_status,
            "validation_allowed": self.validation_allowed,
            "step_review_ready": self.step_review_ready,
            "reviewed_steps": [item.to_dict() for item in self.reviewed_steps],
            "counts": {
                "total": self.total_steps,
                "allowed_for_manual_review": self.allowed_count,
                "needs_scope_check": self.needs_scope_check_count,
                "rejected_unsafe": self.rejected_unsafe_count,
            },
            "blocking_reasons": list(self.blocking_reasons),
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

    def to_markdown(self, title: str = "Brain Chat Validation Plan Step Review Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Gate Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Plan status: `{self.plan_status}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Step review ready: `{self.step_review_ready}`",
            "",
            "## Counts",
            "",
            f"- Total steps: `{self.total_steps}`",
            f"- Allowed for manual review: `{self.allowed_count}`",
            f"- Needs scope check: `{self.needs_scope_check_count}`",
            f"- Rejected unsafe: `{self.rejected_unsafe_count}`",
            "",
            "## Reviewed Steps",
            "",
        ]

        if self.reviewed_steps:
            for index, item in enumerate(self.reviewed_steps, start=1):
                lines.append(f"{index}. [{item.status}] {item.step}")
                lines.append(f"   - Reason: {item.reason}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blocking Reasons", ""])
        if self.blocking_reasons:
            for item in self.blocking_reasons:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This step review gate is local and planning-only.",
                "- It does not execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_validation_plan_step_review_gate(
    plan: BrainChatEvidenceApprovedValidationPlan,
    source: str = "brain-chat-validation-plan-step-review-gate",
) -> BrainChatValidationPlanStepReviewGate:
    blocking_reasons: list[str] = []

    if not plan.effective_approval_granted:
        blocking_reasons.append("Effective approval is not granted.")

    if not plan.validation_allowed:
        blocking_reasons.append("Validation is not allowed by the approved validation plan.")

    if not plan.planned_validation_steps:
        blocking_reasons.append("No planned validation steps are available for review.")

    reviewed_steps = tuple(_review_step(step) for step in plan.planned_validation_steps)

    if blocking_reasons:
        gate_status = "blocked-pending-approved-validation-plan"
        step_review_ready = False
    elif any(item.status == "rejected-unsafe" for item in reviewed_steps):
        gate_status = "blocked-unsafe-validation-step"
        step_review_ready = False
        blocking_reasons.append("One or more validation steps were classified as rejected-unsafe.")
    elif any(item.status == "needs-scope-check" for item in reviewed_steps):
        gate_status = "needs-scope-check"
        step_review_ready = False
    else:
        gate_status = "ready-for-manual-step-review"
        step_review_ready = True

    return BrainChatValidationPlanStepReviewGate(
        target_name=plan.target_name,
        focus_endpoint=plan.focus_endpoint,
        gate_status=gate_status,
        plan_status=plan.plan_status,
        validation_allowed=plan.validation_allowed,
        step_review_ready=step_review_ready,
        reviewed_steps=reviewed_steps,
        blocking_reasons=tuple(blocking_reasons),
        rejected_actions=(
            "Do not execute reviewed steps automatically.",
            "Do not run browser, curl, Kali, shell, scanner, or target interaction from this gate.",
            "Do not collect evidence from a target from this gate.",
            "Do not submit a report from step-review state alone.",
            "Do not claim vulnerability confirmation from step-review state alone.",
        ),
        source=source,
    )


def _review_step(step: str) -> ValidationPlanStepReview:
    normalized = step.lower()
    normalized_for_unsafe = (
        normalized
        .replace("non-destructive", "non destructive")
        .replace("non destructive", "safe")
    )

    unsafe_terms = (
        "destructive",
        "high-volume",
        "out-of-scope",
        "brute force",
        "delete",
        "mutate",
        "exploit",
        "execute automatically",
        "submit a report",
        "claim vulnerability",
    )
    if any(term in normalized_for_unsafe for term in unsafe_terms):
        return ValidationPlanStepReview(
            step=step,
            status="rejected-unsafe",
            reason="Step contains unsafe, destructive, out-of-scope, or overclaiming language.",
        )

    scope_terms = (
        "scope",
        "authorization",
        "request",
        "browser",
        "tooling",
        "redaction",
        "evidence-storage",
        "collecting outputs",
    )
    if any(term in normalized for term in scope_terms):
        return ValidationPlanStepReview(
            step=step,
            status="needs-scope-check",
            reason="Step requires explicit scope, authorization, tooling, or evidence-handling review.",
        )

    return ValidationPlanStepReview(
        step=step,
        status="allowed-for-manual-review",
        reason="Step is suitable for human planning review and does not authorize execution.",
    )
