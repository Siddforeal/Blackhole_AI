"""
Brain chat case intelligence briefing review gate.

This module reviews a local case intelligence briefing export and classifies
whether it is blocked, needs human review, or is ready for human case review.
It does not call LLM providers, execute tools, collect evidence, send requests,
mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_briefing_export import (
    BrainChatCaseIntelligenceBriefingExport,
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceBriefingReviewGate:
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    briefing_status: str
    review_status: str
    case_review_ready: bool
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    missing_evidence: tuple[str, ...]
    blockers: tuple[str, ...]
    human_review_items: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    question_count: int
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-briefing-review-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_briefing_review_gate",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "current_stage": self.current_stage,
            "current_status": self.current_status,
            "briefing_status": self.briefing_status,
            "review_status": self.review_status,
            "case_review_ready": self.case_review_ready,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "missing_evidence": list(self.missing_evidence),
            "blockers": list(self.blockers),
            "human_review_items": list(self.human_review_items),
            "required_human_checks": list(self.required_human_checks),
            "rejected_actions": list(self.rejected_actions),
            "question_count": self.question_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
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

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Briefing Review Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Review State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Current stage: `{self.current_stage}`",
            f"- Current status: `{self.current_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Case review ready: `{self.case_review_ready}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            f"- Questions answered: `{self.question_count}`",
            "",
            "## Missing Evidence",
            "",
        ]

        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers", ""])
        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Human Review Items", ""])
        if self.human_review_items:
            for item in self.human_review_items:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Human Checks", ""])
        if self.required_human_checks:
            for item in self.required_human_checks:
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
                "- This review gate is local, deterministic, and planning-only.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_intelligence_briefing_review_gate(
    briefing: BrainChatCaseIntelligenceBriefingExport,
    source: str = "brain-chat-case-intelligence-briefing-review-gate",
) -> BrainChatCaseIntelligenceBriefingReviewGate:
    data = briefing.to_dict()

    missing_evidence = tuple(_string_list(data.get("missing_evidence")))
    blockers = tuple(_string_list(data.get("blockers")))
    human_review_items = tuple(_human_review_items(data, missing_evidence, blockers))
    required_human_checks = tuple(_required_human_checks(data, missing_evidence, blockers))
    rejected_actions = tuple(_rejected_actions())

    unsafe_flags = _unsafe_flags(data)
    has_minimum_detail = _has_minimum_detail(data)

    if unsafe_flags or data.get("briefing_status") == "blocked" or missing_evidence or blockers:
        review_status = "blocked-briefing"
        case_review_ready = False
    elif not has_minimum_detail:
        review_status = "needs-human-review"
        case_review_ready = False
    else:
        review_status = "ready-for-human-case-review"
        case_review_ready = True

    if unsafe_flags:
        blockers = tuple(dict.fromkeys((*blockers, *unsafe_flags)))

    return BrainChatCaseIntelligenceBriefingReviewGate(
        target_name=str(data.get("target_name") or "unknown"),
        focus_endpoint=_string_or_none(data.get("focus_endpoint")),
        current_stage=str(data.get("current_stage") or "unknown"),
        current_status=str(data.get("current_status") or "unknown"),
        briefing_status=str(data.get("briefing_status") or "unknown"),
        review_status=review_status,
        case_review_ready=case_review_ready,
        blocked=bool(data.get("blocked", True)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        missing_evidence=missing_evidence,
        blockers=blockers,
        human_review_items=human_review_items,
        required_human_checks=required_human_checks,
        rejected_actions=rejected_actions,
        question_count=_question_count(data),
        source=source,
    )


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _question_count(data: dict[str, Any]) -> int:
    question_set = data.get("question_set")
    if isinstance(question_set, dict):
        try:
            return int(question_set.get("question_count", 0))
        except (TypeError, ValueError):
            return 0
    return 0


def _unsafe_flags(data: dict[str, Any]) -> list[str]:
    unsafe: list[str] = []

    if bool(data.get("runtime_execution_allowed")):
        unsafe.append("Runtime execution is unexpectedly allowed by the briefing.")

    if bool(data.get("report_submission_allowed")):
        unsafe.append("Report submission is unexpectedly allowed by the briefing.")

    if bool(data.get("vulnerability_confirmation_allowed")):
        unsafe.append("Vulnerability confirmation is unexpectedly allowed by the briefing.")

    safety = data.get("safety")
    if isinstance(safety, dict):
        if bool(safety.get("tool_execution")):
            unsafe.append("Tool execution is unexpectedly enabled in safety metadata.")
        if bool(safety.get("evidence_collection")):
            unsafe.append("Evidence collection is unexpectedly enabled in safety metadata.")
        if bool(safety.get("validation_execution")):
            unsafe.append("Validation execution is unexpectedly enabled in safety metadata.")
        if bool(safety.get("report_submission")):
            unsafe.append("Report submission is unexpectedly enabled in safety metadata.")
        if bool(safety.get("vulnerability_confirmation")):
            unsafe.append("Vulnerability confirmation is unexpectedly enabled in safety metadata.")

    return unsafe


def _has_minimum_detail(data: dict[str, Any]) -> bool:
    required_strings = (
        data.get("target_name"),
        data.get("current_stage"),
        data.get("current_status"),
        data.get("briefing_summary"),
        data.get("safest_next_action"),
    )
    if not all(isinstance(item, str) and item.strip() for item in required_strings):
        return False

    if _question_count(data) <= 0:
        return False

    chain_position = data.get("chain_position")
    if not isinstance(chain_position, list) or not chain_position:
        return False

    return True


def _human_review_items(
    data: dict[str, Any],
    missing_evidence: tuple[str, ...],
    blockers: tuple[str, ...],
) -> list[str]:
    items: list[str] = []

    if missing_evidence:
        items.append("Review and resolve missing evidence before validation or reporting.")

    if blockers:
        items.append("Review and resolve briefing blockers before validation or reporting.")

    if not _has_minimum_detail(data):
        items.append("Review briefing completeness; required case details or question answers are missing.")

    if not items:
        items.append("Review the briefing manually for case accuracy, scope, authorization, and evidence quality.")

    return items


def _required_human_checks(
    data: dict[str, Any],
    missing_evidence: tuple[str, ...],
    blockers: tuple[str, ...],
) -> list[str]:
    checks = [
        "Confirm target scope and authorization before any validation.",
        "Confirm evidence redaction requirements before sharing outputs.",
        "Confirm no runtime execution is permitted from this review gate.",
    ]

    if missing_evidence:
        checks.append("Collect or mark every missing evidence item locally before advancing.")

    if blockers:
        checks.append("Resolve every blocker or explicitly document why it remains blocking.")

    if data.get("validation_allowed"):
        checks.append("Perform separate human review before any validation planning or runtime step.")

    return checks


def _rejected_actions() -> list[str]:
    return [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this review gate.",
        "Do not collect new evidence from a target from this review gate.",
        "Do not submit a report from briefing-review state alone.",
        "Do not claim vulnerability confirmation from briefing-review state alone.",
        "Do not treat this review gate as runtime execution approval.",
    ]
