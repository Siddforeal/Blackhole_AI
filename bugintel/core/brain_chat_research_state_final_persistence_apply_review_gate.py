"""Final persistence apply review gate.

This module converts a local write execution packet into human-reviewable
final persistence apply review items. It does not write persistent research
state, apply confidence changes, mutate hypotheses, execute tools, interact
with targets, collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_PACKET_KIND = "brain_chat_research_state_local_write_execution_packet"
EXPECTED_PACKET_STATUS = "ready-for-final-persistence-apply-review-gate"
EXPECTED_GATE_KIND = "brain_chat_research_state_final_persistence_apply_review_gate"

ALLOWED_HUMAN_DECISIONS: tuple[str, ...] = (
    "approve-final-persistence-apply",
    "reject-final-persistence-apply",
    "request-changes",
    "defer-final-persistence-apply",
)

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


def build_research_state_final_persistence_apply_review_gate(
    local_write_execution_packet: dict[str, Any],
    source: str = "brain-chat-research-state-final-persistence-apply-review-gate",
) -> dict[str, Any]:
    packet = copy.deepcopy(local_write_execution_packet)
    local_items = _object_list(packet.get("local_write_execution_items"))

    source_findings = _source_findings(packet, local_items)
    safety_findings = _unsafe_flag_findings(packet, "local_write_execution_packet")
    review_findings = _review_item_findings(local_items)

    status = _status(source_findings, safety_findings, review_findings, local_items)
    ready = status == "ready-for-human-final-persistence-apply-review"

    review_items = [
        _review_item(index, item, ready)
        for index, item in enumerate(local_items, start=1)
    ]

    result = {
        "kind": EXPECTED_GATE_KIND,
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "gate_status": status,
        "summary": _summary(status, len(review_items)),
        "source_local_write_execution_packet_kind": _text(packet.get("kind")),
        "source_local_write_execution_packet_status": _text(packet.get("packet_status")),
        "source_local_write_execution_packet_digest": _text(packet.get("local_write_execution_packet_digest")),
        "source_write_execution_decision_packet_digest": _text(packet.get("source_write_execution_decision_packet_digest")),
        "source_write_execution_review_gate_digest": _text(packet.get("source_write_execution_review_gate_digest")),
        "source_local_write_packet_preview_digest": _text(packet.get("source_local_write_packet_preview_digest")),
        "source_persistence_write_decision_packet_digest": _text(packet.get("source_persistence_write_decision_packet_digest")),
        "source_persistence_write_review_gate_digest": _text(packet.get("source_persistence_write_review_gate_digest")),
        "source_apply_preview_digest": _text(packet.get("source_apply_preview_digest")),
        "source_apply_decision_packet_digest": _text(packet.get("source_apply_decision_packet_digest")),
        "source_apply_review_gate_digest": _text(packet.get("source_apply_review_gate_digest")),
        "source_transition_packet_digest": _text(packet.get("source_transition_packet_digest")),
        "source_decision_digest": _text(packet.get("source_decision_digest")),
        "source_gate_digest": _text(packet.get("source_gate_digest")),
        "source_template_digest": _text(packet.get("source_template_digest")),
        "source_update_digest": _text(packet.get("source_update_digest")),
        "source_hypothesis_digest": _text(packet.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(packet.get("source_feedback_digest")),
        "local_write_execution_packet_item_count": len(local_items),
        "final_persistence_apply_review_item_count": len(review_items),
        "human_final_persistence_apply_decision_required": ready,
        "human_final_persistence_apply_decision_complete": False,
        "final_persistence_apply_decision_packet_required": ready,
        "final_persistence_apply_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_persistence_apply_review_items": review_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "review_item_findings": review_findings,
        "counts": {
            "local_write_execution_packet_items": len(local_items),
            "final_persistence_apply_review_items": len(review_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "review_item_findings": len(review_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(review_findings))
            ),
        },
        "allowed_human_decisions": list(ALLOWED_HUMAN_DECISIONS),
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this review gate.",
            "Do not apply confidence updates from this review gate.",
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
        "persistent_research_state_write_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    result["final_persistence_apply_review_gate_digest"] = _sha256(
        {
            "kind": result["kind"],
            "target_name": result["target_name"],
            "gate_status": result["gate_status"],
            "source_local_write_execution_packet_digest": result["source_local_write_execution_packet_digest"],
            "final_persistence_apply_review_items": result["final_persistence_apply_review_items"],
        }
    )
    return result


def build_final_persistence_apply_review_gate_from_file(
    local_write_execution_packet_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    gate = build_research_state_final_persistence_apply_review_gate(
        load_json_object(local_write_execution_packet_file),
    )
    if json_output is not None:
        write_json(json_output, gate)
    return gate


def _source_findings(packet: dict[str, Any], local_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_PACKET_KIND:
        findings.append(_finding("source-schema", "high", "Invalid local write execution packet kind.", "packet.kind", "Use a local write execution packet."))

    if packet.get("packet_status") != EXPECTED_PACKET_STATUS:
        findings.append(_finding("source-status", "high", "Local write execution packet is not ready for final persistence apply review gate.", "packet.packet_status", "Resolve local write execution packet blockers first."))

    if packet.get("local_write_execution_packet_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Local write execution packet is not marked ready.", "packet.local_write_execution_packet_ready", "Use a ready local write execution packet."))

    if packet.get("final_persistence_apply_review_gate_required") is not True:
        findings.append(_finding("source-readiness", "high", "Local write execution packet does not require a final persistence apply review gate.", "packet.final_persistence_apply_review_gate_required", "Use a local packet requiring final apply review."))

    if packet.get("final_persistence_apply_review_gate_ready") is True:
        findings.append(_finding("source-safety", "high", "Local write execution packet already marks final persistence apply review gate ready.", "packet.final_persistence_apply_review_gate_ready", "Use only pre-review-gate local packets."))

    if packet.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Local write execution packet already marks persistent write ready.", "packet.persistent_research_state_write_ready", "Use only pre-write local packets."))

    if packet.get("persistent_research_state_write_allowed") is True:
        findings.append(_finding("source-safety", "high", "Local write execution packet allows persistent write.", "packet.persistent_research_state_write_allowed", "Use only non-writing local packets."))

    if packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Local write execution packet already marks research-state transition ready.", "packet.research_state_transition_ready", "Use only pre-transition local packets."))

    if not local_items:
        findings.append(_finding("source-content", "high", "No local write execution items are present.", "packet.local_write_execution_items", "Build a local write execution packet with at least one local item."))

    expected_count = _int(packet.get("local_write_execution_packet_item_count"))
    if expected_count and expected_count != len(local_items):
        findings.append(_finding("source-count", "medium", "Local write execution packet item count does not match list length.", "packet.local_write_execution_packet_item_count", "Regenerate the local write execution packet."))

    if not _text(packet.get("local_write_execution_packet_digest")):
        findings.append(_finding("source-digest", "medium", "Local write execution packet digest is missing.", "packet.local_write_execution_packet_digest", "Regenerate the local write execution packet."))

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


def _review_item_findings(local_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_items: set[str] = set()
    seen_fields: set[str] = set()

    for item in local_items:
        item_id = _text(item.get("local_write_execution_packet_item_id"))
        field_path = _text(item.get("field_path"))

        if not item_id:
            findings.append(_finding("review-schema", "high", "Local write execution item is missing local_write_execution_packet_item_id.", "local_item.local_write_execution_packet_item_id", "Regenerate the local write execution packet."))
        elif item_id in seen_items:
            findings.append(_finding("review-coverage", "high", f"Duplicate local write execution item: {item_id}.", item_id, "Resolve duplicate local packet items."))
        seen_items.add(item_id)

        for required in (
            "write_execution_decision_id",
            "write_execution_review_item_id",
            "local_write_packet_preview_item_id",
            "persistence_write_decision_id",
            "persistence_write_review_item_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "source_write_execution_decision_digest",
            "local_write_execution_packet_item_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("review-schema", "high", f"Local write execution item {item_id or '<missing>'} is missing {required}.", item_id, "Regenerate the local write execution packet."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("review-coverage", "high", f"Multiple local write execution items target field {field_path}.", field_path, "Resolve duplicate field updates before final apply review."))
            seen_fields.add(field_path)

        if _text(item.get("local_write_operation")) != "preview-persistent-research-state-field-write":
            findings.append(_finding("review-operation", "high", f"Local write execution item {item_id or '<missing>'} has an unsupported local_write_operation.", item_id, "Use only preview-persistent-research-state-field-write items."))

        if item.get("final_persistence_apply_review_required") is not True:
            findings.append(_finding("review-readiness", "high", f"Local write execution item {item_id or '<missing>'} does not require final persistence apply review.", item_id, "Use items that require final apply review."))

        if item.get("final_persistence_apply_review_ready") is True:
            findings.append(_finding("review-safety", "high", f"Local write execution item {item_id or '<missing>'} already marks final apply review ready.", item_id, "Use pre-review local items only."))

        for flag in (
            "persistent_write_ready",
            "persistent_write_allowed",
            "research_state_transition_ready",
            "research_state_transition_allowed",
            "confidence_update_allowed",
            "hypothesis_mutation_allowed",
            "research_state_mutation_allowed",
            "execution_allowed",
            "runtime_execution_allowed",
        ):
            if bool(item.get(flag)):
                findings.append(_finding("review-unsafe-flag", "high", f"Local write execution item unsafe flag is true: {flag}.", f"{item_id}.{flag}", "Keep review gate records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("review-planning-only", "high", f"Local write execution item {item_id or '<missing>'} is not planning-only.", item_id, "Use only planning-only local packet records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("review-execution-state", "high", f"Local write execution item {item_id or '<missing>'} execution_state is not not_executed.", item_id, "Use only non-executed local packet records."))

    return findings


def _review_item(index: int, local_item: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "final_persistence_apply_review_item_id": f"FPARG-{index:03d}",
        "local_write_execution_packet_item_id": _text(local_item.get("local_write_execution_packet_item_id")),
        "write_execution_decision_id": _text(local_item.get("write_execution_decision_id")),
        "write_execution_review_item_id": _text(local_item.get("write_execution_review_item_id")),
        "local_write_packet_preview_item_id": _text(local_item.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(local_item.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(local_item.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(local_item.get("source_preview_item_id")),
        "apply_decision_id": _text(local_item.get("apply_decision_id")),
        "apply_review_item_id": _text(local_item.get("apply_review_item_id")),
        "operation_id": _text(local_item.get("operation_id")),
        "transition_id": _text(local_item.get("transition_id")),
        "decision_id": _text(local_item.get("decision_id")),
        "hypothesis_id": _text(local_item.get("hypothesis_id")),
        "field_path": _text(local_item.get("field_path")),
        "operation_type": _text(local_item.get("operation_type")),
        "current_value": _text(local_item.get("current_value")),
        "proposed_value": _text(local_item.get("proposed_value")),
        "local_write_operation": _text(local_item.get("local_write_operation")),
        "local_write_summary": _text(local_item.get("local_write_summary")),
        "decision": _text(local_item.get("decision")),
        "decision_reason": _text(local_item.get("decision_reason")),
        "decision_actor": _text(local_item.get("decision_actor"), "human-reviewer"),
        "review_question": "Should this proposed stored-state field write proceed to a separate human final apply decision packet?",
        "allowed_human_decisions": list(ALLOWED_HUMAN_DECISIONS),
        "human_final_persistence_apply_decision_required": ready,
        "human_final_persistence_apply_decision_complete": False,
        "final_persistence_apply_decision_packet_required": ready,
        "final_persistence_apply_decision_packet_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_local_write_execution_packet_item_digest": _text(local_item.get("local_write_execution_packet_item_digest")),
        "source_write_execution_decision_digest": _text(local_item.get("source_write_execution_decision_digest")),
        "source_write_execution_review_item_digest": _text(local_item.get("source_write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(local_item.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(local_item.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(local_item.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(local_item.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(local_item.get("source_apply_decision_digest")),
        "source_operation_digest": _text(local_item.get("source_operation_digest")),
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["final_persistence_apply_review_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    review_findings: list[dict[str, str]],
    local_items: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-local-write-execution-packet"
    if _high(safety_findings):
        return "blocked-unsafe-local-write-execution-packet"
    if not local_items:
        return "blocked-no-local-write-execution-items"
    if _high(review_findings):
        return "blocked-invalid-final-persistence-apply-review-items"
    return "ready-for-human-final-persistence-apply-review"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-human-final-persistence-apply-review":
        return f"{count} local write execution item(s) are ready for human final persistence apply review."
    if status == "blocked-invalid-local-write-execution-packet":
        return "Final persistence apply review gate blocked because the source local write execution packet is invalid."
    if status == "blocked-unsafe-local-write-execution-packet":
        return "Final persistence apply review gate blocked because the source local write execution packet enables mutation, writing, or execution."
    if status == "blocked-no-local-write-execution-items":
        return "Final persistence apply review gate blocked because there are no local write execution items."
    if status == "blocked-invalid-final-persistence-apply-review-items":
        return "Final persistence apply review gate blocked because one or more review items are invalid."
    return "Final persistence apply review gate is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-human-final-persistence-apply-review":
        return [
            "Perform human final persistence apply review.",
            "Record explicit approve, reject, request-changes, or defer decisions.",
            "Build a later human final apply decision packet before any stored-state write path is considered.",
        ]
    return [
        "Resolve blocking findings before human final persistence apply review.",
        "Keep this final persistence apply review gate local-only and non-mutating.",
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
