"""Local human apply decision packet for research-state transition operations.

This module combines an apply review gate with explicit human apply decisions.
It does not write persistent research state, apply hypothesis confidence changes,
execute tools, interact with targets, collect evidence, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_transition_apply_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-apply-review"
EXPECTED_PACKET_KIND = "brain_chat_research_state_transition_apply_decision_packet"

ALLOWED_DECISIONS: tuple[str, ...] = (
    "approve-apply-packet",
    "reject-apply",
    "request-changes",
    "defer-apply",
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


def load_json_array(path: str | Path) -> list[Any]:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError(f"Expected JSON array in {source}")
    return value


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_research_state_transition_apply_decision_packet(
    apply_review_gate: dict[str, Any],
    human_apply_decisions: list[dict[str, Any]],
    source: str = "brain-chat-research-state-transition-apply-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(apply_review_gate)
    decisions = copy.deepcopy(human_apply_decisions)
    review_items = _object_list(gate.get("apply_review_items"))
    decision_map = _decision_map(decisions)

    source_findings = _source_findings(gate, review_items)
    safety_findings = _unsafe_flag_findings(gate, "apply_review_gate")
    decision_findings = _decision_findings(review_items, decision_map)

    status = _status(source_findings, safety_findings, decision_findings, review_items, decision_map)
    complete = status in {
        "ready-for-research-state-transition-apply-preview",
        "blocked-no-approved-apply-decisions",
    }

    apply_decisions = [
        _apply_decision_record(index, item, decision_map.get(_text(item.get("review_item_id"))), complete)
        for index, item in enumerate(review_items, start=1)
    ]
    approved = [
        item
        for item in apply_decisions
        if item["decision"] == "approve-apply-packet"
    ]

    packet = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, len(apply_decisions), len(approved)),
        "source_apply_review_gate_kind": _text(gate.get("kind")),
        "source_apply_review_gate_status": _text(gate.get("gate_status")),
        "source_apply_review_gate_digest": _text(gate.get("apply_review_gate_digest")),
        "source_transition_packet_digest": _text(gate.get("source_transition_packet_digest")),
        "source_decision_digest": _text(gate.get("source_decision_digest")),
        "source_gate_digest": _text(gate.get("source_gate_digest")),
        "source_template_digest": _text(gate.get("source_template_digest")),
        "source_update_digest": _text(gate.get("source_update_digest")),
        "source_hypothesis_digest": _text(gate.get("source_hypothesis_digest")),
        "source_feedback_digest": _text(gate.get("source_feedback_digest")),
        "apply_review_item_count": len(review_items),
        "apply_decision_count": len(apply_decisions),
        "approved_apply_decision_count": len(approved),
        "human_apply_decision_complete": complete,
        "human_apply_decision_required": not complete,
        "research_state_transition_apply_preview_required": bool(approved),
        "research_state_transition_apply_preview_ready": status == "ready-for-research-state-transition-apply-preview",
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "apply_decisions": apply_decisions,
        "approved_apply_items": approved,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "decision_findings": decision_findings,
        "counts": {
            "apply_review_items": len(review_items),
            "input_decisions": len(decisions),
            "apply_decisions": len(apply_decisions),
            "approved_apply_decisions": len(approved),
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
            "Do not write persistent research state from this packet.",
            "Do not apply confidence updates from this packet.",
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

    packet["apply_decision_packet_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "decision_status": packet["decision_status"],
            "source_apply_review_gate_digest": packet["source_apply_review_gate_digest"],
            "apply_decisions": packet["apply_decisions"],
            "approved_apply_items": packet["approved_apply_items"],
        }
    )
    return packet


def build_apply_decision_packet_from_files(
    apply_review_gate_file: str | Path,
    human_apply_decisions_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_transition_apply_decision_packet(
        load_json_object(apply_review_gate_file),
        _object_list(load_json_array(human_apply_decisions_file)),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(gate: dict[str, Any], review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid apply review gate kind.", "gate.kind", "Use a research-state transition apply review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("source-status", "high", "Apply review gate is not ready for human decisions.", "gate.gate_status", "Resolve apply review gate blockers first."))

    if gate.get("apply_review_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Apply review gate is not marked ready.", "gate.apply_review_ready", "Use a ready apply review gate."))

    if gate.get("human_apply_decision_required") is not True:
        findings.append(_finding("source-readiness", "high", "Apply review gate does not require human apply decisions.", "gate.human_apply_decision_required", "Use a gate that requires human apply decisions."))

    if gate.get("human_apply_decision_complete") is True:
        findings.append(_finding("source-safety", "high", "Apply review gate already marks human decisions complete.", "gate.human_apply_decision_complete", "Use a pre-decision apply review gate."))

    if gate.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply review gate already marks persistent write ready.", "gate.persistent_research_state_write_ready", "Use only pre-preview gates."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Apply review gate already marks transition ready.", "gate.research_state_transition_ready", "Use only pre-preview gates."))

    if not review_items:
        findings.append(_finding("source-content", "high", "No apply review items are present.", "gate.apply_review_items", "Create apply review items first."))

    expected_count = _int(gate.get("apply_review_item_count"))
    if expected_count and expected_count != len(review_items):
        findings.append(_finding("source-count", "medium", "Apply review item count does not match list length.", "gate.apply_review_item_count", "Regenerate the apply review gate."))

    if not _text(gate.get("apply_review_gate_digest")):
        findings.append(_finding("source-digest", "medium", "Apply review gate digest is missing.", "gate.apply_review_gate_digest", "Regenerate the apply review gate."))

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
    decision_map: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    expected_ids = {_text(item.get("review_item_id")) for item in review_items if _text(item.get("review_item_id"))}

    for item in review_items:
        review_item_id = _text(item.get("review_item_id"))
        decision = decision_map.get(review_item_id)

        if not review_item_id:
            findings.append(_finding("review-item-schema", "high", "Apply review item is missing review_item_id.", "review_item.review_item_id", "Regenerate the apply review gate."))
            continue

        if decision is None:
            findings.append(_finding("decision-coverage", "high", f"Missing human apply decision for {review_item_id}.", review_item_id, "Provide a human decision for every apply review item."))
            continue

        decision_value = _text(decision.get("decision"))
        if decision_value not in ALLOWED_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Invalid apply decision: {decision_value}.", review_item_id, "Use an allowed apply decision value."))

        if not _text(decision.get("decision_reason")):
            findings.append(_finding("decision-reason", "high", f"Missing decision_reason for {review_item_id}.", review_item_id, "Provide an explicit human decision reason."))

        if bool(decision.get("persistent_write_allowed")):
            findings.append(_finding("decision-unsafe-flag", "high", f"Decision {review_item_id} enables persistent_write_allowed.", review_item_id, "Keep decision records fail-closed."))

        if bool(decision.get("execution_allowed")) or bool(decision.get("runtime_execution_allowed")):
            findings.append(_finding("decision-unsafe-flag", "high", f"Decision {review_item_id} enables execution.", review_item_id, "Keep decision records non-executing."))

        if decision.get("planning_only") is not True:
            findings.append(_finding("decision-planning-only", "high", f"Decision {review_item_id} is not planning-only.", review_item_id, "Use only planning-only decision records."))

        if _text(decision.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("decision-execution-state", "high", f"Decision {review_item_id} execution_state is not not_executed.", review_item_id, "Use only non-executed decision records."))

    for review_item_id in decision_map:
        if review_item_id not in expected_ids:
            findings.append(_finding("decision-coverage", "medium", f"Decision references unknown review item: {review_item_id}.", review_item_id, "Remove decisions that do not match apply review items."))

    return findings


def _decision_map(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        review_item_id = _text(decision.get("review_item_id"))
        if review_item_id and review_item_id not in mapped:
            mapped[review_item_id] = decision
    return mapped


def _apply_decision_record(
    index: int,
    review_item: dict[str, Any],
    human_decision: dict[str, Any] | None,
    complete: bool,
) -> dict[str, Any]:
    decision = human_decision or {}
    decision_value = _text(decision.get("decision"), "missing-decision")
    approved = decision_value == "approve-apply-packet"

    record = {
        "apply_decision_id": f"RSTAD-{index:03d}",
        "review_item_id": _text(review_item.get("review_item_id")),
        "operation_id": _text(review_item.get("operation_id")),
        "transition_id": _text(review_item.get("transition_id")),
        "decision_id": _text(review_item.get("decision_id")),
        "hypothesis_id": _text(review_item.get("hypothesis_id")),
        "field_path": _text(review_item.get("field_path")),
        "operation_type": _text(review_item.get("operation_type")),
        "current_value": _text(review_item.get("current_value")),
        "proposed_value": _text(review_item.get("proposed_value")),
        "decision": decision_value,
        "decision_reason": _text(decision.get("decision_reason")),
        "source_review_item_digest": _text(review_item.get("review_item_digest")),
        "source_operation_digest": _text(review_item.get("source_operation_digest")),
        "human_apply_decision_complete": complete,
        "apply_preview_required": approved,
        "apply_preview_ready": False,
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
    record["apply_decision_digest"] = _sha256(record)
    return record


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    review_items: list[dict[str, Any]],
    decision_map: dict[str, dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-apply-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-apply-review-gate"
    if not review_items:
        return "blocked-no-apply-review-items"
    if _high(decision_findings):
        return "blocked-invalid-apply-decisions"

    approved = [
        decision
        for decision in decision_map.values()
        if _text(decision.get("decision")) == "approve-apply-packet"
    ]
    if not approved:
        return "blocked-no-approved-apply-decisions"

    return "ready-for-research-state-transition-apply-preview"


def _summary(status: str, total: int, approved: int) -> str:
    if status == "ready-for-research-state-transition-apply-preview":
        return f"{approved} of {total} apply decision(s) are approved for a later local apply preview."
    if status == "blocked-no-approved-apply-decisions":
        return "Human apply decisions are complete, but no apply items were approved for preview."
    if status == "blocked-invalid-apply-review-gate":
        return "Apply decision packet blocked because the source apply review gate is invalid."
    if status == "blocked-unsafe-apply-review-gate":
        return "Apply decision packet blocked because the source gate enables mutation, writing, or execution."
    if status == "blocked-no-apply-review-items":
        return "Apply decision packet blocked because there are no apply review items."
    if status == "blocked-invalid-apply-decisions":
        return "Apply decision packet blocked because one or more human apply decisions are invalid or missing."
    return "Apply decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-research-state-transition-apply-preview":
        return [
            "Build a separate local apply preview artifact for approved apply decisions.",
            "Review the preview before any stored-state update is considered.",
            "Keep persistence disabled until a later explicit apply approval stage.",
        ]
    if status == "blocked-no-approved-apply-decisions":
        return [
            "Stop the apply path or revise human decisions.",
            "Do not build an apply preview without approved apply decisions.",
        ]
    return [
        "Resolve blocking findings before building any apply preview.",
        "Keep this apply decision packet local-only and non-mutating.",
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
