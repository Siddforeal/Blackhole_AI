"""
Brain chat case intelligence human review decision importer.

This module imports a local human review decision for a case-intelligence
human-review request. It does not grant side-effectful approval, call LLM
providers, execute tools, collect evidence, send requests, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_case_intelligence_human_review_request import (
    BrainChatCaseIntelligenceHumanReviewRequest,
)


VALID_CASE_INTELLIGENCE_HUMAN_REVIEW_DECISIONS: tuple[str, ...] = (
    "approved-for-human-case-review",
    "changes-requested",
    "rejected",
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceHumanReviewDecision:
    decision: str
    reviewer: str
    reason: str
    request_status: str
    review_status: str
    briefing_status: str
    human_review_request_ready: bool
    case_review_ready: bool
    approval_granted: bool
    effective_human_review_approval_granted: bool
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    allowed_next_steps: tuple[str, ...]
    rejected_next_steps: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-human-review-decision-importer"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_human_review_decision",
            "source": self.source,
            "decision": self.decision,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "request_status": self.request_status,
            "review_status": self.review_status,
            "briefing_status": self.briefing_status,
            "human_review_request_ready": self.human_review_request_ready,
            "case_review_ready": self.case_review_ready,
            "approval_granted": self.approval_granted,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
            "required_human_checks": list(self.required_human_checks),
            "allowed_next_steps": list(self.allowed_next_steps),
            "rejected_next_steps": list(self.rejected_next_steps),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "approval_granted": self.approval_granted,
                "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
                "human_approval_side_effects": False,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Human Review Decision") -> str:
        lines = [
            f"# {title}",
            "",
            "## Decision State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Reviewer: `{self.reviewer}`",
            f"- Request status: `{self.request_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Human review request ready: `{self.human_review_request_ready}`",
            f"- Case review ready: `{self.case_review_ready}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Reason",
            "",
            self.reason or "none",
            "",
            "## Missing Evidence Checklist",
            "",
        ]

        if self.missing_evidence_checklist:
            for item in self.missing_evidence_checklist:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers Checklist", ""])
        if self.blockers_checklist:
            for item in self.blockers_checklist:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Human Checks", ""])
        if self.required_human_checks:
            for item in self.required_human_checks:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Next Steps", ""])
        if self.allowed_next_steps:
            for item in self.allowed_next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected Next Steps", ""])
        for item in self.rejected_next_steps:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This decision import is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def import_case_intelligence_human_review_decision_file(
    request: BrainChatCaseIntelligenceHumanReviewRequest,
    decision_file: Path,
) -> BrainChatCaseIntelligenceHumanReviewDecision:
    data = json.loads(decision_file.read_text(encoding="utf-8"))
    return import_case_intelligence_human_review_decision_data(request, data)


def import_case_intelligence_human_review_decision_data(
    request: BrainChatCaseIntelligenceHumanReviewRequest,
    data: dict[str, Any],
    source: str = "brain-chat-case-intelligence-human-review-decision-importer",
) -> BrainChatCaseIntelligenceHumanReviewDecision:
    decision = str(data.get("decision", "")).strip()
    if decision not in VALID_CASE_INTELLIGENCE_HUMAN_REVIEW_DECISIONS:
        raise ValueError(
            "Invalid case intelligence human review decision. "
            f"Expected one of: {', '.join(VALID_CASE_INTELLIGENCE_HUMAN_REVIEW_DECISIONS)}"
        )

    reviewer = str(data.get("reviewer") or "local-reviewer").strip() or "local-reviewer"
    reason = str(data.get("reason") or "").strip()

    request_data = request.to_dict()
    request_ready = bool(request_data.get("human_review_request_ready", False))
    case_review_ready = bool(request_data.get("case_review_ready", False))

    effective_approval = (
        decision == "approved-for-human-case-review"
        and request_ready
        and case_review_ready
        and not _unsafe_request_state(request_data)
    )

    approval_granted = effective_approval

    return BrainChatCaseIntelligenceHumanReviewDecision(
        decision=decision,
        reviewer=reviewer,
        reason=reason,
        request_status=str(request_data.get("request_status") or "unknown"),
        review_status=str(request_data.get("review_status") or "unknown"),
        briefing_status=str(request_data.get("briefing_status") or "unknown"),
        human_review_request_ready=request_ready,
        case_review_ready=case_review_ready,
        approval_granted=approval_granted,
        effective_human_review_approval_granted=effective_approval,
        blocked=bool(request_data.get("blocked", True)),
        validation_allowed=bool(request_data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(request_data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(request_data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(request_data.get("vulnerability_confirmation_allowed", False)),
        missing_evidence_checklist=tuple(_string_list(request_data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(request_data.get("blockers_checklist"))),
        required_human_checks=tuple(_string_list(request_data.get("required_human_checks"))),
        allowed_next_steps=tuple(_allowed_next_steps(decision, effective_approval, request_data)),
        rejected_next_steps=tuple(_rejected_next_steps(decision, effective_approval)),
        source=source,
    )


def _unsafe_request_state(data: dict[str, Any]) -> bool:
    if bool(data.get("runtime_execution_allowed")):
        return True
    if bool(data.get("report_submission_allowed")):
        return True
    if bool(data.get("vulnerability_confirmation_allowed")):
        return True

    safety = data.get("safety")
    if isinstance(safety, dict):
        unsafe_keys = (
            "tool_execution",
            "evidence_collection",
            "validation_execution",
            "report_submission",
            "vulnerability_confirmation",
            "human_approval_side_effects",
        )
        return any(bool(safety.get(key)) for key in unsafe_keys)

    return False


def _allowed_next_steps(
    decision: str,
    effective_approval: bool,
    request_data: dict[str, Any],
) -> list[str]:
    if effective_approval:
        return [
            "Proceed to human case review of the local briefing packet only.",
            "Keep validation, runtime execution, report submission, and vulnerability confirmation disabled until separate gates allow them.",
        ]

    if decision == "changes-requested":
        return [
            "Apply requested local changes to evidence, blockers, or briefing quality.",
            "Re-run the briefing review gate and human-review request after local changes.",
        ]

    if decision == "rejected":
        return [
            "Stop this case-review path unless a new local briefing review request is produced.",
        ]

    if not bool(request_data.get("human_review_request_ready", False)):
        return [
            "Resolve the blocked human-review request before approval can become effective.",
        ]

    return []


def _rejected_next_steps(decision: str, effective_approval: bool) -> list[str]:
    base = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this decision import.",
        "Do not collect new evidence from a target from this decision import.",
        "Do not submit a report from human-review decision metadata alone.",
        "Do not claim vulnerability confirmation from human-review decision metadata alone.",
        "Do not treat this decision as validation or runtime execution approval.",
    ]

    if decision == "approved-for-human-case-review" and not effective_approval:
        base.insert(0, "Do not treat the approval decision as effective; it is not effective because the human-review request is not ready.")

    return base


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
