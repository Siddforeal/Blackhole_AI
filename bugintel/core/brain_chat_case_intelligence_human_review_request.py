"""
Brain chat case intelligence human review request.

This module turns a local case intelligence briefing review gate into a
human-review request packet. It does not grant approval, call LLM providers,
execute tools, collect evidence, send requests, mutate targets, submit
reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import (
    BrainChatCaseIntelligenceBriefingReviewGate,
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceHumanReviewRequest:
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    briefing_status: str
    review_status: str
    request_status: str
    human_review_request_ready: bool
    case_review_ready: bool
    approval_granted: bool
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    human_review_items: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    requested_human_decision_options: tuple[str, ...]
    question_count: int
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-human-review-request"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_human_review_request",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "current_stage": self.current_stage,
            "current_status": self.current_status,
            "briefing_status": self.briefing_status,
            "review_status": self.review_status,
            "request_status": self.request_status,
            "human_review_request_ready": self.human_review_request_ready,
            "case_review_ready": self.case_review_ready,
            "approval_granted": self.approval_granted,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
            "human_review_items": list(self.human_review_items),
            "required_human_checks": list(self.required_human_checks),
            "rejected_actions": list(self.rejected_actions),
            "requested_human_decision_options": list(self.requested_human_decision_options),
            "question_count": self.question_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "approval_granted": False,
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

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Human Review Request") -> str:
        lines = [
            f"# {title}",
            "",
            "## Request State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Current stage: `{self.current_stage}`",
            f"- Current status: `{self.current_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Request status: `{self.request_status}`",
            f"- Human review request ready: `{self.human_review_request_ready}`",
            f"- Case review ready: `{self.case_review_ready}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            f"- Questions answered: `{self.question_count}`",
            "",
            "## Human Review Items",
            "",
        ]

        if self.human_review_items:
            for item in self.human_review_items:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence Checklist", ""])
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

        lines.extend(["", "## Requested Human Decision Options", ""])
        for item in self.requested_human_decision_options:
            lines.append(f"- `{item}`")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This request is local, deterministic, and planning-only.",
                "- It does not grant approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_intelligence_human_review_request(
    gate: BrainChatCaseIntelligenceBriefingReviewGate,
    source: str = "brain-chat-case-intelligence-human-review-request",
) -> BrainChatCaseIntelligenceHumanReviewRequest:
    data = gate.to_dict()

    request_status = _request_status(data)
    human_review_request_ready = request_status in {
        "ready-for-human-review",
        "ready-for-human-case-review",
    }

    return BrainChatCaseIntelligenceHumanReviewRequest(
        target_name=str(data.get("target_name") or "unknown"),
        focus_endpoint=_string_or_none(data.get("focus_endpoint")),
        current_stage=str(data.get("current_stage") or "unknown"),
        current_status=str(data.get("current_status") or "unknown"),
        briefing_status=str(data.get("briefing_status") or "unknown"),
        review_status=str(data.get("review_status") or "unknown"),
        request_status=request_status,
        human_review_request_ready=human_review_request_ready,
        case_review_ready=bool(data.get("case_review_ready", False)),
        approval_granted=False,
        blocked=bool(data.get("blocked", True)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence"))),
        blockers_checklist=tuple(_string_list(data.get("blockers"))),
        human_review_items=tuple(_string_list(data.get("human_review_items"))),
        required_human_checks=tuple(_string_list(data.get("required_human_checks"))),
        rejected_actions=tuple(_string_list(data.get("rejected_actions")) or _default_rejected_actions()),
        requested_human_decision_options=_decision_options(request_status),
        question_count=_safe_int(data.get("question_count")),
        source=source,
    )


def _request_status(data: dict[str, Any]) -> str:
    review_status = str(data.get("review_status") or "")

    if _unsafe_flags(data):
        return "blocked-pending-safe-review-gate"

    if review_status == "blocked-briefing":
        return "blocked-pending-briefing-review-gate"

    if review_status == "ready-for-human-case-review" and bool(data.get("case_review_ready")):
        return "ready-for-human-case-review"

    if review_status == "needs-human-review":
        return "ready-for-human-review"

    return "blocked-pending-briefing-review-gate"


def _unsafe_flags(data: dict[str, Any]) -> bool:
    if bool(data.get("runtime_execution_allowed")):
        return True
    if bool(data.get("report_submission_allowed")):
        return True
    if bool(data.get("vulnerability_confirmation_allowed")):
        return True

    safety = data.get("safety")
    if isinstance(safety, dict):
        unsafe_keys = (
            "approval_granted",
            "tool_execution",
            "evidence_collection",
            "validation_execution",
            "report_submission",
            "vulnerability_confirmation",
        )
        return any(bool(safety.get(key)) for key in unsafe_keys)

    return False


def _decision_options(request_status: str) -> tuple[str, ...]:
    if request_status.startswith("blocked"):
        return ("changes-requested", "rejected")

    return ("approved-for-human-case-review", "changes-requested", "rejected")


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _default_rejected_actions() -> list[str]:
    return [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this request.",
        "Do not collect new evidence from a target from this request.",
        "Do not submit a report from human-review request state alone.",
        "Do not claim vulnerability confirmation from human-review request state alone.",
        "Do not treat this request as approval.",
    ]
