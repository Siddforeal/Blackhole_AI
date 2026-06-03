"""
Brain chat human case review decision request.

This module turns a reviewed human case-review packet into a local human
case-review decision request. It does not grant side-effectful approval, call
LLM providers, execute tools, collect evidence, send requests, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_human_case_review_packet_review_gate import (
    BrainChatHumanCaseReviewPacketReviewGate,
)


@dataclass(frozen=True)
class BrainChatHumanCaseReviewDecisionRequest:
    decision: str
    decision_gate_status: str
    case_review_packet_status: str
    packet_review_status: str
    decision_request_status: str
    human_case_review_decision_ready: bool
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    blocked: bool
    requested_human_decision_options: tuple[str, ...]
    reviewer_instructions: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    packet_blockers: tuple[str, ...]
    decision_blockers: tuple[str, ...]
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-human-case-review-decision-request"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_human_case_review_decision_request",
            "source": self.source,
            "decision": self.decision,
            "decision_gate_status": self.decision_gate_status,
            "case_review_packet_status": self.case_review_packet_status,
            "packet_review_status": self.packet_review_status,
            "decision_request_status": self.decision_request_status,
            "human_case_review_decision_ready": self.human_case_review_decision_ready,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "blocked": self.blocked,
            "requested_human_decision_options": list(self.requested_human_decision_options),
            "reviewer_instructions": list(self.reviewer_instructions),
            "required_human_checks": list(self.required_human_checks),
            "packet_blockers": list(self.packet_blockers),
            "decision_blockers": list(self.decision_blockers),
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
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
                "human_case_review_decision_ready": self.human_case_review_decision_ready,
                "human_case_review_ready": self.human_case_review_ready,
                "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
                "approval_granted": self.approval_granted,
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

    def to_markdown(self, title: str = "Brain Chat Human Case Review Decision Request") -> str:
        lines = [
            f"# {title}",
            "",
            "## Request State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Decision gate status: `{self.decision_gate_status}`",
            f"- Case review packet status: `{self.case_review_packet_status}`",
            f"- Packet review status: `{self.packet_review_status}`",
            f"- Decision request status: `{self.decision_request_status}`",
            f"- Human case review decision ready: `{self.human_case_review_decision_ready}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Requested Human Decision Options",
            "",
        ]

        for item in self.requested_human_decision_options:
            lines.append(f"- `{item}`")

        lines.extend(["", "## Reviewer Instructions", ""])
        for item in self.reviewer_instructions:
            lines.append(f"- {item}")

        lines.extend(["", "## Required Human Checks", ""])
        if self.required_human_checks:
            for item in self.required_human_checks:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Packet Blockers", ""])
        if self.packet_blockers:
            for item in self.packet_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

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
                "- This decision request is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_human_case_review_decision_request(
    packet_review_gate: BrainChatHumanCaseReviewPacketReviewGate,
    source: str = "brain-chat-human-case-review-decision-request",
) -> BrainChatHumanCaseReviewDecisionRequest:
    data = packet_review_gate.to_dict()

    packet_review_status = str(data.get("packet_review_status") or "unknown")
    unsafe_blockers = _unsafe_blockers(data)
    decision_request_status = _decision_request_status(packet_review_status, unsafe_blockers)

    ready = decision_request_status == "ready-for-human-case-review-decision"

    return BrainChatHumanCaseReviewDecisionRequest(
        decision=str(data.get("decision") or "unknown"),
        decision_gate_status=str(data.get("decision_gate_status") or "unknown"),
        case_review_packet_status=str(data.get("case_review_packet_status") or "unknown"),
        packet_review_status=packet_review_status,
        decision_request_status=decision_request_status,
        human_case_review_decision_ready=ready,
        human_case_review_ready=bool(data.get("human_case_review_ready", False)) and ready,
        effective_human_review_approval_granted=bool(data.get("effective_human_review_approval_granted", False)) and ready,
        approval_granted=bool(data.get("approval_granted", False)) and ready,
        blocked=bool(data.get("blocked", True)) or not ready,
        requested_human_decision_options=tuple(_decision_options(decision_request_status)),
        reviewer_instructions=tuple(_reviewer_instructions(decision_request_status)),
        required_human_checks=tuple(_required_human_checks(data, decision_request_status)),
        packet_blockers=tuple(_string_list(data.get("packet_blockers")) + unsafe_blockers),
        decision_blockers=tuple(_string_list(data.get("decision_blockers"))),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(data.get("blockers_checklist"))),
        allowed_local_next_steps=tuple(_allowed_next_steps(decision_request_status)),
        rejected_actions=tuple(_rejected_actions(decision_request_status)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        source=source,
    )


def _decision_request_status(packet_review_status: str, unsafe_blockers: list[str]) -> str:
    if unsafe_blockers:
        return "blocked-pending-safe-packet-review-gate"

    if packet_review_status == "changes-requested":
        return "changes-requested"

    if packet_review_status == "rejected":
        return "rejected"

    if packet_review_status == "ready-for-human-case-review":
        return "ready-for-human-case-review-decision"

    return "blocked-pending-packet-review-gate"


def _decision_options(decision_request_status: str) -> list[str]:
    if decision_request_status == "ready-for-human-case-review-decision":
        return [
            "approved-for-next-local-planning-gate",
            "changes-requested",
            "rejected",
        ]

    if decision_request_status == "changes-requested":
        return ["changes-requested", "rejected"]

    return ["rejected", "changes-requested"]


def _reviewer_instructions(decision_request_status: str) -> list[str]:
    if decision_request_status == "ready-for-human-case-review-decision":
        return [
            "Review the local packet, evidence posture, safety metadata, and rejected actions before deciding.",
            "Only approve if the case can move to the next local planning gate without execution, collection, reporting, or vulnerability confirmation.",
            "Use changes-requested if evidence, blockers, or review notes require updates.",
            "Use rejected if this case-review path should stop.",
        ]

    if decision_request_status == "changes-requested":
        return [
            "Review the requested changes before another decision request is produced.",
            "Do not approve until the packet review gate becomes ready.",
        ]

    if decision_request_status == "rejected":
        return [
            "Record the rejected path and do not advance unless a new local packet is produced.",
        ]

    return [
        "Do not approve this request while the packet review gate is blocked.",
        "Resolve packet blockers, missing evidence, required checks, and unsafe flags before another decision request.",
    ]


def _required_human_checks(data: dict[str, Any], decision_request_status: str) -> list[str]:
    checks = _string_list(data.get("required_human_checks"))

    if decision_request_status == "ready-for-human-case-review-decision":
        checks.extend(
            [
                "Confirm scope and authorization are documented.",
                "Confirm no validation, execution, evidence collection, report submission, or vulnerability confirmation is being authorized.",
                "Confirm rejected actions remain rejected.",
            ]
        )

    return list(dict.fromkeys(item for item in checks if item))


def _allowed_next_steps(decision_request_status: str) -> list[str]:
    if decision_request_status == "ready-for-human-case-review-decision":
        return [
            "Create or import a local human case-review decision file.",
            "Keep validation, execution, evidence collection, reporting, and vulnerability confirmation behind separate gates.",
        ]

    if decision_request_status == "changes-requested":
        return [
            "Apply requested local changes and rebuild the packet review gate.",
        ]

    if decision_request_status == "rejected":
        return [
            "Stop this human case-review path unless a new local packet is produced.",
        ]

    if decision_request_status == "blocked-pending-safe-packet-review-gate":
        return [
            "Fix unsafe packet review gate state before requesting a human case-review decision.",
        ]

    return [
        "Resolve packet review gate blockers before requesting a human case-review decision.",
    ]


def _rejected_actions(decision_request_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this decision request.",
        "Do not collect new evidence from a target from this decision request.",
        "Do not submit a report from human case-review decision request state alone.",
        "Do not claim vulnerability confirmation from human case-review decision request state alone.",
        "Do not treat this decision request as validation or runtime execution approval.",
    ]

    if decision_request_status != "ready-for-human-case-review-decision":
        rejected.insert(0, "Do not request approval while the decision request is blocked.")

    return rejected


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


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
