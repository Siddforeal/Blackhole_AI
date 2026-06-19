"""Human write execution decision packet.

This module combines a write execution review gate with explicit human write
execution decisions. It does not write persistent research state, apply
confidence changes, mutate hypotheses, execute tools, interact with targets,
collect evidence, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_write_execution_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-write-execution-review"
EXPECTED_PACKET_KIND = "brain_chat_research_state_write_execution_decision_packet"

ALLOWED_DECISIONS: tuple[str, ...] = (
    "approve-write-execution-packet",
    "reject-write-execution",
    "request-changes",
    "defer-write-execution",
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


def build_research_state_write_execution_decision_packet(
    write_execution_review_gate: dict[str, Any],
    human_write_execution_decisions: dict[str, Any],
    source: str = "brain-chat-research-state-write-execution-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(write_execution_review_gate)
    decisions_input = copy.deepcopy(human_write_execution_decisions)

    review_items = _object_list(gate.get("review_items"))
    decisions = _decision_list(decisions_input)
    review_by_id = {
        _text(item.get("write_execution_review_item_id")): item
        for item in review_items
        if _text(item.get("write_execution_review_item_id"))
    }

    source_findings = _source_findings(gate, review_items)
    safety_findings = _unsafe_flag_findings(gate, "write_execution_review_gate")
    decision_findings = _decision_findings(decisions, review_by_id)

    decision_items = [
        _decision_item(index, decision, review_by_id.get(_text(decision.get("write_execution_review_item_id"))))
        for index, decision in enumerate(decisions, start=1)
    ]
    approved = [
        item for item in decision_items
        if item["decision"] == "approve-write-execution-packet" and item["decision_valid"]
    ]

    status = _status(source_findings, safety_findings, decision_findings, review_items, approved)
    ready = status == "ready-for-local-write-execution-packet"

    packet = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, len(approved)),
        "source_write_execution_review_gate_kind": _text(gate.get("kind")),
        "source_write_execution_review_gate_status": _text(gate.get("gate_status")),
        "source_write_execution_review_gate_digest": _text(gate.get("write_execution_review_gate_digest")),
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
        "write_execution_review_item_count": len(review_items),
        "write_execution_decision_count": len(decision_items),
        "approved_write_execution_decision_count": len(approved),
        "human_write_execution_decision_required": True,
        "human_write_execution_decision_complete": ready,
        "local_write_execution_packet_required": ready,
        "local_write_execution_packet_ready": False,
        "persistent_research_state_write_ready": False,
        "persistent_research_state_write_allowed": False,
        "research_state_transition_ready": False,
        "write_execution_decisions": decision_items,
        "approved_write_execution_items": approved,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "decision_findings": decision_findings,
        "counts": {
            "write_execution_review_items": len(review_items),
            "write_execution_decisions": len(decision_items),
            "approved_write_execution_decisions": len(approved),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "decision_findings": len(decision_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(decision_findings))
            ),
        },
        "allowed_decisions": list(ALLOWED_DECISIONS),
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

    packet["write_execution_decision_packet_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "decision_status": packet["decision_status"],
            "source_write_execution_review_gate_digest": packet["source_write_execution_review_gate_digest"],
            "write_execution_decisions": packet["write_execution_decisions"],
            "approved_write_execution_items": packet["approved_write_execution_items"],
        }
    )
    return packet


def build_write_execution_decision_packet_from_files(
    write_execution_review_gate_file: str | Path,
    human_write_execution_decisions_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_write_execution_decision_packet(
        load_json_object(write_execution_review_gate_file),
        load_json_object(human_write_execution_decisions_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(gate: dict[str, Any], review_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid write execution review gate kind.", "gate.kind", "Use a write execution review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("source-status", "high", "Write execution review gate is not ready for human review decisions.", "gate.gate_status", "Resolve review gate blockers first."))

    if gate.get("write_execution_review_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Write execution review gate is not marked ready.", "gate.write_execution_review_ready", "Use a ready write execution review gate."))

    if gate.get("human_write_execution_review_required") is not True:
        findings.append(_finding("source-readiness", "high", "Write execution review gate does not require human review.", "gate.human_write_execution_review_required", "Use a gate that requires human write execution review."))

    if gate.get("human_write_execution_review_complete") is True:
        findings.append(_finding("source-safety", "high", "Write execution review gate already marks human review complete.", "gate.human_write_execution_review_complete", "Use only pre-decision gates."))

    if gate.get("write_execution_decision_packet_ready") is True:
        findings.append(_finding("source-safety", "high", "Write execution review gate already marks decision packet ready.", "gate.write_execution_decision_packet_ready", "Use only pre-decision gates."))

    if gate.get("persistent_research_state_write_ready") is True:
        findings.append(_finding("source-safety", "high", "Write execution review gate already marks persistent write ready.", "gate.persistent_research_state_write_ready", "Use only pre-write gates."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Write execution review gate already marks research-state transition ready.", "gate.research_state_transition_ready", "Use only pre-transition gates."))

    if not review_items:
        findings.append(_finding("source-content", "high", "No write execution review items are present.", "gate.review_items", "Generate write execution review items first."))

    expected_count = _int(gate.get("write_execution_review_item_count"))
    if expected_count and expected_count != len(review_items):
        findings.append(_finding("source-count", "medium", "Write execution review item count does not match list length.", "gate.write_execution_review_item_count", "Regenerate the write execution review gate."))

    if not _text(gate.get("write_execution_review_gate_digest")):
        findings.append(_finding("source-digest", "medium", "Write execution review gate digest is missing.", "gate.write_execution_review_gate_digest", "Regenerate the write execution review gate."))

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


def _decision_findings(decisions: list[dict[str, Any]], review_by_id: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen: set[str] = set()

    if not decisions:
        findings.append(_finding("decision-content", "high", "No human write execution decisions are present.", "human_write_execution_decisions", "Record at least one human write execution decision."))
        return findings

    for decision in decisions:
        review_id = _text(decision.get("write_execution_review_item_id"))
        value = _text(decision.get("decision"))

        if not review_id:
            findings.append(_finding("decision-schema", "high", "Human decision is missing write_execution_review_item_id.", "decision.write_execution_review_item_id", "Provide the target review item ID."))
        elif review_id not in review_by_id:
            findings.append(_finding("decision-coverage", "high", f"Human decision targets unknown review item: {review_id}.", review_id, "Use review item IDs from the gate."))
        elif review_id in seen:
            findings.append(_finding("decision-coverage", "high", f"Duplicate human decision for review item: {review_id}.", review_id, "Record one decision per review item."))
        seen.add(review_id)

        if value not in ALLOWED_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Unsupported human decision: {value or '<missing>'}.", review_id, "Use an allowed write execution decision."))

        if not _text(decision.get("decision_reason")):
            findings.append(_finding("decision-reason", "medium", f"Human decision {review_id or '<missing>'} is missing a reason.", review_id, "Add a concise human decision reason."))

    missing = set(review_by_id) - seen
    for review_id in sorted(missing):
        findings.append(_finding("decision-coverage", "medium", f"No human decision recorded for review item: {review_id}.", review_id, "Record a human decision or keep the packet blocked."))

    return findings


def _decision_item(index: int, decision: dict[str, Any], review_item: dict[str, Any] | None) -> dict[str, Any]:
    matched = review_item or {}
    value = _text(decision.get("decision"))
    review_id = _text(decision.get("write_execution_review_item_id"))
    valid = bool(matched) and value in ALLOWED_DECISIONS

    item = {
        "write_execution_decision_id": f"WEDP-{index:03d}",
        "write_execution_review_item_id": review_id,
        "local_write_packet_preview_item_id": _text(matched.get("local_write_packet_preview_item_id")),
        "persistence_write_decision_id": _text(matched.get("persistence_write_decision_id")),
        "persistence_write_review_item_id": _text(matched.get("persistence_write_review_item_id")),
        "source_preview_item_id": _text(matched.get("source_preview_item_id")),
        "apply_decision_id": _text(matched.get("apply_decision_id")),
        "apply_review_item_id": _text(matched.get("apply_review_item_id")),
        "operation_id": _text(matched.get("operation_id")),
        "transition_id": _text(matched.get("transition_id")),
        "decision_id": _text(matched.get("decision_id")),
        "hypothesis_id": _text(matched.get("hypothesis_id")),
        "field_path": _text(matched.get("field_path")),
        "operation_type": _text(matched.get("operation_type")),
        "current_value": _text(matched.get("current_value")),
        "proposed_value": _text(matched.get("proposed_value")),
        "write_preview_action": _text(matched.get("write_preview_action")),
        "write_preview_summary": _text(matched.get("write_preview_summary")),
        "decision": value,
        "decision_valid": valid,
        "decision_reason": _text(decision.get("decision_reason")),
        "decision_actor": _text(decision.get("decision_actor"), "human-reviewer"),
        "source_write_execution_review_item_digest": _text(matched.get("write_execution_review_item_digest")),
        "source_local_write_packet_preview_item_digest": _text(matched.get("source_local_write_packet_preview_item_digest")),
        "source_persistence_write_decision_digest": _text(matched.get("source_persistence_write_decision_digest")),
        "source_persistence_write_review_item_digest": _text(matched.get("source_persistence_write_review_item_digest")),
        "source_apply_preview_item_digest": _text(matched.get("source_apply_preview_item_digest")),
        "source_apply_decision_digest": _text(matched.get("source_apply_decision_digest")),
        "source_operation_digest": _text(matched.get("source_operation_digest")),
        "human_write_execution_decision_complete": valid,
        "local_write_execution_packet_required": valid and value == "approve-write-execution-packet",
        "local_write_execution_packet_ready": False,
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
    item["write_execution_decision_digest"] = _sha256(item)
    return item


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    review_items: list[dict[str, Any]],
    approved: list[dict[str, Any]],
) -> str:
    if not review_items:
        return "blocked-no-write-execution-review-items"
    if _high(source_findings):
        return "blocked-invalid-write-execution-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-write-execution-review-gate"
    if _high(decision_findings):
        return "blocked-invalid-write-execution-decisions"
    if not approved:
        return "blocked-no-approved-write-execution-decisions"
    return "ready-for-local-write-execution-packet"


def _summary(status: str, approved_count: int) -> str:
    if status == "ready-for-local-write-execution-packet":
        return f"{approved_count} human-approved write execution decision(s) are ready for a later local write execution packet."
    if status == "blocked-no-write-execution-review-items":
        return "Write execution decision packet blocked because no review items are present."
    if status == "blocked-invalid-write-execution-review-gate":
        return "Write execution decision packet blocked because the source review gate is invalid."
    if status == "blocked-unsafe-write-execution-review-gate":
        return "Write execution decision packet blocked because the source review gate enables mutation, writing, or execution."
    if status == "blocked-invalid-write-execution-decisions":
        return "Write execution decision packet blocked because one or more human decisions are invalid."
    if status == "blocked-no-approved-write-execution-decisions":
        return "Write execution decision packet blocked because no human decisions approve a later local write execution packet."
    return "Write execution decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-local-write-execution-packet":
        return [
            "Build a later local write execution packet from approved decisions.",
            "Keep stored-state writes disabled until a separate write path is reviewed.",
            "Preserve all source digests and human decision records.",
        ]
    return [
        "Resolve blocking findings before building any local write execution packet.",
        "Keep this human decision packet local-only and non-mutating.",
    ]


def _decision_list(value: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("human_write_execution_decisions", "write_execution_decisions", "decisions"):
        items = value.get(key)
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


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
