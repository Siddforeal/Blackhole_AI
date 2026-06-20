"""Final local apply preview.

This module converts approved human final apply decisions into local final
apply preview records. It does not write persistent research state, apply
confidence changes, mutate hypotheses, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_PACKET_KIND = "brain_chat_research_state_human_final_apply_decision_packet"
EXPECTED_PACKET_STATUS = "ready-for-final-local-apply-preview"
EXPECTED_PREVIEW_KIND = "brain_chat_research_state_final_local_apply_preview"

APPROVAL_DECISION = "approve-final-persistence-apply"

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


def build_research_state_final_local_apply_preview(
    human_final_apply_decision_packet: dict[str, Any],
    source: str = "brain-chat-research-state-final-local-apply-preview",
) -> dict[str, Any]:
    packet = copy.deepcopy(human_final_apply_decision_packet)
    approved = _object_list(packet.get("approved_final_apply_items"))

    source_findings = _source_findings(packet, approved)
    safety_findings = _unsafe_flag_findings(packet, "human_final_apply_decision_packet")
    preview_findings = _preview_item_findings(approved)

    status = _status(source_findings, safety_findings, preview_findings, approved)
    ready = status == "ready-for-final-apply-execution-review-gate"

    preview_items = [
        _preview_item(index, item, ready)
        for index, item in enumerate(approved, start=1)
    ]

    result = {
        "kind": EXPECTED_PREVIEW_KIND,
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "preview_status": status,
        "summary": _summary(status, len(preview_items)),
        "source_human_final_apply_decision_packet_kind": _text(packet.get("kind")),
        "source_human_final_apply_decision_packet_status": _text(packet.get("decision_status")),
        "source_human_final_apply_decision_packet_digest": _text(packet.get("human_final_apply_decision_packet_digest")),
        "source_final_persistence_apply_review_gate_digest": _text(packet.get("source_final_persistence_apply_review_gate_digest")),
        "source_local_write_execution_packet_digest": _text(packet.get("source_local_write_execution_packet_digest")),
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
        "approved_final_apply_decision_count": len(approved),
        "final_local_apply_preview_item_count": len(preview_items),
        "final_local_apply_preview_ready": ready,
        "final_apply_execution_review_gate_required": ready,
        "final_apply_execution_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_local_apply_preview_items": preview_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "preview_item_findings": preview_findings,
        "counts": {
            "approved_final_apply_decisions": len(approved),
            "final_local_apply_preview_items": len(preview_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "preview_item_findings": len(preview_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(preview_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this final local apply preview.",
            "Do not apply confidence updates from this final local apply preview.",
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

    result["final_local_apply_preview_digest"] = _sha256(
        {
            "kind": result["kind"],
            "target_name": result["target_name"],
            "preview_status": result["preview_status"],
            "source_human_final_apply_decision_packet_digest": result["source_human_final_apply_decision_packet_digest"],
            "final_local_apply_preview_items": result["final_local_apply_preview_items"],
        }
    )
    return result


def build_final_local_apply_preview_from_file(
    human_final_apply_decision_packet_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    preview = build_research_state_final_local_apply_preview(
        load_json_object(human_final_apply_decision_packet_file),
    )
    if json_output is not None:
        write_json(json_output, preview)
    return preview


def _source_findings(packet: dict[str, Any], approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_PACKET_KIND:
        findings.append(_finding("source-schema", "high", "Invalid human final apply decision packet kind.", "packet.kind", "Use a human final apply decision packet."))

    if packet.get("decision_status") != EXPECTED_PACKET_STATUS:
        findings.append(_finding("source-status", "high", "Human final apply decision packet is not ready for final local apply preview.", "packet.decision_status", "Resolve human final apply decision packet blockers first."))

    if packet.get("human_final_apply_decision_complete") is not True:
        findings.append(_finding("source-readiness", "high", "Human final apply decisions are not complete.", "packet.human_final_apply_decision_complete", "Complete human final apply decisions first."))

    if packet.get("final_local_apply_preview_required") is not True:
        findings.append(_finding("source-readiness", "high", "Decision packet does not require a final local apply preview.", "packet.final_local_apply_preview_required", "Use a decision packet that requires final local apply preview generation."))

    if packet.get("final_local_apply_preview_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks final local apply preview ready.", "packet.final_local_apply_preview_ready", "Use only pre-preview decision packets."))

    if packet.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks persistent write ready.", "packet.persistent_research_state_write_ready", "Use only pre-write decision packets."))

    if packet.get("persistent_research_state_write_allowed") is True:
        findings.append(_finding("source-safety", "high", "Decision packet allows persistent write.", "packet.persistent_research_state_write_allowed", "Use only non-writing decision packets."))

    if packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks research-state transition ready.", "packet.research_state_transition_ready", "Use only pre-transition decision packets."))

    if not approved:
        findings.append(_finding("source-content", "high", "No approved final apply items are present.", "packet.approved_final_apply_items", "Approve at least one final apply decision before final local apply preview generation."))

    expected_count = _int(packet.get("approved_final_apply_decision_count"))
    if expected_count and expected_count != len(approved):
        findings.append(_finding("source-count", "medium", "Approved final apply decision count does not match list length.", "packet.approved_final_apply_decision_count", "Regenerate the human final apply decision packet."))

    if not _text(packet.get("human_final_apply_decision_packet_digest")):
        findings.append(_finding("source-digest", "medium", "Human final apply decision packet digest is missing.", "packet.human_final_apply_decision_packet_digest", "Regenerate the human final apply decision packet."))

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


def _preview_item_findings(approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_decisions: set[str] = set()
    seen_fields: set[str] = set()

    for item in approved:
        decision_id = _text(item.get("human_final_apply_decision_id"))
        field_path = _text(item.get("field_path"))
        decision = _text(item.get("decision"))

        if not decision_id:
            findings.append(_finding("preview-schema", "high", "Approved final apply item is missing human_final_apply_decision_id.", "approved.human_final_apply_decision_id", "Regenerate the human final apply decision packet."))
        elif decision_id in seen_decisions:
            findings.append(_finding("preview-coverage", "high", f"Duplicate approved final apply decision: {decision_id}.", decision_id, "Resolve duplicate approved decisions."))
        seen_decisions.add(decision_id)

        for required in (
            "final_persistence_apply_review_item_id",
            "local_write_execution_packet_item_id",
            "write_execution_decision_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "source_final_persistence_apply_review_item_digest",
            "human_final_apply_decision_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("preview-schema", "high", f"Approved final apply item {decision_id or '<missing>'} is missing {required}.", decision_id, "Regenerate the human final apply decision packet."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("preview-coverage", "high", f"Multiple approved final apply items target field {field_path}.", field_path, "Resolve duplicate field updates before final local apply preview generation."))
            seen_fields.add(field_path)

        if decision != APPROVAL_DECISION:
            findings.append(_finding("preview-decision", "high", f"Approved final apply item has non-approval decision: {decision}.", decision_id, "Use only approved final apply decisions."))

        if item.get("decision_valid") is not True:
            findings.append(_finding("preview-decision", "high", f"Approved final apply item {decision_id or '<missing>'} is not marked decision_valid.", decision_id, "Use only valid human decisions."))

        if item.get("human_final_apply_decision_complete") is not True:
            findings.append(_finding("preview-decision", "high", f"Approved final apply item {decision_id or '<missing>'} is incomplete.", decision_id, "Use only complete human decisions."))

        if item.get("final_local_apply_preview_required") is not True:
            findings.append(_finding("preview-readiness", "high", f"Approved final apply item {decision_id or '<missing>'} does not require final local apply preview.", decision_id, "Use approved items that require final local apply preview generation."))

        if item.get("final_local_apply_preview_ready") is True:
            findings.append(_finding("preview-safety", "high", f"Approved final apply item {decision_id or '<missing>'} already marks final local apply preview ready.", decision_id, "Use pre-preview approved items only."))

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
                findings.append(_finding("preview-unsafe-flag", "high", f"Approved final apply item unsafe flag is true: {flag}.", f"{decision_id}.{flag}", "Keep final local apply preview records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("preview-planning-only", "high", f"Approved final apply item {decision_id or '<missing>'} is not planning-only.", decision_id, "Use only planning-only decision records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("preview-execution-state", "high", f"Approved final apply item {decision_id or '<missing>'} execution_state is not not_executed.", decision_id, "Use only non-executed decision records."))

    return findings


def _preview_item(index: int, approved: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "final_local_apply_preview_item_id": f"FLAP-{index:03d}",
        "human_final_apply_decision_id": _text(approved.get("human_final_apply_decision_id")),
        "final_persistence_apply_review_item_id": _text(approved.get("final_persistence_apply_review_item_id")),
        "local_write_execution_packet_item_id": _text(approved.get("local_write_execution_packet_item_id")),
        "write_execution_decision_id": _text(approved.get("write_execution_decision_id")),
        "write_execution_review_item_id": _text(approved.get("write_execution_review_item_id")),
        "local_write_packet_preview_item_id": _text(approved.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(approved.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(approved.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(approved.get("source_preview_item_id")),
        "apply_decision_id": _text(approved.get("apply_decision_id")),
        "apply_review_item_id": _text(approved.get("apply_review_item_id")),
        "operation_id": _text(approved.get("operation_id")),
        "transition_id": _text(approved.get("transition_id")),
        "decision_id": _text(approved.get("decision_id")),
        "hypothesis_id": _text(approved.get("hypothesis_id")),
        "field_path": _text(approved.get("field_path")),
        "operation_type": _text(approved.get("operation_type")),
        "current_value": _text(approved.get("current_value")),
        "proposed_value": _text(approved.get("proposed_value")),
        "local_write_operation": _text(approved.get("local_write_operation"), "preview-persistent-research-state-field-write"),
        "final_local_apply_action": "preview-final-persistent-research-state-field-write",
        "final_local_apply_summary": f"{_text(approved.get('field_path'))}: {_text(approved.get('current_value'))} -> {_text(approved.get('proposed_value'))}",
        "decision": _text(approved.get("decision")),
        "decision_reason": _text(approved.get("decision_reason")),
        "decision_actor": _text(approved.get("decision_actor"), "human-reviewer"),
        "final_apply_execution_review_required": ready,
        "final_apply_execution_review_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_human_final_apply_decision_digest": _text(approved.get("human_final_apply_decision_digest")),
        "source_final_persistence_apply_review_item_digest": _text(approved.get("source_final_persistence_apply_review_item_digest")),
        "source_local_write_execution_packet_item_digest": _text(approved.get("source_local_write_execution_packet_item_digest")),
        "source_write_execution_decision_digest": _text(approved.get("source_write_execution_decision_digest")),
        "source_write_execution_review_item_digest": _text(approved.get("source_write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(approved.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(approved.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(approved.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(approved.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(approved.get("source_apply_decision_digest")),
        "source_operation_digest": _text(approved.get("source_operation_digest")),
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["final_local_apply_preview_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    preview_findings: list[dict[str, str]],
    approved: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-human-final-apply-decision-packet"
    if _high(safety_findings):
        return "blocked-unsafe-human-final-apply-decision-packet"
    if not approved:
        return "blocked-no-approved-final-apply-items"
    if _high(preview_findings):
        return "blocked-invalid-final-local-apply-preview-items"
    return "ready-for-final-apply-execution-review-gate"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-final-apply-execution-review-gate":
        return f"{count} approved final apply item(s) are ready for a later final apply execution review gate."
    if status == "blocked-invalid-human-final-apply-decision-packet":
        return "Final local apply preview blocked because the source human final apply decision packet is invalid."
    if status == "blocked-unsafe-human-final-apply-decision-packet":
        return "Final local apply preview blocked because the source decision packet enables mutation, writing, or execution."
    if status == "blocked-no-approved-final-apply-items":
        return "Final local apply preview blocked because there are no approved final apply items."
    if status == "blocked-invalid-final-local-apply-preview-items":
        return "Final local apply preview blocked because one or more preview items are invalid."
    return "Final local apply preview is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-final-apply-execution-review-gate":
        return [
            "Review the final local apply preview before any final apply execution path is considered.",
            "Build a later final apply execution review gate.",
            "Keep stored-state writes disabled until a separate final apply path is reviewed.",
        ]
    return [
        "Resolve blocking findings before building any final apply execution review gate.",
        "Keep this final local apply preview local-only and non-mutating.",
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
