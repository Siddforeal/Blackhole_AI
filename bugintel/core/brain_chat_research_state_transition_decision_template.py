"""Human decision template for research-state transition review gates.

This module creates a local-only human decision template from a research-state
transition review gate. It does not approve, apply, or mutate persistent
research state.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_GATE_KIND = "brain_chat_research_state_transition_review_gate"
EXPECTED_GATE_STATUS = "ready-for-human-transition-decision"
EXPECTED_TEMPLATE_KIND = "brain_chat_research_state_transition_decision_template"

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


def build_research_state_transition_decision_template(
    review_gate: dict[str, Any],
    source: str = "brain-chat-research-state-transition-decision-template",
) -> dict[str, Any]:
    gate = copy.deepcopy(review_gate)
    candidates = _object_list(gate.get("transition_candidates"))

    gate_findings = _gate_findings(gate, candidates)
    safety_findings = _unsafe_flag_findings(gate, "review_gate")
    status = _status(gate_findings, safety_findings, candidates)
    ready = status == "ready-for-human-transition-decision"

    decisions = [
        _decision_template_record(index, candidate, ready)
        for index, candidate in enumerate(candidates, start=1)
    ]

    template = {
        "kind": EXPECTED_TEMPLATE_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), "unknown-target"),
        "template_status": status,
        "summary": _summary(status, len(decisions)),
        "source_gate_kind": _text(gate.get("kind")),
        "source_gate_status": _text(gate.get("gate_status")),
        "source_gate_digest": _text(gate.get("gate_digest")),
        "source_update_digest": _text(gate.get("source_update_digest")),
        "source_hypothesis_digest": _text(gate.get("source_hypothesis_digest")),
        "source_decision_digest": _text(gate.get("source_decision_digest")),
        "source_feedback_digest": _text(gate.get("source_feedback_digest")),
        "transition_candidate_count": len(candidates),
        "transition_decision_count": len(decisions),
        "human_transition_decision_required": ready,
        "human_transition_decision_complete": False,
        "research_state_transition_packet_ready": False,
        "research_state_transition_ready": False,
        "allowed_decisions": [
            "approve-transition-packet",
            "reject-transition",
            "request-changes",
            "defer-transition",
        ],
        "decision_instructions": [
            "Review each transition candidate against the supporting evidence and scope.",
            "Set exactly one allowed decision for each pending transition decision.",
            "Provide a reason for every decision.",
            "Do not edit source candidate digests or source gate digests.",
            "This template does not apply confidence updates or mutate persistent state.",
        ],
        "transition_decisions": decisions,
        "gate_findings": gate_findings,
        "safety_findings": safety_findings,
        "counts": {
            "transition_candidates": len(candidates),
            "transition_decisions": len(decisions),
            "gate_findings": len(gate_findings),
            "safety_findings": len(safety_findings),
            "high_findings": len(_high(gate_findings)) + len(_high(safety_findings)),
        },
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

    template["template_digest"] = _sha256(
        {
            "kind": template["kind"],
            "target_name": template["target_name"],
            "template_status": template["template_status"],
            "source_gate_digest": template["source_gate_digest"],
            "transition_decisions": template["transition_decisions"],
        }
    )
    return template


def build_decision_template_from_file(
    gate_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    template = build_research_state_transition_decision_template(
        load_json_object(gate_file),
    )
    if json_output is not None:
        write_json(json_output, template)
    return template


def _gate_findings(gate: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("gate-schema", "high", "Invalid review gate kind.", "gate.kind", "Use a research-state transition review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("gate-status", "high", "Review gate is not ready for human transition decision.", "gate.gate_status", "Resolve review gate blockers first."))

    if gate.get("transition_review_ready") is not True:
        findings.append(_finding("gate-readiness", "high", "Review gate is not transition-review ready.", "gate.transition_review_ready", "Use a ready review gate."))

    if gate.get("human_transition_decision_required") is not True:
        findings.append(_finding("gate-readiness", "high", "Review gate does not require human transition decision.", "gate.human_transition_decision_required", "Regenerate the review gate."))

    if gate.get("research_state_transition_ready") is True:
        findings.append(_finding("gate-safety", "high", "Review gate already marks research-state transition ready.", "gate.research_state_transition_ready", "Use only pre-transition review gates."))

    if gate.get("research_state_transition_packet_ready") is True:
        findings.append(_finding("gate-safety", "high", "Review gate already marks state-transition packet ready.", "gate.research_state_transition_packet_ready", "Use only human-decision-required gates."))

    if not candidates:
        findings.append(_finding("gate-content", "high", "No transition candidates are present.", "gate.transition_candidates", "Build a review gate with transition candidates."))

    expected_count = _int(gate.get("transition_candidate_count"))
    if expected_count and expected_count != len(candidates):
        findings.append(_finding("gate-count", "medium", "Transition candidate count does not match list length.", "gate.transition_candidate_count", "Regenerate the review gate."))

    if not _text(gate.get("gate_digest")):
        findings.append(_finding("gate-digest", "medium", "Review gate digest is missing.", "gate.gate_digest", "Regenerate the review gate."))

    return findings


def _unsafe_flag_findings(data: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for flag in FALSE_FLAGS:
        if bool(data.get(flag)):
            findings.append(_finding("unsafe-flag", "high", f"Unsafe flag is true: {flag}.", f"{prefix}.{flag}", "Regenerate with all mutation and execution flags disabled."))

    if data.get("planning_only") is not True:
        findings.append(_finding("planning-only", "high", "Artifact is not marked planning-only.", f"{prefix}.planning_only", "Use only planning-only artifacts."))

    if _text(data.get("execution_state"), "not_executed") != "not_executed":
        findings.append(_finding("execution-state", "high", "Artifact execution_state is not not_executed.", f"{prefix}.execution_state", "Use only non-executed planning artifacts."))

    return findings


def _decision_template_record(index: int, candidate: dict[str, Any], ready: bool) -> dict[str, Any]:
    record = {
        "decision_id": f"RSTD-{index:03d}",
        "transition_id": _text(candidate.get("transition_id")),
        "source_update_id": _text(candidate.get("source_update_id")),
        "hypothesis_id": _text(candidate.get("hypothesis_id")),
        "title": _text(candidate.get("title")),
        "proposed_state_change": _text(candidate.get("proposed_state_change")),
        "current_confidence": _text(candidate.get("current_confidence")),
        "proposed_confidence": _text(candidate.get("proposed_confidence")),
        "source_update_digest": _text(candidate.get("source_update_digest")),
        "source_transition_candidate_digest": _text(candidate.get("transition_candidate_digest")),
        "decision": "pending-human-transition-decision" if ready else "blocked",
        "decision_reason": "",
        "requested_changes": [],
        "human_operator": "",
        "human_reviewed_at": "",
        "approved_for_state_transition_packet": False,
        "state_transition_packet_required": False,
        "human_review_required": ready,
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
    record["decision_template_digest"] = _sha256(record)
    return record


def _status(
    gate_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    candidates: list[dict[str, Any]],
) -> str:
    if _high(gate_findings):
        return "blocked-invalid-transition-review-gate"
    if _high(safety_findings):
        return "blocked-unsafe-review-gate"
    if not candidates:
        return "blocked-no-transition-candidates"
    return "ready-for-human-transition-decision"


def _summary(status: str, count: int) -> str:
    if status == "ready-for-human-transition-decision":
        return f"{count} transition decision(s) require explicit human completion."
    if status == "blocked-invalid-transition-review-gate":
        return "Decision template blocked because the source review gate is invalid."
    if status == "blocked-unsafe-review-gate":
        return "Decision template blocked because the source review gate enables mutation or execution."
    if status == "blocked-no-transition-candidates":
        return "Decision template blocked because no transition candidates are present."
    return "Decision template is blocked."


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
