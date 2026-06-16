"""Local write packet preview for approved persistence write decisions.

This module converts approved human persistence write decisions into a local
write packet preview. It does not write persistent research state, apply
confidence changes, mutate hypotheses, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_DECISION_KIND = "brain_chat_research_state_persistence_write_decision_packet"
EXPECTED_DECISION_STATUS = "ready-for-local-write-packet-preview"
EXPECTED_PREVIEW_KIND = "brain_chat_research_state_local_write_packet_preview"

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


def build_research_state_local_write_packet_preview(
    persistence_write_decision_packet: dict[str, Any],
    source: str = "brain-chat-research-state-local-write-packet-preview",
) -> dict[str, Any]:
    packet = copy.deepcopy(persistence_write_decision_packet)
    approved = _object_list(packet.get("approved_persistence_write_items"))

    source_findings = _source_findings(packet, approved)
    safety_findings = _unsafe_flag_findings(packet, "persistence_write_decision_packet")
    preview_findings = _preview_findings(approved)

    status = _status(source_findings, safety_findings, preview_findings, approved)
    ready = status == "ready-for-write-execution-review-gate"

    preview_items = [
        _preview_item(index, item, ready)
        for index, item in enumerate(approved, start=1)
    ]

    preview = {
        "kind": EXPECTED_PREVIEW_KIND,
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "preview_status": status,
        "summary": _summary(status, len(preview_items)),
        "source_persistence_write_decision_packet_kind": _text(packet.get("kind")),
        "source_persistence_write_decision_packet_status": _text(packet.get("decision_status")),
        "source_persistence_write_decision_packet_digest": _text(packet.get("persistence_write_decision_packet_digest")),
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
        "approved_persistence_write_decision_count": len(approved),
        "local_write_packet_preview_item_count": len(preview_items),
        "local_write_packet_preview_ready": ready,
        "write_execution_review_gate_required": ready,
        "write_execution_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "preview_items": preview_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "preview_findings": preview_findings,
        "counts": {
            "approved_persistence_write_decisions": len(approved),
            "local_write_packet_preview_items": len(preview_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "preview_findings": len(preview_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(preview_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this local write packet preview.",
            "Do not apply confidence updates from this local write packet preview.",
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

    preview["local_write_packet_preview_digest"] = _sha256(
        {
            "kind": preview["kind"],
            "target_name": preview["target_name"],
            "preview_status": preview["preview_status"],
            "source_persistence_write_decision_packet_digest": preview["source_persistence_write_decision_packet_digest"],
            "preview_items": preview["preview_items"],
        }
    )
    return preview


def build_local_write_packet_preview_from_file(
    persistence_write_decision_packet_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    preview = build_research_state_local_write_packet_preview(
        load_json_object(persistence_write_decision_packet_file),
    )
    if json_output is not None:
        write_json(json_output, preview)
    return preview


def _source_findings(packet: dict[str, Any], approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_DECISION_KIND:
        findings.append(_finding("source-schema", "high", "Invalid persistence write decision packet kind.", "packet.kind", "Use a persistence write decision packet."))

    if packet.get("decision_status") != EXPECTED_DECISION_STATUS:
        findings.append(_finding("source-status", "high", "Persistence write decision packet is not ready for local write packet preview.", "packet.decision_status", "Resolve decision packet blockers first."))

    if packet.get("human_persistence_write_decision_complete") is not True:
        findings.append(_finding("source-readiness", "high", "Human persistence write decisions are not complete.", "packet.human_persistence_write_decision_complete", "Complete human persistence write decisions first."))

    if packet.get("local_write_packet_preview_required") is not True:
        findings.append(_finding("source-readiness", "high", "Decision packet does not require local write packet preview.", "packet.local_write_packet_preview_required", "Use a decision packet that requires local write packet preview."))

    if packet.get("local_write_packet_preview_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Decision packet is not marked ready for local write packet preview.", "packet.local_write_packet_preview_ready", "Use a ready persistence write decision packet."))

    if packet.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks persistent write ready.", "packet.persistent_research_state_write_ready", "Use only pre-write-preview packets."))

    if packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Decision packet already marks research-state transition ready.", "packet.research_state_transition_ready", "Use only pre-write-preview packets."))

    if not approved:
        findings.append(_finding("source-content", "high", "No approved persistence write items are present.", "packet.approved_persistence_write_items", "Approve at least one persistence write decision before preview."))

    expected_count = _int(packet.get("approved_persistence_write_decision_count"))
    if expected_count and expected_count != len(approved):
        findings.append(_finding("source-count", "medium", "Approved persistence write decision count does not match list length.", "packet.approved_persistence_write_decision_count", "Regenerate the persistence write decision packet."))

    if not _text(packet.get("persistence_write_decision_packet_digest")):
        findings.append(_finding("source-digest", "medium", "Persistence write decision packet digest is missing.", "packet.persistence_write_decision_packet_digest", "Regenerate the persistence write decision packet."))

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


def _preview_findings(approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_decisions: set[str] = set()
    seen_fields: set[str] = set()

    for item in approved:
        decision_id = _text(item.get("persistence_write_decision_id"))
        field_path = _text(item.get("field_path"))
        decision = _text(item.get("decision"))

        if not decision_id:
            findings.append(_finding("preview-schema", "high", "Approved persistence write item is missing persistence_write_decision_id.", "approved.persistence_write_decision_id", "Regenerate the persistence write decision packet."))
        elif decision_id in seen_decisions:
            findings.append(_finding("preview-coverage", "high", f"Duplicate approved persistence write decision: {decision_id}.", decision_id, "Resolve duplicate approved decisions."))
        seen_decisions.add(decision_id)

        for required in (
            "persistence_write_review_item_id",
            "preview_item_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "persistence_write_decision_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("preview-schema", "high", f"Approved persistence write item {decision_id or '<missing>'} is missing {required}.", decision_id, "Regenerate the persistence write decision packet."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("preview-coverage", "high", f"Multiple approved persistence write items target field {field_path}.", field_path, "Resolve duplicate field previews."))
            seen_fields.add(field_path)

        if decision != "approve-persistence-write-packet":
            findings.append(_finding("preview-decision", "high", f"Approved persistence write item has non-approval decision: {decision}.", decision_id, "Use only approved persistence write decisions."))

        if item.get("decision_valid") is not True:
            findings.append(_finding("preview-decision", "high", f"Approved persistence write item {decision_id or '<missing>'} is not marked decision_valid.", decision_id, "Use only valid human decisions."))

        if item.get("human_persistence_write_decision_complete") is not True:
            findings.append(_finding("preview-decision", "high", f"Approved persistence write item {decision_id or '<missing>'} is incomplete.", decision_id, "Use only complete human decisions."))

        if item.get("local_write_packet_preview_required") is not True:
            findings.append(_finding("preview-readiness", "high", f"Approved persistence write item {decision_id or '<missing>'} does not require local write packet preview.", decision_id, "Use approved items that require local write packet preview."))

        if item.get("local_write_packet_preview_ready") is True:
            findings.append(_finding("preview-safety", "high", f"Approved persistence write item {decision_id or '<missing>'} already marks local write packet preview ready.", decision_id, "Use pre-preview approved items only."))

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
                findings.append(_finding("preview-unsafe-flag", "high", f"Approved persistence write item unsafe flag is true: {flag}.", f"{decision_id}.{flag}", "Keep preview records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("preview-planning-only", "high", f"Approved persistence write item {decision_id or '<missing>'} is not planning-only.", decision_id, "Use only planning-only decision records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("preview-execution-state", "high", f"Approved persistence write item {decision_id or '<missing>'} execution_state is not not_executed.", decision_id, "Use only non-executed decision records."))

    return findings


def _preview_item(index: int, approved: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "local_write_packet_preview_item_id": f"LWPP-{index:03d}",
        "persistence_write_decision_id": _text(approved.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(approved.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(approved.get("preview_item_id")),
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
        "decision": _text(approved.get("decision")),
        "decision_reason": _text(approved.get("decision_reason")),
        "decision_actor": _text(approved.get("decision_actor"), "human-reviewer"),
        "source_persistence_write_decision_digest": _text(approved.get("persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(approved.get("source_review_item_digest")),
        "source_apply_preview_item_digest": _text(approved.get("source_preview_item_digest")),
        "source_apply_decision_digest": _text(approved.get("source_apply_decision_digest")),
        "source_operation_digest": _text(approved.get("source_operation_digest")),
        "write_preview_action": "preview-stored-state-field-update",
        "write_preview_summary": f"{_text(approved.get('field_path'))}: {_text(approved.get('current_value'))} -> {_text(approved.get('proposed_value'))}",
        "write_execution_review_required": ready,
        "write_execution_review_ready": False,
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
    item["local_write_packet_preview_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    preview_findings: list[dict[str, str]],
    approved: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-persistence-write-decision-packet"
    if _high(safety_findings):
        return "blocked-unsafe-persistence-write-decision-packet"
    if not approved:
        return "blocked-no-approved-persistence-write-items"
    if _high(preview_findings):
        return "blocked-invalid-local-write-packet-preview-items"
    return "ready-for-write-execution-review-gate"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-write-execution-review-gate":
        return f"{count} approved persistence write item(s) are ready for a later write execution review gate."
    if status == "blocked-invalid-persistence-write-decision-packet":
        return "Local write packet preview blocked because the source decision packet is invalid."
    if status == "blocked-unsafe-persistence-write-decision-packet":
        return "Local write packet preview blocked because the source decision packet enables mutation, writing, or execution."
    if status == "blocked-no-approved-persistence-write-items":
        return "Local write packet preview blocked because there are no approved persistence write items."
    if status == "blocked-invalid-local-write-packet-preview-items":
        return "Local write packet preview blocked because one or more preview items are invalid."
    return "Local write packet preview is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-write-execution-review-gate":
        return [
            "Review the local write packet preview before any write execution path is considered.",
            "Build a later write execution review gate.",
            "Keep stored-state writes disabled until a separate write path is reviewed.",
        ]
    return [
        "Resolve blocking findings before building any write execution review gate.",
        "Keep this local write packet preview local-only and non-mutating.",
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
