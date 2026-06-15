"""Human persistence write decision packet.

This module combines a persistence write review gate with explicit human
persistence write decisions. It records approved items for a later local write
packet preview. It does not write persistent research state, apply confidence
changes, mutate hypotheses, execute tools, interact with targets, collect
evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_persistence_write_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-persistence-write-review"
EXPECTED_DECISION_KIND = "brain_chat_research_state_persistence_write_decision_packet"

ALLOWED_DECISIONS: tuple[str, ...] = (
    "approve-persistence-write-packet",
    "reject-persistence-write",
    "request-changes",
    "defer-persistence-write",
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


def build_research_state_persistence_write_decision_packet(
    persistence_write_review_gate: dict[str, Any],
    human_persistence_write_decisions: dict[str, Any],
    source: str = "brain-chat-research-state-persistence-write-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(persistence_write_review_gate)
    human = copy.deepcopy(human_persistence_write_decisions)

    review_items = _object_list(gate.get("review_items"))
    human_decisions = _extract_human_decisions(human)

    source_findings = _source_findings(gate, review_items)
    safety_findings = _unsafe_flag_findings(gate, "persistence_write_review_gate")
    decision_findings = _decision_findings(review_items, human, human_decisions)

    decisions = [
        _decision_item(index, review_item, human_decisions.get(_text(review_item.get("persistence_write_review_item_id"))))
        for index, review_item in enumerate(review_items, start=1)
    ]

    approved_items = [
        item for item in decisions
        if item["decision"] == "approve-persistence-write-packet"
        and item["decision_valid"] is True
        and item["human_persistence_write_decision_complete"] is True
    ]

    status = _status(source_findings, safety_findings, decision_findings, review_items, approved_items)
    ready = status == "ready-for-local-write-packet-preview"

    packet = {
        "kind": EXPECTED_DECISION_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, len(decisions), len(approved_items)),
        "source_persistence_write_review_gate_kind": _text(gate.get("kind")),
        "source_persistence_write_review_gate_status": _text(gate.get("gate_status")),
        "source_persistence_write_review_gate_digest": _text(gate.get("persistence_write_review_gate_digest")),
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
        "human_persistence_write_decision_source": _text(human.get("source"), "human-persistence-write-decisions"),
        "persistence_write_review_item_count": len(review_items),
        "persistence_write_decision_count": len(decisions),
        "approved_persistence_write_decision_count": len(approved_items),
        "human_persistence_write_decision_required": bool(review_items),
        "human_persistence_write_decision_complete": status in (
            "ready-for-local-write-packet-preview",
            "blocked-no-approved-persistence-write-decisions",
        ),
        "local_write_packet_preview_required": ready,
        "local_write_packet_preview_ready": ready,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "persistence_write_decisions": decisions,
        "approved_persistence_write_items": approved_items,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "decision_findings": decision_findings,
        "counts": {
            "review_items": len(review_items),
            "human_decisions": len(human_decisions),
            "persistence_write_decisions": len(decisions),
            "approved_persistence_write_decisions": len(approved_items),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "decision_findings": len(decision_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(decision_findings))
            ),
        },
        "allowed_persistence_write_decisions": list(ALLOWED_DECISIONS),
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

    packet["persistence_write_decision_packet_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "decision_status": packet["decision_status"],
            "source_persistence_write_review_gate_digest": packet["source_persistence_write_review_gate_digest"],
            "persistence_write_decisions": packet["persistence_write_decisions"],
        }
    )
    return packet


def build_persistence_write_decision_packet_from_files(
    persistence_write_review_gate_file: str | Path,
    human_persistence_write_decisions_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_persistence_write_decision_packet(
        load_json_object(persistence_write_review_gate_file),
        load_json_object(human_persistence_write_decisions_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(gate: dict[str, Any], review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid persistence write review gate kind.", "gate.kind", "Use a persistence write review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("source-status", "high", "Persistence write review gate is not ready for human review.", "gate.gate_status", "Resolve review gate blockers first."))

    if gate.get("persistence_write_review_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Persistence write review gate is not marked ready.", "gate.persistence_write_review_ready", "Use a ready persistence write review gate."))

    if gate.get("human_persistence_write_decision_required") is not True:
        findings.append(_finding("source-readiness", "high", "Persistence write review gate does not require human decisions.", "gate.human_persistence_write_decision_required", "Use a review gate that requires decisions."))

    if gate.get("human_persistence_write_decision_complete") is True:
        findings.append(_finding("source-safety", "high", "Review gate already marks human persistence write decisions complete.", "gate.human_persistence_write_decision_complete", "Use only pre-decision review gates."))

    if gate.get("persistence_write_decision_packet_ready") is True:
        findings.append(_finding("source-safety", "high", "Review gate already marks decision packet ready.", "gate.persistence_write_decision_packet_ready", "Use only pre-decision review gates."))

    if gate.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Review gate already marks persistent write ready.", "gate.persistent_research_state_write_ready", "Use only pre-write review gates."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Review gate already marks research-state transition ready.", "gate.research_state_transition_ready", "Use only pre-write review gates."))

    if not review_items:
        findings.append(_finding("source-content", "high", "No persistence write review items are present.", "gate.review_items", "Create a review gate with at least one item."))

    expected_count = _int(gate.get("persistence_write_review_item_count"))
    if expected_count and expected_count != len(review_items):
        findings.append(_finding("source-count", "medium", "Review item count does not match list length.", "gate.persistence_write_review_item_count", "Regenerate the persistence write review gate."))

    if not _text(gate.get("persistence_write_review_gate_digest")):
        findings.append(_finding("source-digest", "medium", "Persistence write review gate digest is missing.", "gate.persistence_write_review_gate_digest", "Regenerate the persistence write review gate."))

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
    human: dict[str, Any],
    human_decisions: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    required_ids = {_text(item.get("persistence_write_review_item_id")) for item in review_items}
    required_ids.discard("")

    if human.get("planning_only") is not True:
        findings.append(_finding("decision-source", "high", "Human persistence write decisions are not marked planning-only.", "human.planning_only", "Use planning-only human decisions."))

    for review_id in sorted(required_ids):
        if review_id not in human_decisions:
            findings.append(_finding("decision-coverage", "high", f"Missing human decision for review item {review_id}.", review_id, "Record an explicit human decision for every review item."))

    for review_id, decision in sorted(human_decisions.items()):
        if review_id not in required_ids:
            findings.append(_finding("decision-coverage", "high", f"Human decision references unknown review item {review_id}.", review_id, "Remove decisions for unknown review items."))

        value = _text(decision.get("decision"))
        if value not in ALLOWED_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Invalid persistence write decision: {value}.", review_id, "Use one of the allowed persistence write decisions."))

        if not _text(decision.get("decision_reason")):
            findings.append(_finding("decision-reason", "high", f"Missing decision reason for {review_id}.", review_id, "Record a human reason for each persistence write decision."))

        if decision.get("human_persistence_write_decision_complete") is not True:
            findings.append(_finding("decision-complete", "high", f"Human persistence write decision is incomplete for {review_id}.", review_id, "Mark each decision complete only after human review."))

        if bool(decision.get("persistent_write_allowed")):
            findings.append(_finding("decision-unsafe-flag", "high", f"Human decision for {review_id} enables persistent_write_allowed.", review_id, "Decision records must not enable writes."))

        if bool(decision.get("persistent_research_state_write_allowed")):
            findings.append(_finding("decision-unsafe-flag", "high", f"Human decision for {review_id} enables persistent_research_state_write_allowed.", review_id, "Decision records must not enable writes."))

        if bool(decision.get("execution_allowed")) or bool(decision.get("runtime_execution_allowed")):
            findings.append(_finding("decision-unsafe-flag", "high", f"Human decision for {review_id} enables execution.", review_id, "Decision records must not enable execution."))

        if decision.get("planning_only") is not True:
            findings.append(_finding("decision-planning-only", "high", f"Human decision for {review_id} is not planning-only.", review_id, "Use only planning-only human decision records."))

    return findings


def _decision_item(
    index: int,
    review_item: dict[str, Any],
    human_decision: dict[str, Any] | None,
) -> dict[str, Any]:
    human_decision = human_decision or {}
    decision_value = _text(human_decision.get("decision"))

    item = {
        "persistence_write_decision_id": f"PWRD-{index:03d}",
        "persistence_write_review_item_id": _text(review_item.get("persistence_write_review_item_id")),
        "preview_item_id": _text(review_item.get("preview_item_id")),
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
        "source_review_item_digest": _text(review_item.get("persistence_write_review_item_digest")),
        "source_preview_item_digest": _text(review_item.get("source_preview_item_digest")),
        "source_apply_decision_digest": _text(review_item.get("source_apply_decision_digest")),
        "source_operation_digest": _text(review_item.get("source_operation_digest")),
        "decision": decision_value,
        "decision_valid": decision_value in ALLOWED_DECISIONS,
        "decision_reason": _text(human_decision.get("decision_reason")),
        "decision_actor": _text(human_decision.get("decision_actor"), "human-reviewer"),
        "human_persistence_write_decision_complete": human_decision.get("human_persistence_write_decision_complete") is True,
        "local_write_packet_preview_required": decision_value == "approve-persistence-write-packet",
        "local_write_packet_preview_ready": False,
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
    item["persistence_write_decision_digest"] = _sha256(item)
    return item


def _extract_human_decisions(human: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw = human.get("persistence_write_decisions", human.get("decisions", []))
    if not isinstance(raw, list):
        return {}

    decisions: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, dict):
            continue
        review_id = _text(item.get("persistence_write_review_item_id"))
        if review_id:
            decisions[review_id] = item
    return decisions


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    review_items: list[dict[str, Any]],
    approved_items: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-persistence-write-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-persistence-write-review-gate"
    if not review_items:
        return "blocked-no-persistence-write-review-items"
    if _high(decision_findings):
        return "blocked-invalid-persistence-write-decisions"
    if not approved_items:
        return "blocked-no-approved-persistence-write-decisions"
    return "ready-for-local-write-packet-preview"


def _summary(status: str, total: int, approved: int) -> str:
    if status == "ready-for-local-write-packet-preview":
        return f"{approved} of {total} persistence write decision(s) are approved for a later local write packet preview."
    if status == "blocked-invalid-persistence-write-review-gate":
        return "Persistence write decision packet blocked because the source review gate is invalid."
    if status == "blocked-unsafe-persistence-write-review-gate":
        return "Persistence write decision packet blocked because the source review gate enables mutation, writing, or execution."
    if status == "blocked-no-persistence-write-review-items":
        return "Persistence write decision packet blocked because there are no review items."
    if status == "blocked-invalid-persistence-write-decisions":
        return "Persistence write decision packet blocked because one or more human decisions are invalid."
    if status == "blocked-no-approved-persistence-write-decisions":
        return "Persistence write decision packet blocked because no persistence write decisions were approved."
    return "Persistence write decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-local-write-packet-preview":
        return [
            "Build a later local write packet preview from approved persistence write decisions.",
            "Keep stored-state writes disabled until a separate write path is reviewed.",
            "Do not treat this decision packet as a write operation.",
        ]
    return [
        "Resolve blocking findings before building any local write packet preview.",
        "Keep this decision packet local-only and non-mutating.",
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
