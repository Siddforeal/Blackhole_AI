"""Local research-state transition apply preview.

This module converts approved human apply decisions into a local preview of
proposed stored-state changes. It does not write persistent research state,
apply hypothesis confidence changes, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_DECISION_KIND = "brain_chat_research_state_transition_apply_decision_packet"
EXPECTED_DECISION_STATUS = "ready-for-research-state-transition-apply-preview"
EXPECTED_PREVIEW_KIND = "brain_chat_research_state_transition_apply_preview"

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


def build_research_state_transition_apply_preview(
    apply_decision_packet: dict[str, Any],
    source: str = "brain-chat-research-state-transition-apply-preview",
) -> dict[str, Any]:
    packet = copy.deepcopy(apply_decision_packet)
    approved = _object_list(packet.get("approved_apply_items"))

    source_findings = _source_findings(packet, approved)
    safety_findings = _unsafe_flag_findings(packet, "apply_decision_packet")
    preview_findings = _preview_findings(approved)

    status = _status(source_findings, safety_findings, preview_findings, approved)
    ready = status == "ready-for-persistence-write-review-gate"

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
        "source_apply_decision_kind": _text(packet.get("kind")),
        "source_apply_decision_status": _text(packet.get("decision_status")),
        "source_apply_decision_packet_digest": _text(packet.get("apply_decision_packet_digest")),
        "source_apply_review_gate_digest": _text(packet.get("source_apply_review_gate_digest")),
        "source_transition_packet_digest": _text(packet.get("source_transition_packet_digest")),
        "source_decision_digest": _text(packet.get("source_decision_digest")),
        "source_gate_digest": _text(packet.get("source_gate_digest")),
        "source_template_digest": _text(packet.get("source_template_digest")),
        "source_update_digest": _text(packet.get("source_update_digest")),
        "source_hypothesis_digest": _text(packet.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(packet.get("source_feedback_digest")),
        "approved_apply_decision_count": len(approved),
        "preview_item_count": len(preview_items),
        "apply_preview_ready": ready,
        "persistence_write_review_gate_required": ready,
        "persistence_write_review_gate_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "preview_items": preview_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "preview_findings": preview_findings,
        "counts": {
            "approved_apply_decisions": len(approved),
            "preview_items": len(preview_items),
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
            "Do not write persistent research state from this preview.",
            "Do not apply confidence updates from this preview.",
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

    preview["apply_preview_digest"] = _sha256(
        {
            "kind": preview["kind"],
            "target_name": preview["target_name"],
            "preview_status": preview["preview_status"],
            "source_apply_decision_packet_digest": preview["source_apply_decision_packet_digest"],
            "preview_items": preview["preview_items"],
        }
    )
    return preview


def build_apply_preview_from_file(
    apply_decision_packet_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    preview = build_research_state_transition_apply_preview(
        load_json_object(apply_decision_packet_file),
    )
    if json_output is not None:
        write_json(json_output, preview)
    return preview


def _source_findings(packet: dict[str, Any], approved: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_DECISION_KIND:
        findings.append(_finding("source-schema", "high", "Invalid apply decision packet kind.", "packet.kind", "Use a research-state transition apply decision packet."))

    if packet.get("decision_status") != EXPECTED_DECISION_STATUS:
        findings.append(_finding("source-status", "high", "Apply decision packet is not ready for apply preview.", "packet.decision_status", "Resolve apply decision packet blockers first."))

    if packet.get("human_apply_decision_complete") is not True:
        findings.append(_finding("source-readiness", "high", "Human apply decisions are not complete.", "packet.human_apply_decision_complete", "Complete human apply decisions first."))

    if packet.get("research_state_transition_apply_preview_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Apply decision packet is not marked ready for apply preview.", "packet.research_state_transition_apply_preview_ready", "Use a ready apply decision packet."))

    if packet.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply decision packet already marks persistent write ready.", "packet.persistent_research_state_write_ready", "Use only pre-write-preview packets."))

    if packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply decision packet already marks transition ready.", "packet.research_state_transition_ready", "Use only pre-write-preview packets."))

    if not approved:
        findings.append(_finding("source-content", "high", "No approved apply items are present.", "packet.approved_apply_items", "Approve at least one apply decision before preview."))

    expected_count = _int(packet.get("approved_apply_decision_count"))
    if expected_count and expected_count != len(approved):
        findings.append(_finding("source-count", "medium", "Approved apply decision count does not match list length.", "packet.approved_apply_decision_count", "Regenerate the apply decision packet."))

    if not _text(packet.get("apply_decision_packet_digest")):
        findings.append(_finding("source-digest", "medium", "Apply decision packet digest is missing.", "packet.apply_decision_packet_digest", "Regenerate the apply decision packet."))

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
        apply_decision_id = _text(item.get("apply_decision_id"))
        field_path = _text(item.get("field_path"))
        decision = _text(item.get("decision"))

        if not apply_decision_id:
            findings.append(_finding("preview-schema", "high", "Approved apply item is missing apply_decision_id.", "approved.apply_decision_id", "Regenerate the apply decision packet."))
        elif apply_decision_id in seen_decisions:
            findings.append(_finding("preview-coverage", "high", f"Duplicate approved apply decision: {apply_decision_id}.", apply_decision_id, "Resolve duplicate approved apply decisions."))
        seen_decisions.add(apply_decision_id)

        if not _text(item.get("review_item_id")):
            findings.append(_finding("preview-schema", "high", f"Approved apply item {apply_decision_id or '<missing>'} is missing review_item_id.", apply_decision_id, "Regenerate the apply decision packet."))

        if not _text(item.get("operation_id")):
            findings.append(_finding("preview-schema", "high", f"Approved apply item {apply_decision_id or '<missing>'} is missing operation_id.", apply_decision_id, "Regenerate the apply decision packet."))

        if not _text(item.get("hypothesis_id")):
            findings.append(_finding("preview-schema", "high", f"Approved apply item {apply_decision_id or '<missing>'} is missing hypothesis_id.", apply_decision_id, "Regenerate the apply decision packet."))

        if not field_path:
            findings.append(_finding("preview-schema", "high", f"Approved apply item {apply_decision_id or '<missing>'} is missing field_path.", apply_decision_id, "Regenerate the apply decision packet."))
        elif field_path in seen_fields:
            findings.append(_finding("preview-coverage", "high", f"Multiple approved apply items target field {field_path}.", field_path, "Resolve duplicate field previews."))
        seen_fields.add(field_path)

        if not _text(item.get("current_value")):
            findings.append(_finding("preview-value", "high", f"Approved apply item {apply_decision_id or '<missing>'} lacks current_value.", apply_decision_id, "Regenerate the apply decision packet."))

        if not _text(item.get("proposed_value")):
            findings.append(_finding("preview-value", "high", f"Approved apply item {apply_decision_id or '<missing>'} lacks proposed_value.", apply_decision_id, "Regenerate the apply decision packet."))

        if decision != "approve-apply-packet":
            findings.append(_finding("preview-decision", "high", f"Approved apply item has non-approval decision: {decision}.", apply_decision_id, "Use only approved apply decisions."))

        if item.get("apply_preview_required") is not True:
            findings.append(_finding("preview-readiness", "high", f"Approved apply item {apply_decision_id or '<missing>'} does not require preview.", apply_decision_id, "Use approved apply items that require preview."))

        if not _text(item.get("apply_decision_digest")):
            findings.append(_finding("preview-digest", "medium", f"Approved apply item {apply_decision_id or '<missing>'} lacks apply_decision_digest.", apply_decision_id, "Regenerate the apply decision packet."))

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
                findings.append(_finding("preview-unsafe-flag", "high", f"Approved apply item unsafe flag is true: {flag}.", f"{apply_decision_id}.{flag}", "Keep preview records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("preview-planning-only", "high", f"Approved apply item {apply_decision_id or '<missing>'} is not planning-only.", apply_decision_id, "Use only planning-only apply decision records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("preview-execution-state", "high", f"Approved apply item {apply_decision_id or '<missing>'} execution_state is not not_executed.", apply_decision_id, "Use only non-executed apply decision records."))

    return findings


def _preview_item(index: int, approved: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "preview_item_id": f"RSTPV-{index:03d}",
        "apply_decision_id": _text(approved.get("apply_decision_id")),
        "review_item_id": _text(approved.get("review_item_id")),
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
        "source_apply_decision_digest": _text(approved.get("apply_decision_digest")),
        "source_review_item_digest": _text(approved.get("source_review_item_digest")),
        "source_operation_digest": _text(approved.get("source_operation_digest")),
        "change_summary": f"{_text(approved.get('field_path'))}: {_text(approved.get('current_value'))} -> {_text(approved.get('proposed_value'))}",
        "persistence_write_review_required": ready,
        "persistence_write_review_ready": False,
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
    item["preview_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    preview_findings: list[dict[str, str]],
    approved: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-apply-decision-packet"
    if _high(safety_findings):
        return "blocked-unsafe-apply-decision-packet"
    if not approved:
        return "blocked-no-approved-apply-items"
    if _high(preview_findings):
        return "blocked-invalid-apply-preview-items"
    return "ready-for-persistence-write-review-gate"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-persistence-write-review-gate":
        return f"{count} approved apply item(s) are ready for a later persistence write review gate."
    if status == "blocked-invalid-apply-decision-packet":
        return "Apply preview blocked because the source apply decision packet is invalid."
    if status == "blocked-unsafe-apply-decision-packet":
        return "Apply preview blocked because the source apply decision packet enables mutation, writing, or execution."
    if status == "blocked-no-approved-apply-items":
        return "Apply preview blocked because there are no approved apply items."
    if status == "blocked-invalid-apply-preview-items":
        return "Apply preview blocked because one or more preview items are invalid."
    return "Apply preview is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-persistence-write-review-gate":
        return [
            "Review the local apply preview before any stored-state update is considered.",
            "Build a separate persistence write review gate.",
            "Keep stored-state writes disabled until a later explicit write approval stage.",
        ]
    return [
        "Resolve blocking findings before building any persistence write review gate.",
        "Keep this apply preview local-only and non-mutating.",
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
