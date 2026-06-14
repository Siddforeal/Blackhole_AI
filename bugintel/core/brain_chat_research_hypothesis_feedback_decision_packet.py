"""Human decision packet for hypothesis feedback proposals.

Records explicit human decisions for reviewed hypothesis feedback proposals.
It does not mutate confidence, selection, investigation plans, research state,
targets, reports, or vulnerability status.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


EXPECTED_FEEDBACK_KIND = "brain_chat_research_hypothesis_feedback_packet"
EXPECTED_FEEDBACK_STATUS = "ready-for-hypothesis-feedback-review"
EXPECTED_DECISION_INPUT_KIND = (
    "brain_chat_research_hypothesis_feedback_decision_input"
)

VALID_DECISIONS: tuple[str, ...] = (
    "accepted",
    "rejected",
    "changes-requested",
    "deferred",
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


def build_research_hypothesis_feedback_decision_packet(
    feedback_packet: dict[str, Any],
    decision_input: dict[str, Any],
    source: str = "brain-chat-research-hypothesis-feedback-decision-packet",
) -> dict[str, Any]:
    feedback = copy.deepcopy(feedback_packet)
    decision = copy.deepcopy(decision_input)
    proposals = _object_list(feedback.get("feedback_proposals"))

    source_findings = _source_findings(feedback, proposals)
    decision_findings = _decision_findings(feedback, decision, proposals)
    decision_map = _decision_map(decision)

    preliminary = [
        _record(
            proposal,
            decision_map.get(_text(proposal.get("feedback_id"))),
            effective=False,
        )
        for proposal in proposals
    ]
    counts = _counts(preliminary)
    status = _status(source_findings, decision_findings, counts)
    update_ready = status == "ready-for-hypothesis-confidence-update-packet"

    records = [
        _record(
            proposal,
            decision_map.get(_text(proposal.get("feedback_id"))),
            effective=update_ready,
        )
        for proposal in proposals
    ]
    counts = _counts(records)

    accepted = [r for r in records if r["decision"] == "accepted"]
    rejected = [r for r in records if r["decision"] == "rejected"]
    changes = [r for r in records if r["decision"] == "changes-requested"]
    deferred = [r for r in records if r["decision"] == "deferred"]
    missing = [r["feedback_id"] for r in records if r["decision"] == "missing"]

    packet = {
        "kind": "brain_chat_research_hypothesis_feedback_decision_packet",
        "source": source,
        "target_name": _text(feedback.get("target_name"), "unknown-target"),
        "decision_status": status,
        "summary": _summary(status, counts),
        "reviewer": _text(decision.get("reviewer")),
        "overall_reason": _text(decision.get("overall_reason")),
        "source_feedback_kind": _text(feedback.get("kind")),
        "source_feedback_status": _text(feedback.get("packet_status")),
        "source_feedback_ready": bool(
            feedback.get("hypothesis_feedback_review_ready")
        ),
        "source_feedback_digest": _text(feedback.get("feedback_digest")),
        "source_decision_input_kind": _text(decision.get("kind")),
        "feedback_proposal_count": len(proposals),
        "decision_count": len(_object_list(decision.get("decisions"))),
        "decision_ready": not _high(source_findings) and not _high(decision_findings),
        "hypothesis_confidence_update_packet_ready": update_ready,
        "effective_acceptance_granted": bool(accepted)
        and update_ready
        and all(r["effective_confidence_update_granted"] for r in accepted),
        "confidence_update_ready": False,
        "selection_update_ready": False,
        "investigation_plan_update_ready": False,
        "research_state_transition_ready": False,
        "accepted_feedback_count": counts["accepted"],
        "rejected_feedback_count": counts["rejected"],
        "changes_requested_feedback_count": counts["changes-requested"],
        "deferred_feedback_count": counts["deferred"],
        "missing_decision_count": counts["missing"],
        "feedback_decisions": records,
        "accepted_feedback": accepted,
        "rejected_feedback": rejected,
        "changes_requested_feedback": changes,
        "deferred_feedback": deferred,
        "unresolved_feedback_ids": missing,
        "source_findings": source_findings,
        "decision_findings": decision_findings,
        "counts": {
            "feedback_proposals": len(proposals),
            "feedback_decisions": len(records),
            "accepted": counts["accepted"],
            "rejected": counts["rejected"],
            "changes_requested": counts["changes-requested"],
            "deferred": counts["deferred"],
            "missing": counts["missing"],
            "source_findings": len(source_findings),
            "decision_findings": len(decision_findings),
            "high_findings": len(_high(source_findings)) + len(_high(decision_findings)),
        },
        "allowed_next_steps": _allowed_next_steps(status),
        "rejected_next_steps": [
            "Do not directly update hypothesis confidence from this packet.",
            "Do not mutate the source hypothesis packet.",
            "Do not reorder selected hypotheses.",
            "Do not alter investigation plans or approved actions.",
            "Do not mutate persistent research state.",
            "Do not generate or execute commands.",
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
            "source_feedback_digest": packet["source_feedback_digest"],
            "reviewer": packet["reviewer"],
            "overall_reason": packet["overall_reason"],
            "decision_status": packet["decision_status"],
            "feedback_decisions": packet["feedback_decisions"],
        }
    )
    return packet


def build_decision_packet_from_files(
    feedback_file: str | Path,
    decision_file: str | Path,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    packet = build_research_hypothesis_feedback_decision_packet(
        load_json_object(feedback_file),
        load_json_object(decision_file),
    )
    if json_output is not None:
        write_json(json_output, packet)
    return packet


def _source_findings(feedback: dict[str, Any], proposals: list[dict[str, Any]]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if feedback.get("kind") != EXPECTED_FEEDBACK_KIND:
        findings.append(_finding("source-schema", "high", "Invalid feedback packet kind.", "feedback.kind", "Use a hypothesis feedback packet."))

    if _text(feedback.get("packet_status")) != EXPECTED_FEEDBACK_STATUS:
        findings.append(_finding("source-readiness", "high", "Feedback packet is not review-ready.", "feedback.packet_status", "Resolve feedback blockers first."))

    if not bool(feedback.get("hypothesis_feedback_review_ready")):
        findings.append(_finding("source-readiness", "high", "Feedback review-ready flag is false.", "feedback.hypothesis_feedback_review_ready", "Regenerate a ready feedback packet."))

    if _int(feedback.get("feedback_proposal_count")) != len(proposals):
        findings.append(_finding("source-integrity", "high", "Feedback proposal count mismatch.", "feedback.feedback_proposal_count", "Regenerate the feedback packet."))

    seen: set[str] = set()
    for index, proposal in enumerate(proposals):
        subject = f"feedback.feedback_proposals[{index}]"
        feedback_id = _text(proposal.get("feedback_id"))
        if not feedback_id:
            findings.append(_finding("source-schema", "high", "Feedback proposal missing feedback_id.", subject, "Regenerate the feedback packet."))
            continue
        if feedback_id in seen:
            findings.append(_finding("source-integrity", "high", f"Duplicate feedback_id: {feedback_id}.", subject, "Regenerate the feedback packet."))
        seen.add(feedback_id)

        if bool(proposal.get("confidence_mutation_allowed")):
            findings.append(_finding("source-safety", "high", f"Proposal {feedback_id} allows confidence mutation.", f"{subject}.confidence_mutation_allowed", "Block the unsafe feedback packet."))

        if not bool(proposal.get("human_review_required")):
            findings.append(_finding("source-safety", "high", f"Proposal {feedback_id} lacks human review requirement.", f"{subject}.human_review_required", "Regenerate the feedback packet."))

    for field in FALSE_FLAGS:
        if bool(feedback.get(field)):
            findings.append(_finding("source-safety", "high", f"Unsafe feedback flag is true: {field}.", f"feedback.{field}", "Block the unsafe feedback packet."))

    return findings


def _decision_findings(
    feedback: dict[str, Any],
    decision: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    proposal_ids = {
        _text(item.get("feedback_id"))
        for item in proposals
        if _text(item.get("feedback_id"))
    }

    if decision.get("kind") != EXPECTED_DECISION_INPUT_KIND:
        findings.append(_finding("decision-schema", "high", "Invalid decision input kind.", "decision.kind", "Use the generated decision template."))

    if _text(feedback.get("target_name")) != _text(decision.get("target_name")):
        findings.append(_finding("decision-consistency", "high", "Decision target does not match feedback target.", "decision.target_name", "Use the matching decision template."))

    if _text(feedback.get("feedback_digest")) != _text(decision.get("source_feedback_digest")):
        findings.append(_finding("decision-consistency", "high", "Decision references a different feedback digest.", "decision.source_feedback_digest", "Regenerate the decision template."))

    if not _text(decision.get("reviewer")):
        findings.append(_finding("decision-schema", "high", "reviewer must not be empty.", "decision.reviewer", "Record the human reviewer."))

    decisions = decision.get("decisions")
    if not isinstance(decisions, list):
        findings.append(_finding("decision-schema", "high", "decisions must be a list.", "decision.decisions", "Use the generated decision template."))
        decisions = []

    seen: set[str] = set()
    for index, item in enumerate(decisions):
        subject = f"decision.decisions[{index}]"
        if not isinstance(item, dict):
            findings.append(_finding("decision-schema", "high", "Decision item must be an object.", subject, "Use a structured decision item."))
            continue

        feedback_id = _text(item.get("feedback_id"))
        if not feedback_id:
            findings.append(_finding("decision-schema", "high", "Decision missing feedback_id.", subject, "Associate decision with a feedback proposal."))
            continue

        if feedback_id in seen:
            findings.append(_finding("decision-schema", "high", f"Duplicate decision for feedback_id: {feedback_id}.", subject, "Keep one decision per feedback proposal."))
        seen.add(feedback_id)

        if feedback_id not in proposal_ids:
            findings.append(_finding("decision-consistency", "high", f"Unknown feedback_id: {feedback_id}.", subject, "Remove unknown feedback decisions."))

        normalized = _normalize_decision(_text(item.get("decision")))
        if normalized not in VALID_DECISIONS:
            findings.append(_finding("decision-schema", "high", f"Invalid decision for {feedback_id}.", subject, "Use accepted, rejected, changes-requested, or deferred."))

        if not _text(item.get("reason")):
            findings.append(_finding("decision-quality", "medium", f"Decision {feedback_id} is missing a reason.", subject, "Record a rationale."))

        if normalized == "accepted" and not bool(item.get("accepted_proposed_confidence")):
            findings.append(_finding("decision-confirmation", "high", f"Accepted decision {feedback_id} did not confirm proposed confidence.", subject, "Set accepted_proposed_confidence true or change decision."))

    for feedback_id in sorted(proposal_ids - seen):
        findings.append(_finding("decision-coverage", "high", f"Missing decision for feedback_id: {feedback_id}.", "decision.decisions", "Decide every feedback proposal exactly once."))

    if not bool(decision.get("planning_only")):
        findings.append(_finding("decision-safety", "high", "Decision input must remain planning_only.", "decision.planning_only", "Use a planning-only decision input."))

    if _text(decision.get("execution_state")) != "not_executed":
        findings.append(_finding("decision-safety", "high", "Decision execution_state must be not_executed.", "decision.execution_state", "Reset execution_state."))

    for field in FALSE_FLAGS:
        if bool(decision.get(field)):
            findings.append(_finding("decision-safety", "high", f"Unsafe decision flag is true: {field}.", f"decision.{field}", "Block the unsafe decision input."))

    return findings


def _decision_map(decision: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        _text(item.get("feedback_id")): item
        for item in _object_list(decision.get("decisions"))
        if _text(item.get("feedback_id"))
    }


def _record(proposal: dict[str, Any], decision: dict[str, Any] | None, effective: bool) -> dict[str, Any]:
    normalized = _normalize_decision(_text(decision.get("decision") if decision else ""))
    if normalized not in VALID_DECISIONS:
        normalized = "missing"

    confirmed = bool(decision.get("accepted_proposed_confidence") if decision else False)
    effective_update = effective and normalized == "accepted" and confirmed

    record = {
        "feedback_id": _text(proposal.get("feedback_id")),
        "hypothesis_id": _text(proposal.get("hypothesis_id")),
        "title": _text(proposal.get("title")),
        "current_confidence": _text(proposal.get("current_confidence")),
        "proposed_confidence": _text(proposal.get("proposed_confidence")),
        "categorical_confidence_change": bool(proposal.get("categorical_confidence_change")),
        "net_confidence_delta": _int(proposal.get("net_confidence_delta")),
        "proposed_disposition": _text(proposal.get("proposed_disposition")),
        "observation_ids": _list_of_text(proposal.get("observation_ids")),
        "proposal_digest": _text(proposal.get("proposal_digest")),
        "decision": normalized,
        "decision_reason": _text(decision.get("reason") if decision else ""),
        "accepted_proposed_confidence": confirmed,
        "effective_confidence_update_granted": effective_update,
        "confidence_update_packet_required": effective_update,
        "confidence_update_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "research_state_mutation_allowed": False,
        "planning_only": True,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
    }

    record["decision_digest"] = _sha256(record)
    return record


def _counts(records: list[dict[str, Any]]) -> dict[str, int]:
    result = {key: 0 for key in (*VALID_DECISIONS, "missing")}
    for item in records:
        decision = _text(item.get("decision"))
        result[decision if decision in result else "missing"] += 1
    return result


def _status(
    source_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    counts: dict[str, int],
) -> str:
    if any(f["severity"] == "high" and f["category"] == "source-safety" for f in source_findings):
        return "blocked-unsafe-source"
    if _high(source_findings):
        return "blocked-invalid-source"
    if any(f["severity"] == "high" and f["category"] == "decision-safety" for f in decision_findings):
        return "blocked-unsafe-decisions"
    if _high(decision_findings) or counts["missing"]:
        return "blocked-invalid-decisions"
    if counts["changes-requested"]:
        return "changes-requested"
    if counts["accepted"]:
        return "ready-for-hypothesis-confidence-update-packet"
    if counts["deferred"]:
        return "deferred"
    return "rejected"


def _summary(status: str, counts: dict[str, int]) -> str:
    if status == "ready-for-hypothesis-confidence-update-packet":
        return f"{counts['accepted']} accepted feedback decision(s) are ready for a separate confidence update packet. No confidence was mutated."
    if status == "changes-requested":
        return "Human review requested changes. No confidence update packet is ready."
    if status == "rejected":
        return "Human review rejected all feedback. No confidence update packet is ready."
    if status == "deferred":
        return "Human review deferred feedback. No confidence update packet is ready."
    return f"Hypothesis feedback decision packet is blocked: {status}."


def _allowed_next_steps(status: str) -> list[str]:
    if status == "ready-for-hypothesis-confidence-update-packet":
        return [
            "Build a separate confidence update packet from accepted feedback decisions.",
            "Preserve feedback, decision, proposal, and observation digests.",
            "Keep persistent state mutation blocked until a later transition gate.",
        ]
    if status == "changes-requested":
        return ["Revise feedback or observations before rebuilding the decision packet."]
    if status in {"deferred", "rejected"}:
        return ["Keep source hypotheses and research state unchanged."]
    return ["Resolve blockers before continuing."]


def _high(findings: list[dict[str, str]]) -> list[dict[str, str]]:
    return [item for item in findings if item.get("severity") == "high"]


def _normalize_decision(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-").replace(" ", "-")
    aliases = {
        "accept": "accepted",
        "approve": "accepted",
        "approved": "accepted",
        "reject": "rejected",
        "change-requested": "changes-requested",
        "changes-request": "changes-requested",
        "defer": "deferred",
    }
    return aliases.get(normalized, normalized)


def _finding(category: str, severity: str, message: str, subject: str, required_action: str) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "subject": subject,
        "required_action": required_action,
    }


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
    return text or default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    return 0


def _sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "EXPECTED_DECISION_INPUT_KIND",
    "EXPECTED_FEEDBACK_KIND",
    "EXPECTED_FEEDBACK_STATUS",
    "VALID_DECISIONS",
    "build_decision_packet_from_files",
    "build_research_hypothesis_feedback_decision_packet",
    "load_json_object",
    "write_json",
]
