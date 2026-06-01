"""
Brain chat case intelligence human review decision gate.

This module reviews an imported case-intelligence human-review decision and
classifies the next local state. It does not grant side-effectful approval,
call LLM providers, execute tools, collect evidence, send requests, mutate
targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_human_review_decision_importer import (
    BrainChatCaseIntelligenceHumanReviewDecision,
)


@dataclass(frozen=True)
class BrainChatCaseIntelligenceHumanReviewDecisionGate:
    decision: str
    decision_gate_status: str
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    request_status: str
    review_status: str
    briefing_status: str
    human_review_request_ready: bool
    case_review_ready: bool
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    decision_blockers: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-human-review-decision-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_human_review_decision_gate",
            "source": self.source,
            "decision": self.decision,
            "decision_gate_status": self.decision_gate_status,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "request_status": self.request_status,
            "review_status": self.review_status,
            "briefing_status": self.briefing_status,
            "human_review_request_ready": self.human_review_request_ready,
            "case_review_ready": self.case_review_ready,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "decision_blockers": list(self.decision_blockers),
            "allowed_local_next_steps": list(self.allowed_local_next_steps),
            "rejected_actions": list(self.rejected_actions),
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
            "required_human_checks": list(self.required_human_checks),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "human_case_review_ready": self.human_case_review_ready,
                "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
                "approval_side_effects": False,
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

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Human Review Decision Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Gate State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Decision gate status: `{self.decision_gate_status}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Request status: `{self.request_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Human review request ready: `{self.human_review_request_ready}`",
            f"- Case review ready: `{self.case_review_ready}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Decision Blockers",
            "",
        ]

        if self.decision_blockers:
            for item in self.decision_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Local Next Steps", ""])
        if self.allowed_local_next_steps:
            for item in self.allowed_local_next_steps:
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

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This decision gate is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_intelligence_human_review_decision_gate(
    decision: BrainChatCaseIntelligenceHumanReviewDecision,
    source: str = "brain-chat-case-intelligence-human-review-decision-gate",
) -> BrainChatCaseIntelligenceHumanReviewDecisionGate:
    data = decision.to_dict()

    decision_value = str(data.get("decision") or "unknown")
    unsafe_blockers = _unsafe_blockers(data)
    effective_approval = bool(data.get("effective_human_review_approval_granted", False))
    approval_granted = bool(data.get("approval_granted", False))
    request_ready = bool(data.get("human_review_request_ready", False))
    case_review_ready = bool(data.get("case_review_ready", False))

    decision_blockers = list(unsafe_blockers)
    decision_gate_status = "blocked-pending-effective-human-review"
    human_case_review_ready = False

    if decision_value == "changes-requested":
        decision_gate_status = "changes-requested"
        decision_blockers.extend(_changes_requested_blockers(data))
    elif decision_value == "rejected":
        decision_gate_status = "rejected"
        decision_blockers.extend(_rejected_blockers(data))
    elif decision_value == "approved-for-human-case-review":
        if effective_approval and approval_granted and request_ready and case_review_ready and not unsafe_blockers:
            decision_gate_status = "ready-for-human-case-review"
            human_case_review_ready = True
        else:
            decision_gate_status = "blocked-pending-effective-human-review"
            decision_blockers.extend(_approval_blockers(data, effective_approval, request_ready, case_review_ready))
    else:
        decision_gate_status = "blocked-pending-effective-human-review"
        decision_blockers.append("Decision value is not recognized by the decision gate.")

    decision_blockers = list(dict.fromkeys(item for item in decision_blockers if item))

    return BrainChatCaseIntelligenceHumanReviewDecisionGate(
        decision=decision_value,
        decision_gate_status=decision_gate_status,
        human_case_review_ready=human_case_review_ready,
        effective_human_review_approval_granted=effective_approval and human_case_review_ready,
        approval_granted=approval_granted and human_case_review_ready,
        request_status=str(data.get("request_status") or "unknown"),
        review_status=str(data.get("review_status") or "unknown"),
        briefing_status=str(data.get("briefing_status") or "unknown"),
        human_review_request_ready=request_ready,
        case_review_ready=case_review_ready,
        blocked=bool(data.get("blocked", True)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        decision_blockers=tuple(decision_blockers),
        allowed_local_next_steps=tuple(_allowed_local_next_steps(decision_gate_status)),
        rejected_actions=tuple(_rejected_actions(decision_gate_status)),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(data.get("blockers_checklist"))),
        required_human_checks=tuple(_string_list(data.get("required_human_checks"))),
        source=source,
    )


def _approval_blockers(
    data: dict[str, Any],
    effective_approval: bool,
    request_ready: bool,
    case_review_ready: bool,
) -> list[str]:
    blockers: list[str] = []

    if not effective_approval:
        blockers.append("Human review approval is not effective.")

    if not request_ready:
        blockers.append("Human review request is not ready.")

    if not case_review_ready:
        blockers.append("Case review gate is not ready.")

    if bool(data.get("blocked", True)):
        blockers.append("Case remains blocked.")

    if _string_list(data.get("missing_evidence_checklist")):
        blockers.append("Missing evidence checklist is not empty.")

    if _string_list(data.get("blockers_checklist")):
        blockers.append("Blockers checklist is not empty.")

    return blockers


def _changes_requested_blockers(data: dict[str, Any]) -> list[str]:
    blockers = ["Human review requested changes."]
    if _string_list(data.get("missing_evidence_checklist")):
        blockers.append("Missing evidence must be updated before another review request.")
    if _string_list(data.get("blockers_checklist")):
        blockers.append("Blockers must be resolved or documented before another review request.")
    return blockers


def _rejected_blockers(data: dict[str, Any]) -> list[str]:
    return ["Human review rejected this case-review path."]


def _unsafe_blockers(data: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    if bool(data.get("runtime_execution_allowed")):
        blockers.append("Runtime execution is unexpectedly allowed.")
    if bool(data.get("report_submission_allowed")):
        blockers.append("Report submission is unexpectedly allowed.")
    if bool(data.get("vulnerability_confirmation_allowed")):
        blockers.append("Vulnerability confirmation is unexpectedly allowed.")

    safety = data.get("safety")
    if isinstance(safety, dict):
        if bool(safety.get("human_approval_side_effects")):
            blockers.append("Human approval side effects are unexpectedly enabled.")
        if bool(safety.get("tool_execution")):
            blockers.append("Tool execution is unexpectedly enabled.")
        if bool(safety.get("evidence_collection")):
            blockers.append("Evidence collection is unexpectedly enabled.")
        if bool(safety.get("validation_execution")):
            blockers.append("Validation execution is unexpectedly enabled.")
        if bool(safety.get("report_submission")):
            blockers.append("Report submission is unexpectedly enabled in safety metadata.")
        if bool(safety.get("vulnerability_confirmation")):
            blockers.append("Vulnerability confirmation is unexpectedly enabled in safety metadata.")

    return blockers


def _allowed_local_next_steps(decision_gate_status: str) -> list[str]:
    if decision_gate_status == "ready-for-human-case-review":
        return [
            "Proceed to local human case review of the briefing and decision packet.",
            "Keep validation, runtime execution, evidence collection, report submission, and vulnerability confirmation behind separate gates.",
        ]

    if decision_gate_status == "changes-requested":
        return [
            "Apply requested local changes to the case artifacts.",
            "Re-run the briefing review, human-review request, and decision import after changes.",
        ]

    if decision_gate_status == "rejected":
        return [
            "Stop this case-review path unless a new local case review request is produced.",
        ]

    return [
        "Resolve the blocked human-review request and decision blockers before advancing.",
    ]


def _rejected_actions(decision_gate_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this decision gate.",
        "Do not collect new evidence from a target from this decision gate.",
        "Do not submit a report from human-review decision-gate state alone.",
        "Do not claim vulnerability confirmation from human-review decision-gate state alone.",
        "Do not treat this gate as validation or runtime execution approval.",
    ]

    if decision_gate_status != "ready-for-human-case-review":
        rejected.insert(0, "Do not proceed to human case review until the gate is ready.")

    return rejected


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
