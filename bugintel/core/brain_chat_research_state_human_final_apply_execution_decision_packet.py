"""Human final apply execution decision packet.

This module combines a final apply execution review gate with explicit human
final apply execution decisions. It does not write persistent research state,
apply confidence changes, mutate hypotheses, execute tools, interact with
targets, collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_final_apply_execution_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-final-apply-execution-review"
EXPECTED_PACKET_KIND = "brain_chat_research_state_human_final_apply_execution_decision_packet"

APPROVAL_DECISION = "approve-final-apply-execution"
READY_STATUS = "ready-for-final-apply-execution-packet"

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


def build_human_final_apply_execution_decision_packet(
    final_apply_execution_review_gate: dict[str, Any],
    human_final_apply_execution_decisions: dict[str, Any] | list[dict[str, Any]],
    source: str = "brain-chat-research-state-human-final-apply-execution-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(final_apply_execution_review_gate)
    decisions_input = copy.deepcopy(human_final_apply_execution_decisions)

    review_items = _object_list(gate.get("final_apply_execution_review_items"))
    decisions = _decision_list(decisions_input)

    source_findings = _source_findings(gate, review_items)
    safety_findings = _unsafe_flag_findings(gate, "final_apply_execution_review_gate")
    review_item_findings = _review_item_findings(review_items)
    decision_findings = _decision_findings(review_items, decisions)

    status = _status(
        source_findings=source_findings,
        safety_findings=safety_findings,
        review_item_findings=review_item_findings,
        decision_findings=decision_findings,
        review_items=review_items,
        decisions=decisions,
    )
    ready = status == READY_STATUS

    review_by_id = {
        _text(item.get("final_apply_execution_review_item_id")): item
        for item in review_items
        if _text(item.get("final_apply_execution_review_item_id"))
    }

    decision_records = [
        _decision_record(index, decision, review_by_id, ready)
        for index, decision in enumerate(decisions, start=1)
    ]
    approved_records = [
        item
        for item in decision_records
        if item["decision"] == APPROVAL_DECISION and item["decision_valid"] is True
    ]

    result = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, len(decision_records), len(approved_records)),
        "source_final_apply_execution_review_gate_kind": _text(gate.get("kind")),
        "source_final_apply_execution_review_gate_status": _text(gate.get("review_status")),
        "source_final_apply_execution_review_gate_digest": _text(gate.get("final_apply_execution_review_gate_digest")),
        "source_final_local_apply_preview_digest": _text(gate.get("source_final_local_apply_preview_digest")),
        "source_human_final_apply_decision_packet_digest": _text(gate.get("source_human_final_apply_decision_packet_digest")),
        "source_final_persistence_apply_review_gate_digest": _text(gate.get("source_final_persistence_apply_review_gate_digest")),
        "source_local_write_execution_packet_digest": _text(gate.get("source_local_write_execution_packet_digest")),
        "source_write_execution_decision_packet_digest": _text(gate.get("source_write_execution_decision_packet_digest")),
        "source_write_execution_review_gate_digest": _text(gate.get("source_write_execution_review_gate_digest")),
        "source_local_write_packet_preview_digest": _text(gate.get("source_local_write_packet_preview_digest")),
        "source_persistence_write_decision_packet_digest": _text(gate.get("source_persistence_write_decision_packet_digest")),
        "source_persistence_write_review_gate_digest": _text(gate.get("source_persistence_write_review_gate_digest")),
        "source_apply_preview_digest": _text(gate.get("source_apply_preview_digest")),
        "source_apply_decision_packet_digest": _text(gate.get("source_apply_decision_packet_digest")),
        "source_apply_review_gate_digest": _text(gate.get("source_apply_review_gate_digest")),
        "source_transition_packet_digest": _text(gate.get("source_transition_packet_digest")),
        "source_decision_digest": _text(gate.get("source_decision_digest")),
        "source_gate_digest": _text(gate.get("source_gate_digest")),
        "source_template_digest": _text(gate.get("source_template_digest")),
        "source_update_digest": _text(gate.get("source_update_digest")),
        "source_hypothesis_digest": _text(gate.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(gate.get("source_feedback_digest")),
        "final_apply_execution_review_item_count": len(review_items),
        "human_final_apply_execution_decision_count": len(decision_records),
        "approved_final_apply_execution_decision_count": len(approved_records),
        "human_final_apply_execution_decision_required": bool(review_items),
        "human_final_apply_execution_decision_complete": (
            bool(decisions)
            and not _high(source_findings)
            and not _high(safety_findings)
            and not _high(review_item_findings)
            and not _high(decision_findings)
        ),
        "final_apply_execution_packet_required": ready,
        "final_apply_execution_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "allowed_human_final_execution_decisions": list(ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS),
        "human_final_apply_execution_decisions": decision_records,
        "approved_final_apply_execution_items": approved_records,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "review_item_findings": review_item_findings,
        "decision_findings": decision_findings,
        "counts": {
            "final_apply_execution_review_items": len(review_items),
            "human_final_apply_execution_decisions": len(decision_records),
            "approved_final_apply_execution_decisions": len(approved_records),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "review_item_findings": len(review_item_findings),
            "decision_findings": len(decision_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(review_item_findings))
                + len(_high(decision_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not execute the final apply path from this decision packet.",
            "Do not write persistent research state from this decision packet.",
            "Do not apply confidence changes from this decision packet.",
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

    result["human_final_apply_execution_decision_packet_digest"] = _sha256(
        {
            "kind": result["kind"],
            "target_name": result["target_name"],
            "decision_status": result["decision_status"],
            "source_final_apply_execution_review_gate_digest": result["source_final_apply_execution_review_gate_digest"],
            "human_final_apply_execution_decisions": result["human_final_apply_execution_decisions"],
        }
    )
    return result


def build_human_final_apply_execution_decision_packet_from_files(
    final_apply_execution_review_gate_file: str | Path,
    human_final_apply_execution_decisions_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_human_final_apply_execution_decision_packet(
        load_json_object(final_apply_execution_review_gate_file),
        load_json_object(human_final_apply_execution_decisions_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(gate: dict[str, Any], review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid final apply execution review gate kind.", "gate.kind", "Use a final apply execution review gate artifact."))

    if gate.get("review_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("source-status", "high", "Final apply execution review gate is not ready for human final apply execution review.", "gate.review_status", "Resolve final apply execution review gate blockers first."))

    if gate.get("final_apply_execution_review_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Final apply execution review gate is not marked ready.", "gate.final_apply_execution_review_ready", "Use a ready final apply execution review gate."))

    if gate.get("human_final_apply_execution_decision_required") is not True:
        findings.append(_finding("source-readiness", "high", "Human final apply execution decision is not required by the source gate.", "gate.human_final_apply_execution_decision_required", "Use a gate that requires human final apply execution decisions."))

    if gate.get("human_final_apply_execution_decision_complete") is True:
        findings.append(_finding("source-safety", "high", "Source gate already marks human final apply execution decisions complete.", "gate.human_final_apply_execution_decision_complete", "Use only pre-decision review gates."))

    if gate.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Source gate already marks persistent write ready.", "gate.persistent_research_state_write_ready", "Use only pre-write review gates."))

    if gate.get("persistent_research_state_write_allowed") is True:
        findings.append(_finding("source-safety", "high", "Source gate allows persistent write.", "gate.persistent_research_state_write_allowed", "Use only non-writing review gates."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Source gate already marks research-state transition ready.", "gate.research_state_transition_ready", "Use only pre-transition review gates."))

    if not review_items:
        findings.append(_finding("source-content", "high", "No final apply execution review items are present.", "gate.final_apply_execution_review_items", "Generate at least one review item before human decision packet generation."))

    expected_count = _int(gate.get("final_apply_execution_review_item_count"))
    if expected_count and expected_count != len(review_items):
        findings.append(_finding("source-count", "medium", "Final apply execution review item count does not match list length.", "gate.final_apply_execution_review_item_count", "Regenerate the final apply execution review gate."))

    if not _text(gate.get("final_apply_execution_review_gate_digest")):
        findings.append(_finding("source-digest", "medium", "Final apply execution review gate digest is missing.", "gate.final_apply_execution_review_gate_digest", "Regenerate the final apply execution review gate."))

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


def _review_item_findings(review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_fields: set[str] = set()

    for item in review_items:
        review_id = _text(item.get("final_apply_execution_review_item_id"))
        field_path = _text(item.get("field_path"))

        if not review_id:
            findings.append(_finding("review-schema", "high", "Review item is missing final_apply_execution_review_item_id.", "review_item.final_apply_execution_review_item_id", "Regenerate the final apply execution review gate."))
        elif review_id in seen_ids:
            findings.append(_finding("review-coverage", "high", f"Duplicate final apply execution review item: {review_id}.", review_id, "Resolve duplicate review items."))
        seen_ids.add(review_id)

        for required in (
            "final_local_apply_preview_item_id",
            "operation_id",
            "hypothesis_id",
            "field_path",
            "current_value",
            "proposed_value",
            "final_apply_execution_review_item_digest",
            "source_final_local_apply_preview_item_digest",
        ):
            if not _text(item.get(required)):
                findings.append(_finding("review-schema", "high", f"Review item {review_id or '<missing>'} is missing {required}.", review_id, "Regenerate the final apply execution review gate."))

        if field_path:
            if field_path in seen_fields:
                findings.append(_finding("review-coverage", "high", f"Multiple final apply execution review items target field {field_path}.", field_path, "Resolve duplicate field updates before human decision packet generation."))
            seen_fields.add(field_path)

        if item.get("human_final_apply_execution_decision_required") is not True:
            findings.append(_finding("review-readiness", "high", f"Review item {review_id or '<missing>'} does not require human final apply execution decision.", review_id, "Use review items requiring human final apply execution decisions."))

        if item.get("human_final_apply_execution_decision_complete") is True:
            findings.append(_finding("review-safety", "high", f"Review item {review_id or '<missing>'} already marks human decision complete.", review_id, "Use pre-decision review items only."))

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
                findings.append(_finding("review-unsafe-flag", "high", f"Review item unsafe flag is true: {flag}.", f"{review_id}.{flag}", "Keep human decision packet generation fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("review-planning-only", "high", f"Review item {review_id or '<missing>'} is not planning-only.", review_id, "Use only planning-only review records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("review-execution-state", "high", f"Review item {review_id or '<missing>'} execution_state is not not_executed.", review_id, "Use only non-executed review records."))

    return findings


def _decision_findings(review_items: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    review_ids = {
        _text(item.get("final_apply_execution_review_item_id"))
        for item in review_items
        if _text(item.get("final_apply_execution_review_item_id"))
    }
    seen: set[str] = set()

    for decision in decisions:
        review_id = _text(decision.get("final_apply_execution_review_item_id"))
        action = _text(decision.get("decision"))
        reason = _text(decision.get("decision_reason"))

        if not review_id:
            findings.append(_finding("decision-schema", "high", "Human final apply execution decision is missing final_apply_execution_review_item_id.", "decision.final_apply_execution_review_item_id", "Provide one decision per review item."))
            continue

        if review_id in seen:
            findings.append(_finding("decision-coverage", "high", f"Duplicate human final apply execution decision for review item {review_id}.", review_id, "Provide only one decision per review item."))
        seen.add(review_id)

        if review_id not in review_ids:
            findings.append(_finding("decision-coverage", "high", f"Human final apply execution decision references unknown review item {review_id}.", review_id, "Use only review item IDs from the final apply execution review gate."))

        if action not in ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Invalid human final apply execution decision: {action or '<missing>'}.", review_id, "Use approve, reject, request-changes, or defer."))

        if not reason:
            findings.append(_finding("decision-rationale", "high", f"Human final apply execution decision for {review_id} is missing decision_reason.", review_id, "Record a human-readable reason for the decision."))

    missing = sorted(review_ids - seen)
    for review_id in missing:
        findings.append(_finding("decision-coverage", "high", f"Missing human final apply execution decision for review item {review_id}.", review_id, "Provide one decision for every final apply execution review item."))

    return findings


def _decision_record(index: int, decision: dict[str, Any], review_by_id: dict[str, dict[str, Any]], ready: bool) -> dict[str, Any]:
    review_id = _text(decision.get("final_apply_execution_review_item_id"))
    review = review_by_id.get(review_id, {})
    action = _text(decision.get("decision"))
    reason = _text(decision.get("decision_reason"))
    actor = _text(decision.get("decision_actor"), "human-reviewer")
    valid = bool(review) and action in ALLOWED_HUMAN_FINAL_EXECUTION_DECISIONS and bool(reason)
    approved = valid and action == APPROVAL_DECISION

    item = {
        "human_final_apply_execution_decision_id": _text(decision.get("human_final_apply_execution_decision_id"), f"HFAED-{index:03d}"),
        "final_apply_execution_review_item_id": review_id,
        "final_local_apply_preview_item_id": _text(review.get("final_local_apply_preview_item_id")),
        "human_final_apply_decision_id": _text(review.get("human_final_apply_decision_id")),
        "final_persistence_apply_review_item_id": _text(review.get("final_persistence_apply_review_item_id")),
        "local_write_execution_packet_item_id": _text(review.get("local_write_execution_packet_item_id")),
        "write_execution_decision_id": _text(review.get("write_execution_decision_id")),
        "write_execution_review_item_id": _text(review.get("write_execution_review_item_id")),
        "local_write_packet_preview_item_id": _text(review.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(review.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(review.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(review.get("source_preview_item_id")),
        "apply_decision_id": _text(review.get("apply_decision_id")),
        "apply_review_item_id": _text(review.get("apply_review_item_id")),
        "operation_id": _text(review.get("operation_id")),
        "transition_id": _text(review.get("transition_id")),
        "decision_id": _text(review.get("decision_id")),
        "hypothesis_id": _text(review.get("hypothesis_id")),
        "field_path": _text(review.get("field_path")),
        "operation_type": _text(review.get("operation_type")),
        "current_value": _text(review.get("current_value")),
        "proposed_value": _text(review.get("proposed_value")),
        "final_apply_execution_review_summary": _text(review.get("final_apply_execution_review_summary")),
        "decision": action,
        "decision_valid": valid,
        "decision_reason": reason,
        "decision_actor": actor,
        "human_final_apply_execution_decision_complete": valid,
        "final_apply_execution_approved": approved,
        "final_apply_execution_packet_required": approved and ready,
        "final_apply_execution_packet_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_final_apply_execution_review_item_digest": _text(review.get("final_apply_execution_review_item_digest")),
        "source_final_local_apply_preview_item_digest": _text(review.get("source_final_local_apply_preview_item_digest")),
        "source_human_final_apply_decision_digest": _text(review.get("source_human_final_apply_decision_digest")),
        "source_final_persistence_apply_review_item_digest": _text(review.get("source_final_persistence_apply_review_item_digest")),
        "source_local_write_execution_packet_item_digest": _text(review.get("source_local_write_execution_packet_item_digest")),
        "source_write_execution_decision_digest": _text(review.get("source_write_execution_decision_digest")),
        "source_write_execution_review_item_digest": _text(review.get("source_write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(review.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(review.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(review.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(review.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(review.get("source_apply_decision_digest")),
        "source_operation_digest": _text(review.get("source_operation_digest")),
        "planning_only": True,
        "execution_state": "not_executed",
    }
    item["human_final_apply_execution_decision_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    review_item_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    review_items: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-final-apply-execution-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-final-apply-execution-review-gate"
    if not review_items:
        return "blocked-no-final-apply-execution-review-items"
    if _high(review_item_findings):
        return "blocked-invalid-final-apply-execution-review-items"
    if not decisions:
        return "blocked-no-human-final-apply-execution-decisions"
    if _high(decision_findings):
        return "blocked-invalid-human-final-apply-execution-decisions"
    if not any(_text(item.get("decision")) == APPROVAL_DECISION for item in decisions):
        return "blocked-no-approved-final-apply-execution-decisions"
    return READY_STATUS


def _summary(status: str, decision_count: int, approved_count: int) -> str:
    if status == READY_STATUS:
        return f"{approved_count} of {decision_count} human final apply execution decision(s) are approved for a later final apply execution packet."
    if status == "blocked-invalid-final-apply-execution-review-gate":
        return "Human final apply execution decision packet blocked because the source review gate is invalid."
    if status == "blocked-unsafe-final-apply-execution-review-gate":
        return "Human final apply execution decision packet blocked because the source review gate enables mutation, writing, or execution."
    if status == "blocked-no-final-apply-execution-review-items":
        return "Human final apply execution decision packet blocked because there are no review items."
    if status == "blocked-invalid-final-apply-execution-review-items":
        return "Human final apply execution decision packet blocked because one or more review items are invalid."
    if status == "blocked-no-human-final-apply-execution-decisions":
        return "Human final apply execution decision packet blocked because no human decisions were provided."
    if status == "blocked-invalid-human-final-apply-execution-decisions":
        return "Human final apply execution decision packet blocked because one or more human decisions are invalid."
    if status == "blocked-no-approved-final-apply-execution-decisions":
        return "Human final apply execution decision packet blocked because no final apply execution decisions were approved."
    return "Human final apply execution decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == READY_STATUS:
        return [
            "Review the approved human final apply execution decisions.",
            "Build a later final apply execution packet.",
            "Keep stored-state writes disabled until a separate final apply path is reviewed.",
        ]
    return [
        "Resolve blocking findings before building a final apply execution packet.",
        "Keep this human final apply execution decision packet local-only and non-mutating.",
    ]


def _decision_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        for key in (
            "human_final_apply_execution_decisions",
            "final_apply_execution_decisions",
            "decisions",
        ):
            if key in value:
                return _object_list(value.get(key))
        return []
    return _object_list(value)


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
