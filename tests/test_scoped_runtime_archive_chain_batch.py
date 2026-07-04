from __future__ import annotations

import json
from pathlib import Path

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
)
from bugintel.adapters.scoped_runtime.archive_chain_batch import (
    validate_scoped_runtime_archive_chain_directory,
)


def _safe_artifact(kind: str, **extra: object) -> dict:
    artifact = {
        "kind": kind,
        "gate_id": "SREG-TEST",
        "request_id": "REQ-TEST",
        "bundle_mode": "local_files_only_no_execution",
        "safety": {key: False for key in SAFETY_FALSE_KEYS},
    }
    artifact.update({flag: False for flag in NO_EXECUTION_FLAGS})
    artifact.update(extra)
    return artifact


def test_archive_chain_batch_validation_accepts_multiple_known_artifacts(tmp_path: Path) -> None:
    (tmp_path / "archive.json").write_text(json.dumps(_safe_artifact(
        "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        archive_manifest_id="ARCHIVE-TEST",
        receipt_id="RECEIPT-TEST",
        summary_id="SUMMARY-TEST",
        checklist_id="CHECKLIST-TEST",
        handoff_packet_id="HANDOFF-TEST",
        archive_status="archived-local-bundle-handoff-receipt-manifest-no-execution",
        archive_state="archive_manifest_local_only",
        upstream_artifact_chain=list(EXPECTED_ARCHIVE_CHAIN),
    )))
    (tmp_path / "archive-review.json").write_text(json.dumps(_safe_artifact(
        "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification_review_packet",
        review_packet_id="REVIEW-TEST",
        verification_id="VERIFY-TEST",
        archive_manifest_id="ARCHIVE-TEST",
        receipt_id="RECEIPT-TEST",
        review_status="accepted-local-bundle-handoff-receipt-archive-manifest-verification-review-no-execution",
        review_state="reviewed_archive_manifest_verification_local_only",
    )))

    report = validate_scoped_runtime_archive_chain_directory(tmp_path)
    data = report.to_dict()

    assert data["kind"] == "scoped_runtime_archive_chain_batch_validation_report"
    assert data["batch_status"] == "validated-local-archive-chain-batch-no-execution"
    assert data["batch_state"] == "batch_validated_archive_chain_local_only"
    assert data["artifact_count"] == 2
    assert data["accepted_count"] == 2
    assert data["blocked_count"] == 0
    assert data["kind_counts"]["scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest"] == 1
    assert data["kind_counts"]["scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification_review_packet"] == 1
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["blocking_findings"] == []


def test_archive_chain_batch_validation_blocks_bad_artifact(tmp_path: Path) -> None:
    bad = _safe_artifact(
        "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        archive_manifest_id="ARCHIVE-TEST",
        receipt_id="RECEIPT-TEST",
        summary_id="SUMMARY-TEST",
        checklist_id="CHECKLIST-TEST",
        handoff_packet_id="HANDOFF-TEST",
        archive_status="blocked",
        archive_state="archive_manifest_local_only",
        upstream_artifact_chain=["wrong"],
    )
    bad["network_requests_allowed"] = True
    bad["safety"]["network_requests"] = True
    (tmp_path / "bad.json").write_text(json.dumps(bad))

    data = validate_scoped_runtime_archive_chain_directory(tmp_path).to_dict()

    assert data["batch_status"] == "blocked-local-archive-chain-batch-validation"
    assert data["artifact_count"] == 1
    assert data["accepted_count"] == 0
    assert data["blocked_count"] == 1
    assert any("archive_status" in item for item in data["blocking_findings"])
    assert any("upstream artifact chain" in item for item in data["blocking_findings"])
    assert any("network_requests_allowed" in item for item in data["blocking_findings"])


def test_archive_chain_batch_validation_blocks_empty_directory(tmp_path: Path) -> None:
    data = validate_scoped_runtime_archive_chain_directory(tmp_path).to_dict()

    assert data["batch_status"] == "blocked-local-archive-chain-batch-validation"
    assert data["artifact_count"] == 0
    assert data["accepted_count"] == 0
    assert data["blocked_count"] == 0
    assert data["blocking_findings"] == ["Artifact directory contained no JSON files."]


def test_archive_chain_batch_validation_markdown_is_human_readable_and_safe(tmp_path: Path) -> None:
    (tmp_path / "archive.json").write_text(json.dumps(_safe_artifact(
        "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        archive_manifest_id="ARCHIVE-TEST",
        receipt_id="RECEIPT-TEST",
        summary_id="SUMMARY-TEST",
        checklist_id="CHECKLIST-TEST",
        handoff_packet_id="HANDOFF-TEST",
        archive_status="archived-local-bundle-handoff-receipt-manifest-no-execution",
        archive_state="archive_manifest_local_only",
        upstream_artifact_chain=list(EXPECTED_ARCHIVE_CHAIN),
    )))

    markdown = validate_scoped_runtime_archive_chain_directory(tmp_path).to_markdown()

    assert "# Scoped Runtime Archive Chain Batch Validation" in markdown
    assert "Batch status: `validated-local-archive-chain-batch-no-execution`" in markdown
    assert "Artifact count: `1`" in markdown
    assert "Network requests allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "does not execute curl" in markdown
