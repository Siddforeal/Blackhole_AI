"""Local research-state transition apply review gate.

This module converts a local research-state transition packet into a review
gate for a later human apply decision. It does not write persistent research
state, mutate hypothesis confidence, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_TRANSITION_KIND = "brain_chat_research_state_transition_packet"
EXPECTED_TRANSITION_STATUS = "ready-for-research-state-transition-apply-review"
EXPECTED_GATE_KIND = "brain_chat_research_state_transition_apply_review_gate"

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
    "persistent_research_state_write_allowed",
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


def build_research_state_transition_apply_review_gate(
    transition_packet: dict[str, Any],
    source: str = "brain-chat-research-state-transition-apply-review-gate",
) -> dict[str, Any]:
    packet = copy.deepcopy(transition_packet)
    operations = _object_list(packet.get("transition_operations"))

    source_findings = _source_findings(packet, operations)
    safety_findings = _unsafe_flag_findings(packet, "transition_packet")
    operation_findings = _operation_findings(operations)

    status = _status(source_findings, safety_findings, operation_findings, operations)
    ready = status == "ready-for-human-apply-review"

    review_items = [
        _review_item(index, operation, ready)
        for index, operation in enumerate(operations, start=1)
    ]

    gate = {
        "kind": EXPECTED_GATE_KIND,
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "gate_status": status,
        "summary": _summary(status, len(review_items)),
        "source_transition_kind": _text(packet.get("kind")),
        "source_transition_status": _text(packet.get("packet_status")),
        "source_transition_packet_digest": _text(packet.get("transition_packet_digest")),
        "source_decision_digest": _text(packet.get("source_decision_digest")),
        "source_gate_digest": _text(packet.get("source_gate_digest")),
        "source_template_digest": _text(packet.get("source_template_digest")),
        "source_update_digest": _text(packet.get("source_update_digest")),
        "source_hypothesis_digest": _text(packet.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(packet.get("source_feedback_digest")),
        "transition_operation_count": len(operations),
        "apply_review_item_count": len(review_items),
        "apply_review_ready": ready,
        "human_apply_decision_required": ready,
        "human_apply_decision_complete": False,
        "research_state_transition_apply_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "apply_review_items": review_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "operation_findings": operation_findings,
        "counts": {
            "transition_operations": len(operations),
            "apply_review_items": len(review_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "operation_findings": len(operation_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(operation_findings))
            ),
        },
        "allowed_apply_decisions": [
            "approve-apply-packet",
            "reject-apply",
            "request-changes",
            "defer-apply",
        ],
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this gate.",
            "Do not apply confidence updates from this gate.",
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

    gate["apply_review_gate_digest"] = _sha256(
        {
            "kind": gate["kind"],
            "target_name": gate["target_name"],
            "gate_status": gate["gate_status"],
            "source_transition_packet_digest": gate["source_transition_packet_digest"],
            "apply_review_items": gate["apply_review_items"],
        }
    )
    return gate


def build_apply_review_gate_from_file(
    transition_packet_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    gate = build_research_state_transition_apply_review_gate(
        load_json_object(transition_packet_file),
    )
    if json_output is not None:
        write_json(json_output, gate)
    return gate


def _source_findings(packet: dict[str, Any], operations: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_TRANSITION_KIND:
        findings.append(_finding("source-schema", "high", "Invalid transition packet kind.", "packet.kind", "Use a local research-state transition packet."))

    if packet.get("packet_status") != EXPECTED_TRANSITION_STATUS:
        findings.append(_finding("source-status", "high", "Transition packet is not ready for apply review.", "packet.packet_status", "Resolve transition packet blockers first."))

    if packet.get("local_transition_packet_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Transition packet is not marked locally ready.", "packet.local_transition_packet_ready", "Use a ready local transition packet."))

    if packet.get("research_state_transition_apply_review_required") is not True:
        findings.append(_finding("source-readiness", "high", "Transition packet does not require apply review.", "packet.research_state_transition_apply_review_required", "Use a transition packet that requires apply review."))

    if packet.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Transition packet already marks persistent write ready.", "packet.persistent_research_state_write_ready", "Use only pre-apply-review packets."))

    if packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Transition packet already marks research-state transition ready.", "packet.research_state_transition_ready", "Use only pre-apply-review packets."))

    if not operations:
        findings.append(_finding("source-content", "high", "No transition operations are present.", "packet.transition_operations", "Create transition operations before apply review."))

    expected_count = _int(packet.get("transition_operation_count"))
    if expected_count and expected_count != len(operations):
        findings.append(_finding("source-count", "medium", "Transition operation count does not match list length.", "packet.transition_operation_count", "Regenerate the transition packet."))

    if not _text(packet.get("transition_packet_digest")):
        findings.append(_finding("source-digest", "medium", "Transition packet digest is missing.", "packet.transition_packet_digest", "Regenerate the transition packet."))

    return findings


def _unsafe_flag_findings(data: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for flag in FALSE_FLAGS:
        if bool(data.get(flag)):
            findings.append(_finding("unsafe-flag", "high", f"Unsafe flag is true: {flag}.", f"{prefix}.{flag}", "Regenerate with all mutation, write, and execution flags disabled."))

    if data.get("planning_only") is not True:
        findings.append(_finding("planning-only", "high", "Artifact is not marked planning-only.", f"{prefix}.planning_only", "Use only planning-only artifacts."))

    if _text(data.get("execution_state"), "not_executed") != "not_executed":
        findings.append(_finding("execution-state", "high", "Artifact execution_state is not not_executed.", f"{prefix}.execution_state", "Use only non-executed planning artifacts."))

    return findings


def _operation_findings(operations: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_operations: set[str] = set()
    seen_fields: set[str] = set()

    for operation in operations:
        operation_id = _text(operation.get("operation_id"))
        hypothesis_id = _text(operation.get("hypothesis_id"))
        field_path = _text(operation.get("field_path"))
        operation_type = _text(operation.get("operation_type"))

        if not operation_id:
            findings.append(_finding("operation-schema", "high", "Transition operation is missing operation_id.", "operation.operation_id", "Regenerate the transition packet."))
        elif operation_id in seen_operations:
            findings.append(_finding("operation-coverage", "high", f"Duplicate transition operation: {operation_id}.", operation_id, "Resolve duplicate transition operations."))
        seen_operations.add(operation_id)

        if not hypothesis_id:
            findings.append(_finding("operation-schema", "high", f"Transition operation {operation_id or '<missing>'} is missing hypothesis_id.", operation_id, "Regenerate the transition packet."))

        if not field_path:
            findings.append(_finding("operation-schema", "high", f"Transition operation {operation_id or '<missing>'} is missing field_path.", operation_id, "Regenerate the transition packet."))
        elif field_path in seen_fields:
            findings.append(_finding("operation-coverage", "high", f"Multiple operations target field {field_path}.", field_path, "Resolve duplicate field operations."))
        seen_fields.add(field_path)

        if operation_type != "local-proposed-hypothesis-confidence-update":
            findings.append(_finding("operation-type", "high", f"Unsupported operation_type: {operation_type}.", operation_id, "Only local proposed hypothesis confidence updates are supported."))

        if operation.get("apply_review_required") is not True:
            findings.append(_finding("operation-readiness", "high", f"Operation {operation_id or '<missing>'} does not require apply review.", operation_id, "Use operations that require apply review."))

        if not _text(operation.get("current_value")):
            findings.append(_finding("operation-value", "high", f"Operation {operation_id or '<missing>'} lacks current_value.", operation_id, "Regenerate the transition packet."))

        if not _text(operation.get("proposed_value")):
            findings.append(_finding("operation-value", "high", f"Operation {operation_id or '<missing>'} lacks proposed_value.", operation_id, "Regenerate the transition packet."))

        if not _text(operation.get("decision_reason")):
            findings.append(_finding("operation-reason", "high", f"Operation {operation_id or '<missing>'} lacks decision_reason.", operation_id, "Provide the human decision reason."))

        if not _text(operation.get("operation_digest")):
            findings.append(_finding("operation-digest", "medium", f"Operation {operation_id or '<missing>'} lacks operation_digest.", operation_id, "Regenerate the transition packet."))

        for flag in (
            "persistent_write_allowed",
            "research_state_transition_allowed",
            "confidence_update_allowed",
            "hypothesis_mutation_allowed",
            "research_state_mutation_allowed",
            "execution_allowed",
            "runtime_execution_allowed",
        ):
            if bool(operation.get(flag)):
                findings.append(_finding("operation-unsafe-flag", "high", f"Operation unsafe flag is true: {flag}.", f"{operation_id}.{flag}", "Keep operations fail-closed until a later explicit apply gate."))

        if operation.get("planning_only") is not True:
            findings.append(_finding("operation-planning-only", "high", f"Operation {operation_id or '<missing>'} is not planning-only.", operation_id, "Use only planning-only transition operations."))

        if _text(operation.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("operation-execution-state", "high", f"Operation {operation_id or '<missing>'} execution_state is not not_executed.", operation_id, "Use only non-executed transition operations."))

    return findings


def _review_item(index: int, operation: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "review_item_id": f"RSTAR-{index:03d}",
        "operation_id": _text(operation.get("operation_id")),
        "transition_id": _text(operation.get("transition_id")),
        "decision_id": _text(operation.get("decision_id")),
        "hypothesis_id": _text(operation.get("hypothesis_id")),
        "field_path": _text(operation.get("field_path")),
        "operation_type": _text(operation.get("operation_type")),
        "current_value": _text(operation.get("current_value")),
        "proposed_value": _text(operation.get("proposed_value")),
        "decision_reason": _text(operation.get("decision_reason")),
        "source_operation_digest": _text(operation.get("operation_digest")),
        "human_apply_decision_required": ready,
        "allowed_decisions": [
            "approve-apply-packet",
            "reject-apply",
            "request-changes",
            "defer-apply",
        ],
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["review_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    operation_findings: list[dict[str, str]],
    operations: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-transition-packet"
    if _high(safety_findings):
        return "blocked-unsafe-transition-packet"
    if not operations:
        return "blocked-no-transition-operations"
    if _high(operation_findings):
        return "blocked-invalid-transition-operations"
    return "ready-for-human-apply-review"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-human-apply-review":
        return f"{count} local transition operation(s) are ready for human apply review."
    if status == "blocked-invalid-transition-packet":
        return "Apply review gate blocked because the source transition packet is invalid."
    if status == "blocked-unsafe-transition-packet":
        return "Apply review gate blocked because the source transition packet enables mutation, writing, or execution."
    if status == "blocked-no-transition-operations":
        return "Apply review gate blocked because there are no transition operations."
    if status == "blocked-invalid-transition-operations":
        return "Apply review gate blocked because one or more transition operations are invalid."
    return "Apply review gate is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-human-apply-review":
        return [
            "Review each local transition operation before any persistence step.",
            "Record an explicit human apply decision in a later apply decision packet.",
            "Only after a later explicit apply approval may persistence be considered.",
        ]
    return [
        "Resolve blocking findings before collecting any apply decision.",
        "Keep this gate local-only and non-mutating.",
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
