from __future__ import annotations

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
    no_execution_flag_findings,
    safety_metadata_findings,
    validate_scoped_runtime_archive_chain_artifact,
)


def _safe_artifact() -> dict:
    artifact = {
        "kind": "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
        "archive_state": "archive_manifest_local_only",
        "receipt_status": "accepted-local-bundle-handoff-checklist-summary-receipt-no-execution",
        "gate_id": "SREG-TEST",
        "request_id": "REQ-TEST",
        "archive_manifest_id": "ARCHIVE-TEST",
        "receipt_id": "RECEIPT-TEST",
        "summary_id": "SUMMARY-TEST",
        "checklist_id": "CHECKLIST-TEST",
        "handoff_packet_id": "HANDOFF-TEST",
        "upstream_artifact_chain": list(EXPECTED_ARCHIVE_CHAIN),
        "safety": {key: False for key in SAFETY_FALSE_KEYS},
    }
    artifact.update({flag: False for flag in NO_EXECUTION_FLAGS})
    return artifact


def test_archive_chain_validation_accepts_expected_artifact_without_execution() -> None:
    artifact = _safe_artifact()

    result = validate_scoped_runtime_archive_chain_artifact(
        artifact,
        expected_kind="scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        required_fields=("gate_id", "request_id", "archive_manifest_id"),
        expected_statuses={
            "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
            "archive_state": "archive_manifest_local_only",
        },
        expected_upstream_chain=EXPECTED_ARCHIVE_CHAIN,
        validated_by="human-reviewer",
        validation_note="Validated local archive-chain artifact only; no execution authorized.",
    )
    data = result.to_dict()

    assert data["kind"] == "scoped_runtime_archive_chain_validation_result"
    assert data["validation_status"] == "validated-local-archive-chain-artifact-no-execution"
    assert data["validation_state"] == "validated_archive_chain_local_only"
    assert data["validated_by"] == "human-reviewer"
    assert data["artifact_kind"] == "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest"
    assert data["upstream_artifact_count"] == 7
    assert data["expected_upstream_artifact_count"] == 7
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["blocking_findings"] == []


def test_archive_chain_validation_blocks_bad_status_chain_flags_and_safety() -> None:
    artifact = _safe_artifact()
    artifact["archive_status"] = "blocked"
    artifact["network_requests_allowed"] = True
    artifact["safety"]["network_requests"] = True
    artifact["upstream_artifact_chain"] = ["wrong"]
    artifact.pop("archive_manifest_id")

    result = validate_scoped_runtime_archive_chain_artifact(
        artifact,
        expected_kind="scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        required_fields=("gate_id", "request_id", "archive_manifest_id"),
        expected_statuses={
            "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
        },
        expected_upstream_chain=EXPECTED_ARCHIVE_CHAIN,
    )
    data = result.to_dict()

    assert data["validation_status"] == "blocked-local-archive-chain-artifact-validation"
    assert any("missing archive_manifest_id" in item for item in data["blocking_findings"])
    assert any("archive_status" in item for item in data["blocking_findings"])
    assert any("upstream artifact chain" in item for item in data["blocking_findings"])
    assert any("network_requests_allowed" in item for item in data["blocking_findings"])
    assert any("network_requests false" in item for item in data["blocking_findings"])


def test_archive_chain_helpers_report_no_execution_and_safety_findings() -> None:
    artifact = _safe_artifact()
    assert no_execution_flag_findings(artifact) == ()
    assert safety_metadata_findings(artifact) == ()

    artifact["tool_execution_allowed"] = True
    artifact["safety"]["tool_execution"] = True

    assert no_execution_flag_findings(artifact) == ("artifact does not keep tool_execution_allowed false.",)
    assert safety_metadata_findings(artifact) == ("artifact safety metadata does not keep tool_execution false.",)


def test_archive_chain_validation_markdown_is_human_readable_and_safe() -> None:
    artifact = _safe_artifact()
    result = validate_scoped_runtime_archive_chain_artifact(
        artifact,
        expected_kind="scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        required_fields=("gate_id", "request_id", "archive_manifest_id"),
        expected_statuses={
            "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
        },
        expected_upstream_chain=EXPECTED_ARCHIVE_CHAIN,
        validation_note="Validated local archive-chain artifact only; no execution authorized.",
    )

    markdown = result.to_markdown()

    assert "# Scoped Runtime Archive Chain Validation" in markdown
    assert "Validation status: `validated-local-archive-chain-artifact-no-execution`" in markdown
    assert "Validation state: `validated_archive_chain_local_only`" in markdown
    assert "Network requests allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "does not execute curl" in markdown
