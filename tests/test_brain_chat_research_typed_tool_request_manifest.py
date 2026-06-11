from __future__ import annotations

import copy
import json
import string

from bugintel.core.brain_chat_research_action_decision_packet import (
    build_research_action_decision_packet,
    build_research_action_decision_template,
)
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    build_research_action_proposal_review_gate,
)
from bugintel.core.brain_chat_research_approved_action_packet import (
    build_research_approved_action_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
)
from bugintel.core.brain_chat_research_typed_tool_request_manifest import (
    ADAPTER_CONTRACTS,
    EXPECTED_APPROVED_PACKET_KIND,
    EXPECTED_APPROVED_PACKET_STATUS,
    build_research_typed_tool_request_manifest,
    build_typed_manifest_from_file,
    render_research_typed_tool_request_manifest_markdown,
)


def _selection_packet() -> dict:
    return {
        "kind": (
            "brain_chat_research_hypothesis_selection_packet"
        ),
        "target_name": "demo-self-hosted-product",
        "selection_status": (
            "ready-for-local-investigation-planning"
        ),
        "primary_hypothesis_id": "HYP-005",
        "selected_hypotheses": [
            {
                "hypothesis_id": "HYP-005",
                "hypothesis_type": (
                    "worker-execution-trust-boundary"
                ),
                "title": "Worker execution trust boundary",
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": [
                    "worker",
                    "runner",
                    "deployment",
                ],
            },
        ],
    }


def _approved_action_packet(
    decisions: list[str] | None = None,
) -> dict:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = build_research_investigation_plan_review_gate(
        plan
    )

    proposal = build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()

    proposal_review = (
        build_research_action_proposal_review_gate(
            proposal
        )
    )

    decision_input = (
        build_research_action_decision_template(
            proposal
        )
    )
    decision_input["reviewer"] = (
        "authorized-human-reviewer"
    )
    decision_input["overall_reason"] = (
        "Approved for typed tool-request planning."
    )

    values = decisions or [
        "approved"
        for _ in decision_input["decisions"]
    ]

    assert len(values) == len(
        decision_input["decisions"]
    )

    for item, decision in zip(
        decision_input["decisions"],
        values,
        strict=True,
    ):
        item["decision"] = decision
        item["reason"] = (
            f"Human decision recorded as {decision}."
        )

    decision_packet = (
        build_research_action_decision_packet(
            proposal,
            proposal_review,
            decision_input,
        )
    )

    return build_research_approved_action_packet(
        decision_packet
    )


def _manifest(
    decisions: list[str] | None = None,
    focus_endpoint: str | None = None,
) -> dict:
    packet = _approved_action_packet(decisions)

    if focus_endpoint is not None:
        packet["focus_endpoint"] = focus_endpoint

    return build_research_typed_tool_request_manifest(
        packet
    )


def _subjects(
    manifest: dict,
    section: str,
) -> list[str]:
    return [
        item["subject"]
        for item in manifest[section]
        if isinstance(item, dict)
    ]


def _messages(
    manifest: dict,
    section: str,
) -> list[str]:
    return [
        item["message"]
        for item in manifest[section]
        if isinstance(item, dict)
    ]


def _request(
    manifest: dict,
    action_type: str,
) -> dict:
    return next(
        item
        for item in manifest["typed_requests"]
        if item["action_type"] == action_type
    )


def _is_sha256(value: str) -> bool:
    return (
        len(value) == 64
        and all(
            character in string.hexdigits
            for character in value
        )
    )


def test_expected_source_constants() -> None:
    assert EXPECTED_APPROVED_PACKET_KIND == (
        "brain_chat_research_approved_action_packet"
    )
    assert EXPECTED_APPROVED_PACKET_STATUS == (
        "ready-for-typed-tool-request-manifest"
    )


def test_adapter_contracts_cover_all_adapter_families() -> None:
    assert set(ADAPTER_CONTRACTS) == {
        "local-file",
        "local-artifact",
        "scope-review",
        "controlled-assets",
        "browser",
        "burp",
        "shell-review",
        "evidence",
    }

    for adapter_family, contract in (
        ADAPTER_CONTRACTS.items()
    ):
        assert adapter_family
        assert contract["allowed_inputs"]
        assert contract["required_outputs"]
        assert contract["prohibited_operations"]

        assert isinstance(
            contract["allowed_inputs"],
            tuple,
        )
        assert isinstance(
            contract["required_outputs"],
            tuple,
        )
        assert isinstance(
            contract["prohibited_operations"],
            tuple,
        )


def test_ready_manifest_contains_all_typed_requests() -> None:
    manifest = _manifest()

    assert manifest["kind"] == (
        "brain_chat_research_typed_tool_request_manifest"
    )
    assert manifest["target_name"] == (
        "demo-self-hosted-product"
    )
    assert manifest["focus_endpoint"] is None
    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert manifest["manifest_ready"] is True
    assert manifest["execution_gate_input_ready"] is True
    assert manifest["execution_gate_review_ready"] is True
    assert (
        manifest[
            "existing_tool_execution_gate_compatible"
        ]
        is True
    )

    assert manifest["source_packet_kind"] == (
        "brain_chat_research_approved_action_packet"
    )
    assert manifest["source_packet_status"] == (
        "ready-for-typed-tool-request-manifest"
    )
    assert manifest["source_packet_ready"] is True
    assert manifest["source_manifest_ready"] is True
    assert manifest["source_approved_action_count"] == 8

    assert manifest["typed_request_count"] == 8
    assert len(manifest["typed_requests"]) == 8
    assert manifest["source_findings"] == []
    assert manifest["request_findings"] == []
    assert manifest["counts"]["high_findings"] == 0
    assert manifest["counts"]["medium_findings"] == 0


def test_request_identifiers_are_deterministic() -> None:
    manifest = _manifest()

    assert [
        item["request_id"]
        for item in manifest["typed_requests"]
    ] == [
        "RTR-001",
        "RTR-002",
        "RTR-003",
        "RTR-004",
        "RTR-005",
        "RTR-006",
        "RTR-007",
        "RTR-008",
    ]

    assert [
        item["manual_order"]
        for item in manifest["typed_requests"]
    ] == list(range(1, 9))


def test_request_action_ids_remain_unique() -> None:
    manifest = _manifest()

    action_ids = [
        item["action_id"]
        for item in manifest["typed_requests"]
    ]

    assert len(action_ids) == len(set(action_ids))


def test_request_digests_are_valid_and_unique() -> None:
    manifest = _manifest()

    digests = [
        item["request_digest"]
        for item in manifest["typed_requests"]
    ]

    assert all(_is_sha256(value) for value in digests)
    assert len(digests) == len(set(digests))


def test_manifest_digests_are_valid() -> None:
    manifest = _manifest()

    assert _is_sha256(
        manifest["approved_action_packet_digest"]
    )
    assert _is_sha256(manifest["manifest_digest"])


def test_manifest_generation_is_deterministic() -> None:
    packet = _approved_action_packet()

    first = build_research_typed_tool_request_manifest(
        packet
    )
    second = build_research_typed_tool_request_manifest(
        packet
    )

    assert (
        first["approved_action_packet_digest"]
        == second["approved_action_packet_digest"]
    )
    assert (
        first["manifest_digest"]
        == second["manifest_digest"]
    )
    assert (
        first["typed_requests"]
        == second["typed_requests"]
    )


def test_manifest_digest_changes_when_source_changes() -> None:
    packet = _approved_action_packet()

    first = build_research_typed_tool_request_manifest(
        packet
    )

    packet["approved_actions"][0]["purpose"] = (
        "Changed approved purpose."
    )

    second = build_research_typed_tool_request_manifest(
        packet
    )

    assert (
        first["approved_action_packet_digest"]
        != second["approved_action_packet_digest"]
    )
    assert (
        first["manifest_digest"]
        != second["manifest_digest"]
    )


def test_builder_does_not_mutate_source_packet() -> None:
    packet = _approved_action_packet()
    before = copy.deepcopy(packet)

    build_research_typed_tool_request_manifest(packet)

    assert packet == before


def test_tool_family_counts_are_deterministic() -> None:
    manifest = _manifest()

    assert manifest["tool_family_counts"] == {
        "browser": 1,
        "burp": 1,
        "evidence-planning": 1,
        "local-artifact-analysis": 1,
        "local-file-analysis": 1,
        "scope": 1,
        "shell-review": 1,
        "test-controls": 1,
    }
    assert manifest["counts"]["tool_families"] == 8


def test_adapter_family_counts_are_deterministic() -> None:
    manifest = _manifest()

    assert manifest["adapter_family_counts"] == {
        "browser": 1,
        "burp": 1,
        "controlled-assets": 1,
        "evidence": 1,
        "local-artifact": 1,
        "local-file": 1,
        "scope-review": 1,
        "shell-review": 1,
    }
    assert manifest["counts"]["adapter_families"] == 8


def test_request_kind_counts_are_deterministic() -> None:
    manifest = _manifest()

    assert manifest["request_kind_counts"] == {
        "browser-observation-request": 1,
        "burp-request-review-request": 1,
        "command-review-preparation-request": 1,
        "controlled-account-preparation-request": 1,
        "evidence-plan-request": 1,
        "local-artifact-inspection-request": 1,
        "local-source-inspection-request": 1,
        "scope-confirmation-request": 1,
    }
    assert manifest["counts"]["request_kinds"] == 8


def test_risk_counts_are_deterministic() -> None:
    manifest = _manifest()

    assert manifest["risk_level_counts"] == {
        "high": 1,
        "low": 3,
        "medium": 4,
    }
    assert manifest["counts"]["risk_levels"] == 3


def test_requirement_counts_are_deterministic() -> None:
    manifest = _manifest()

    assert manifest["runtime_gated_request_count"] == 4
    assert manifest["scope_required_request_count"] == 6
    assert manifest["controlled_assets_request_count"] == 5
    assert (
        manifest["observation_capture_request_count"]
        == 4
    )

    assert (
        manifest["counts"]["runtime_gated_requests"]
        == 4
    )
    assert (
        manifest["counts"]["scope_required_requests"]
        == 6
    )
    assert (
        manifest[
            "counts"
        ]["controlled_assets_requests"]
        == 5
    )
    assert (
        manifest[
            "counts"
        ]["observation_capture_requests"]
        == 4
    )


def test_every_typed_request_remains_non_executable() -> None:
    manifest = _manifest()

    for request in manifest["typed_requests"]:
        assert request["requires_human_approval"] is True
        assert request["approval_state"] == (
            "human-approved-for-planning"
        )
        assert request["request_state"] == (
            "typed-request-not-executable"
        )
        assert request["manifest_eligible"] is True

        assert request["command_generated"] is False
        assert request["payload_generated"] is False
        assert (
            request["package_installation_allowed"]
            is False
        )
        assert request["execution_allowed"] is False
        assert (
            request["runtime_execution_allowed"]
            is False
        )
        assert (
            request["network_interaction_allowed"]
            is False
        )
        assert (
            request["target_interaction_allowed"]
            is False
        )
        assert (
            request["evidence_collection_allowed"]
            is False
        )
        assert request["validation_allowed"] is False
        assert request["state_mutation_allowed"] is False


def test_every_request_has_adapter_contract() -> None:
    manifest = _manifest()

    for request in manifest["typed_requests"]:
        contract = ADAPTER_CONTRACTS[
            request["adapter_family"]
        ]

        assert request["allowed_inputs"] == list(
            contract["allowed_inputs"]
        )
        assert request["required_outputs"] == list(
            contract["required_outputs"]
        )
        assert (
            request["prohibited_operations"]
            == list(contract["prohibited_operations"])
        )


def test_every_request_has_downstream_blockers() -> None:
    manifest = _manifest()

    for request in manifest["typed_requests"]:
        assert (
            "typed-request-human-review-required"
            in request["blocked_by"]
        )
        assert (
            "execution-gate-review-required"
            in request["blocked_by"]
        )
        assert (
            "runtime-execution-disabled"
            in request["blocked_by"]
        )


def test_runtime_requests_require_focus_endpoint() -> None:
    manifest = _manifest()

    for request in manifest["typed_requests"]:
        if request["requires_runtime_gate"]:
            assert (
                request["requires_focus_endpoint"]
                is True
            )
            assert "focus-endpoint-required" in (
                request["blocked_by"]
            )
            assert (
                "runtime-human-approval-required"
                in request["blocked_by"]
            )
            assert (
                "runtime-guard-confirmation-required"
                in request["blocked_by"]
            )
        else:
            assert (
                request["requires_focus_endpoint"]
                is False
            )


def test_local_source_request_contract() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "local-source-review",
    )

    assert request["tool_family"] == (
        "local-file-analysis"
    )
    assert request["adapter_family"] == "local-file"
    assert request["risk_level"] == "low"
    assert request["requires_runtime_gate"] is False
    assert request["requires_focus_endpoint"] is False
    assert "network access" in (
        request["prohibited_operations"]
    )
    assert "shell execution" in (
        request["prohibited_operations"]
    )


def test_local_artifact_request_contract() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "local-artifact-review",
    )

    assert request["tool_family"] == (
        "local-artifact-analysis"
    )
    assert request["adapter_family"] == (
        "local-artifact"
    )
    assert request["risk_level"] == "low"
    assert "network replay" in (
        request["prohibited_operations"]
    )
    assert "artifact mutation" in (
        request["prohibited_operations"]
    )


def test_browser_request_contract() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "browser-observation-proposal",
    )

    assert request["tool_family"] == "browser"
    assert request["adapter_family"] == "browser"
    assert request["risk_level"] == "medium"
    assert request["requires_runtime_gate"] is True
    assert request["requires_focus_endpoint"] is True
    assert request["requires_observation_capture"] is True
    assert "automatic navigation" in (
        request["prohibited_operations"]
    )
    assert "form submission" in (
        request["prohibited_operations"]
    )
    assert "credential entry" in (
        request["prohibited_operations"]
    )


def test_burp_request_contract() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "burp-request-review-proposal",
    )

    assert request["tool_family"] == "burp"
    assert request["adapter_family"] == "burp"
    assert request["risk_level"] == "medium"
    assert request["requires_runtime_gate"] is True
    assert "request replay" in (
        request["prohibited_operations"]
    )
    assert "intruder execution" in (
        request["prohibited_operations"]
    )
    assert "active scanning" in (
        request["prohibited_operations"]
    )


def test_shell_review_contract_prohibits_commands() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "command-proposal-preparation",
    )

    assert request["tool_family"] == "shell-review"
    assert request["adapter_family"] == "shell-review"
    assert request["risk_level"] == "high"
    assert "command generation" in (
        request["prohibited_operations"]
    )
    assert "shell execution" in (
        request["prohibited_operations"]
    )
    assert "package installation" in (
        request["prohibited_operations"]
    )
    assert "process creation" in (
        request["prohibited_operations"]
    )


def test_evidence_contract_prohibits_collection() -> None:
    manifest = _manifest()
    request = _request(
        manifest,
        "evidence-plan-preparation",
    )

    assert request["tool_family"] == (
        "evidence-planning"
    )
    assert request["adapter_family"] == "evidence"
    assert request["requires_runtime_gate"] is True
    assert "evidence collection" in (
        request["prohibited_operations"]
    )
    assert "screenshot capture" in (
        request["prohibited_operations"]
    )
    assert "traffic capture" in (
        request["prohibited_operations"]
    )


def test_execution_gate_input_is_compatible() -> None:
    manifest = _manifest()
    gate_input = manifest["execution_gate_input"]

    assert gate_input["target_name"] == (
        "demo-self-hosted-product"
    )
    assert gate_input["focus_endpoint"] is None
    assert gate_input["source_approval_status"] == (
        "human-approved-for-planning"
    )
    assert gate_input["execution_allowed"] is False
    assert gate_input["provider_execution_enabled"] is False
    assert gate_input["planning_only"] is True
    assert gate_input["execution_state"] == "not_executed"
    assert len(gate_input["requests"]) == 8

    for request in gate_input["requests"]:
        assert request["name"]
        assert request["tool_family"]
        assert request["purpose"]
        assert (
            request["requires_human_approval"]
            is True
        )
        assert request["execution_allowed"] is False
        assert request["blocked_by"]
        assert request["expected_artifact"]


def test_gate_preview_fails_closed_without_endpoint() -> None:
    manifest = _manifest()
    preview = manifest["execution_gate_preview"]

    assert (
        manifest["execution_gate_preview_decision"]
        == "blocked-missing-focus-endpoint"
    )
    assert (
        manifest[
            "execution_gate_preview_execution_allowed"
        ]
        is False
    )
    assert preview["gate_decision"] == (
        "blocked-missing-focus-endpoint"
    )
    assert preview["execution_allowed"] is False
    assert preview["planning_only"] is True
    assert preview["execution_state"] == "not_executed"
    assert len(preview["gate_items"]) == 8


def test_focus_endpoint_changes_gate_preview() -> None:
    endpoint = "/api/projects/123/workers/456"
    manifest = _manifest(
        focus_endpoint=endpoint
    )

    assert manifest["focus_endpoint"] == endpoint
    assert (
        manifest[
            "requires_focus_endpoint_before_runtime_review"
        ]
        is False
    )
    assert (
        manifest["execution_gate_preview_decision"]
        == "blocked-manifest-execution-disabled"
    )
    assert (
        manifest[
            "execution_gate_preview_execution_allowed"
        ]
        is False
    )
    assert (
        manifest["execution_gate_input"][
            "focus_endpoint"
        ]
        == endpoint
    )


def test_missing_focus_endpoint_is_reported() -> None:
    manifest = _manifest()

    assert (
        manifest[
            "requires_focus_endpoint_before_runtime_review"
        ]
        is True
    )

    allowed = "\n".join(
        manifest["allowed_next_steps"]
    )

    assert "Select and validate a focus endpoint" in allowed


def test_mixed_decisions_create_subset_manifest() -> None:
    manifest = _manifest(
        decisions=[
            "approved",
            "rejected",
            "approved",
            "deferred",
            "approved",
            "rejected",
            "approved",
            "rejected",
        ]
    )

    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert manifest["typed_request_count"] == 4
    assert len(manifest["typed_requests"]) == 4
    assert {
        item["manual_order"]
        for item in manifest["typed_requests"]
    } == {1, 3, 5, 7}


def test_wrong_source_kind_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["kind"] = "wrong-kind"

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-approved-action-packet"
    )
    assert manifest["manifest_ready"] is False
    assert "kind" in _subjects(
        manifest,
        "source_findings",
    )


def test_missing_target_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["target_name"] = ""

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-approved-action-packet"
    )
    assert "target_name" in _subjects(
        manifest,
        "source_findings",
    )


def test_non_ready_source_status_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["packet_status"] = (
        "blocked-no-approved-actions"
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-approved-action-packet-not-ready"
    )
    assert manifest["manifest_ready"] is False


def test_packet_ready_false_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["packet_ready"] = False

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-approved-action-packet-not-ready"
    )


def test_source_manifest_ready_false_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["typed_tool_request_manifest_ready"] = False

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-approved-action-packet-not-ready"
    )


def test_non_list_approved_actions_are_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"] = {
        "wrong": True
    }

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-approved-action-packet"
    )
    assert "approved_actions" in _subjects(
        manifest,
        "source_findings",
    )


def test_approved_action_count_mismatch_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_action_count"] = 999

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-approved-action-packet"
    )
    assert "approved_action_count" in _subjects(
        manifest,
        "source_findings",
    )


def test_synthetic_empty_ready_packet_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"] = []
    packet["approved_action_count"] = 0

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-no-approved-actions"
    )
    assert manifest["typed_request_count"] == 0
    assert manifest["manifest_ready"] is False


def test_top_level_unsafe_source_flag_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["execution_allowed"] = True

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-unsafe-approved-action-packet"
    )
    assert manifest["runtime_execution_allowed"] is False


def test_source_must_remain_planning_only() -> None:
    packet = _approved_action_packet()
    packet["planning_only"] = False

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-unsafe-approved-action-packet"
    )


def test_source_must_remain_not_executed() -> None:
    packet = _approved_action_packet()
    packet["execution_state"] = "executed"

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-unsafe-approved-action-packet"
    )


def test_missing_source_safety_object_is_blocked() -> None:
    packet = _approved_action_packet()
    del packet["safety"]

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-unsafe-approved-action-packet"
    )
    assert "safety" in _subjects(
        manifest,
        "source_findings",
    )


def test_required_true_source_safety_is_enforced() -> None:
    fields = (
        "local_only",
        "planning_only",
        "human_approval_recorded",
        "typed_normalization_only",
    )

    for field in fields:
        packet = _approved_action_packet()
        packet["safety"][field] = False

        manifest = (
            build_research_typed_tool_request_manifest(
                packet
            )
        )

        assert manifest["manifest_status"] == (
            "blocked-unsafe-approved-action-packet"
        )
        assert f"safety.{field}" in _subjects(
            manifest,
            "source_findings",
        )


def test_required_false_source_safety_is_enforced() -> None:
    fields = (
        "network_interaction",
        "target_mutation",
        "command_generation",
        "tool_execution",
        "browser_execution",
        "curl_execution",
        "kali_execution",
        "burp_execution",
        "provider_execution",
        "package_installation",
        "target_interaction",
        "evidence_collection",
        "validation_execution",
        "runtime_execution_allowed",
        "state_mutation",
        "report_submission",
        "vulnerability_confirmation",
    )

    for field in fields:
        packet = _approved_action_packet()
        packet["safety"][field] = True

        manifest = (
            build_research_typed_tool_request_manifest(
                packet
            )
        )

        assert manifest["manifest_status"] == (
            "blocked-unsafe-approved-action-packet"
        )
        assert f"safety.{field}" in _subjects(
            manifest,
            "source_findings",
        )


def test_missing_action_field_is_blocked() -> None:
    packet = _approved_action_packet()
    del packet["approved_actions"][0]["purpose"]

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "Required action field is missing: purpose."
        == message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_duplicate_action_id_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][1]["action_id"] = (
        packet["approved_actions"][0]["action_id"]
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "Duplicate action_id" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_unsupported_action_type_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["action_type"] = (
        "autonomous-runtime-execution"
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "Unsupported action type" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_tool_family_mismatch_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["tool_family"] = (
        "browser"
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "tool_family mismatch" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_adapter_family_mismatch_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "adapter_family"
    ] = "unknown-adapter"

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "adapter_family mismatch" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )
    assert any(
        "No adapter contract exists" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_request_kind_mismatch_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "request_kind"
    ] = "wrong-request-kind"

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "request_kind mismatch" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_risk_level_mismatch_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["risk_level"] = (
        "critical"
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "risk_level mismatch" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_human_approval_requirement_is_enforced() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "requires_human_approval"
    ] = False

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "requires_human_approval must be true"
        in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_manifest_eligibility_is_enforced() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "manifest_eligible"
    ] = False

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "manifest_eligible must be true"
        in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_action_execution_flag_is_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "execution_allowed"
    ] = True

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "Action field must remain false"
        in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_empty_blockers_are_blocked() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["blocked_by"] = []

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "blocked-invalid-typed-requests"
    )
    assert any(
        "blocked_by must not be empty" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_empty_expected_artifact_is_medium_only() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0][
        "expected_artifact"
    ] = ""

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert manifest["manifest_ready"] is True
    assert manifest["counts"]["high_findings"] == 0
    assert manifest["counts"]["medium_findings"] == 1


def test_invalid_manual_order_is_medium_only() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][0]["manual_order"] = 0

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert manifest["counts"]["medium_findings"] >= 1


def test_duplicate_manual_order_is_medium_only() -> None:
    packet = _approved_action_packet()
    packet["approved_actions"][1]["manual_order"] = (
        packet["approved_actions"][0]["manual_order"]
    )

    manifest = build_research_typed_tool_request_manifest(
        packet
    )

    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert any(
        "Duplicate manual_order" in message
        for message in _messages(
            manifest,
            "request_findings",
        )
    )


def test_manifest_remains_fail_closed() -> None:
    manifest = _manifest()

    assert manifest["command_generation_allowed"] is False
    assert manifest["payload_generation_allowed"] is False
    assert manifest["package_installation_allowed"] is False
    assert manifest["execution_allowed"] is False
    assert manifest["runtime_execution_allowed"] is False
    assert manifest["network_interaction_allowed"] is False
    assert manifest["target_interaction_allowed"] is False
    assert manifest["evidence_collection_allowed"] is False
    assert manifest["validation_allowed"] is False
    assert manifest["state_mutation_allowed"] is False
    assert manifest["report_submission_allowed"] is False
    assert (
        manifest["vulnerability_confirmation_allowed"]
        is False
    )

    assert manifest["planning_only"] is True
    assert manifest["execution_state"] == "not_executed"

    safety = manifest["safety"]

    assert safety["local_only"] is True
    assert safety["planning_only"] is True
    assert safety["typed_requests_only"] is True
    assert (
        safety["source_human_approval_required"]
        is True
    )
    assert safety["execution_gate_required"] is True
    assert safety["command_generation"] is False
    assert safety["payload_generation"] is False
    assert safety["tool_execution"] is False
    assert safety["browser_execution"] is False
    assert safety["burp_execution"] is False
    assert safety["kali_execution"] is False
    assert safety["package_installation"] is False
    assert safety["network_interaction"] is False
    assert safety["target_interaction"] is False
    assert safety["evidence_collection"] is False
    assert safety["validation_execution"] is False
    assert safety["runtime_execution_allowed"] is False


def test_markdown_contains_required_sections() -> None:
    manifest = _manifest()

    markdown = (
        render_research_typed_tool_request_manifest_markdown(
            manifest
        )
    )

    assert "# Research Typed Tool Request Manifest" in markdown
    assert "## Manifest Status" in markdown
    assert "## Typed Requests" in markdown
    assert "## Adapter Contracts" in markdown
    assert "## Execution Gate Compatibility" in markdown
    assert "## Source Findings" in markdown
    assert "## Request Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Rejected Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "manifest_status: "
        "`ready-for-tool-execution-gate-review`"
        in markdown
    )
    assert "manifest_ready: `true`" in markdown
    assert (
        "execution_gate_input_ready: `true`"
        in markdown
    )
    assert "runtime_execution_allowed: `false`" in markdown
    assert "Command generation allowed: `false`" in markdown
    assert "Payload generation allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "\\n" not in markdown


def test_file_builder_writes_markdown_and_json(
    tmp_path,
) -> None:
    packet = _approved_action_packet()

    packet_file = tmp_path / "approved-actions.json"
    markdown_file = (
        tmp_path
        / "output"
        / "typed-manifest.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "typed-manifest.json"
    )

    packet_file.write_text(
        json.dumps(packet),
        encoding="utf-8",
    )

    manifest = build_typed_manifest_from_file(
        packet_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert manifest["manifest_status"] == (
        "ready-for-tool-execution-gate-review"
    )
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_typed_tool_request_manifest"
    )
    assert written["typed_request_count"] == 8
    assert written["manifest_ready"] is True
    assert written["runtime_execution_allowed"] is False
    assert written["execution_gate_input"]["requests"]

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Typed Tool Request Manifest" in markdown
