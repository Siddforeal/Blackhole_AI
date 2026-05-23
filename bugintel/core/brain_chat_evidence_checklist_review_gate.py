"""
Brain chat evidence checklist review gate.

This module reviews a local evidence checklist and decides whether it is
blocked, needs review, or ready for validation approval. It does not collect
evidence, execute tools, send requests, call providers, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_evidence_checklist import BrainChatEvidenceChecklist


@dataclass(frozen=True)
class BrainChatEvidenceChecklistReviewGate:
    target_name: str
    focus_endpoint: str | None
    gate_status: str
    recommendation: str
    checklist_complete: bool
    validation_approval_ready: bool
    total_items: int
    missing_count: int
    collected_count: int
    review_needed_count: int
    blocked_count: int
    blocking_reasons: tuple[str, ...]
    review_reasons: tuple[str, ...]
    approval_requirements: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-evidence-checklist-review-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_checklist_review_gate",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "gate_status": self.gate_status,
            "recommendation": self.recommendation,
            "checklist_complete": self.checklist_complete,
            "validation_approval_ready": self.validation_approval_ready,
            "counts": {
                "total": self.total_items,
                "missing": self.missing_count,
                "collected": self.collected_count,
                "review_needed": self.review_needed_count,
                "blocked": self.blocked_count,
            },
            "blocking_reasons": list(self.blocking_reasons),
            "review_reasons": list(self.review_reasons),
            "approval_requirements": list(self.approval_requirements),
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
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Evidence Checklist Review Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Gate Decision",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Recommendation: {self.recommendation}",
            f"- Checklist complete: `{self.checklist_complete}`",
            f"- Validation approval ready: `{self.validation_approval_ready}`",
            "",
            "## Counts",
            "",
            f"- Total: `{self.total_items}`",
            f"- Missing: `{self.missing_count}`",
            f"- Collected: `{self.collected_count}`",
            f"- Review needed: `{self.review_needed_count}`",
            f"- Blocked: `{self.blocked_count}`",
            "",
            "## Blocking Reasons",
            "",
        ]

        if self.blocking_reasons:
            for reason in self.blocking_reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("- none")

        lines.extend(["", "## Review Reasons", ""])
        if self.review_reasons:
            for reason in self.review_reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("- none")

        lines.extend(["", "## Approval Requirements", ""])
        for requirement in self.approval_requirements:
            lines.append(f"- {requirement}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This review gate is local and planning-only.",
                "- It does not collect evidence, execute tools, send requests, call providers, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_evidence_checklist_review_gate(
    checklist: BrainChatEvidenceChecklist,
    source: str = "brain-chat-evidence-checklist-review-gate",
) -> BrainChatEvidenceChecklistReviewGate:
    blocking_reasons = _blocking_reasons(checklist)
    review_reasons = _review_reasons(checklist)

    if blocking_reasons:
        gate_status = "blocked"
        recommendation = "Resolve blocked or missing evidence before requesting validation approval."
        validation_approval_ready = False
    elif review_reasons:
        gate_status = "needs-review"
        recommendation = "Review marked evidence items before requesting validation approval."
        validation_approval_ready = False
    else:
        gate_status = "ready-for-validation-approval"
        recommendation = "Checklist evidence is collected; prepare a human validation approval request."
        validation_approval_ready = True

    return BrainChatEvidenceChecklistReviewGate(
        target_name=checklist.target_name,
        focus_endpoint=checklist.focus_endpoint,
        gate_status=gate_status,
        recommendation=recommendation,
        checklist_complete=checklist.complete,
        validation_approval_ready=validation_approval_ready,
        total_items=len(checklist.items),
        missing_count=checklist.missing_count,
        collected_count=checklist.collected_count,
        review_needed_count=checklist.review_needed_count,
        blocked_count=checklist.blocked_count,
        blocking_reasons=tuple(blocking_reasons),
        review_reasons=tuple(review_reasons),
        approval_requirements=(
            "Confirm scope and authorization before any active validation.",
            "Confirm controlled accounts, roles, and object ownership.",
            "Confirm redaction requirements before saving or sharing evidence.",
            "Obtain explicit human approval before executing validation steps.",
        ),
        source=source,
    )


def _blocking_reasons(checklist: BrainChatEvidenceChecklist) -> list[str]:
    reasons: list[str] = []

    if not checklist.items:
        reasons.append("No evidence checklist items are available.")

    if checklist.blocked_count:
        reasons.append(f"{checklist.blocked_count} evidence item(s) are blocked.")

    if checklist.missing_count:
        reasons.append(f"{checklist.missing_count} evidence item(s) are still missing.")

    return reasons


def _review_reasons(checklist: BrainChatEvidenceChecklist) -> list[str]:
    reasons: list[str] = []

    if checklist.review_needed_count:
        reasons.append(f"{checklist.review_needed_count} evidence item(s) still need review.")

    return reasons
