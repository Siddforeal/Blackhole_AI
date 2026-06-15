"""Local research-state transition packet.

This module converts an approved human transition decision packet into a local,
reviewable research-state transition packet. It does not write persistent
research state, mutate hypothesis confidence, execute tools, interact with
targets, collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_DECISION_KIND = "brain_chat_research_state_transition_decision_packet"
EXPECTED_DECISION_STATUS = "ready-for-research-state-transition-packet"
EXPECTED_PACKET_KIND = "brain_chat_research_state_transition_packet"

FALSE_FLAGS: tuple[str, ...] = (
    "command_generation_allowed",
    "payload_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "confidence_update_allowed",
    "hypothesis_mutation_allowed",
    "selection_mutation_allowed",
    "investigation_plan_mutation_allowed",
    "research_state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {source}")
    return value


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_research_state_transition_packet(
    decision_packet: dict[str, Any],
    source: str = "brain-chat-research-state-transition-packet",
) -> dict[str, Any]:
    decision = copy.deepcopy(decision_packet)
    approved = _object_list(decision.get("approved_transition_candidates"))

    source_findings = _source_findings(decision, approved)
    safety_findings = _unsafe_flag_findings(decision, "decision_packet")
    operation_findings = _operation_findings(approved)

    status = _status(source_findings, safety_findings, operation_findings, approved)
    ready = status == "ready-for-research-state-transition-apply-review"

    operations = [
        _operation_record(index, item, ready)
        for index, item in enumerate(approved, start=1)
    ]

    packet = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(decision.get("target_name"), "unknown-target"),
        "packet_status": status,
        "summary": _summary(status, len(operations)),
        "source_decision_kind": _text(decision.get("kind")),
        "source_decision_status": _text(decision.get("decision_status")),
        "source_decision_digest": _text(decision.get("decision_digest")),
        "source_gate_digest": _text(decision.get("source_gate_digest")),
        "source_template_digest": _text(decision.get("source_template_digest")),
        "source_update_digest": _text(decision.get("source_update_digest")),
        "source_hypothesis_digest": _text(decision.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(decision.get("source_feedback_digest")),
        "approved_transition_count": len(approved),
        "transition_operation_count": len(operations),
        "local_transition_packet_ready": ready,
        "research_state_transition_apply_review_required": ready,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "transition_operations": operations,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "operation_findings": operation_findings,
        "counts": {
            "approved_transitions": len(approved),
            "transition_operations": len(operations),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "operation_findings": len(operation_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(operation_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this packet.",
            "Do not directly update hypothesis confidence from this packet.",
            "Do not mutate selected hypotheses or investigation plans.",
            "Do not execute tools or interact with targets.",
            "Do not collect evidence, submit reports, or confirm vulnerabilities.",
        ],
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    packet["transition_packet_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "packet_status": packet["packet_status"],
            "source_decision_digest": packet["source_decision_digest"],
            "transition_operations": packet["transition_operations"],
        }
    )
    return packet


def build_transition_packet_from_file(
    decision_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_transition_packet(
        load_json_object(decision_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(decision: dict[str, Any], approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if decision.get("kind") != EXPECTED_DECISION_KIND:
        findings.append(_finding("source-schema", "high", "Invalid transition decision packet kind.", "decision.kind", "Use a research-state transition decision packet."))

    if decision.get("decision_status") != EXPECTED_DECISION_STATUS:
        findings.append(_finding("source-status", "high", "Transition decision packet is not ready for state-transition packet creation.", "decision.decision_status", "Resolve decision packet blockers first."))

    if decision.get("human_transition_decision_complete") is not True:
        findings.append(_finding("source-readiness", "high", "Human transition decision is not complete.", "decision.human_transition_decision_complete", "Complete human transition decisions first."))

    if decision.get("research_state_transition_packet_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Decision packet is not marked ready for transition packet creation.", "decision.research_state_transition_packet_ready", "Use an approved transition decision packet."))

    if decision.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks research-state transition ready.", "decision.research_state_transition_ready", "Use only pre-apply decision packets."))

    if not approved:
        findings.append(_finding("source-content", "high", "No approved transition candidates are present.", "decision.approved_transition_candidates", "Approve at least one transition before building this packet."))

    expected_count = _int(decision.get("approved_transition_count"))
    if expected_count and expected_count != len(approved):
        findings.append(_finding("source-count", "medium", "Approved transition count does not match list length.", "decision.approved_transition_count", "Regenerate the decision packet."))

    if not _text(decision.get("decision_digest")):
        findings.append(_finding("source-digest", "medium", "Decision packet digest is missing.", "decision.decision_digest", "Regenerate the decision packet."))

    return findings


def _unsafe_flag_findings(data: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for flag in FALSE_FLAGS:
        if bool(data.get(flag)):
            findings.append(_finding("unsafe-flag", "high", f"Unsafe flag is true: {flag}.", f"{prefix}.{flag}", "Regenerate with all mutation and execution flags disabled."))

    if data.get("planning_only") is not True:
        findings.append(_finding("planning-only", "high", "Artifact is not marked planning-only.", f"{prefix}.planning_only", "Use only planning-only artifacts."))

    if _text(data.get("execution_state"), "not_executed") != "not_executed":
        findings.append(_finding("execution-state", "high", "Artifact execution_state is not not_executed.", f"{prefix}.execution_state", "Use only non-executed planning artifacts."))

    return findings


def _operation_findings(approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_transitions: set[str] = set()
    seen_hypotheses: set[str] = set()

    for item in approved:
        transition_id = _text(item.get("transition_id"))
        hypothesis_id = _text(item.get("hypothesis_id"))
        proposed_state_change = _text(item.get("proposed_state_change"))
        decision = _text(item.get("decision"))

        if not transition_id:
            findings.append(_finding("operation-schema", "high", "Approved transition is missing transition_id.", "approved.transition_id", "Regenerate the decision packet."))
        elif transition_id in seen_transitions:
            findings.append(_finding("operation-coverage", "high", f"Duplicate approved transition: {transition_id}.", transition_id, "Resolve duplicate approved transitions."))
        seen_transitions.add(transition_id)

        if not hypothesis_id:
            findings.append(_finding("operation-schema", "high", f"Approved transition {transition_id or '<missing>'} is missing hypothesis_id.", transition_id, "Regenerate the decision packet."))
        elif hypothesis_id in seen_hypotheses:
            findings.append(_finding("operation-coverage", "high", f"Multiple approved transitions target hypothesis {hypothesis_id}.", hypothesis_id, "Resolve duplicate hypothesis transitions."))
        seen_hypotheses.add(hypothesis_id)

        if proposed_state_change != "update-hypothesis-confidence":
            findings.append(_finding("operation-type", "high", f"Unsupported proposed_state_change: {proposed_state_change}.", transition_id, "Only update-hypothesis-confidence is supported in this packet."))

        if decision != "approve-transition-packet":
            findings.append(_finding("operation-decision", "high", f"Approved transition has non-approval decision: {decision}.", transition_id, "Use only approved transition decisions."))

        if not _text(item.get("current_confidence")):
            findings.append(_finding("operation-confidence", "high", f"Approved transition {transition_id or '<missing>'} lacks current_confidence.", transition_id, "Regenerate the decision packet."))

        if not _text(item.get("proposed_confidence")):
            findings.append(_finding("operation-confidence", "high", f"Approved transition {transition_id or '<missing>'} lacks proposed_confidence.", transition_id, "Regenerate the decision packet."))

        if not _text(item.get("decision_reason")):
            findings.append(_finding("operation-reason", "high", f"Approved transition {transition_id or '<missing>'} lacks decision_reason.", transition_id, "Provide the human decision reason."))

        if not _text(item.get("approved_transition_digest")):
            findings.append(_finding("operation-digest", "medium", f"Approved transition {transition_id or '<missing>'} lacks approved_transition_digest.", transition_id, "Regenerate the decision packet."))

        for flag in (
            "research_state_transition_allowed",
            "confidence_update_allowed",
            "research_state_mutation_allowed",
            "execution_allowed",
            "runtime_execution_allowed",
        ):
            if bool(item.get(flag)):
                findings.append(_finding("operation-unsafe-flag", "high", f"Approved transition unsafe flag is true: {flag}.", f"{transition_id}.{flag}", "Keep transition records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("operation-planning-only", "high", f"Approved transition {transition_id or '<missing>'} is not planning-only.", transition_id, "Use only planning-only transition records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("operation-execution-state", "high", f"Approved transition {transition_id or '<missing>'} execution_state is not not_executed.", transition_id, "Use only non-executed transition records."))

    return findings


def _operation_record(index: int, transition: dict[str, Any], ready: bool) -> dict[str, Any]:
    record = {
        "operation_id": f"RSTO-{index:03d}",
        "transition_id": _text(transition.get("transition_id")),
        "decision_id": _text(transition.get("decision_id")),
        "source_update_id": _text(transition.get("source_update_id")),
        "hypothesis_id": _text(transition.get("hypothesis_id")),
        "title": _text(transition.get("title")),
        "operation_type": "local-proposed-hypothesis-confidence-update",
        "field_path": f"hypotheses.{_text(transition.get('hypothesis_id'))}.confidence",
        "current_value": _text(transition.get("current_confidence")),
        "proposed_value": _text(transition.get("proposed_confidence")),
        "decision": _text(transition.get("decision")),
        "decision_reason": _text(transition.get("decision_reason")),
        "source_update_digest": _text(transition.get("source_update_digest")),
        "source_transition_candidate_digest": _text(transition.get("source_transition_candidate_digest")),
        "source_approved_transition_digest": _text(transition.get("approved_transition_digest")),
        "apply_review_required": ready,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    record["operation_digest"] = _sha256(record)
    return record


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    operation_findings: list[dict[str, str]],
    approved: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-transition-decision-packet"
    if _high(safety_findings):
        return "blocked-unsafe-transition-decision-packet"
    if not approved:
        return "blocked-no-approved-transitions"
    if _high(operation_findings):
        return "blocked-invalid-transition-operations"
    return "ready-for-research-state-transition-apply-review"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-research-state-transition-apply-review":
        return f"{count} local transition operation(s) are ready for a later apply review gate."
    if status == "blocked-invalid-transition-decision-packet":
        return "Transition packet blocked because the source decision packet is invalid."
    if status == "blocked-unsafe-transition-decision-packet":
        return "Transition packet blocked because the source decision packet enables mutation or execution."
    if status == "blocked-no-approved-transitions":
        return "Transition packet blocked because there are no approved transitions."
    if status == "blocked-invalid-transition-operations":
        return "Transition packet blocked because one or more transition operations are invalid."
    return "Transition packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-research-state-transition-apply-review":
        return [
            "Review local transition operations before any persistence step.",
            "Build a separate research-state transition apply review gate.",
            "Only after a later explicit apply approval may persistence be considered.",
        ]
    return [
        "Resolve blocking findings before building any apply review gate.",
        "Keep this transition packet local-only and non-mutating.",
    ]


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _finding(category: str, severity: str, message: str, subject: str, recommendation: str) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "subject": subject,
        "recommendation": recommendation,
    }


def _high(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    return [item for item in findings if item.get("severity") == "high"]


def _sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
