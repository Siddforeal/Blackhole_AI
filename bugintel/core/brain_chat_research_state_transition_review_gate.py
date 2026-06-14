"""Research-state transition review gate for proposed confidence updates.

This module reviews a hypothesis confidence update packet and creates a local,
deterministic human review gate. It does not mutate persistent research state,
hypothesis packets, selected hypotheses, investigation plans, targets, reports,
or vulnerability status.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_UPDATE_KIND = "brain_chat_research_hypothesis_confidence_update_packet"
EXPECTED_UPDATE_STATUS = "ready-for-research-state-transition-review"
EXPECTED_GATE_KIND = "brain_chat_research_state_transition_review_gate"

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


def build_research_state_transition_review_gate(
    confidence_update_packet: dict[str, Any],
    source: str = "brain-chat-research-state-transition-review-gate",
) -> dict[str, Any]:
    update_packet = copy.deepcopy(confidence_update_packet)
    updates = _object_list(update_packet.get("confidence_updates"))

    source_findings = _source_findings(update_packet, updates)
    safety_findings = _unsafe_flag_findings(update_packet, "confidence_update_packet")
    candidate_findings = _candidate_findings(updates)

    status = _status(source_findings, safety_findings, candidate_findings, updates)
    ready = status == "ready-for-human-transition-decision"

    candidates = [
        _candidate_record(index, update, ready)
        for index, update in enumerate(updates, start=1)
    ]

    gate = {
        "kind": EXPECTED_GATE_KIND,
        "source": source,
        "target_name": _text(update_packet.get("target_name"), "unknown-target"),
        "gate_status": status,
        "summary": _summary(status, len(candidates)),
        "source_update_kind": _text(update_packet.get("kind")),
        "source_update_status": _text(update_packet.get("update_status")),
        "source_update_digest": _text(update_packet.get("update_digest")),
        "source_hypothesis_digest": _text(update_packet.get("source_hypothesis_digest")),
        "source_decision_digest": _text(update_packet.get("source_decision_digest")),
        "source_feedback_digest": _text(update_packet.get("source_feedback_digest")),
        "confidence_update_count": len(updates),
        "transition_candidate_count": len(candidates),
        "transition_review_ready": ready,
        "human_transition_decision_required": ready,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "transition_candidates": candidates,
        "source_findings": source_findings,
        "safety_findings": safety_findings,
        "candidate_findings": candidate_findings,
        "counts": {
            "confidence_updates": len(updates),
            "transition_candidates": len(candidates),
            "source_findings": len(source_findings),
            "safety_findings": len(safety_findings),
            "candidate_findings": len(candidate_findings),
            "high_findings": (
                len(_high(source_findings))
                + len(_high(safety_findings))
                + len(_high(candidate_findings))
            ),
        },
        "allowed_decisions": [
            "approve-transition-packet",
            "reject-transition",
            "request-changes",
            "defer-transition",
        ],
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not mutate persistent research state from this review gate.",
            "Do not directly update hypothesis confidence from this review gate.",
            "Do not mutate the source hypothesis packet.",
            "Do not alter selected hypotheses or investigation plans.",
            "Do not generate or execute commands.",
            "Do not interact with targets or networks.",
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
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    gate["gate_digest"] = _sha256(
        {
            "kind": gate["kind"],
            "target_name": gate["target_name"],
            "gate_status": gate["gate_status"],
            "source_update_digest": gate["source_update_digest"],
            "transition_candidates": gate["transition_candidates"],
        }
    )
    return gate


def build_review_gate_from_file(
    update_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    gate = build_research_state_transition_review_gate(
        load_json_object(update_file),
    )
    if json_output is not None:
        write_json(json_output, gate)
    return gate


def _source_findings(update_packet: dict[str, Any], updates: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if update_packet.get("kind") != EXPECTED_UPDATE_KIND:
        findings.append(_finding("source-schema", "high", "Invalid confidence update packet kind.", "update.kind", "Use a hypothesis confidence update packet."))

    if update_packet.get("update_status") != EXPECTED_UPDATE_STATUS:
        findings.append(_finding("source-status", "high", "Confidence update packet is not ready for transition review.", "update.update_status", "Resolve confidence update packet blockers first."))

    if update_packet.get("confidence_update_packet_ready") is not True:
        findings.append(_finding("source-readiness", "high", "Confidence update packet is not marked ready.", "update.confidence_update_packet_ready", "Use a ready confidence update packet."))

    if update_packet.get("research_state_transition_review_required") is not True:
        findings.append(_finding("source-readiness", "high", "Research-state transition review was not required by the update packet.", "update.research_state_transition_review_required", "Regenerate the confidence update packet."))

    if update_packet.get("research_state_transition_ready") is True:
        findings.append(_finding("source-safety", "high", "Source packet already marks research-state transition ready.", "update.research_state_transition_ready", "Use only pre-transition review packets."))

    if not updates:
        findings.append(_finding("source-content", "high", "No confidence updates were present.", "update.confidence_updates", "Build a confidence update packet with accepted updates."))

    expected_count = _int(update_packet.get("confidence_update_count"))
    if expected_count and expected_count != len(updates):
        findings.append(_finding("source-count", "medium", "Confidence update count does not match list length.", "update.confidence_update_count", "Regenerate the confidence update packet."))

    if not _text(update_packet.get("update_digest")):
        findings.append(_finding("source-digest", "medium", "Confidence update packet digest is missing.", "update.update_digest", "Regenerate the confidence update packet."))

    return findings


def _unsafe_flag_findings(data: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for flag in FALSE_FLAGS:
        if bool(data.get(flag)):
            findings.append(_finding("unsafe-flag", "high", f"Unsafe flag is true: {flag}.", f"{prefix}.{flag}", "Regenerate packet with all mutation/execution flags disabled."))

    if data.get("planning_only") is not True:
        findings.append(_finding("planning-only", "high", "Packet is not marked planning-only.", f"{prefix}.planning_only", "Use only planning-only packets."))

    execution_state = _text(data.get("execution_state"), "not_executed")
    if execution_state != "not_executed":
        findings.append(_finding("execution-state", "high", "Packet execution_state is not not_executed.", f"{prefix}.execution_state", "Use only non-executed planning artifacts."))

    return findings


def _candidate_findings(updates: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen_hypotheses: set[str] = set()
    seen_updates: set[str] = set()

    for item in updates:
        update_id = _text(item.get("update_id"))
        hypothesis_id = _text(item.get("hypothesis_id"))

        if not update_id:
            findings.append(_finding("candidate-schema", "high", "Confidence update is missing update_id.", "confidence_updates.update_id", "Regenerate the confidence update packet."))
        elif update_id in seen_updates:
            findings.append(_finding("candidate-coverage", "high", f"Duplicate confidence update ID: {update_id}.", update_id, "Resolve duplicate update IDs."))
        seen_updates.add(update_id)

        if not hypothesis_id:
            findings.append(_finding("candidate-schema", "high", f"Confidence update {update_id or '<missing>'} is missing hypothesis_id.", "confidence_updates.hypothesis_id", "Regenerate the confidence update packet."))
        elif hypothesis_id in seen_hypotheses:
            findings.append(_finding("candidate-coverage", "high", f"Multiple confidence updates target hypothesis {hypothesis_id}.", hypothesis_id, "Resolve duplicate hypothesis transitions before review."))
        seen_hypotheses.add(hypothesis_id)

        if not _text(item.get("current_confidence")):
            findings.append(_finding("confidence-schema", "high", f"Confidence update {update_id or '<missing>'} lacks current_confidence.", update_id, "Regenerate the confidence update packet."))

        if not _text(item.get("proposed_confidence")):
            findings.append(_finding("confidence-schema", "high", f"Confidence update {update_id or '<missing>'} lacks proposed_confidence.", update_id, "Regenerate the confidence update packet."))

        if item.get("effective_confidence_update_ready") is not True:
            findings.append(_finding("candidate-readiness", "high", f"Confidence update {update_id or '<missing>'} is not effectively ready.", update_id, "Use only accepted and ready confidence updates."))

        if item.get("research_state_transition_review_required") is not True:
            findings.append(_finding("candidate-readiness", "high", f"Confidence update {update_id or '<missing>'} does not require transition review.", update_id, "Regenerate the confidence update packet."))

        if not _text(item.get("update_digest")):
            findings.append(_finding("candidate-digest", "medium", f"Confidence update {update_id or '<missing>'} lacks update_digest.", update_id, "Regenerate the confidence update packet."))

        for flag in FALSE_FLAGS:
            if bool(item.get(flag)):
                findings.append(_finding("candidate-unsafe-flag", "high", f"Candidate unsafe flag is true: {flag}.", f"{update_id}.{flag}", "Use only fail-closed confidence update records."))

        if item.get("planning_only") is not True:
            findings.append(_finding("candidate-planning-only", "high", f"Confidence update {update_id or '<missing>'} is not planning-only.", update_id, "Use only planning-only update records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("candidate-execution-state", "high", f"Confidence update {update_id or '<missing>'} execution_state is not not_executed.", update_id, "Use only non-executed update records."))

    return findings


def _candidate_record(index: int, update: dict[str, Any], ready: bool) -> dict[str, Any]:
    record = {
        "transition_id": f"RST-{index:03d}",
        "source_update_id": _text(update.get("update_id")),
        "source_feedback_id": _text(update.get("feedback_id")),
        "hypothesis_id": _text(update.get("hypothesis_id")),
        "title": _text(update.get("title")),
        "proposed_state_change": "update-hypothesis-confidence",
        "current_confidence": _text(update.get("current_confidence")),
        "proposed_confidence": _text(update.get("proposed_confidence")),
        "categorical_confidence_change": bool(update.get("categorical_confidence_change")),
        "net_confidence_delta": _int(update.get("net_confidence_delta")),
        "observation_ids": _list_of_text(update.get("observation_ids")),
        "source_update_digest": _text(update.get("update_digest")),
        "review_decision": "pending-human-transition-decision",
        "human_review_required": ready,
        "transition_packet_required_after_approval": ready,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    record["transition_candidate_digest"] = _sha256(record)
    return record


def _status(
    source_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    candidate_findings: list[dict[str, str]],
    updates: list[dict[str, Any]],
) -> str:
    if _high(source_findings):
        return "blocked-invalid-confidence-update-packet"
    if _high(safety_findings):
        return "blocked-unsafe-source"
    if not updates:
        return "blocked-no-transition-candidates"
    if _high(candidate_findings):
        return "blocked-invalid-transition-candidates"
    return "ready-for-human-transition-decision"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-human-transition-decision":
        return f"{count} transition candidate(s) are ready for explicit human review before any state transition packet is created."
    if status == "blocked-invalid-confidence-update-packet":
        return "Transition review gate blocked because the source confidence update packet is invalid."
    if status == "blocked-unsafe-source":
        return "Transition review gate blocked because the source packet enables mutation or execution."
    if status == "blocked-no-transition-candidates":
        return "Transition review gate blocked because no transition candidates are present."
    if status == "blocked-invalid-transition-candidates":
        return "Transition review gate blocked because transition candidates are invalid or unsafe."
    return "Transition review gate is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-human-transition-decision":
        return [
            "Review proposed research-state transition candidates locally.",
            "Record an explicit human transition decision in a later decision artifact.",
            "Only after approval, build a separate state-transition packet.",
        ]
    return [
        "Resolve blocking findings before requesting human transition decision.",
        "Keep this gate local-only and non-mutating.",
    ]


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_of_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


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
