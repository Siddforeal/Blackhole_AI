from __future__ import annotations

import copy
import hashlib
import json
import re

import pytest

from bugintel.core.brain_chat_research_observation_packet import (
    build_research_observation_packet,
)
from bugintel.core.brain_chat_research_observation_review_gate import (
    EXPECTED_KIND,
    EXPECTED_STATUS,
    INTEGRITY_CATEGORIES,
    OBSERVATION_REQUIRED_FALSE_FLAGS,
    PACKET_REQUIRED_FALSE_FLAGS,
    PACKET_REQUIRED_TRUE_FLAGS,
    READY_STATUS,
    SAFETY_REQUIRED_FALSE_FLAGS,
    SAFETY_REQUIRED_TRUE_FLAGS,
    UNSAFE_CATEGORIES,
    build_research_observation_review_gate,
    build_review_gate_from_file,
    render_research_observation_review_gate_markdown,
)


FOCUS_ENDPOINT = "/api/projects/123/workers/456"


def _base_observation(**overrides) -> dict:
    observation = {
        "request_id": "RTR-001",
        "action_id": "ACT-001",
        "hypothesis_id": "HYP-005",
        "source_type": "manual-note",
        "outcome": "supports-hypothesis",
        "evidence_strength": "moderate",
        "summary": (
            "Local source review shows worker configuration "
            "reaches job planning."
        ),
        "details": [
            "Reviewed local controller data flow.",
            "No live target interaction was performed.",
        ],
        "artifact_refs": [
            "notes/worker-dataflow.md",
        ],
        "signals": [
            "worker trust boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    observation.update(overrides)
    return observation


def _packet(
    observations: list | None = None,
    **overrides,
) -> dict:
    payload = {
        "target_name": "demo-self-hosted-product",
        "focus_endpoint": FOCUS_ENDPOINT,
        "source_manifest_digest": "a" * 64,
        "source_review_digest": "b" * 64,
        "observations": (
            observations
            if observations is not None
            else [_base_observation()]
        ),
    }
    payload.update(overrides)

    return build_research_observation_packet(
        payload
    )


def _review(
    observations: list | None = None,
    **overrides,
) -> dict:
    return build_research_observation_review_gate(
        _packet(
            observations=observations,
            **overrides,
        )
    )


def _sha256(value) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _rehash_observation(
    observation: dict,
) -> None:
    material = copy.deepcopy(observation)
    material.pop("observation_digest", None)
    observation["observation_digest"] = _sha256(
        material
    )


def _rehash_packet(packet: dict) -> None:
    material = {
        "target_name": str(
            packet.get("target_name")
            or "unknown-target"
        ).strip(),
        "focus_endpoint": (
            str(packet["focus_endpoint"]).strip()
            if packet.get("focus_endpoint")
            else None
        ),
        "source_manifest_digest": (
            str(
                packet["source_manifest_digest"]
            ).strip()
            if packet.get("source_manifest_digest")
            else None
        ),
        "source_review_digest": (
            str(
                packet["source_review_digest"]
            ).strip()
            if packet.get("source_review_digest")
            else None
        ),
        "observations": packet.get(
            "observations",
            [],
        ),
    }

    packet["packet_digest"] = _sha256(material)


def _all_findings(review: dict) -> list[dict]:
    return (
        review["packet_findings"]
        + review["observation_findings"]
        + review["impact_findings"]
    )


def _categories(review: dict) -> set[str]:
    return {
        item["category"]
        for item in _all_findings(review)
    }


def _high_categories(review: dict) -> set[str]:
    return {
        item["category"]
        for item in _all_findings(review)
        if item["severity"] == "high"
    }


def _subjects(review: dict) -> set[str]:
    return {
        item["subject"]
        for item in _all_findings(review)
    }


def test_review_gate_constants() -> None:
    assert EXPECTED_KIND == (
        "brain_chat_research_observation_packet"
    )
    assert EXPECTED_STATUS == (
        "ready-for-observation-review"
    )
    assert READY_STATUS == (
        "ready-for-hypothesis-feedback-review"
    )

    assert "packet-integrity" in INTEGRITY_CATEGORIES
    assert (
        "observation-integrity"
        in INTEGRITY_CATEGORIES
    )
    assert "impact-integrity" in INTEGRITY_CATEGORIES
    assert "packet-safety" in UNSAFE_CATEGORIES
    assert "observation-safety" in UNSAFE_CATEGORIES


def test_valid_packet_is_ready() -> None:
    review = _review()

    assert review["kind"] == (
        "brain_chat_research_observation_review_gate"
    )
    assert review["target_name"] == (
        "demo-self-hosted-product"
    )
    assert review["focus_endpoint"] == FOCUS_ENDPOINT
    assert review["source_packet_kind"] == EXPECTED_KIND
    assert review["source_packet_status"] == (
        EXPECTED_STATUS
    )
    assert review["review_status"] == READY_STATUS
    assert review["review_ready"] is True
    assert (
        review["hypothesis_feedback_packet_ready"]
        is True
    )
    assert (
        review["research_state_transition_ready"]
        is False
    )
    assert review["critic_review_ready"] is False
    assert review["replanning_ready"] is False
    assert review["observation_count"] == 1

    assert review["counts"]["observations"] == 1
    assert (
        review["counts"]["ready_observations"]
        == 1
    )
    assert (
        review["counts"]["blocked_observations"]
        == 0
    )
    assert review["counts"]["high_findings"] == 0
    assert review["counts"]["medium_findings"] == 0
    assert review["counts"]["low_findings"] == 0


def test_ready_observation_review_fields() -> None:
    review = _review()
    item = review["observation_reviews"][0]

    assert item["observation_id"] == "OBS-001"
    assert item["request_id"] == "RTR-001"
    assert item["action_id"] == "ACT-001"
    assert item["hypothesis_id"] == "HYP-005"
    assert item["source_type"] == "manual-note"
    assert item["outcome"] == (
        "supports-hypothesis"
    )
    assert item["evidence_strength"] == "moderate"
    assert item["expected_confidence_delta"] == 2
    assert item["expected_hypothesis_effect"] == (
        "slightly-strengthen"
    )
    assert item["review_status"] == READY_STATUS
    assert item["review_ready"] is True
    assert item["hypothesis_feedback_ready"] is True
    assert (
        item["automatic_hypothesis_update_allowed"]
        is False
    )
    assert item["state_mutation_allowed"] is False
    assert item["runtime_execution_allowed"] is False
    assert item["finding_count"] == 0
    assert item["findings"] == []


def test_expected_hypothesis_impact_is_rebuilt() -> None:
    review = _review()

    assert review[
        "expected_preliminary_hypothesis_impacts"
    ] == [
        {
            "hypothesis_id": "HYP-005",
            "observation_count": 1,
            "observation_ids": ["OBS-001"],
            "net_confidence_delta": 2,
            "preliminary_direction": (
                "slightly-strengthen"
            ),
            "automatic_update_allowed": False,
            "human_review_required": True,
        }
    ]


def test_review_digest_is_sha256() -> None:
    review = _review()

    assert re.fullmatch(
        r"[0-9a-f]{64}",
        review["review_digest"],
    )


def test_review_is_deterministic() -> None:
    packet = _packet()

    first = build_research_observation_review_gate(
        packet
    )
    second = build_research_observation_review_gate(
        packet
    )

    assert first == second
    assert (
        first["review_digest"]
        == second["review_digest"]
    )


def test_review_does_not_mutate_packet() -> None:
    packet = _packet()
    before = copy.deepcopy(packet)

    build_research_observation_review_gate(
        packet
    )

    assert packet == before


def test_changed_valid_packet_changes_review_digest() -> None:
    first = _review()

    second = _review(
        observations=[
            _base_observation(
                outcome="contradicts-hypothesis",
                evidence_strength="strong",
            )
        ]
    )

    assert (
        first["review_digest"]
        != second["review_digest"]
    )


def test_empty_packet_is_blocked() -> None:
    packet = build_research_observation_packet({})
    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_ready"] is False
    assert review["observation_count"] == 0
    assert review["review_status"] == (
        "blocked-invalid-observation-packet"
    )
    assert "packet-schema" in _high_categories(
        review
    )


def test_wrong_packet_kind_is_blocked() -> None:
    packet = _packet()
    packet["kind"] = "wrong-kind"

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observation-packet"
    )
    assert "packet-schema" in _high_categories(
        review
    )
    assert "kind" in _subjects(review)


def test_source_packet_not_ready_is_blocked() -> None:
    packet = _packet()
    packet["packet_status"] = (
        "review-needed-observation-gaps"
    )

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-packet-not-ready"
    )
    assert "packet-readiness" in _categories(
        review
    )


@pytest.mark.parametrize(
    "field",
    PACKET_REQUIRED_TRUE_FLAGS,
)
def test_required_packet_true_flags(
    field: str,
) -> None:
    packet = _packet()
    packet[field] = False

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_ready"] is False
    assert "packet-readiness" in _categories(
        review
    )
    assert field in _subjects(review)


@pytest.mark.parametrize(
    "field",
    PACKET_REQUIRED_FALSE_FLAGS,
)
def test_required_packet_false_flags(
    field: str,
) -> None:
    packet = _packet()
    packet[field] = True

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        review
    )
    assert field in _subjects(review)


def test_packet_execution_state_must_be_not_executed() -> None:
    packet = _packet()
    packet["execution_state"] = "executed"

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        review
    )


def test_observation_count_must_match() -> None:
    packet = _packet()
    packet["observation_count"] = 99

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observation-packet"
    )
    assert "packet-schema" in _high_categories(
        review
    )
    assert "observation_count" in _subjects(review)


@pytest.mark.parametrize(
    "field",
    [
        "source_manifest_digest",
        "source_review_digest",
    ],
)
def test_invalid_source_digest_is_blocked(
    field: str,
) -> None:
    packet = _packet()
    packet[field] = "not-a-valid-digest"
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "source-integrity" in _high_categories(
        review
    )
    assert field in _subjects(review)


def test_source_digests_are_optional() -> None:
    packet = _packet()
    packet["source_manifest_digest"] = None
    packet["source_review_digest"] = None
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == READY_STATUS
    assert review["review_ready"] is True


def test_missing_packet_digest_is_blocked() -> None:
    packet = _packet()
    packet["packet_digest"] = None

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "packet-integrity" in _high_categories(
        review
    )


def test_invalid_packet_digest_format_is_blocked() -> None:
    packet = _packet()
    packet["packet_digest"] = "not-a-digest"

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "packet-integrity" in _high_categories(
        review
    )


def test_tampered_observation_breaks_both_digests() -> None:
    packet = _packet()
    packet["observations"][0]["summary"] = (
        "Tampered summary."
    )

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )

    categories = _high_categories(review)

    assert "packet-integrity" in categories
    assert "observation-integrity" in categories


def test_tampered_packet_digest_is_blocked() -> None:
    packet = _packet()
    packet["packet_digest"] = "c" * 64

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "packet-integrity" in _high_categories(
        review
    )


def test_safety_object_is_required() -> None:
    packet = _packet()
    packet["safety"] = None

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        review
    )


@pytest.mark.parametrize(
    "field",
    SAFETY_REQUIRED_TRUE_FLAGS,
)
def test_safety_true_flags_are_required(
    field: str,
) -> None:
    packet = _packet()
    packet["safety"][field] = False

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        review
    )
    assert f"safety.{field}" in _subjects(review)


@pytest.mark.parametrize(
    "field",
    SAFETY_REQUIRED_FALSE_FLAGS,
)
def test_safety_false_flags_remain_false(
    field: str,
) -> None:
    packet = _packet()
    packet["safety"][field] = True

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        review
    )
    assert f"safety.{field}" in _subjects(review)


@pytest.mark.parametrize(
    "field",
    [
        "linked_request_ids",
        "linked_action_ids",
        "linked_hypothesis_ids",
    ],
)
def test_linkage_aggregates_are_verified(
    field: str,
) -> None:
    packet = _packet()
    packet[field] = ["tampered-id"]

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "packet-consistency" in _high_categories(
        review
    )
    assert field in _subjects(review)


@pytest.mark.parametrize(
    "field",
    [
        "outcome_counts",
        "source_type_counts",
        "evidence_strength_counts",
        "redaction_status_counts",
        "scope_status_counts",
    ],
)
def test_aggregate_count_maps_are_verified(
    field: str,
) -> None:
    packet = _packet()
    packet[field] = {"tampered": 99}

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "packet-consistency" in _high_categories(
        review
    )
    assert field in _subjects(review)


def test_non_deterministic_observation_id_is_blocked() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["observation_id"] = "CUSTOM-ID"
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-schema" in _high_categories(
        review
    )


def test_duplicate_observation_ids_are_blocked() -> None:
    packet = _packet(
        observations=[
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
            ),
        ]
    )

    second = packet["observations"][1]
    second["observation_id"] = "OBS-001"
    _rehash_observation(second)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-schema" in _high_categories(
        review
    )


def test_missing_source_linkage_needs_review() -> None:
    packet = _packet()
    observation = packet["observations"][0]

    observation["request_id"] = None
    observation["action_id"] = None
    observation["hypothesis_id"] = None
    _rehash_observation(observation)

    packet["linked_request_ids"] = []
    packet["linked_action_ids"] = []
    packet["linked_hypothesis_ids"] = []
    packet["preliminary_hypothesis_impacts"] = []
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-linkage" in _categories(
        review
    )


def test_action_only_linkage_is_ready() -> None:
    packet = _packet()
    observation = packet["observations"][0]

    observation["request_id"] = None
    observation["hypothesis_id"] = None
    _rehash_observation(observation)

    packet["linked_request_ids"] = []
    packet["linked_hypothesis_ids"] = []
    packet["preliminary_hypothesis_impacts"] = []
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == READY_STATUS
    assert (
        review["observation_reviews"][0][
            "hypothesis_feedback_ready"
        ]
        is False
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_type", "unsupported-source"),
        ("outcome", "confirmed-vulnerability"),
        ("evidence_strength", "absolute"),
        ("redaction_status", "finished"),
        ("scope_status", "maybe"),
        ("controlled_assets_status", "mostly"),
    ],
)
def test_unsupported_observation_enums_are_blocked(
    field: str,
    value: str,
) -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[field] = value
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-schema" in _high_categories(
        review
    )


def test_empty_summary_is_blocked() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["summary"] = ""
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-quality" in _high_categories(
        review
    )


@pytest.mark.parametrize(
    "field",
    [
        "details",
        "artifact_refs",
        "signals",
        "errors",
    ],
)
def test_observation_text_lists_are_required(
    field: str,
) -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[field] = "not-a-list"
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-schema" in _high_categories(
        review
    )


@pytest.mark.parametrize(
    "status",
    [
        "pending",
        "failed",
        "unknown",
    ],
)
def test_incomplete_redaction_is_blocked(
    status: str,
) -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["redaction_status"] = status
    _rehash_observation(observation)

    packet["redaction_status_counts"] = {
        status: 1,
    }
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-redaction" in _high_categories(
        review
    )


def test_live_observation_requires_confirmed_scope() -> None:
    packet = _packet(
        observations=[
            _base_observation(
                source_type="http-response",
                scope_status="confirmed",
                controlled_assets_status="confirmed",
                redaction_status="reviewed",
            )
        ]
    )

    observation = packet["observations"][0]
    observation["scope_status"] = "pending"
    _rehash_observation(observation)

    packet["scope_status_counts"] = {
        "pending": 1,
    }
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-scope" in _high_categories(
        review
    )


def test_local_pending_scope_needs_review() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["scope_status"] = "pending"
    _rehash_observation(observation)

    packet["scope_status_counts"] = {
        "pending": 1,
    }
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-scope" in _categories(
        review
    )


def test_live_observation_requires_controlled_assets() -> None:
    packet = _packet(
        observations=[
            _base_observation(
                source_type="browser-network",
                scope_status="confirmed",
                controlled_assets_status="confirmed",
                redaction_status="reviewed",
            )
        ]
    )

    observation = packet["observations"][0]
    observation[
        "controlled_assets_status"
    ] = "pending"
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert "controlled-assets" in _high_categories(
        review
    )


def test_unreviewed_observation_needs_review() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["human_reviewed"] = False
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-review" in _categories(
        review
    )


@pytest.mark.parametrize(
    "field",
    OBSERVATION_REQUIRED_FALSE_FLAGS,
)
def test_observation_false_flags_remain_false(
    field: str,
) -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[field] = True
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "observation-safety" in _high_categories(
        review
    )


@pytest.mark.parametrize(
    "field",
    [
        "local_only",
        "planning_only",
    ],
)
def test_observation_required_true_flags(
    field: str,
) -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[field] = False
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "observation-safety" in _high_categories(
        review
    )


def test_observation_execution_state_is_fail_closed() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation["execution_state"] = "executed"
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-unsafe-observations"
    )
    assert "observation-safety" in _high_categories(
        review
    )


def test_preliminary_delta_is_recalculated() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[
        "preliminary_confidence_delta"
    ] = 99
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert (
        "observation-consistency"
        in _high_categories(review)
    )


def test_preliminary_effect_is_recalculated() -> None:
    packet = _packet()
    observation = packet["observations"][0]
    observation[
        "preliminary_hypothesis_effect"
    ] = "strengthen"
    _rehash_observation(observation)
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-invalid-observations"
    )
    assert (
        "observation-consistency"
        in _high_categories(review)
    )


def test_missing_observation_digest_is_blocked() -> None:
    packet = _packet()
    packet["observations"][0][
        "observation_digest"
    ] = None
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert (
        "observation-integrity"
        in _high_categories(review)
    )


def test_invalid_observation_digest_is_blocked() -> None:
    packet = _packet()
    packet["observations"][0][
        "observation_digest"
    ] = "c" * 64
    _rehash_packet(packet)

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert (
        "observation-integrity"
        in _high_categories(review)
    )


def test_impacts_must_be_a_list() -> None:
    packet = _packet()
    packet[
        "preliminary_hypothesis_impacts"
    ] = {}

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "impact-integrity" in _high_categories(
        review
    )


def test_tampered_hypothesis_impacts_are_blocked() -> None:
    packet = _packet()
    packet[
        "preliminary_hypothesis_impacts"
    ][0]["net_confidence_delta"] = 99

    review = build_research_observation_review_gate(
        packet
    )

    assert review["review_status"] == (
        "blocked-observation-integrity-failure"
    )
    assert "impact-integrity" in _high_categories(
        review
    )


def test_multiple_hypothesis_impacts_are_rebuilt() -> None:
    review = _review(
        observations=[
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
                hypothesis_id="HYP-005",
                outcome="supports-hypothesis",
                evidence_strength="strong",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                hypothesis_id="HYP-005",
                outcome="contradicts-hypothesis",
                evidence_strength="weak",
            ),
            _base_observation(
                request_id="RTR-003",
                action_id="ACT-003",
                hypothesis_id="HYP-007",
                outcome="contradicts-hypothesis",
                evidence_strength="moderate",
            ),
        ]
    )

    assert review["review_status"] == READY_STATUS

    impacts = {
        item["hypothesis_id"]: item
        for item in review[
            "expected_preliminary_hypothesis_impacts"
        ]
    }

    assert impacts["HYP-005"][
        "net_confidence_delta"
    ] == 2
    assert impacts["HYP-005"][
        "preliminary_direction"
    ] == "slightly-strengthen"

    assert impacts["HYP-007"][
        "net_confidence_delta"
    ] == -2
    assert impacts["HYP-007"][
        "preliminary_direction"
    ] == "slightly-weaken"


@pytest.mark.parametrize(
    (
        "outcome",
        "strength",
        "expected_delta",
        "expected_effect",
    ),
    [
        (
            "supports-hypothesis",
            "strong",
            3,
            "strengthen",
        ),
        (
            "supports-hypothesis",
            "moderate",
            2,
            "slightly-strengthen",
        ),
        (
            "weakly-supports-hypothesis",
            "strong",
            1,
            "slightly-strengthen",
        ),
        (
            "contradicts-hypothesis",
            "strong",
            -3,
            "weaken",
        ),
        (
            "contradicts-hypothesis",
            "moderate",
            -2,
            "slightly-weaken",
        ),
        (
            "weakly-contradicts-hypothesis",
            "strong",
            -1,
            "slightly-weaken",
        ),
        (
            "inconclusive",
            "strong",
            0,
            "hold",
        ),
        (
            "blocked",
            "moderate",
            0,
            "hold",
        ),
        (
            "error",
            "moderate",
            0,
            "hold",
        ),
        (
            "no-observable-change",
            "strong",
            0,
            "hold",
        ),
        (
            "not-tested",
            "strong",
            0,
            "hold",
        ),
    ],
)
def test_confidence_mapping_is_verified(
    outcome: str,
    strength: str,
    expected_delta: int,
    expected_effect: str,
) -> None:
    review = _review(
        observations=[
            _base_observation(
                outcome=outcome,
                evidence_strength=strength,
            )
        ]
    )

    item = review["observation_reviews"][0]

    assert item[
        "expected_confidence_delta"
    ] == expected_delta
    assert item[
        "expected_hypothesis_effect"
    ] == expected_effect


def test_allowed_next_steps_only_when_ready() -> None:
    ready = _review()

    packet = _packet()
    packet["packet_digest"] = "c" * 64

    blocked = build_research_observation_review_gate(
        packet
    )

    assert len(ready["allowed_next_steps"]) == 4
    assert blocked["allowed_next_steps"] == []


def test_rejected_next_steps_are_explicit() -> None:
    review = _review()
    text = " ".join(review["rejected_next_steps"])

    assert "hypothesis confidence" in text
    assert "persistent research state" in text
    assert "commands" in text
    assert "network requests" in text
    assert "collect additional evidence" in text
    assert "confirm vulnerabilities" in text


def test_review_output_remains_fail_closed() -> None:
    review = _review()

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
        "state_mutation_allowed",
        "report_submission_allowed",
        "vulnerability_confirmation_allowed",
    ):
        assert review[field] is False

    assert review["planning_only"] is True
    assert review["execution_state"] == (
        "not_executed"
    )


def test_review_safety_contract() -> None:
    review = _review()
    safety = review["safety"]

    assert safety["local_only"] is True
    assert safety["deterministic"] is True
    assert safety["planning_only"] is True
    assert safety["review_only"] is True
    assert (
        safety["packet_integrity_verified"]
        is True
    )
    assert (
        safety["observation_integrity_verified"]
        is True
    )
    assert (
        safety[
            "hypothesis_feedback_review_required"
        ]
        is True
    )
    assert (
        safety[
            "research_state_transition_review_required"
        ]
        is True
    )

    for field in (
        "command_generation",
        "payload_generation",
        "package_installation",
        "tool_execution",
        "browser_execution",
        "curl_execution",
        "kali_execution",
        "burp_execution",
        "provider_execution",
        "network_interaction",
        "target_interaction",
        "evidence_collection",
        "validation_execution",
        "hypothesis_mutation",
        "state_mutation",
        "runtime_execution_allowed",
        "report_submission",
        "vulnerability_confirmation",
    ):
        assert safety[field] is False


def test_markdown_contains_required_sections() -> None:
    review = _review()

    markdown = (
        render_research_observation_review_gate_markdown(
            review
        )
    )

    assert "# Research Observation Review Gate" in markdown
    assert "## Review Status" in markdown
    assert "## Counts" in markdown
    assert "## Observation Reviews" in markdown
    assert (
        "## Expected Preliminary Hypothesis Impacts"
        in markdown
    )
    assert "## Packet Findings" in markdown
    assert "## Observation Findings" in markdown
    assert "## Impact Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Rejected Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "review_status: "
        "`ready-for-hypothesis-feedback-review`"
        in markdown
    )
    assert "review_ready: `true`" in markdown
    assert (
        "research_state_transition_ready: `false`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )
    assert "OBS-001" in markdown
    assert "HYP-005" in markdown


def test_blocked_markdown_renders_findings() -> None:
    packet = _packet()
    packet["packet_digest"] = "c" * 64

    review = build_research_observation_review_gate(
        packet
    )

    markdown = (
        render_research_observation_review_gate_markdown(
            review
        )
    )

    assert (
        "blocked-observation-integrity-failure"
        in markdown
    )
    assert "[high] packet-integrity" in markdown


def test_file_builder_writes_outputs(
    tmp_path,
) -> None:
    packet_file = tmp_path / "observation-packet.json"
    markdown_file = (
        tmp_path
        / "output"
        / "observation-review.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "observation-review.json"
    )

    packet_file.write_text(
        json.dumps(_packet()),
        encoding="utf-8",
    )

    review = build_review_gate_from_file(
        packet_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert review["review_status"] == READY_STATUS
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_observation_review_gate"
    )
    assert written["review_ready"] is True
    assert (
        written["hypothesis_feedback_packet_ready"]
        is True
    )
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert (
        "# Research Observation Review Gate"
        in markdown
    )


def test_non_object_file_is_rejected(
    tmp_path,
) -> None:
    packet_file = tmp_path / "list.json"
    packet_file.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Expected JSON object",
    ):
        build_review_gate_from_file(
            packet_file
        )


def test_custom_source_is_preserved() -> None:
    review = (
        build_research_observation_review_gate(
            _packet(),
            source="custom-observation-review",
        )
    )

    assert review["source"] == (
        "custom-observation-review"
    )
