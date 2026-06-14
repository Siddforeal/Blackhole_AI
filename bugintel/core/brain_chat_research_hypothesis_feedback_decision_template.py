"""Human decision template for hypothesis feedback proposals.

This module converts a ready hypothesis feedback packet into a local
human-fillable decision input template.

It does not accept, reject, apply, or mutate hypothesis confidence.
It does not mutate selection, investigation plans, research state,
targets, reports, or vulnerability status.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


EXPECTED_FEEDBACK_KIND = "brain_chat_research_hypothesis_feedback_packet"
EXPECTED_FEEDBACK_STATUS = "ready-for-hypothesis-feedback-review"
EXPECTED_TEMPLATE_KIND = "brain_chat_research_hypothesis_feedback_decision_input"

DEFAULT_DECISION = "deferred"

SAFETY_FALSE_FLAGS: tuple[str, ...] = (
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
    """Load a JSON object from disk."""
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {source}")
    return value


def write_json(path: str | Path, value: dict[str, Any]) -> None:
    """Write deterministic JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_research_hypothesis_feedback_decision_template(
    feedback_packet: dict[str, Any],
) -> dict[str, Any]:
    """Build a local human decision template for feedback proposals."""

    source = copy.deepcopy(feedback_packet)
    proposals = _object_list(source.get("feedback_proposals"))

    decisions = [
        _decision_template_item(proposal)
        for proposal in proposals
        if _text(proposal.get("feedback_id"))
    ]

    template = {
        "kind": EXPECTED_TEMPLATE_KIND,
        "target_name": _text(
            source.get("target_name"),
            "unknown-target",
        ),
        "source_feedback_kind": _text(source.get("kind")),
        "source_feedback_status": _text(
            source.get("packet_status")
        ),
        "source_feedback_ready": bool(
            source.get("hypothesis_feedback_review_ready")
        ),
        "source_feedback_digest": _text(
            source.get("feedback_digest")
        ),
        "source_feedback_proposal_count": len(proposals),
        "decision_count": len(decisions),
        "reviewer": "",
        "overall_reason": "",
        "decisions": decisions,
        "allowed_decisions": [
            "accepted",
            "rejected",
            "changes-requested",
            "deferred",
        ],
        "planning_only": True,
        "execution_state": "not_executed",
        "confidence_update_ready": False,
        "selection_update_ready": False,
        "investigation_plan_update_ready": False,
        "research_state_transition_ready": False,
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
    }

    return template


def _decision_template_item(
    proposal: dict[str, Any],
) -> dict[str, Any]:
    """Create one human-fillable decision item."""
    return {
        "feedback_id": _text(proposal.get("feedback_id")),
        "hypothesis_id": _text(proposal.get("hypothesis_id")),
        "title": _text(proposal.get("title")),
        "current_confidence": _text(
            proposal.get("current_confidence")
        ),
        "proposed_confidence": _text(
            proposal.get("proposed_confidence")
        ),
        "proposed_disposition": _text(
            proposal.get("proposed_disposition")
        ),
        "categorical_confidence_change": bool(
            proposal.get("categorical_confidence_change")
        ),
        "net_confidence_delta": _int(
            proposal.get("net_confidence_delta")
        ),
        "evidence_direction": _text(
            proposal.get("evidence_direction")
        ),
        "observation_ids": _list_of_text(
            proposal.get("observation_ids")
        ),
        "proposal_digest": _text(
            proposal.get("proposal_digest")
        ),
        "decision": DEFAULT_DECISION,
        "accepted_proposed_confidence": False,
        "reason": "Pending explicit human decision.",
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


__all__ = [
    "EXPECTED_FEEDBACK_KIND",
    "EXPECTED_FEEDBACK_STATUS",
    "EXPECTED_TEMPLATE_KIND",
    "build_research_hypothesis_feedback_decision_template",
    "load_json_object",
    "write_json",
]
