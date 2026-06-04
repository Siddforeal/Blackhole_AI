"""
Brain chat human case review decision gate.

This module reviews an imported human case-review decision and determines
whether the case can move to the next local planning gate. It does not grant
runtime execution, validation execution, evidence collection, report submission,
or vulnerability confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_human_case_review_decision_importer import (
    BrainChatHumanCaseReviewDecisionImport,
)


@dataclass(frozen=True)
class BrainChatHumanCaseReviewDecisionGate:
    decision: str
    decision_request_status: str
    decision_import_status: str
    decision_gate_status: str
    human_case_review_decision_ready: bool
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    effective_next_local_planning_approval_granted: bool
    next_local_planning_gate_ready: bool
    decision_effective: bool
    decision_blockers: tuple[str, ...]
    packet_blockers: tuple[str, ...]
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
    source: str = "brain-chat-human-case-review-decision-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_human_case_review_decision_gate",
            "source": self.source,
            "decision": self.decision,
            "decision_request_status": self.decision_request_status,
            "decision_import_status": self.decision_import_status,
            "decision_gate_status": self.decision_gate_status,
            "human_case_review_decision_ready": self.human_case_review_decision_ready,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "effective_next_local_planning_approval_granted": self.effective_next_local_planning_approval_granted,
            "next_local_planning_gate_ready": self.next_local_planning_gate_ready,
            "decision_effective": self.decision_effective,
            "decision_blockers": list(self.decision_blockers),
            "packet_blockers": list(self.packet_blockers),
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
                "next_local_planning_gate_ready": self.next_local_planning_gate_ready,
                "effective_next_local_planning_approval_granted": self.effective_next_local_planning_approval_granted,
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

    def to_markdown(self, title: str = "Brain Chat Human Case Review Decision Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Gate State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Decision request status: `{self.decision_request_status}`",
            f"- Decision import status: `{self.decision_import_status}`",
            f"- Decision gate status: `{self.decision_gate_status}`",
            f"- Human case review decision ready: `{self.human_case_review_decision_ready}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Effective next local planning approval granted: `{self.effective_next_local_planning_approval_granted}`",
            f"- Next local planning gate ready: `{self.next_local_planning_gate_ready}`",
            f"- Decision effective: `{self.decision_effective}`",
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

        lines.extend(["", "## Packet Blockers", ""])
        if self.packet_blockers:
            for item in self.packet_blockers:
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
        for item in self.allowed_local_next_steps:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This decision gate is local, deterministic, and planning-only.",
                "- It does not grant runtime execution, validation execution, evidence collection, report submission, or vulnerability confirmation.",
                "",
            ]
        )

        return "\n".join(lines)


def build_human_case_review_decision_gate(
    imported_decision: BrainChatHumanCaseReviewDecisionImport,
    source: str = "brain-chat-human-case-review-decision-gate",
) -> BrainChatHumanCaseReviewDecisionGate:
    data = imported_decision.to_dict()
    unsafe_blockers = _unsafe_blockers(data)

    decision = str(data.get("decision") or "unknown")
    import_status = str(data.get("decision_import_status") or "unknown")
    effective_next = bool(data.get("effective_next_local_planning_approval_granted", False))
    decision_effective = bool(data.get("decision_effective", False))

    gate_status = _gate_status(
        decision=decision,
        import_status=import_status,
        effective_next=effective_next,
        decision_effective=decision_effective,
        unsafe_blockers=unsafe_blockers,
    )

    ready = gate_status == "ready-for-next-local-planning-gate"

    decision_blockers = _string_list(data.get("decision_blockers"))
    if unsafe_blockers:
        decision_blockers.extend(unsafe_blockers)
    if not ready and import_status.startswith("blocked"):
        decision_blockers.insert(0, f"Decision import is blocked: {import_status}.")
    if not ready and decision == "approved-for-next-local-planning-gate":
        decision_blockers.insert(0, "Approval is not effective for the next local planning gate.")

    return BrainChatHumanCaseReviewDecisionGate(
        decision=decision,
        decision_request_status=str(data.get("decision_request_status") or "unknown"),
        decision_import_status=import_status,
        decision_gate_status=gate_status,
        human_case_review_decision_ready=bool(data.get("human_case_review_decision_ready", False)) and ready,
        human_case_review_ready=bool(data.get("human_case_review_ready", False)) and ready,
        effective_human_review_approval_granted=bool(data.get("effective_human_review_approval_granted", False)) and ready,
        approval_granted=bool(data.get("approval_granted", False)) and ready,
        effective_next_local_planning_approval_granted=effective_next and ready,
        next_local_planning_gate_ready=ready,
        decision_effective=decision_effective,
        decision_blockers=tuple(dict.fromkeys(item for item in decision_blockers if item)),
        packet_blockers=tuple(_string_list(data.get("packet_blockers"))),
        missing_evidence_checklist=tuple(_string_list(data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(data.get("blockers_checklist"))),
        required_human_checks=tuple(_string_list(data.get("required_human_checks"))),
        allowed_local_next_steps=tuple(_allowed_next_steps(gate_status)),
        rejected_actions=tuple(_rejected_actions(gate_status)),
        validation_allowed=bool(data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(data.get("vulnerability_confirmation_allowed", False)),
        source=source,
    )


def _gate_status(
    decision: str,
    import_status: str,
    effective_next: bool,
    decision_effective: bool,
    unsafe_blockers: list[str],
) -> str:
    if unsafe_blockers:
        return "blocked-pending-safe-human-case-review-decision-import"

    if import_status == "changes-requested":
        return "changes-requested"

    if import_status == "rejected":
        return "rejected"

    if decision == "approved-for-next-local-planning-gate" and effective_next and decision_effective:
        return "ready-for-next-local-planning-gate"

    return "blocked-pending-effective-human-case-review-decision"


def _allowed_next_steps(gate_status: str) -> list[str]:
    if gate_status == "ready-for-next-local-planning-gate":
        return [
            "Proceed to the next local planning gate only.",
            "Keep validation, execution, evidence collection, reporting, and vulnerability confirmation behind separate gates.",
        ]

    if gate_status == "changes-requested":
        return [
            "Apply requested local changes before rebuilding the human case-review decision request.",
        ]

    if gate_status == "rejected":
        return [
            "Stop this human case-review path unless a new local decision request is produced.",
        ]

    if gate_status == "blocked-pending-safe-human-case-review-decision-import":
        return [
            "Fix unsafe imported decision state before moving to the next local planning gate.",
        ]

    return [
        "Resolve human case-review decision import blockers before moving to the next local planning gate.",
    ]


def _rejected_actions(gate_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this decision gate.",
        "Do not collect new evidence from a target from this decision gate.",
        "Do not submit a report from human case-review decision gate state alone.",
        "Do not claim vulnerability confirmation from human case-review decision gate state alone.",
        "Do not treat this decision gate as validation or runtime execution approval.",
    ]

    if gate_status != "ready-for-next-local-planning-gate":
        rejected.insert(0, "Do not advance to the next local planning gate while this gate is blocked.")

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
