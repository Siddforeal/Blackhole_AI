"""
Brain chat human case review packet review gate.

This module reviews a local human case-review packet and classifies whether
the packet is blocked, changes-requested, rejected, or ready for human case
review. It does not grant side-effectful approval, call LLM providers, execute
tools, collect evidence, send requests, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_human_case_review_packet import (
    BrainChatHumanCaseReviewPacket,
)


@dataclass(frozen=True)
class BrainChatHumanCaseReviewPacketReviewGate:
    decision: str
    decision_gate_status: str
    case_review_packet_status: str
    packet_review_status: str
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    blocked: bool
    packet_blockers: tuple[str, ...]
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
    source: str = "brain-chat-human-case-review-packet-review-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_human_case_review_packet_review_gate",
            "source": self.source,
            "decision": self.decision,
            "decision_gate_status": self.decision_gate_status,
            "case_review_packet_status": self.case_review_packet_status,
            "packet_review_status": self.packet_review_status,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "blocked": self.blocked,
            "packet_blockers": list(self.packet_blockers),
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

    def to_markdown(self, title: str = "Brain Chat Human Case Review Packet Review Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Review Gate State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Decision gate status: `{self.decision_gate_status}`",
            f"- Case review packet status: `{self.case_review_packet_status}`",
            f"- Packet review status: `{self.packet_review_status}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Packet Blockers",
            "",
        ]

        if self.packet_blockers:
            for item in self.packet_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Review Scope", ""])
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
                "- This review gate is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_human_case_review_packet_review_gate(
    packet: BrainChatHumanCaseReviewPacket,
    source: str = "brain-chat-human-case-review-packet-review-gate",
) -> BrainChatHumanCaseReviewPacketReviewGate:
    data = packet.to_dict()

    packet_status = str(data.get("case_review_packet_status") or "unknown")
    human_ready = bool(data.get("human_case_review_ready", False))
    effective_approval = bool(data.get("effective_human_review_approval_granted", False))
    approval_granted = bool(data.get("approval_granted", False))

    unsafe_blockers = _unsafe_blockers(data)
    packet_blockers = list(unsafe_blockers)
    review_status = _review_status(packet_status, human_ready, effective_approval, approval_granted, unsafe_blockers)

    if review_status == "blocked-pending-human-case-review-packet":
        packet_blockers.extend(_blocked_packet_reasons(data, human_ready, effective_approval, approval_granted))
    elif review_status == "changes-requested":
        packet_blockers.append("Human case-review packet has changes requested.")
    elif review_status == "rejected":
        packet_blockers.append("Human case-review packet path is rejected.")

    packet_blockers = tuple(dict.fromkeys(item for item in packet_blockers if item))

    ready = review_status == "ready-for-human-case-review"

    return BrainChatHumanCaseReviewPacketReviewGate(
        decision=str(data.get("decision") or "unknown"),
        decision_gate_status=str(data.get("decision_gate_status") or "unknown"),
        case_review_packet_status=packet_status,
        packet_review_status=review_status,
        human_case_review_ready=ready,
        effective_human_review_approval_granted=effective_approval and ready,
        approval_granted=approval_granted and ready,
        blocked=bool(data.get("blocked", True)) or not ready,
        packet_blockers=packet_blockers,
        review_scope=tuple(_string_list(data.get("review_scope"))),
        human_review_tasks=tuple(_string_list(data.get("human_review_tasks"))),
        decision_blockers=tuple(_string_list(data.get("decision_blockers"))),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(data.get("blockers_checklist"))),
        required_human_checks=tuple(_string_list(data.get("required_human_checks"))),
        allowed_local_next_steps=tuple(_allowed_next_steps(review_status)),
        rejected_actions=tuple(_rejected_actions(review_status)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        source=source,
    )


def _review_status(
    packet_status: str,
    human_ready: bool,
    effective_approval: bool,
    approval_granted: bool,
    unsafe_blockers: list[str],
) -> str:
    if packet_status == "changes-requested":
        return "changes-requested"

    if packet_status == "rejected":
        return "rejected"

    if (
        packet_status == "ready-for-human-case-review"
        and human_ready
        and effective_approval
        and approval_granted
        and not unsafe_blockers
    ):
        return "ready-for-human-case-review"

    return "blocked-pending-human-case-review-packet"


def _blocked_packet_reasons(
    data: dict[str, Any],
    human_ready: bool,
    effective_approval: bool,
    approval_granted: bool,
) -> list[str]:
    blockers: list[str] = []

    if not human_ready:
        blockers.append("Human case-review packet is not ready.")

    if not effective_approval:
        blockers.append("Effective human review approval is not granted.")

    if not approval_granted:
        blockers.append("Approval is not granted.")

    if bool(data.get("blocked", True)):
        blockers.append("Case remains blocked.")

    if _string_list(data.get("decision_blockers")):
        blockers.append("Decision blockers remain.")

    if _string_list(data.get("missing_evidence_checklist")):
        blockers.append("Missing evidence checklist is not empty.")

    if _string_list(data.get("blockers_checklist")):
        blockers.append("Blockers checklist is not empty.")

    if _string_list(data.get("required_human_checks")):
        blockers.append("Required human checks remain.")

    return blockers


def _unsafe_blockers(data: dict[str, Any]) -> list[str]:
    blockers: list[str] = []

    if bool(data.get("validation_allowed")):
        blockers.append("Validation is unexpectedly allowed.")
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


def _allowed_next_steps(review_status: str) -> list[str]:
    if review_status == "ready-for-human-case-review":
        return [
            "Begin local human case review only.",
            "Keep validation, execution, evidence collection, reporting, and vulnerability confirmation behind separate gates.",
        ]

    if review_status == "changes-requested":
        return [
            "Apply requested local changes and rebuild the human case-review packet.",
        ]

    if review_status == "rejected":
        return [
            "Stop this human case-review path unless a new local packet is produced.",
        ]

    return [
        "Resolve packet blockers before starting human case review.",
    ]


def _rejected_actions(review_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this packet review gate.",
        "Do not collect new evidence from a target from this packet review gate.",
        "Do not submit a report from human case-review packet review state alone.",
        "Do not claim vulnerability confirmation from human case-review packet review state alone.",
        "Do not treat this packet review gate as validation or runtime execution approval.",
    ]

    if review_status != "ready-for-human-case-review":
        rejected.insert(0, "Do not begin human case review until the packet review gate is ready.")

    return rejected


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
