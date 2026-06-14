"""Proposed confidence update packet for accepted hypothesis feedback decisions.

This module converts an accepted human feedback decision packet into a local,
deterministic, reviewable confidence-update packet. It does not mutate hypothesis
packets, selected hypotheses, investigation plans, persistent research state,
targets, evidence, reports, or vulnerability status.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_HYPOTHESIS_KIND = "brain_chat_research_hypothesis_packet"
EXPECTED_HYPOTHESIS_STATUS = "ready-for-hypothesis-review"
EXPECTED_DECISION_KIND = "brain_chat_research_hypothesis_feedback_decision_packet"
EXPECTED_DECISION_STATUS = "ready-for-hypothesis-confidence-update-packet"
EXPECTED_UPDATE_KIND = "brain_chat_research_hypothesis_confidence_update_packet"

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


def build_research_hypothesis_confidence_update_packet(
    hypothesis_packet: dict[str, Any],
    decision_packet: dict[str, Any],
    source: str = "brain-chat-research-hypothesis-confidence-update-packet",
) -> dict[str, Any]:
    hypothesis = copy.deepcopy(hypothesis_packet)
    decision = copy.deepcopy(decision_packet)

    hypotheses = _object_list(hypothesis.get("hypotheses"))
    accepted_feedback = _object_list(decision.get("accepted_feedback"))
    hypothesis_map = {
        _text(item.get("hypothesis_id")): item
        for item in hypotheses
        if _text(item.get("hypothesis_id"))
    }

    hypothesis_findings = _hypothesis_findings(hypothesis, hypotheses)
    decision_findings = _decision_findings(decision, accepted_feedback)
    safety_findings = (
        _unsafe_flag_findings(hypothesis, "hypothesis")
        + _unsafe_flag_findings(decision, "decision")
    )
    consistency_findings = _consistency_findings(
        hypothesis,
        decision,
        accepted_feedback,
        hypothesis_map,
    )

    status = _status(
        hypothesis_findings=hypothesis_findings,
        decision_findings=decision_findings,
        safety_findings=safety_findings,
        consistency_findings=consistency_findings,
        accepted_feedback=accepted_feedback,
    )
    ready = status == "ready-for-research-state-transition-review"

    updates = [
        _update_record(index, feedback, hypothesis_map.get(_text(feedback.get("hypothesis_id"))), ready)
        for index, feedback in enumerate(accepted_feedback, start=1)
    ]

    packet = {
        "kind": EXPECTED_UPDATE_KIND,
        "source": source,
        "target_name": _text(hypothesis.get("target_name"), "unknown-target"),
        "update_status": status,
        "summary": _summary(status, len(updates)),
        "source_hypothesis_kind": _text(hypothesis.get("kind")),
        "source_hypothesis_status": _text(hypothesis.get("packet_status")),
        "source_hypothesis_digest": _sha256(
            {
                "kind": _text(hypothesis.get("kind")),
                "target_name": _text(hypothesis.get("target_name")),
                "packet_status": _text(hypothesis.get("packet_status")),
                "hypotheses": hypotheses,
            }
        ),
        "source_decision_kind": _text(decision.get("kind")),
        "source_decision_status": _text(decision.get("decision_status")),
        "source_decision_digest": _text(decision.get("decision_digest")),
        "source_feedback_digest": _text(decision.get("source_feedback_digest")),
        "hypothesis_count": len(hypotheses),
        "accepted_feedback_count": len(accepted_feedback),
        "confidence_update_count": len(updates),
        "confidence_update_packet_ready": ready,
        "research_state_transition_review_required": ready,
        "research_state_transition_ready": False,
        "confidence_updates": updates,
        "hypothesis_findings": hypothesis_findings,
        "decision_findings": decision_findings,
        "safety_findings": safety_findings,
        "consistency_findings": consistency_findings,
        "counts": {
            "hypotheses": len(hypotheses),
            "accepted_feedback": len(accepted_feedback),
            "confidence_updates": len(updates),
            "hypothesis_findings": len(hypothesis_findings),
            "decision_findings": len(decision_findings),
            "safety_findings": len(safety_findings),
            "consistency_findings": len(consistency_findings),
            "high_findings": (
                len(_high(hypothesis_findings))
                + len(_high(decision_findings))
                + len(_high(safety_findings))
                + len(_high(consistency_findings))
            ),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not mutate the source hypothesis packet.",
            "Do not directly update persistent research state from this packet.",
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

    packet["update_digest"] = _sha256(
        {
            "kind": packet["kind"],
            "target_name": packet["target_name"],
            "update_status": packet["update_status"],
            "source_hypothesis_digest": packet["source_hypothesis_digest"],
            "source_decision_digest": packet["source_decision_digest"],
            "confidence_updates": packet["confidence_updates"],
        }
    )
    return packet


def build_confidence_update_packet_from_files(
    hypothesis_file: str | Path,
    decision_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_hypothesis_confidence_update_packet(
        load_json_object(hypothesis_file),
        load_json_object(decision_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _hypothesis_findings(hypothesis: dict[str, Any], hypotheses: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if hypothesis.get("kind") != EXPECTED_HYPOTHESIS_KIND:
        findings.append(_finding("hypothesis-schema", "high", "Invalid hypothesis packet kind.", "hypothesis.kind", "Use a brain chat research hypothesis packet."))

    if hypothesis.get("packet_status") != EXPECTED_HYPOTHESIS_STATUS:
        findings.append(_finding("hypothesis-status", "high", "Hypothesis packet is not ready for hypothesis review.", "hypothesis.packet_status", "Resolve hypothesis packet gaps first."))

    if not hypotheses:
        findings.append(_finding("hypothesis-content", "high", "No hypotheses were present.", "hypothesis.hypotheses", "Regenerate the hypothesis packet."))

    expected_count = _int(hypothesis.get("hypothesis_count"))
    if expected_count and expected_count != len(hypotheses):
        findings.append(_finding("hypothesis-count", "medium", "Hypothesis count does not match hypothesis list length.", "hypothesis.hypothesis_count", "Regenerate the hypothesis packet."))

    return findings


def _decision_findings(decision: dict[str, Any], accepted_feedback: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if decision.get("kind") != EXPECTED_DECISION_KIND:
        findings.append(_finding("decision-schema", "high", "Invalid feedback decision packet kind.", "decision.kind", "Use a hypothesis feedback decision packet."))

    if decision.get("decision_status") != EXPECTED_DECISION_STATUS:
        findings.append(_finding("decision-status", "high", "Decision packet is not ready for confidence update packet generation.", "decision.decision_status", "Resolve rejected, deferred, changes-requested, missing, or unsafe decisions first."))

    if decision.get("hypothesis_confidence_update_packet_ready") is not True:
        findings.append(_finding("decision-readiness", "high", "Decision packet did not grant confidence update packet readiness.", "decision.hypothesis_confidence_update_packet_ready", "Only accepted and confirmed feedback decisions can continue."))

    if decision.get("effective_acceptance_granted") is not True:
        findings.append(_finding("decision-acceptance", "high", "Decision packet did not grant effective acceptance.", "decision.effective_acceptance_granted", "Require explicit human acceptance before building confidence updates."))

    if not accepted_feedback:
        findings.append(_finding("decision-content", "high", "No accepted feedback records were present.", "decision.accepted_feedback", "Accept at least one feedback proposal before building confidence updates."))

    expected_count = _int(decision.get("accepted_feedback_count"))
    if expected_count and expected_count != len(accepted_feedback):
        findings.append(_finding("decision-count", "medium", "Accepted feedback count does not match accepted feedback list length.", "decision.accepted_feedback_count", "Regenerate the decision packet."))

    if not _text(decision.get("decision_digest")):
        findings.append(_finding("decision-digest", "medium", "Decision packet digest is missing.", "decision.decision_digest", "Regenerate the decision packet."))

    return findings


def _unsafe_flag_findings(data: dict[str, Any], prefix: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for flag in FALSE_FLAGS:
        if bool(data.get(flag)):
            findings.append(_finding("unsafe-flag", "high", f"Unsafe flag is true: {flag}.", f"{prefix}.{flag}", "Regenerate packet with all mutation/execution flags disabled."))

    if data.get("planning_only") is not True:
        findings.append(_finding("planning-only", "high", "Packet is not marked planning-only.", f"{prefix}.planning_only", "Regenerate packet as planning-only."))

    execution_state = _text(data.get("execution_state"), "not_executed")
    if execution_state != "not_executed":
        findings.append(_finding("execution-state", "high", "Packet execution_state is not not_executed.", f"{prefix}.execution_state", "Use only non-executed planning artifacts."))

    return findings


def _consistency_findings(
    hypothesis: dict[str, Any],
    decision: dict[str, Any],
    accepted_feedback: list[dict[str, Any]],
    hypothesis_map: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if _text(hypothesis.get("target_name")) != _text(decision.get("target_name")):
        findings.append(_finding("target-consistency", "high", "Hypothesis and decision packets target different names.", "target_name", "Use packets from the same target."))

    seen: set[str] = set()
    for item in accepted_feedback:
        feedback_id = _text(item.get("feedback_id"))
        hypothesis_id = _text(item.get("hypothesis_id"))

        if not feedback_id:
            findings.append(_finding("feedback-schema", "high", "Accepted feedback is missing feedback_id.", "accepted_feedback.feedback_id", "Regenerate the decision packet."))

        if not hypothesis_id:
            findings.append(_finding("feedback-schema", "high", f"Accepted feedback {feedback_id or '<missing>'} is missing hypothesis_id.", "accepted_feedback.hypothesis_id", "Regenerate the decision packet."))
            continue

        if hypothesis_id in seen:
            findings.append(_finding("update-coverage", "high", f"Multiple accepted feedback records target hypothesis {hypothesis_id}.", hypothesis_id, "Merge or resolve duplicate confidence proposals before generating an update packet."))
        seen.add(hypothesis_id)

        hypothesis_item = hypothesis_map.get(hypothesis_id)
        if hypothesis_item is None:
            findings.append(_finding("update-coverage", "high", f"Accepted feedback references missing hypothesis {hypothesis_id}.", hypothesis_id, "Use a matching source hypothesis packet."))

        if item.get("decision") != "accepted":
            findings.append(_finding("decision-consistency", "high", f"Accepted feedback list contains a non-accepted decision for {feedback_id}.", feedback_id, "Regenerate the decision packet."))

        if item.get("accepted_proposed_confidence") is not True:
            findings.append(_finding("decision-confirmation", "high", f"Accepted feedback {feedback_id} lacks explicit proposed confidence confirmation.", feedback_id, "Require accepted_proposed_confidence=true."))

        if item.get("effective_confidence_update_granted") is not True:
            findings.append(_finding("decision-effectiveness", "high", f"Accepted feedback {feedback_id} did not grant an effective confidence update.", feedback_id, "Regenerate the decision packet from accepted decisions."))

        if item.get("confidence_update_packet_required") is not True:
            findings.append(_finding("decision-effectiveness", "high", f"Accepted feedback {feedback_id} does not require a confidence update packet.", feedback_id, "Regenerate the decision packet."))

        proposed = _text(item.get("proposed_confidence"))
        if not proposed:
            findings.append(_finding("confidence-schema", "high", f"Accepted feedback {feedback_id} lacks proposed_confidence.", feedback_id, "Regenerate feedback with proposed confidence."))

        if hypothesis_item is not None:
            current = _text(hypothesis_item.get("confidence"))
            decision_current = _text(item.get("current_confidence"))
            if current != decision_current:
                findings.append(_finding("confidence-consistency", "high", f"Accepted feedback {feedback_id} current confidence is stale.", hypothesis_id, "Regenerate feedback against the current hypothesis packet."))

    return findings


def _update_record(index: int, feedback: dict[str, Any], hypothesis: dict[str, Any] | None, effective: bool) -> dict[str, Any]:
    hypothesis_id = _text(feedback.get("hypothesis_id"))
    current_confidence = _text(hypothesis.get("confidence") if hypothesis else feedback.get("current_confidence"))
    proposed_confidence = _text(feedback.get("proposed_confidence"))

    record = {
        "update_id": f"HCU-{index:03d}",
        "feedback_id": _text(feedback.get("feedback_id")),
        "hypothesis_id": hypothesis_id,
        "title": _text((hypothesis or {}).get("title"), _text(feedback.get("title"))),
        "current_confidence": current_confidence,
        "proposed_confidence": proposed_confidence,
        "decision_current_confidence": _text(feedback.get("current_confidence")),
        "categorical_confidence_change": current_confidence != proposed_confidence,
        "net_confidence_delta": _int(feedback.get("net_confidence_delta")),
        "proposed_disposition": _text(feedback.get("proposed_disposition")),
        "observation_ids": _list_of_text(feedback.get("observation_ids")),
        "source_feedback_id": _text(feedback.get("feedback_id")),
        "source_proposal_digest": _text(feedback.get("proposal_digest")),
        "source_decision_digest": _text(feedback.get("decision_digest")),
        "effective_confidence_update_ready": effective,
        "research_state_transition_review_required": effective,
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
    record["update_digest"] = _sha256(record)
    return record


def _status(
    *,
    hypothesis_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    consistency_findings: list[dict[str, str]],
    accepted_feedback: list[dict[str, Any]],
) -> str:
    if _high(hypothesis_findings):
        return "blocked-invalid-hypothesis-packet"
    if _high(decision_findings):
        return "blocked-invalid-decision-packet"
    if _high(safety_findings):
        return "blocked-unsafe-source"
    if not accepted_feedback:
        return "blocked-no-accepted-feedback"
    if _high(consistency_findings):
        return "blocked-invalid-confidence-update"
    return "ready-for-research-state-transition-review"


def _summary(status: str, update_count: int) -> str:
    if status == "ready-for-research-state-transition-review":
        return f"{update_count} proposed confidence update(s) are ready for a separate research-state transition review."
    if status == "blocked-invalid-hypothesis-packet":
        return "Confidence update packet blocked because the source hypothesis packet is invalid."
    if status == "blocked-invalid-decision-packet":
        return "Confidence update packet blocked because the feedback decision packet is invalid or not accepted."
    if status == "blocked-unsafe-source":
        return "Confidence update packet blocked because a source packet enables mutation or execution."
    if status == "blocked-no-accepted-feedback":
        return "Confidence update packet blocked because there are no accepted feedback records."
    if status == "blocked-invalid-confidence-update":
        return "Confidence update packet blocked because accepted feedback is stale or inconsistent."
    return "Confidence update packet is blocked."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-research-state-transition-review":
        return [
            "Review proposed confidence updates locally.",
            "Build a separate research-state transition review gate.",
            "Do not apply updates until the transition review gate explicitly allows a later state packet.",
        ]
    return [
        "Resolve blocking findings before building a transition review gate.",
        "Keep this packet local-only and non-mutating.",
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
