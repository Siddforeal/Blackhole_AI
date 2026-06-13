from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from bugintel.core.brain_chat_research_hypothesis_feedback_packet import (
    CONFIDENCE_LEVELS,
    EXPECTED_HYPOTHESIS_KIND,
    EXPECTED_HYPOTHESIS_STATUS,
    EXPECTED_OBSERVATION_KIND,
    EXPECTED_OBSERVATION_STATUS,
    EXPECTED_REVIEW_KIND,
    EXPECTED_REVIEW_STATUS,
    FEEDBACK_SAFETY,
    INPUT_REQUIRED_FALSE_FLAGS,
    READY_STATUS,
    build_feedback_packet_from_files,
    build_research_hypothesis_feedback_packet,
    render_research_hypothesis_feedback_packet_markdown,
)
from bugintel.core.brain_chat_research_observation_packet import (
    build_research_observation_packet,
)
from bugintel.core.brain_chat_research_observation_review_gate import (
    build_research_observation_review_gate,
)


TARGET = "demo-self-hosted-product"


def _hypothesis(
    hypothesis_id: str = "HYP-005",
    **overrides,
) -> dict:
    value = {
        "hypothesis_id": hypothesis_id,
        "title": "Worker trust-boundary weakness",
        "attack_surface": "worker execution",
        "hypothesis_type": (
            "worker-execution-trust-boundary"
        ),
        "rationale": (
            "Worker configuration may cross into a "
            "privileged execution context."
        ),
        "local_review_questions": [
            "Where is worker configuration validated?",
        ],
        "evidence_needed": [
            "Local controller-to-worker dataflow.",
        ],
        "allowed_local_checks": [
            "Review local worker planning code.",
        ],
        "rejected_actions": [
            "Do not execute worker jobs.",
        ],
        "priority": "high",
        "confidence": "medium",
        "tags": [
            "worker",
            "execution-boundary",
        ],
    }
    value.update(overrides)
    return value


def _hypothesis_packet(
    hypotheses: list[dict] | None = None,
    **overrides,
) -> dict:
    items = (
        hypotheses
        if hypotheses is not None
        else [_hypothesis()]
    )

    value = {
        "kind": EXPECTED_HYPOTHESIS_KIND,
        "source": (
            "brain-chat-research-hypothesis-packet"
        ),
        "target_name": TARGET,
        "packet_status": EXPECTED_HYPOTHESIS_STATUS,
        "source_packet_status": (
            "ready-for-research-review"
        ),
        "hypothesis_count": len(items),
        "hypotheses": items,
        "source_gaps": [],
        "hypothesis_gaps": [],
        "allowed_local_next_steps": [],
        "rejected_actions": [],
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": {
            "local_only": True,
            "deterministic": True,
            "planning_only": True,
            "command_generation": False,
            "tool_execution": False,
            "network_interaction": False,
            "runtime_execution_allowed": False,
        },
    }
    value.update(overrides)
    return value


def _observation(
    hypothesis_id: str | None = "HYP-005",
    **overrides,
) -> dict:
    value = {
        "request_id": "RTR-001",
        "action_id": "ACT-001",
        "hypothesis_id": hypothesis_id,
        "source_type": "manual-note",
        "outcome": "supports-hypothesis",
        "evidence_strength": "strong",
        "summary": (
            "Local review supports the worker "
            "trust-boundary hypothesis."
        ),
        "details": [
            "Reviewed local controller-to-worker flow.",
        ],
        "artifact_refs": [
            "notes/worker-flow.md",
        ],
        "signals": [
            "privileged worker boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    value.update(overrides)
    return value


def _observation_packet(
    observations: list[dict] | None = None,
    **overrides,
) -> dict:
    payload = {
        "target_name": TARGET,
        "observations": (
            observations
            if observations is not None
            else [_observation()]
        ),
    }
    payload.update(overrides)

    return build_research_observation_packet(
        payload
    )


def _artifacts(
    hypotheses: list[dict] | None = None,
    observations: list[dict] | None = None,
    hypothesis_overrides: dict | None = None,
    observation_overrides: dict | None = None,
):
    hypothesis_packet = _hypothesis_packet(
        hypotheses=hypotheses,
        **(hypothesis_overrides or {}),
    )
    observation_packet = _observation_packet(
        observations=observations,
        **(observation_overrides or {}),
    )
    observation_review = (
        build_research_observation_review_gate(
            observation_packet
        )
    )

    return (
        hypothesis_packet,
        observation_packet,
        observation_review,
    )


def _feedback(
    hypotheses: list[dict] | None = None,
    observations: list[dict] | None = None,
    hypothesis_overrides: dict | None = None,
    observation_overrides: dict | None = None,
) -> dict:
    artifacts = _artifacts(
        hypotheses=hypotheses,
        observations=observations,
        hypothesis_overrides=hypothesis_overrides,
        observation_overrides=observation_overrides,
    )

    return (
        build_research_hypothesis_feedback_packet(
            *artifacts
        )
    )


def _all_categories(
    packet: dict,
) -> set[str]:
    return {
        item["category"]
        for item in packet["findings"]
    }


def _high_categories(
    packet: dict,
) -> set[str]:
    return {
        item["category"]
        for item in packet["findings"]
        if item["severity"] == "high"
    }


def _subjects(
    packet: dict,
) -> set[str]:
    return {
        item["subject"]
        for item in packet["findings"]
    }


def _sha256(value) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _rehash_review(
    review: dict,
) -> None:
    material = {
        "source_packet_digest": (
            review.get("source_packet_digest")
        ),
        "review_status": review.get(
            "review_status"
        ),
        "packet_findings": review.get(
            "packet_findings"
        ),
        "observation_reviews": review.get(
            "observation_reviews"
        ),
        (
            "expected_preliminary_"
            "hypothesis_impacts"
        ): review.get(
            "expected_preliminary_hypothesis_impacts"
        ),
        "impact_findings": review.get(
            "impact_findings"
        ),
    }

    review["review_digest"] = _sha256(
        material
    )


def test_constants() -> None:
    assert CONFIDENCE_LEVELS == (
        "low",
        "medium",
        "high",
    )
    assert EXPECTED_HYPOTHESIS_KIND == (
        "brain_chat_research_hypothesis_packet"
    )
    assert EXPECTED_HYPOTHESIS_STATUS == (
        "ready-for-hypothesis-review"
    )
    assert EXPECTED_OBSERVATION_KIND == (
        "brain_chat_research_observation_packet"
    )
    assert EXPECTED_OBSERVATION_STATUS == (
        "ready-for-observation-review"
    )
    assert EXPECTED_REVIEW_KIND == (
        "brain_chat_research_observation_review_gate"
    )
    assert EXPECTED_REVIEW_STATUS == (
        "ready-for-hypothesis-feedback-review"
    )
    assert READY_STATUS == (
        "ready-for-hypothesis-feedback-review"
    )


def test_ready_feedback_packet() -> None:
    packet = _feedback()

    assert packet["kind"] == (
        "brain_chat_research_hypothesis_feedback_packet"
    )
    assert packet["target_name"] == TARGET
    assert packet["packet_status"] == READY_STATUS
    assert packet["packet_ready"] is True
    assert (
        packet["hypothesis_feedback_review_ready"]
        is True
    )
    assert packet["confidence_update_ready"] is False
    assert packet["selection_update_ready"] is False
    assert (
        packet["investigation_plan_update_ready"]
        is False
    )
    assert (
        packet["research_state_transition_ready"]
        is False
    )
    assert packet["critic_review_ready"] is False
    assert packet["replanning_ready"] is False
    assert packet["feedback_proposal_count"] == 1
    assert packet["findings"] == []


def test_ready_proposal_fields() -> None:
    packet = _feedback()
    proposal = packet["feedback_proposals"][0]

    assert proposal["feedback_id"] == "HFB-001"
    assert proposal["hypothesis_id"] == "HYP-005"
    assert proposal["current_confidence"] == (
        "medium"
    )
    assert proposal["proposed_confidence"] == "high"
    assert (
        proposal["categorical_confidence_change"]
        is True
    )
    assert proposal["net_confidence_delta"] == 3
    assert proposal["evidence_direction"] == (
        "strengthen"
    )
    assert proposal["proposed_disposition"] == (
        "propose-confidence-promotion"
    )
    assert proposal["observation_count"] == 1
    assert proposal["observation_ids"] == [
        "OBS-001"
    ]
    assert proposal["human_review_required"] is True
    assert proposal["automatic_update_allowed"] is False
    assert (
        proposal["confidence_mutation_allowed"]
        is False
    )
    assert (
        proposal["selection_mutation_allowed"]
        is False
    )
    assert (
        proposal[
            "investigation_plan_mutation_allowed"
        ]
        is False
    )
    assert proposal["state_mutation_allowed"] is False
    assert proposal["planning_only"] is True
    assert proposal["execution_allowed"] is False
    assert (
        proposal["runtime_execution_allowed"]
        is False
    )


def test_packet_counts() -> None:
    packet = _feedback()
    counts = packet["counts"]

    assert counts["source_hypotheses"] == 1
    assert counts["verified_hypothesis_impacts"] == 1
    assert counts["feedback_proposals"] == 1
    assert counts[
        "categorical_confidence_changes"
    ] == 1
    assert counts["strengthening_proposals"] == 1
    assert counts["weakening_proposals"] == 0
    assert counts["hold_proposals"] == 0
    assert counts["findings"] == 0
    assert counts["high_findings"] == 0
    assert counts["medium_findings"] == 0
    assert counts["low_findings"] == 0


def test_source_digests_are_present() -> None:
    packet = _feedback()

    for field in (
        "hypothesis_packet_digest",
        "observation_packet_digest",
        "observation_review_digest",
        "feedback_digest",
    ):
        assert re.fullmatch(
            r"[0-9a-f]{64}",
            packet[field],
        )


def test_proposal_digest_matches_content() -> None:
    packet = _feedback()
    proposal = copy.deepcopy(
        packet["feedback_proposals"][0]
    )
    digest = proposal.pop("proposal_digest")

    assert digest == _sha256(proposal)


def test_feedback_is_deterministic() -> None:
    artifacts = _artifacts()

    first = (
        build_research_hypothesis_feedback_packet(
            *artifacts
        )
    )
    second = (
        build_research_hypothesis_feedback_packet(
            *artifacts
        )
    )

    assert first == second
    assert (
        first["feedback_digest"]
        == second["feedback_digest"]
    )


def test_builder_does_not_mutate_inputs() -> None:
    artifacts = _artifacts()
    before = copy.deepcopy(artifacts)

    build_research_hypothesis_feedback_packet(
        *artifacts
    )

    assert artifacts == before


def test_changed_feedback_changes_digest() -> None:
    positive = _feedback()

    negative = _feedback(
        observations=[
            _observation(
                outcome="contradicts-hypothesis",
                evidence_strength="strong",
            )
        ]
    )

    assert (
        positive["feedback_digest"]
        != negative["feedback_digest"]
    )


@pytest.mark.parametrize(
    (
        "current",
        "outcome",
        "strength",
        "expected",
        "changed",
        "disposition",
    ),
    [
        (
            "low",
            "supports-hypothesis",
            "strong",
            "medium",
            True,
            "propose-confidence-promotion",
        ),
        (
            "medium",
            "supports-hypothesis",
            "strong",
            "high",
            True,
            "propose-confidence-promotion",
        ),
        (
            "high",
            "supports-hypothesis",
            "strong",
            "high",
            False,
            (
                "retain-confidence-with-"
                "positive-trend"
            ),
        ),
        (
            "high",
            "contradicts-hypothesis",
            "strong",
            "medium",
            True,
            "propose-confidence-demotion",
        ),
        (
            "medium",
            "contradicts-hypothesis",
            "strong",
            "low",
            True,
            "propose-confidence-demotion",
        ),
        (
            "low",
            "contradicts-hypothesis",
            "strong",
            "low",
            False,
            (
                "retain-confidence-with-"
                "negative-trend"
            ),
        ),
        (
            "medium",
            "supports-hypothesis",
            "moderate",
            "medium",
            False,
            (
                "retain-confidence-with-"
                "positive-trend"
            ),
        ),
        (
            "medium",
            "contradicts-hypothesis",
            "moderate",
            "medium",
            False,
            (
                "retain-confidence-with-"
                "negative-trend"
            ),
        ),
        (
            "medium",
            "inconclusive",
            "strong",
            "medium",
            False,
            "retain-confidence",
        ),
    ],
)
def test_confidence_proposal_mapping(
    current: str,
    outcome: str,
    strength: str,
    expected: str,
    changed: bool,
    disposition: str,
) -> None:
    packet = _feedback(
        hypotheses=[
            _hypothesis(
                confidence=current,
            )
        ],
        observations=[
            _observation(
                outcome=outcome,
                evidence_strength=strength,
            )
        ],
    )
    proposal = packet["feedback_proposals"][0]

    assert proposal["current_confidence"] == current
    assert proposal["proposed_confidence"] == (
        expected
    )
    assert (
        proposal["categorical_confidence_change"]
        is changed
    )
    assert proposal["proposed_disposition"] == (
        disposition
    )


def test_multiple_proposals_are_sorted_by_hypothesis_id(
) -> None:
    packet = _feedback(
        hypotheses=[
            _hypothesis(
                hypothesis_id="HYP-020",
                title="Second",
                confidence="high",
            ),
            _hypothesis(
                hypothesis_id="HYP-003",
                title="First",
                confidence="low",
            ),
        ],
        observations=[
            _observation(
                hypothesis_id="HYP-020",
                request_id="RTR-020",
                action_id="ACT-020",
            ),
            _observation(
                hypothesis_id="HYP-003",
                request_id="RTR-003",
                action_id="ACT-003",
            ),
        ],
    )

    assert packet["packet_status"] == READY_STATUS
    assert [
        item["hypothesis_id"]
        for item in packet["feedback_proposals"]
    ] == [
        "HYP-003",
        "HYP-020",
    ]
    assert [
        item["feedback_id"]
        for item in packet["feedback_proposals"]
    ] == [
        "HFB-001",
        "HFB-002",
    ]


def test_action_only_observation_has_no_impacts() -> None:
    packet = _feedback(
        observations=[
            _observation(
                hypothesis_id=None,
                action_id="ACT-100",
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-no-hypothesis-impacts"
    )
    assert packet["packet_ready"] is False
    assert packet["feedback_proposal_count"] == 0
    assert packet["feedback_proposals"] == []
    assert packet["allowed_next_steps"] == []


def test_unknown_hypothesis_is_blocked() -> None:
    packet = _feedback(
        observations=[
            _observation(
                hypothesis_id="HYP-999",
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-unknown-hypothesis"
    )
    assert packet["packet_ready"] is False
    assert (
        "hypothesis-linkage"
        in _high_categories(packet)
    )
    assert "HYP-999" in _subjects(packet)


def test_wrong_hypothesis_kind_is_blocked() -> None:
    packet = _feedback(
        hypothesis_overrides={
            "kind": "wrong-kind",
        }
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


def test_hypothesis_packet_not_ready_is_blocked(
) -> None:
    packet = _feedback(
        hypothesis_overrides={
            "packet_status": (
                "review-needed-hypothesis-gaps"
            ),
        }
    )

    assert packet["packet_status"] == (
        "blocked-hypothesis-packet-not-ready"
    )
    assert (
        "hypothesis-readiness"
        in _high_categories(packet)
    )


def test_hypothesis_count_mismatch_is_blocked() -> None:
    packet = _feedback(
        hypothesis_overrides={
            "hypothesis_count": 99,
        }
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


def test_empty_hypothesis_packet_is_blocked() -> None:
    packet = _feedback(
        hypotheses=[],
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


def test_missing_hypothesis_id_is_blocked() -> None:
    packet = _feedback(
        hypotheses=[
            _hypothesis(
                hypothesis_id="",
            )
        ],
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


def test_duplicate_hypothesis_ids_are_blocked() -> None:
    packet = _feedback(
        hypotheses=[
            _hypothesis(
                hypothesis_id="HYP-005",
            ),
            _hypothesis(
                hypothesis_id="HYP-005",
                title="Duplicate",
            ),
        ],
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    "confidence",
    [
        "",
        "unknown",
        "very-high",
        "HIGH",
    ],
)
def test_unsupported_confidence_is_blocked(
    confidence: str,
) -> None:
    packet = _feedback(
        hypotheses=[
            _hypothesis(
                confidence=confidence,
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "hypothesis-schema" in _high_categories(
        packet
    )


def test_hypothesis_planning_only_is_required() -> None:
    packet = _feedback(
        hypothesis_overrides={
            "planning_only": False,
        }
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "hypothesis-safety" in _high_categories(
        packet
    )


def test_hypothesis_execution_state_is_fail_closed(
) -> None:
    packet = _feedback(
        hypothesis_overrides={
            "execution_state": "executed",
        }
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "hypothesis-safety" in _high_categories(
        packet
    )


def test_wrong_observation_kind_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()
    observations["kind"] = "wrong-kind"

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "observation-schema" in _high_categories(
        packet
    )


def test_observation_packet_not_ready_is_blocked(
) -> None:
    hypotheses, observations, review = _artifacts()
    observations["packet_status"] = (
        "review-needed-observation-gaps"
    )

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-observation-packet-not-ready"
    )
    assert (
        "observation-readiness"
        in _high_categories(packet)
    )


def test_invalid_observation_packet_digest_is_blocked(
) -> None:
    hypotheses, observations, review = _artifacts()
    observations["packet_digest"] = (
        "not-a-valid-digest"
    )

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-feedback-integrity-failure"
    )
    assert "source-integrity" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    "field",
    INPUT_REQUIRED_FALSE_FLAGS,
)
def test_observation_packet_authority_flags_are_blocked(
    field: str,
) -> None:
    hypotheses, observations, review = _artifacts()
    observations[field] = True

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "observation-safety" in _high_categories(
        packet
    )
    assert field in _subjects(packet)


def test_wrong_review_kind_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()
    review["kind"] = "wrong-kind"

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "review-schema" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    (
        "field",
        "value",
    ),
    [
        (
            "review_status",
            "blocked-invalid-observations",
        ),
        (
            "review_ready",
            False,
        ),
        (
            "hypothesis_feedback_packet_ready",
            False,
        ),
    ],
)
def test_review_readiness_is_required(
    field: str,
    value,
) -> None:
    hypotheses, observations, review = _artifacts()
    review[field] = value

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-observation-review-not-ready"
    )
    assert "review-readiness" in _high_categories(
        packet
    )


def test_mismatched_review_packet_digest_is_blocked(
) -> None:
    hypotheses, observations, review = _artifacts()
    review["source_packet_digest"] = "c" * 64
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-feedback-integrity-failure"
    )
    assert "source-integrity" in _high_categories(
        packet
    )


def test_invalid_review_digest_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()
    review["review_digest"] = "not-a-digest"

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-feedback-integrity-failure"
    )
    assert "source-integrity" in _high_categories(
        packet
    )


def test_tampered_review_contents_are_blocked() -> None:
    hypotheses, observations, review = _artifacts()
    review[
        "expected_preliminary_hypothesis_impacts"
    ][0]["net_confidence_delta"] = 99

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-feedback-integrity-failure"
    )
    assert "source-integrity" in _high_categories(
        packet
    )


def test_packet_and_review_impacts_must_match() -> None:
    hypotheses, observations, review = _artifacts()

    observations[
        "preliminary_hypothesis_impacts"
    ][0]["net_confidence_delta"] = 1

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-feedback-integrity-failure"
    )
    assert "impact-integrity" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    "field",
    INPUT_REQUIRED_FALSE_FLAGS,
)
def test_review_authority_flags_are_blocked(
    field: str,
) -> None:
    hypotheses, observations, review = _artifacts()
    review[field] = True

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "review-safety" in _high_categories(
        packet
    )


def test_duplicate_impacts_are_blocked() -> None:
    hypotheses, observations, review = _artifacts()

    duplicate = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ][0]
    )

    review[
        "expected_preliminary_hypothesis_impacts"
    ].append(duplicate)

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "impact-schema" in _high_categories(
        packet
    )


def test_missing_impact_hypothesis_id_is_blocked(
) -> None:
    hypotheses, observations, review = _artifacts()

    impact = review[
        "expected_preliminary_hypothesis_impacts"
    ][0]
    impact["hypothesis_id"] = ""

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "impact-schema" in _high_categories(
        packet
    )


def test_non_integer_delta_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()

    impact = review[
        "expected_preliminary_hypothesis_impacts"
    ][0]
    impact["net_confidence_delta"] = "3"

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert "impact-schema" in _high_categories(
        packet
    )


def test_impact_direction_is_verified() -> None:
    hypotheses, observations, review = _artifacts()

    impact = review[
        "expected_preliminary_hypothesis_impacts"
    ][0]
    impact["preliminary_direction"] = "weaken"

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-invalid-feedback-input"
    )
    assert (
        "impact-consistency"
        in _high_categories(packet)
    )


def test_automatic_update_flag_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()

    impact = review[
        "expected_preliminary_hypothesis_impacts"
    ][0]
    impact["automatic_update_allowed"] = True

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "impact-safety" in _high_categories(
        packet
    )


def test_human_review_requirement_is_enforced() -> None:
    hypotheses, observations, review = _artifacts()

    impact = review[
        "expected_preliminary_hypothesis_impacts"
    ][0]
    impact["human_review_required"] = False

    observations[
        "preliminary_hypothesis_impacts"
    ] = copy.deepcopy(
        review[
            "expected_preliminary_hypothesis_impacts"
        ]
    )
    _rehash_review(review)

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-feedback-input"
    )
    assert "impact-safety" in _high_categories(
        packet
    )


def test_allowed_next_steps_only_when_ready() -> None:
    ready = _feedback()

    blocked = _feedback(
        hypothesis_overrides={
            "kind": "wrong-kind",
        }
    )

    assert len(ready["allowed_next_steps"]) == 4
    assert blocked["allowed_next_steps"] == []


def test_rejected_next_steps_are_explicit() -> None:
    packet = _feedback()
    text = " ".join(
        packet["rejected_next_steps"]
    )

    assert "confidence values" in text
    assert "selected hypotheses" in text
    assert "investigation plans" in text
    assert "persistent research state" in text
    assert "commands" in text
    assert "confirm vulnerabilities" in text


def test_output_remains_fail_closed() -> None:
    packet = _feedback()

    for field in (
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
        "state_mutation_allowed",
        "report_submission_allowed",
        "vulnerability_confirmation_allowed",
    ):
        assert packet[field] is False

    assert packet["planning_only"] is True
    assert packet["execution_state"] == (
        "not_executed"
    )


def test_feedback_safety_contract() -> None:
    packet = _feedback()

    assert packet["safety"] == FEEDBACK_SAFETY

    for field, value in FEEDBACK_SAFETY.items():
        assert packet["safety"][field] is value


def test_markdown_contains_required_sections() -> None:
    packet = _feedback()

    markdown = (
        render_research_hypothesis_feedback_packet_markdown(
            packet
        )
    )

    assert (
        "# Research Hypothesis Feedback Packet"
        in markdown
    )
    assert "## Packet Status" in markdown
    assert "## Counts" in markdown
    assert "## Feedback Proposals" in markdown
    assert "## Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Rejected Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "packet_status: "
        "`ready-for-hypothesis-feedback-review`"
        in markdown
    )
    assert "packet_ready: `true`" in markdown
    assert "confidence_update_ready: `false`" in markdown
    assert (
        "research_state_transition_ready: `false`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )
    assert "HFB-001" in markdown
    assert "HYP-005" in markdown
    assert "`medium`" in markdown
    assert "`high`" in markdown


def test_blocked_markdown_renders_findings() -> None:
    packet = _feedback(
        hypothesis_overrides={
            "kind": "wrong-kind",
        }
    )

    markdown = (
        render_research_hypothesis_feedback_packet_markdown(
            packet
        )
    )

    assert (
        "blocked-invalid-feedback-input"
        in markdown
    )
    assert "[high] hypothesis-schema" in markdown


def test_file_builder_writes_outputs(
    tmp_path,
) -> None:
    hypotheses, observations, review = _artifacts()

    hypothesis_file = (
        tmp_path
        / "hypotheses.json"
    )
    observation_file = (
        tmp_path
        / "observations.json"
    )
    review_file = (
        tmp_path
        / "observation-review.json"
    )
    markdown_file = (
        tmp_path
        / "output"
        / "hypothesis-feedback.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "hypothesis-feedback.json"
    )

    hypothesis_file.write_text(
        json.dumps(hypotheses),
        encoding="utf-8",
    )
    observation_file.write_text(
        json.dumps(observations),
        encoding="utf-8",
    )
    review_file.write_text(
        json.dumps(review),
        encoding="utf-8",
    )

    packet = build_feedback_packet_from_files(
        hypothesis_file,
        observation_file,
        review_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert packet["packet_status"] == READY_STATUS
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_hypothesis_feedback_packet"
    )
    assert written["packet_ready"] is True
    assert written["confidence_update_ready"] is False
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Hypothesis Feedback Packet"
        in markdown
    )


@pytest.mark.parametrize(
    "file_index",
    [
        0,
        1,
        2,
    ],
)
def test_non_object_input_file_is_rejected(
    tmp_path,
    file_index: int,
) -> None:
    hypotheses, observations, review = _artifacts()
    values = [
        hypotheses,
        observations,
        review,
    ]

    values[file_index] = [
        "not",
        "an",
        "object",
    ]

    paths = []

    for index, value in enumerate(values):
        path = tmp_path / f"input-{index}.json"
        path.write_text(
            json.dumps(value),
            encoding="utf-8",
        )
        paths.append(path)

    with pytest.raises(
        ValueError,
        match="Expected JSON object",
    ):
        build_feedback_packet_from_files(
            paths[0],
            paths[1],
            paths[2],
        )


def test_custom_source_is_preserved() -> None:
    artifacts = _artifacts()

    packet = (
        build_research_hypothesis_feedback_packet(
            *artifacts,
            source="custom-feedback-source",
        )
    )

    assert packet["source"] == (
        "custom-feedback-source"
    )


def test_object_with_to_dict_is_supported() -> None:
    class HypothesisObject:
        def __init__(self, value: dict) -> None:
            self.value = value

        def to_dict(self) -> dict:
            return copy.deepcopy(self.value)

    hypotheses, observations, review = _artifacts()

    packet = (
        build_research_hypothesis_feedback_packet(
            HypothesisObject(hypotheses),
            observations,
            review,
        )
    )

    assert packet["packet_status"] == READY_STATUS
    assert packet["packet_ready"] is True


def test_invalid_hypothesis_object_is_blocked() -> None:
    hypotheses, observations, review = _artifacts()

    packet = (
        build_research_hypothesis_feedback_packet(
            object(),
            observations,
            review,
        )
    )

    assert packet["packet_status"] == (
        "blocked-hypothesis-packet-not-ready"
    )
    assert packet["packet_ready"] is False
