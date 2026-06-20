"""Human final apply decision packet.

This module combines final persistence apply review gate items with explicit
human final apply decisions. It does not write persistent research state, apply
confidence changes, mutate hypotheses, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_final_persistence_apply_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-final-persistence-apply-review"
EXPECTED_PACKET_KIND = "brain_chat_research_state_human_final_apply_decision_packet"

ALLOWED_HUMAN_DECISIONS: tuple[str, ...] = (
    "approve-final-persistence-apply",
    "reject-final-persistence-apply",
    "request-changes",
    "defer-final-persistence-apply",
)

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


def build_research_state_human_final_apply_decision_packet(
    final_persistence_apply_review_gate: dict[str, Any],
    human_final_apply_decisions: dict[str, Any],
    source: str = "brain-chat-research-state-human-final-apply-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(final_persistence_apply_review_gate)
    decisions = copy.deepcopy(human_final_apply_decisions)

    review_items = _object_list(gate.get("final_persistence_apply_review_items"))
    decision_items = _object_list(
        decisions.get("human_final_apply_decisions")
        or decisions.get("final_persistence_apply_decisions")
        or decisions.get("decisions")
    )

    source_findings = _source_findings(gate, review_items)
    safety_findings = _unsafe_flag_findings(gate, "final_persistence_apply_review_gate")
    decision_findings = _decision_findings(review_items, decision_items, decisions)

    status = _status(source_findings, safety_findings, decision_findings, review_items, decision_items)
    ready = status == "ready-for-final-local-apply-preview"

    final_decisions = [
        _decision_record(index, review_item, decision_items, ready)
        for index, review_item in enumerate(review_items, start=1)
    ]
    approved = [
        item
        for item in final_decisions
        if item["decision"] == APPROVAL_DECISION and item["decision_valid"] is True
    ]

    result = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, len(final_decisions), len(approved)),
        "source_final_persistence_apply_review_gate_kind": _text(gate.get("kind")),
        "source_final_persistence_apply_review_gate_status": _text(gate.get("gate_status")),
        "source_final_persistence_apply_review_gate_digest": _text(gate.get("final_persistence_apply_review_gate_digest")),
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
        "human_final_apply_decision_required": ready,
        "human_final_apply_decision_complete": ready,
        "final_local_apply_preview_required": ready,
        "final_local_apply_preview_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "final_persistence_apply_review_item_count": len(review_items),
        "human_final_apply_decision_count": len(final_decisions),
        "approved_final_apply_decision_count": len(approved),
        "final_apply_decisions": final_decisions,
        "approved_final_apply_items": approved,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "decision_findings": decision_findings,
        "counts": {
            "final_persistence_apply_review_items": len(review_items),
            "human_final_apply_decisions": len(final_decisions),
            "approved_final_apply_decisions": len(approved),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "decision_findings": len(decision_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(decision_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not write persistent research state from this decision packet.",
            "Do not apply confidence updates from this decision packet.",
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

    result["human_final_apply_decision_packet_digest"] = _sha256(
        {
            "kind": result["kind"],
            "target_name": result["target_name"],
            "decision_status": result["decision_status"],
            "source_final_persistence_apply_review_gate_digest": result["source_final_persistence_apply_review_gate_digest"],
            "final_apply_decisions": result["final_apply_decisions"],
        }
    )
    return result


def build_human_final_apply_decision_packet_from_files(
    final_persistence_apply_review_gate_file: str | Path,
    human_final_apply_decisions_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_human_final_apply_decision_packet(
        load_json_object(final_persistence_apply_review_gate_file),
        load_json_object(human_final_apply_decisions_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(gate: dict[str, Any], review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid final persistence apply review gate kind.", "gate.kind", "Use a final persistence apply review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("source-status", "high", "Final persistence apply review gate is not ready for human final apply review.", "gate.gate_status", "Resolve final persistence apply review gate blockers first."))

    if gate.get("human_final_persistence_apply_decision_required") is not True:
        findings.append(_finding("source-readiness", "high", "Final persistence apply review gate does not require human final apply decisions.", "gate.human_final_persistence_apply_decision_required", "Use a gate that requires human final apply decisions."))

    if gate.get("human_final_persistence_apply_decision_complete") is True:
        findings.append(_finding("source-safety", "high", "Final persistence apply review gate already marks human final apply decision complete.", "gate.human_final_persistence_apply_decision_complete", "Use pre-decision review gates only."))

    if gate.get("final_persistence_apply_decision_packet_ready") is True:
        findings.append(_finding("source-safety", "high", "Final persistence apply review gate already marks decision packet ready.", "gate.final_persistence_apply_decision_packet_ready", "Use pre-decision review gates only."))

    if gate.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Final persistence apply review gate already marks persistent write ready.", "gate.persistent_research_state_write_ready", "Use only pre-write review gates."))

    if gate.get("persistent_research_state_write_allowed") is True:
        findings.append(_finding("source-safety", "high", "Final persistence apply review gate allows persistent write.", "gate.persistent_research_state_write_allowed", "Use only non-writing review gates."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Final persistence apply review gate already marks research-state transition ready.", "gate.research_state_transition_ready", "Use only pre-transition review gates."))

    if not review_items:
        findings.append(_finding("source-content", "high", "No final persistence apply review items are present.", "gate.final_persistence_apply_review_items", "Build a gate with at least one review item."))

    expected_count = _int(gate.get("final_persistence_apply_review_item_count"))
    if expected_count and expected_count != len(review_items):
        findings.append(_finding("source-count", "medium", "Final persistence apply review item count does not match list length.", "gate.final_persistence_apply_review_item_count", "Regenerate the final persistence apply review gate."))

    if not _text(gate.get("final_persistence_apply_review_gate_digest")):
        findings.append(_finding("source-digest", "medium", "Final persistence apply review gate digest is missing.", "gate.final_persistence_apply_review_gate_digest", "Regenerate the final persistence apply review gate."))

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


def _decision_findings(
    review_items: list[dict[str, Any]],
    decision_items: list[dict[str, Any]],
    decisions: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not isinstance(decisions, dict):
        findings.append(_finding("decision-schema", "high", "Human final apply decisions input must be a JSON object.", "decisions", "Provide a JSON object containing human_final_apply_decisions."))
        return findings

    if not decision_items:
        findings.append(_finding("decision-content", "high", "No human final apply decisions are present.", "human_final_apply_decisions", "Provide explicit human decisions for every review item."))
        return findings

    review_by_id = {
        _text(item.get("final_persistence_apply_review_item_id")): item
        for item in review_items
        if _text(item.get("final_persistence_apply_review_item_id"))
    }
    review_ids = set(review_by_id)

    seen_decision_ids: set[str] = set()
    seen_review_ids: set[str] = set()

    for decision in decision_items:
        decision_id = _text(decision.get("human_final_apply_decision_id") or decision.get("final_apply_decision_id"))
        review_id = _text(decision.get("final_persistence_apply_review_item_id"))
        decision_value = _text(decision.get("decision"))
        reason = _text(decision.get("decision_reason"))
        actor = _text(decision.get("decision_actor"))

        if not decision_id:
            findings.append(_finding("decision-schema", "high", "Human final apply decision is missing decision id.", "decision.human_final_apply_decision_id", "Provide a stable decision id."))
        elif decision_id in seen_decision_ids:
            findings.append(_finding("decision-coverage", "high", f"Duplicate human final apply decision id: {decision_id}.", decision_id, "Resolve duplicate decision ids."))
        seen_decision_ids.add(decision_id)

        if not review_id:
            findings.append(_finding("decision-schema", "high", f"Decision {decision_id or '<missing>'} is missing final_persistence_apply_review_item_id.", decision_id, "Map every decision to a review item."))
        elif review_id not in review_ids:
            findings.append(_finding("decision-coverage", "high", f"Decision {decision_id or '<missing>'} references unknown review item {review_id}.", review_id, "Use only review item ids from the gate."))
        elif review_id in seen_review_ids:
            findings.append(_finding("decision-coverage", "high", f"Multiple decisions reference review item {review_id}.", review_id, "Provide exactly one decision per review item."))
        seen_review_ids.add(review_id)

        if decision_value not in ALLOWED_HUMAN_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Decision {decision_id or '<missing>'} has unsupported value: {decision_value}.", decision_id, "Use an allowed human final apply decision."))

        if not reason:
            findings.append(_finding("decision-reason", "medium", f"Decision {decision_id or '<missing>'} has no reason.", decision_id, "Add a human-readable decision reason."))

        if not actor:
            findings.append(_finding("decision-actor", "medium", f"Decision {decision_id or '<missing>'} has no actor.", decision_id, "Add a decision actor."))

    missing = sorted(review_ids - seen_review_ids)
    for review_id in missing:
        findings.append(_finding("decision-coverage", "high", f"Missing human final apply decision for review item {review_id}.", review_id, "Provide exactly one decision per review item."))

    return findings


def _decision_record(
    index: int,
    review_item: dict[str, Any],
    decision_items: list[dict[str, Any]],
    ready: bool,
) -> dict[str, Any]:
    review_id = _text(review_item.get("final_persistence_apply_review_item_id"))
    decision = next(
        (
            item
            for item in decision_items
            if _text(item.get("final_persistence_apply_review_item_id")) == review_id
        ),
        {},
    )
    decision_value = _text(decision.get("decision"))
    decision_valid = decision_value in ALLOWED_HUMAN_DECISIONS

    record = {
        "human_final_apply_decision_id": _text(
            decision.get("human_final_apply_decision_id")
            or decision.get("final_apply_decision_id")
            or f"HFAD-{index:03d}"
        ),
        "final_persistence_apply_review_item_id": review_id,
        "local_write_execution_packet_item_id": _text(review_item.get("local_write_execution_packet_item_id")),
        "write_execution_decision_id": _text(review_item.get("write_execution_decision_id")),
        "write_execution_review_item_id": _text(review_item.get("write_execution_review_item_id")),
        "local_write_packet_preview_item_id": _text(review_item.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(review_item.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(review_item.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(review_item.get("source_preview_item_id")),
        "apply_decision_id": _text(review_item.get("apply_decision_id")),
        "apply_review_item_id": _text(review_item.get("apply_review_item_id")),
        "operation_id": _text(review_item.get("operation_id")),
        "transition_id": _text(review_item.get("transition_id")),
        "decision_id": _text(review_item.get("decision_id")),
        "hypothesis_id": _text(review_item.get("hypothesis_id")),
        "field_path": _text(review_item.get("field_path")),
        "operation_type": _text(review_item.get("operation_type")),
        "current_value": _text(review_item.get("current_value")),
        "proposed_value": _text(review_item.get("proposed_value")),
        "local_write_operation": _text(review_item.get("local_write_operation")),
        "local_write_summary": _text(review_item.get("local_write_summary")),
        "decision": decision_value,
        "decision_valid": decision_valid,
        "decision_reason": _text(decision.get("decision_reason")),
        "decision_actor": _text(decision.get("decision_actor"), "human-reviewer"),
        "human_final_apply_decision_complete": ready and decision_valid,
        "final_local_apply_preview_required": ready and decision_value == APPROVAL_DECISION,
        "final_local_apply_preview_ready": False,
        "persistent_write_ready": False,
        "persistent_write_allowed": False,
        "research_state_transition_ready": False,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "source_final_persistence_apply_review_item_digest": _text(review_item.get("final_persistence_apply_review_item_digest")),
        "source_local_write_execution_packet_item_digest": _text(review_item.get("source_local_write_execution_packet_item_digest")),
        "source_write_execution_decision_digest": _text(review_item.get("source_write_execution_decision_digest")),
        "source_write_execution_review_item_digest": _text(review_item.get("source_write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(review_item.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(review_item.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(review_item.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(review_item.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(review_item.get("source_apply_decision_digest")),
        "source_operation_digest": _text(review_item.get("source_operation_digest")),
        "planning_only": True,
        "execution_state": "not_executed",
    }
    record["human_final_apply_decision_digest"] = _sha256(record)
    return record


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    review_items: list[dict[str, Any]],
    decision_items: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-final-persistence-apply-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-final-persistence-apply-review-gate"
    if not review_items:
        return "blocked-no-final-persistence-apply-review-items"
    if not decision_items:
        return "blocked-no-human-final-apply-decisions"
    if _high(decision_findings):
        return "blocked-invalid-human-final-apply-decisions"
    if not any(_text(item.get("decision")) == APPROVAL_DECISION for item in decision_items):
        return "blocked-no-approved-final-apply-decisions"
    return "ready-for-final-local-apply-preview"


def _summary(status: str, decision_count: int, approved_count: int) -> str:
    if status == "ready-for-final-local-apply-preview":
        return f"{approved_count} of {decision_count} final apply decision(s) are approved for a later final local apply preview."
    if status == "blocked-invalid-final-persistence-apply-review-gate":
        return "Human final apply decision packet blocked because the source review gate is invalid."
    if status == "blocked-unsafe-final-persistence-apply-review-gate":
        return "Human final apply decision packet blocked because the source review gate enables mutation, writing, or execution."
    if status == "blocked-no-final-persistence-apply-review-items":
        return "Human final apply decision packet blocked because there are no final persistence apply review items."
    if status == "blocked-no-human-final-apply-decisions":
        return "Human final apply decision packet blocked because there are no human final apply decisions."
    if status == "blocked-invalid-human-final-apply-decisions":
        return "Human final apply decision packet blocked because one or more human decisions are invalid."
    if status == "blocked-no-approved-final-apply-decisions":
        return "Human final apply decision packet blocked because no final apply decision was approved."
    return "Human final apply decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-final-local-apply-preview":
        return [
            "Build a later final local apply preview from approved human final apply decisions.",
            "Keep stored-state writes disabled until a separate final apply path is reviewed.",
            "Preserve all decision records for auditability.",
        ]
    return [
        "Resolve blocking findings before building any final local apply preview.",
        "Keep this human final apply decision packet local-only and non-mutating.",
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
