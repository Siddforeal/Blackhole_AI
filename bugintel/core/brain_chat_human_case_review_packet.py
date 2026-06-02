"""
Brain chat human case review packet.

This module turns a case-intelligence human-review decision gate into a local
human case review packet. It does not grant side-effectful approval, call LLM
providers, execute tools, collect evidence, send requests, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_intelligence_human_review_decision_gate import (
    BrainChatCaseIntelligenceHumanReviewDecisionGate,
)


@dataclass(frozen=True)
class BrainChatHumanCaseReviewPacket:
    decision: str
    decision_gate_status: str
    case_review_packet_status: str
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    request_status: str
    review_status: str
    briefing_status: str
    blocked: bool
    review_objective: str
    review_scope: tuple[str, ...]
    human_review_tasks: tuple[str, ...]
    decision_blockers: tuple[str, ...]
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-human-case-review-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_human_case_review_packet",
            "source": self.source,
            "decision": self.decision,
            "decision_gate_status": self.decision_gate_status,
            "case_review_packet_status": self.case_review_packet_status,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "request_status": self.request_status,
            "review_status": self.review_status,
            "briefing_status": self.briefing_status,
            "blocked": self.blocked,
            "review_objective": self.review_objective,
            "review_scope": list(self.review_scope),
            "human_review_tasks": list(self.human_review_tasks),
            "decision_blockers": list(self.decision_blockers),
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
            "required_human_checks": list(self.required_human_checks),
            "allowed_local_next_steps": list(self.allowed_local_next_steps),
            "rejected_actions": list(self.rejected_actions),
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
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

    def to_markdown(self, title: str = "Brain Chat Human Case Review Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Packet State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Decision gate status: `{self.decision_gate_status}`",
            f"- Case review packet status: `{self.case_review_packet_status}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Request status: `{self.request_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Briefing status: `{self.briefing_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Review Objective",
            "",
            self.review_objective,
            "",
            "## Review Scope",
            "",
        ]

        for item in self.review_scope:
            lines.append(f"- {item}")

        lines.extend(["", "## Human Review Tasks", ""])
        for item in self.human_review_tasks:
            lines.append(f"- [ ] {item}")

        lines.extend(["", "## Decision Blockers", ""])
        if self.decision_blockers:
            for item in self.decision_blockers:
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

        lines.extend(["", "## Allowed Local Next Steps", ""])
        if self.allowed_local_next_steps:
            for item in self.allowed_local_next_steps:
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
                "- This packet is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_human_case_review_packet(
    gate: BrainChatCaseIntelligenceHumanReviewDecisionGate,
    source: str = "brain-chat-human-case-review-packet",
) -> BrainChatHumanCaseReviewPacket:
    data = gate.to_dict()

    decision_gate_status = str(data.get("decision_gate_status") or "unknown")
    human_case_review_ready = bool(data.get("human_case_review_ready", False))
    effective_approval = bool(data.get("effective_human_review_approval_granted", False))
    approval_granted = bool(data.get("approval_granted", False))

    packet_status = _packet_status(decision_gate_status, human_case_review_ready, effective_approval, approval_granted)

    return BrainChatHumanCaseReviewPacket(
        decision=str(data.get("decision") or "unknown"),
        decision_gate_status=decision_gate_status,
        case_review_packet_status=packet_status,
        human_case_review_ready=human_case_review_ready and packet_status == "ready-for-human-case-review",
        effective_human_review_approval_granted=effective_approval and packet_status == "ready-for-human-case-review",
        approval_granted=approval_granted and packet_status == "ready-for-human-case-review",
        request_status=str(data.get("request_status") or "unknown"),
        review_status=str(data.get("review_status") or "unknown"),
        briefing_status=str(data.get("briefing_status") or "unknown"),
        blocked=bool(data.get("blocked", True)),
        review_objective=_review_objective(packet_status),
        review_scope=tuple(_review_scope(packet_status)),
        human_review_tasks=tuple(_human_review_tasks(packet_status)),
        decision_blockers=tuple(_string_list(data.get("decision_blockers"))),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(data.get("blockers_checklist"))),
        required_human_checks=tuple(_string_list(data.get("required_human_checks"))),
        allowed_local_next_steps=tuple(_string_list(data.get("allowed_local_next_steps")) or _allowed_next_steps(packet_status)),
        rejected_actions=tuple(_string_list(data.get("rejected_actions")) or _rejected_actions(packet_status)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        source=source,
    )


def _packet_status(
    decision_gate_status: str,
    human_case_review_ready: bool,
    effective_approval: bool,
    approval_granted: bool,
) -> str:
    if decision_gate_status == "changes-requested":
        return "changes-requested"

    if decision_gate_status == "rejected":
        return "rejected"

    if (
        decision_gate_status == "ready-for-human-case-review"
        and human_case_review_ready
        and effective_approval
        and approval_granted
    ):
        return "ready-for-human-case-review"

    return "blocked-pending-human-review-decision-gate"


def _review_objective(packet_status: str) -> str:
    if packet_status == "ready-for-human-case-review":
        return "Review the local case briefing, evidence posture, and decision chain for human case-review readiness only."

    if packet_status == "changes-requested":
        return "Review requested changes before rebuilding the human case-review packet."

    if packet_status == "rejected":
        return "Record that this human case-review path is rejected unless a new local request is produced."

    return "Resolve decision blockers before human case review can begin."


def _review_scope(packet_status: str) -> list[str]:
    base = [
        "Local case state and briefing metadata.",
        "Evidence checklist status and remaining gaps.",
        "Approval and decision-gate chain state.",
        "Safety metadata and rejected actions.",
    ]

    if packet_status == "ready-for-human-case-review":
        base.append("Human case-review notes and local follow-up planning.")
    else:
        base.append("Blocked-state remediation planning only.")

    return base


def _human_review_tasks(packet_status: str) -> list[str]:
    if packet_status == "ready-for-human-case-review":
        return [
            "Confirm the case is in scope and authorized.",
            "Review evidence quality and redaction requirements.",
            "Review decision-chain consistency.",
            "Document whether the case can proceed to the next local planning gate.",
        ]

    if packet_status == "changes-requested":
        return [
            "Review the requested changes.",
            "Update local case artifacts before requesting another review.",
        ]

    if packet_status == "rejected":
        return [
            "Document the rejection reason.",
            "Do not advance this case-review path unless a new request is produced.",
        ]

    return [
        "Review decision blockers.",
        "Resolve missing evidence or blocker checklist items.",
        "Re-run the human-review decision gate after local fixes.",
    ]


def _allowed_next_steps(packet_status: str) -> list[str]:
    if packet_status == "ready-for-human-case-review":
        return [
            "Proceed with local human case review only.",
            "Keep validation, execution, reporting, and vulnerability confirmation behind separate gates.",
        ]

    if packet_status == "changes-requested":
        return [
            "Apply requested local changes and rebuild the review chain.",
        ]

    if packet_status == "rejected":
        return [
            "Stop this case-review path unless a new local review request is created.",
        ]

    return [
        "Resolve decision-gate blockers before advancing.",
    ]


def _rejected_actions(packet_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this packet.",
        "Do not collect new evidence from a target from this packet.",
        "Do not submit a report from human case-review packet state alone.",
        "Do not claim vulnerability confirmation from human case-review packet state alone.",
        "Do not treat this packet as validation or runtime execution approval.",
    ]

    if packet_status != "ready-for-human-case-review":
        rejected.insert(0, "Do not start human case review until the packet is ready.")

    return rejected


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
