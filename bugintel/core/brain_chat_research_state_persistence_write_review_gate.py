"""Persistence write review gate for local research-state apply previews.

This module converts a local apply preview into human-reviewable persistence
write review items. It does not write persistent research state, apply
confidence changes, mutate hypotheses, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_PREVIEW_KIND = "brain_chat_research_state_transition_apply_preview"
EXPECTED_PREVIEW_STATUS = "ready-for-persistence-write-review-gate"
EXPECTED_GATE_KIND = "brain_chat_research_state_persistence_write_review_gate"

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


def build_research_state_persistence_write_review_gate(
    apply_preview: dict[str, Any],
    source: str = "brain-chat-research-state-persistence-write-review-gate",
) -> dict[str, Any]:
    preview = copy.deepcopy(apply_preview)
    preview_items = _object_list(preview.get("preview_items"))

    source_findings = _source_findings(preview, preview_items)
    safety_findings = _unsafe_flag_findings(preview, "apply_preview")
    review_findings = _review_findings(preview_items)

    status = _status(source_findings, safety_findings, review_findings, preview_items)
    ready = status == "ready-for-human-persistence-write-review"

    review_items = [
        _review_item(index, item, ready)
        for index, item in enumerate(preview_items, start=1)
    ]

    gate = {
        "kind": EXPECTED_GATE_KIND,
        "source": source,
        "target_name": _text(preview.get("target_name"), "unknown-target"),
        "gate_status": status,
        "summary": _summary(status, len(review_items)),
        "source_apply_preview_kind": _text(preview.get("kind")),
        "source_apply_preview_status": _text(preview.get("preview_status")),
        "source_apply_preview_digest": _text(preview.get("apply_preview_digest")),
        "source_apply_decision_packet_digest": _text(preview.get("source_apply_decision_packet_digest")),
        "source_apply_review_gate_digest": _text(preview.get("source_apply_review_gate_digest")),
        "source_transition_packet_digest": _text(preview.get("source_transition_packet_digest")),
        "source_decision_digest": _text(preview.get("source_decision_digest")),
        "source_gate_digest": _text(preview.get("source_gate_digest")),
        "source_template_digest": _text(preview.get("source_template_digest")),
        "source_update_digest": _text(preview.get("source_update_digest")),
        "source_hypothesis_digest": _text(preview.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(preview.get("source_feedback_digest")),
        "approved_apply_decision_count": _int(preview.get("approved_apply_decision_count")),
        "apply_preview_item_count": len(preview_items),
        "persistence_write_review_item_count": len(review_items),
        "persistence_write_review_ready": ready,
        "human_persistence_write_decision_required": ready,
        "human_persistence_write_decision_complete": False,
        "persistence_write_decision_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "review_items": review_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "review_findings": review_findings,
        "counts": {
            "apply_preview_items": len(preview_items),
            "persistence_write_review_items": len(review_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "review_findings": len(review_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(review_findings))
            ),
        },
        "allowed_persistence_write_decisions": [
            "approve-persistence-write-packet",
            "reject-persistence-write",
            "request-changes",
            "defer-persistence-write",
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
        "persistent_research_state_write_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    gate["persistence_write_review_gate_digest"] = _sha256(
        {
            "kind": gate["kind"],
            "target_name": gate["target_name"],
            "gate_status": gate["gate_status"],
            "source_apply_preview_digest": gate["source_apply_preview_digest"],
            "review_items": gate["review_items"],
        }
    )
    return gate


def build_persistence_write_review_gate_from_file(
    apply_preview_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    gate = build_research_state_persistence_write_review_gate(
        load_json_object(apply_preview_file),
    )
    if json_output is not None:
        write_json(json_output, gate)
    return gate


def _source_findings(preview: dict[str, Any], preview_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if preview.get("kind") != EXPECTED_PREVIEW_KIND:
        findings.append(_finding("source-schema", "high", "Invalid apply preview kind.", "preview.kind", "Use a research-state transition apply preview."))

    if preview.get("preview_status") != EXPECTED_PREVIEW_STATUS:
        findings.append(_finding("source-status", "high", "Apply preview is not ready for persistence write review.", "preview.preview_status", "Resolve apply preview blockers first."))

    if preview.get("apply_preview_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Apply preview is not marked ready.", "preview.apply_preview_ready", "Use a ready local apply preview."))

    if preview.get("persistence_write_review_gate_required") is not True:
        findings.append(_finding("source-readiness", "high", "Apply preview does not require a persistence write review gate.", "preview.persistence_write_review_gate_required", "Use a preview that requires this review gate."))

    if preview.get("persistence_write_review_gate_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply preview already marks persistence review ready.", "preview.persistence_write_review_gate_ready", "Use only pre-review-gate preview artifacts."))

    if preview.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply preview already marks persistent write ready.", "preview.persistent_research_state_write_ready", "Use only pre-write preview artifacts."))

    if preview.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply preview already marks research-state transition ready.", "preview.research_state_transition_ready", "Use only pre-write review artifacts."))

    if not preview_items:
        findings.append(_finding("source-content", "high", "No apply preview items are present.", "preview.preview_items", "Create an apply preview with at least one approved item."))

    expected_count = _int(preview.get("preview_item_count"))
    if expected_count and expected_count != len(preview_items):
        findings.append(_finding("source-count", "medium", "Apply preview item count does not match list length.", "preview.preview_item_count", "Regenerate the apply preview."))

    if not _text(preview.get("apply_preview_digest")):
        findings.append(_finding("source-digest", "medium", "Apply preview digest is missing.", "preview.apply_preview_digest", "Regenerate the apply preview."))

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


def _review_findings(preview_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_preview_ids: set[str] = set()
    seen_fields: set[str] = set()

    for item in preview_items:
        preview_item_id = _text(item.get("preview_item_id"))
        field_path = _text(item.get("field_path"))

        if not preview_item_id:
            findings.append(_finding("review-schema", "high", "Preview item is missing preview_item_id.", "preview_item.preview_item_id", "Regenerate the apply preview."))
        elif preview_item_id in seen_preview_ids:
            findings.append(_finding("review-coverage", "high", f"Duplicate preview item: {preview_item_id}.", preview_item_id, "Resolve duplicate preview items."))
        seen_preview_ids.add(preview_item_id)

        for required in (
            "apply_decision_id",
            "review_item_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "preview_item_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("review-schema", "high", f"Preview item {preview_item_id or '<missing>'} is missing {required}.", preview_item_id, "Regenerate the apply preview."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("review-coverage", "high", f"Multiple preview items target field {field_path}.", field_path, "Resolve duplicate field previews."))
            seen_fields.add(field_path)

        if item.get("persistence_write_review_required") is not True:
            findings.append(_finding("review-readiness", "high", f"Preview item {preview_item_id or '<missing>'} does not require persistence write review.", preview_item_id, "Use preview items that require persistence write review."))

        if item.get("persistence_write_review_ready") is True:
            findings.append(_finding("review-safety", "high", f"Preview item {preview_item_id or '<missing>'} is already marked review-ready.", preview_item_id, "Use pre-review preview items only."))

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
                findings.append(_finding("review-unsafe-flag", "high", f"Preview item unsafe flag is true: {flag}.", f"{preview_item_id}.{flag}", "Keep review records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("review-planning-only", "high", f"Preview item {preview_item_id or '<missing>'} is not planning-only.", preview_item_id, "Use only planning-only preview records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("review-execution-state", "high", f"Preview item {preview_item_id or '<missing>'} execution_state is not not_executed.", preview_item_id, "Use only non-executed preview records."))

    return findings


def _review_item(index: int, preview_item: dict[str, Any], ready: bool) -> dict[str, Any]:
    item = {
        "persistence_write_review_item_id": f"PWRG-{index:03d}",
        "preview_item_id": _text(preview_item.get("preview_item_id")),
        "apply_decision_id": _text(preview_item.get("apply_decision_id")),
        "apply_review_item_id": _text(preview_item.get("review_item_id")),
        "operation_id": _text(preview_item.get("operation_id")),
        "transition_id": _text(preview_item.get("transition_id")),
        "decision_id": _text(preview_item.get("decision_id")),
        "hypothesis_id": _text(preview_item.get("hypothesis_id")),
        "field_path": _text(preview_item.get("field_path")),
        "operation_type": _text(preview_item.get("operation_type")),
        "current_value": _text(preview_item.get("current_value")),
        "proposed_value": _text(preview_item.get("proposed_value")),
        "source_preview_item_digest": _text(preview_item.get("preview_item_digest")),
        "source_apply_decision_digest": _text(preview_item.get("source_apply_decision_digest")),
        "source_operation_digest": _text(preview_item.get("source_operation_digest")),
        "review_question": "Should this proposed stored-state field update be approved for a later explicit write decision packet?",
        "allowed_decisions": [
            "approve-persistence-write-packet",
            "reject-persistence-write",
            "request-changes",
            "defer-persistence-write",
        ],
        "human_persistence_write_decision_required": ready,
        "human_persistence_write_decision_complete": False,
        "persistence_write_decision_packet_ready": False,
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
    item["persistence_write_review_item_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    review_findings: list[dict[str, str]],
    preview_items: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-apply-preview"
    if _high(safety_findings):
        return "blocked-unsafe-apply-preview"
    if not preview_items:
        return "blocked-no-apply-preview-items"
    if _high(review_findings):
        return "blocked-invalid-persistence-write-review-items"
    return "ready-for-human-persistence-write-review"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-human-persistence-write-review":
        return f"{count} preview item(s) are ready for human persistence write review."
    if status == "blocked-invalid-apply-preview":
        return "Persistence write review gate blocked because the source apply preview is invalid."
    if status == "blocked-unsafe-apply-preview":
        return "Persistence write review gate blocked because the source apply preview enables mutation, writing, or execution."
    if status == "blocked-no-apply-preview-items":
        return "Persistence write review gate blocked because there are no apply preview items."
    if status == "blocked-invalid-persistence-write-review-items":
        return "Persistence write review gate blocked because one or more review items are invalid."
    return "Persistence write review gate is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-human-persistence-write-review":
        return [
            "Review each persistence write review item manually.",
            "Record explicit human persistence write decisions in a later decision packet.",
            "Keep stored-state writes disabled until a separate write decision stage is complete.",
        ]
    return [
        "Resolve blocking findings before recording any persistence write decision.",
        "Keep this review gate local-only and non-mutating.",
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
