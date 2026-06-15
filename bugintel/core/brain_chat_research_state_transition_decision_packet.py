"""Human decision packet for research-state transition review gates.

This module validates a completed human decision template and creates a
local-only decision packet. It does not apply confidence updates or mutate
persistent research state.
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
EXPECTED_TEMPLATE_STATUS = "ready-for-human-transition-decision"
EXPECTED_PACKET_KIND = "brain_chat_research_state_transition_decision_packet"

FINAL_DECISIONS: tuple[str, ...] = (
    "approve-transition-packet",
    "reject-transition",
    "request-changes",
    "defer-transition",
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


def build_research_state_transition_decision_packet(
    review_gate: dict[str, Any],
    decision_template: dict[str, Any],
    source: str = "brain-chat-research-state-transition-decision-packet",
) -> dict[str, Any]:
    gate = copy.deepcopy(review_gate)
    template = copy.deepcopy(decision_template)
    candidates = _object_list(gate.get("transition_candidates"))
    decisions = _object_list(template.get("transition_decisions"))

    gate_findings = _gate_findings(gate, candidates)
    template_findings = _template_findings(gate, template, decisions)
    safety_findings = (
        _unsafe_flag_findings(gate, "review_gate")
        + _unsafe_flag_findings(template, "decision_template")
    )
    decision_findings = _decision_findings(candidates, decisions)

    approved = [
        _approved_transition_record(item)
        for item in decisions
        if item.get("decision") == "approve-transition-packet"
    ]

    status = _status(
        gate_findings,
        template_findings,
        safety_findings,
        decision_findings,
        decisions,
        approved,
    )
    complete = status in {
        "ready-for-research-state-transition-packet",
        "ready-no-research-state-transition-packet",
    }

    packet = {
        "kind": EXPECTED_PACKET_KIND,
        "source": source,
        "target_name": _text(gate.get("target_name"), _text(template.get("target_name"), "unknown-target")),
        "decision_status": status,
        "summary": _summary(status, len(approved), len(decisions)),
        "source_gate_kind": _text(gate.get("kind")),
        "source_gate_status": _text(gate.get("gate_status")),
        "source_gate_digest": _text(gate.get("gate_digest")),
        "source_template_kind": _text(template.get("kind")),
        "source_template_status": _text(template.get("template_status")),
        "source_template_digest": _text(template.get("template_digest")),
        "source_update_digest": _text(gate.get("source_update_digest"), _text(template.get("source_update_digest"))),
        "source_hypothesis_digest": _text(gate.get("source_hypothesis_digest"), _text(template.get("source_hypothesis_digest"))),
        "source_decision_digest": _text(gate.get("source_decision_digest"), _text(template.get("source_decision_digest"))),
        "source_feedback_digest": _text(gate.get("source_feedback_digest"), _text(template.get("source_feedback_digest"))),
        "transition_candidate_count": len(candidates),
        "transition_decision_count": len(decisions),
        "approved_transition_count": len(approved),
        "rejected_transition_count": _decision_count(decisions, "reject-transition"),
        "changes_requested_count": _decision_count(decisions, "request-changes"),
        "deferred_transition_count": _decision_count(decisions, "defer-transition"),
        "human_transition_decision_complete": complete,
        "human_transition_decision_required": False,
        "research_state_transition_packet_required": len(approved) > 0 and complete,
        "research_state_transition_packet_ready": len(approved) > 0 and complete,
        "research_state_transition_ready": False,
        "transition_decisions": decisions,
        "approved_transition_candidates": approved,
        "gate_findings": gate_findings,
        "template_findings": template_findings,
        "safety_findings": safety_findings,
        "decision_findings": decision_findings,
        "counts": {
            "transition_candidates": len(candidates),
            "transition_decisions": len(decisions),
            "approved_transitions": len(approved),
            "gate_findings": len(gate_findings),
            "template_findings": len(template_findings),
            "safety_findings": len(safety_findings),
            "decision_findings": len(decision_findings),
            "high_findings": (
                len(_high(gate_findings))
                + len(_high(template_findings))
                + len(_high(safety_findings))
                + len(_high(decision_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not mutate persistent research state from this decision packet.",
            "Do not directly update hypothesis confidence from this decision packet.",
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
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    packet["decision_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "decision_status": packet["decision_status"],
            "source_gate_digest": packet["source_gate_digest"],
            "source_template_digest": packet["source_template_digest"],
            "approved_transition_candidates": packet["approved_transition_candidates"],
            "transition_decisions": packet["transition_decisions"],
        }
    )
    return packet


def build_decision_packet_from_files(
    gate_file: str | Path,
    template_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_state_transition_decision_packet(
        load_json_object(gate_file),
        load_json_object(template_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _gate_findings(gate: dict[str, Any], candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if gate.get("kind") != EXPECTED_GATE_KIND:
        findings.append(_finding("gate-schema", "high", "Invalid review gate kind.", "gate.kind", "Use a research-state transition review gate."))

    if gate.get("gate_status") != EXPECTED_GATE_STATUS:
        findings.append(_finding("gate-status", "high", "Review gate is not ready for human transition decision.", "gate.gate_status", "Resolve review gate blockers first."))

    if gate.get("transition_review_ready") is not True:
        findings.append(_finding("gate-readiness", "high", "Review gate is not transition-review ready.", "gate.transition_review_ready", "Use a ready review gate."))

    if not candidates:
        findings.append(_finding("gate-content", "high", "No transition candidates are present.", "gate.transition_candidates", "Build a review gate with candidates."))

    if not _text(gate.get("gate_digest")):
        findings.append(_finding("gate-digest", "medium", "Review gate digest is missing.", "gate.gate_digest", "Regenerate the review gate."))

    return findings


def _template_findings(
    gate: dict[str, Any],
    template: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if template.get("kind") != EXPECTED_TEMPLATE_KIND:
        findings.append(_finding("template-schema", "high", "Invalid decision template kind.", "template.kind", "Use a research-state transition decision template."))

    if template.get("template_status") != EXPECTED_TEMPLATE_STATUS:
        findings.append(_finding("template-status", "high", "Decision template is not ready for human transition decision.", "template.template_status", "Resolve template blockers first."))

    if template.get("source_gate_digest") != gate.get("gate_digest"):
        findings.append(_finding("template-linkage", "high", "Decision template does not reference the source review gate digest.", "template.source_gate_digest", "Regenerate the template from the current review gate."))

    if template.get("human_transition_decision_required") is not True:
        findings.append(_finding("template-readiness", "high", "Template is not marked as requiring human transition decision.", "template.human_transition_decision_required", "Use an uncompleted ready template."))

    if not decisions:
        findings.append(_finding("template-content", "high", "No transition decisions are present.", "template.transition_decisions", "Complete a decision template with transition decisions."))

    expected_count = _int(template.get("transition_decision_count"))
    if expected_count and expected_count != len(decisions):
        findings.append(_finding("template-count", "medium", "Transition decision count does not match list length.", "template.transition_decision_count", "Regenerate the decision template."))

    if not _text(template.get("template_digest")):
        findings.append(_finding("template-digest", "medium", "Decision template digest is missing.", "template.template_digest", "Regenerate the decision template."))

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


def _decision_findings(
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    candidate_by_transition = {
        _text(item.get("transition_id")): item
        for item in candidates
        if _text(item.get("transition_id"))
    }
    seen: set[str] = set()

    for item in decisions:
        decision_id = _text(item.get("decision_id"), "<missing>")
        transition_id = _text(item.get("transition_id"))
        decision = _text(item.get("decision"))

        if not transition_id:
            findings.append(_finding("decision-schema", "high", f"Decision {decision_id} is missing transition_id.", decision_id, "Regenerate the decision template."))
            continue

        if transition_id in seen:
            findings.append(_finding("decision-coverage", "high", f"Duplicate decision for transition {transition_id}.", transition_id, "Resolve duplicate transition decisions."))
        seen.add(transition_id)

        candidate = candidate_by_transition.get(transition_id)
        if candidate is None:
            findings.append(_finding("decision-linkage", "high", f"Decision {decision_id} references an unknown transition candidate.", transition_id, "Regenerate the template from the current review gate."))
            continue

        if item.get("source_transition_candidate_digest") != candidate.get("transition_candidate_digest"):
            findings.append(_finding("decision-linkage", "high", f"Decision {decision_id} candidate digest mismatch.", transition_id, "Regenerate the template from the current review gate."))

        if decision not in FINAL_DECISIONS:
            findings.append(_finding("decision-value", "high", f"Decision {decision_id} is not final.", decision_id, "Choose approve-transition-packet, reject-transition, request-changes, or defer-transition."))

        if not _text(item.get("decision_reason")):
            findings.append(_finding("decision-reason", "high", f"Decision {decision_id} is missing decision_reason.", decision_id, "Provide a reason for the human transition decision."))

        if decision == "approve-transition-packet" and item.get("approved_for_state_transition_packet") is not True:
            findings.append(_finding("decision-approval", "high", f"Decision {decision_id} approves transition but is not marked approved_for_state_transition_packet.", decision_id, "Set approved_for_state_transition_packet=true for approved transitions."))

        if decision != "approve-transition-packet" and item.get("approved_for_state_transition_packet") is True:
            findings.append(_finding("decision-approval", "high", f"Decision {decision_id} is approved despite non-approval decision.", decision_id, "Only approve state-transition packet creation for approve-transition-packet decisions."))

        if decision == "request-changes" and not _list_of_text(item.get("requested_changes")):
            findings.append(_finding("decision-changes", "high", f"Decision {decision_id} requests changes but requested_changes is empty.", decision_id, "List requested changes."))

        for flag in FALSE_FLAGS:
            if bool(item.get(flag)):
                findings.append(_finding("decision-unsafe-flag", "high", f"Decision unsafe flag is true: {flag}.", f"{decision_id}.{flag}", "Keep decision records fail-closed."))

        if item.get("planning_only") is not True:
            findings.append(_finding("decision-planning-only", "high", f"Decision {decision_id} is not planning-only.", decision_id, "Use only planning-only decision records."))

        if _text(item.get("execution_state"), "not_executed") != "not_executed":
            findings.append(_finding("decision-execution-state", "high", f"Decision {decision_id} execution_state is not not_executed.", decision_id, "Use only non-executed decision records."))

    missing = sorted(set(candidate_by_transition) - seen)
    for transition_id in missing:
        findings.append(_finding("decision-coverage", "high", f"Missing decision for transition {transition_id}.", transition_id, "Complete all transition decisions."))

    return findings


def _approved_transition_record(decision: dict[str, Any]) -> dict[str, Any]:
    record = {
        "decision_id": _text(decision.get("decision_id")),
        "transition_id": _text(decision.get("transition_id")),
        "source_update_id": _text(decision.get("source_update_id")),
        "hypothesis_id": _text(decision.get("hypothesis_id")),
        "title": _text(decision.get("title")),
        "proposed_state_change": _text(decision.get("proposed_state_change")),
        "current_confidence": _text(decision.get("current_confidence")),
        "proposed_confidence": _text(decision.get("proposed_confidence")),
        "decision": _text(decision.get("decision")),
        "decision_reason": _text(decision.get("decision_reason")),
        "source_update_digest": _text(decision.get("source_update_digest")),
        "source_transition_candidate_digest": _text(decision.get("source_transition_candidate_digest")),
        "state_transition_packet_required": True,
        "research_state_transition_allowed": False,
        "confidence_update_allowed": False,
        "research_state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
    }
    record["approved_transition_digest"] = _sha256(record)
    return record


def _status(
    gate_findings: list[dict[str, str]],
    template_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    decisions: list[dict[str, Any]],
    approved: list[dict[str, Any]],
) -> str:
    if _high(gate_findings):
        return "blocked-invalid-transition-review-gate"
    if _high(template_findings):
        return "blocked-invalid-transition-decision-template"
    if _high(safety_findings):
        return "blocked-unsafe-transition-decision-source"
    if not decisions:
        return "blocked-no-transition-decisions"
    if _high(decision_findings):
        return "blocked-invalid-transition-decisions"
    if approved:
        return "ready-for-research-state-transition-packet"
    return "ready-no-research-state-transition-packet"


def _summary(status: str, approved_count: int, decision_count: int) -> str:
    if status == "ready-for-research-state-transition-packet":
        return f"{approved_count} of {decision_count} transition decision(s) approved for later state-transition packet creation."
    if status == "ready-no-research-state-transition-packet":
        return f"0 of {decision_count} transition decision(s) approved; no state-transition packet is required."
    if status == "blocked-invalid-transition-review-gate":
        return "Decision packet blocked because the source review gate is invalid."
    if status == "blocked-invalid-transition-decision-template":
        return "Decision packet blocked because the decision template is invalid."
    if status == "blocked-unsafe-transition-decision-source":
        return "Decision packet blocked because source artifacts enable mutation or execution."
    if status == "blocked-no-transition-decisions":
        return "Decision packet blocked because no transition decisions are present."
    if status == "blocked-invalid-transition-decisions":
        return "Decision packet blocked because transition decisions are incomplete or invalid."
    return "Decision packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-research-state-transition-packet":
        return [
            "Build a separate research-state transition packet from approved transitions.",
            "Keep later transition packet local-only until another explicit review gate approves persistence.",
        ]
    if status == "ready-no-research-state-transition-packet":
        return [
            "Record the completed decision packet.",
            "Return to research planning or address requested changes as needed.",
        ]
    return [
        "Resolve blocking findings before building any state-transition packet.",
        "Keep this decision packet local-only and non-mutating.",
    ]


def _decision_count(decisions: list[dict[str, Any]], value: str) -> int:
    return sum(1 for item in decisions if item.get("decision") == value)


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
