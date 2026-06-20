"""Final apply execution review gate.

This module converts final local apply preview records into a human-reviewable
final apply execution review gate. It does not write persistent research state,
apply confidence changes, mutate hypotheses, execute tools, interact with
targets, collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_PREVIEW_KIND = "brain_chat_research_state_final_local_apply_preview"
EXPECTED_PREVIEW_STATUS = "ready-for-final-apply-execution-review-gate"
EXPECTED_GATE_KIND = "brain_chat_research_state_final_apply_execution_review_gate"

READY_STATUS = "ready-for-human-final-apply-execution-review"

ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS: tuple[str, ...] = (
    "approve-final-apply-execution",
    "reject-final-apply-execution",
    "request-changes",
    "defer-final-apply-execution",
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


def build_research_state_final_apply_execution_review_gate(
    final_local_apply_preview: dict[str, Any],
    source: str = "brain-chat-research-state-final-apply-execution-review-gate",
) -> dict[str, Any]:
    preview = copy.deepcopy(final_local_apply_preview)
    preview_items = _object_list(preview.get("final_local_apply_preview_items"))

    source_findings = _source_findings(preview, preview_items)
    safety_findings = _unsafe_flag_findings(preview, "final_local_apply_preview")
    review_item_findings = _review_item_findings(preview_items)

    status = _status(source_findings, safety_findings, review_item_findings, preview_items)
    ready = status == READY_STATUS

    review_items = [
        _review_item(index, item, ready)
        for index, item in enumerate(preview_items, start=1)
    ]

    result = {
        "kind": EXPECTED_GATE_KIND,
        "source": source,
        "target_name": _text(preview.get("target_name"), "unknown-target"),
        "review_status": status,
        "summary": _summary(status, len(review_items)),
        "source_final_local_apply_preview_kind": _text(preview.get("kind")),
        "source_final_local_apply_preview_status": _text(preview.get("preview_status")),
        "source_final_local_apply_preview_digest": _text(preview.get("final_local_apply_preview_digest")),
        "source_human_final_apply_decision_packet_digest": _text(preview.get("source_human_final_apply_decision_packet_digest")),
        "source_final_persistence_apply_review_gate_digest": _text(preview.get("source_final_persistence_apply_review_gate_digest")),
        "source_local_write_execution_packet_digest": _text(preview.get("source_local_write_execution_packet_digest")),
        "source_write_execution_decision_packet_digest": _text(preview.get("source_write_execution_decision_packet_digest")),
        "source_write_execution_review_gate_digest": _text(preview.get("source_write_execution_review_gate_digest")),
        "source_local_write_packet_preview_digest": _text(preview.get("source_local_write_packet_preview_digest")),
        "source_persistence_write_decision_packet_digest": _text(preview.get("source_persistence_write_decision_packet_digest")),
        "source_persistence_write_review_gate_digest": _text(preview.get("source_persistence_write_review_gate_digest")),
        "source_apply_preview_digest": _text(preview.get("source_apply_preview_digest")),
        "source_apply_decision_packet_digest": _text(preview.get("source_apply_decision_packet_digest")),
        "source_apply_review_gate_digest": _text(preview.get("source_apply_review_gate_digest")),
        "source_transition_packet_digest": _text(preview.get("source_transition_packet_digest")),
        "source_decision_digest": _text(preview.get("source_decision_digest")),
        "source_gate_digest": _text(preview.get("source_gate_digest")),
        "source_template_digest": _text(preview.get("source_template_digest")),
        "source_update_digest": _text(preview.get("source_update_digest")),
        "source_hypothesis_digest": _text(preview.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(preview.get("source_feedback_digest")),
        "final_local_apply_preview_item_count": len(preview_items),
        "final_apply_execution_review_item_count": len(review_items),
        "final_apply_execution_review_ready": ready,
        "human_final_apply_execution_decision_required": ready,
        "human_final_apply_execution_decision_complete": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "allowed_human_final_execution_decisions": list(ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS),
        "final_apply_execution_review_items": review_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "review_item_findings": review_item_findings,
        "counts": {
            "final_local_apply_preview_items": len(preview_items),
            "final_apply_execution_review_items": len(review_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "review_item_findings": len(review_item_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(review_item_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not execute the final apply path from this review gate.",
            "Do not write persistent research state from this review gate.",
            "Do not apply confidence changes from this review gate.",
            "Do not mutate selected hypotheses or investigation plans.",
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

    result["final_apply_execution_review_gate_digest"] = _sha256(
        {
            "kind": result["kind"],
            "target_name": result["target_name"],
            "review_status": result["review_status"],
            "source_final_local_apply_preview_digest": result["source_final_local_apply_preview_digest"],
            "final_apply_execution_review_items": result["final_apply_execution_review_items"],
        }
    )
    return result


def build_final_apply_execution_review_gate_from_file(
    final_local_apply_preview_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    gate = build_research_state_final_apply_execution_review_gate(
        load_json_object(final_local_apply_preview_file),
    )
    if json_output is not None:
        write_json(json_output, gate)
    return gate


def _source_findings(preview: dict[str, Any], preview_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if preview.get("kind") != EXPECTED_PREVIEW_KIND:
        findings.append(_finding("source-schema", "high", "Invalid final local apply preview kind.", "preview.kind", "Use a final local apply preview artifact."))

    if preview.get("preview_status") != EXPECTED_PREVIEW_STATUS:
        findings.append(_finding("source-status", "high", "Final local apply preview is not ready for final apply execution review.", "preview.preview_status", "Resolve final local apply preview blockers first."))

    if preview.get("final_local_apply_preview_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Final local apply preview is not marked ready.", "preview.final_local_apply_preview_ready", "Use a ready final local apply preview."))

    if preview.get("final_apply_execution_review_gate_required") is not True:
        findings.append(_finding("source-readiness", "high", "Final apply execution review gate is not required by the source preview.", "preview.final_apply_execution_review_gate_required", "Use a final local apply preview that requires a final apply execution review gate."))

    if preview.get("final_apply_execution_review_gate_ready") is True:
        findings.append(_finding("source-safety", "high", "Source preview already marks final apply execution review gate ready.", "preview.final_apply_execution_review_gate_ready", "Use only pre-review-gate final local apply previews."))

    if preview.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Source preview already marks persistent write ready.", "preview.persistent_research_state_write_ready", "Use only pre-write preview artifacts."))

    if preview.get("persistent_research_state_write_allowed") is True:
        findings.append(_finding("source-safety", "high", "Source preview allows persistent write.", "preview.persistent_research_state_write_allowed", "Use only non-writing preview artifacts."))

    if preview.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Source preview already marks research-state transition ready.", "preview.research_state_transition_ready", "Use only pre-transition preview artifacts."))

    if not preview_items:
        findings.append(_finding("source-content", "high", "No final local apply preview items are present.", "preview.final_local_apply_preview_items", "Generate at least one final local apply preview item before review gate generation."))

    expected_count = _int(preview.get("final_local_apply_preview_item_count"))
    if expected_count and expected_count != len(preview_items):
        findings.append(_finding("source-count", "medium", "Final local apply preview item count does not match list length.", "preview.final_local_apply_preview_item_count", "Regenerate the final local apply preview."))

    if not _text(preview.get("final_local_apply_preview_digest")):
        findings.append(_finding("source-digest", "medium", "Final local apply preview digest is missing.", "preview.final_local_apply_preview_digest", "Regenerate the final local apply preview."))

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


def _review_item_findings(preview_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_preview_ids: set[str] = set()
    seen_fields: set[str] = set()

    for item in preview_items:
        preview_id = _text(item.get("final_local_apply_preview_item_id"))
        field_path = _text(item.get("field_path"))

        if not preview_id:
            findings.append(_finding("review-schema", "high", "Preview item is missing final_local_apply_preview_item_id.", "preview_item.final_local_apply_preview_item_id", "Regenerate the final local apply preview."))
        elif preview_id in seen_preview_ids:
            findings.append(_finding("review-coverage", "high", f"Duplicate final local apply preview item: {preview_id}.", preview_id, "Resolve duplicate final local apply preview items."))
        seen_preview_ids.add(preview_id)

        for required in (
            "human_final_apply_decision_id",
            "final_persistence_apply_review_item_id",
            "local_write_execution_packet_item_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "final_local_apply_preview_item_digest",
            "source_human_final_apply_decision_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("review-schema", "high", f"Preview item {preview_id or '<missing>'} is missing {required}.", preview_id, "Regenerate the final local apply preview."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("review-coverage", "high", f"Multiple final local apply preview items target field {field_path}.", field_path, "Resolve duplicate field updates before final apply execution review."))
            seen_fields.add(field_path)

        if item.get("final_apply_execution_review_required") is not True:
            findings.append(_finding("review-readiness", "high", f"Preview item {preview_id or '<missing>'} does not require final apply execution review.", preview_id, "Use preview items that require final apply execution review."))

        if item.get("final_apply_execution_review_ready") is True:
            findings.append(_finding("review-safety", "high", f"Preview item {preview_id or '<missing>'} already marks final apply execution review ready.", preview_id, "Use pre-review-gate preview items only."))

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
                findings.append(_finding("review-unsafe-flag", "high", f"Preview item unsafe flag is true: {flag}.", f"{preview_id}.{flag}", "Keep final apply execution review records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("review-planning-only", "high", f"Preview item {preview_id or '<missing>'} is not planning-only.", preview_id, "Use only planning-only preview records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("review-execution-state", "high", f"Preview item {preview_id or '<missing>'} execution_state is not not_executed.", preview_id, "Use only non-executed preview records."))

    return findings


def _review_item(index: int, preview: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "final_apply_execution_review_item_id": f"FAERG-{index:03d}",
        "final_local_apply_preview_item_id": _text(preview.get("final_local_apply_preview_item_id")),
        "human_final_apply_decision_id": _text(preview.get("human_final_apply_decision_id")),
        "final_persistence_apply_review_item_id": _text(preview.get("final_persistence_apply_review_item_id")),
        "local_write_execution_packet_item_id": _text(preview.get("local_write_execution_packet_item_id")),
        "write_execution_decision_id": _text(preview.get("write_execution_decision_id")),
        "write_execution_review_item_id": _text(preview.get("write_execution_review_item_id")),
        "local_write_packet_preview_item_id": _text(preview.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(preview.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(preview.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(preview.get("source_preview_item_id")),
        "apply_decision_id": _text(preview.get("apply_decision_id")),
        "apply_review_item_id": _text(preview.get("apply_review_item_id")),
        "operation_id": _text(preview.get("operation_id")),
        "transition_id": _text(preview.get("transition_id")),
        "decision_id": _text(preview.get("decision_id")),
        "hypothesis_id": _text(preview.get("hypothesis_id")),
        "field_path": _text(preview.get("field_path")),
        "operation_type": _text(preview.get("operation_type")),
        "current_value": _text(preview.get("current_value")),
        "proposed_value": _text(preview.get("proposed_value")),
        "local_write_operation": _text(preview.get("local_write_operation"), "preview-persistent-research-state-field-write"),
        "final_local_apply_action": _text(preview.get("final_local_apply_action"), "preview-final-persistent-research-state-field-write"),
        "final_apply_execution_review_summary": f"{_text(preview.get('field_path'))}: {_text(preview.get('current_value'))} -> {_text(preview.get('proposed_value'))}",
        "human_final_apply_decision": _text(preview.get("decision")),
        "human_final_apply_decision_reason": _text(preview.get("decision_reason")),
        "human_final_apply_decision_actor": _text(preview.get("decision_actor"), "human-reviewer"),
        "allowed_human_final_execution_decisions": list(ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS),
        "human_final_apply_execution_decision_required": ready,
        "human_final_apply_execution_decision_complete": False,
        "final_apply_execution_approved": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_final_local_apply_preview_item_digest": _text(preview.get("final_local_apply_preview_item_digest")),
        "source_human_final_apply_decision_digest": _text(preview.get("source_human_final_apply_decision_digest")),
        "source_final_persistence_apply_review_item_digest": _text(preview.get("source_final_persistence_apply_review_item_digest")),
        "source_local_write_execution_packet_item_digest": _text(preview.get("source_local_write_execution_packet_item_digest")),
        "source_write_execution_decision_digest": _text(preview.get("source_write_execution_decision_digest")),
        "source_write_execution_review_item_digest": _text(preview.get("source_write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(preview.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(preview.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(preview.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(preview.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(preview.get("source_apply_decision_digest")),
        "source_operation_digest": _text(preview.get("source_operation_digest")),
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["final_apply_execution_review_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    review_findings: list[dict[str, str]],
    preview_items: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-final-local-apply-preview"
    if _high(safety_findings):
        return "blocked-unsafe-final-local-apply-preview"
    if not preview_items:
        return "blocked-no-final-local-apply-preview-items"
    if _high(review_findings):
        return "blocked-invalid-final-apply-execution-review-items"
    return READY_STATUS


def _summary(status: str, count: int) -> str:
    if status == READY_STATUS:
        return f"{count} final local apply preview item(s) are ready for human final apply execution review."
    if status == "blocked-invalid-final-local-apply-preview":
        return "Final apply execution review gate blocked because the source final local apply preview is invalid."
    if status == "blocked-unsafe-final-local-apply-preview":
        return "Final apply execution review gate blocked because the source preview enables mutation, writing, or execution."
    if status == "blocked-no-final-local-apply-preview-items":
        return "Final apply execution review gate blocked because there are no final local apply preview items."
    if status == "blocked-invalid-final-apply-execution-review-items":
        return "Final apply execution review gate blocked because one or more review items are invalid."
    return "Final apply execution review gate is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == READY_STATUS:
        return [
            "Perform human final apply execution review.",
            "Record explicit human decisions for each final apply execution review item.",
            "Keep stored-state writes disabled until a later final apply path is separately reviewed.",
        ]
    return [
        "Resolve blocking findings before human final apply execution review.",
        "Keep this final apply execution review gate local-only and non-mutating.",
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
