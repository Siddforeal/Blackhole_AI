from __future__ import annotations

import json
from pathlib import Path

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
)
from bugintel.adapters.scoped_runtime.archive_chain_integrity import (
    build_scoped_runtime_archive_chain_integrity_manifest,
    verify_scoped_runtime_archive_chain_integrity_manifest,
)


def _safe_archive() -> dict:
    artifact = {
        "kind": "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        "gate_id": "SREG-TEST",
        "request_id": "REQ-TEST",
        "bundle_mode": "local_files_only_no_execution",
        "archive_manifest_id": "ARCHIVE-TEST",
        "receipt_id": "RECEIPT-TEST",
        "summary_id": "SUMMARY-TEST",
        "checklist_id": "CHECKLIST-TEST",
        "handoff_packet_id": "HANDOFF-TEST",
        "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
        "archive_state": "archive_manifest_local_only",
        "upstream_artifact_chain": list(EXPECTED_ARCHIVE_CHAIN),
        "safety": {key: False for key in SAFETY_FALSE_KEYS},
    }
    artifact.update({flag: False for flag in NO_EXECUTION_FLAGS})
    return artifact


def test_archive_chain_integrity_manifest_hashes_and_batch_validates_local_artifacts(tmp_path: Path) -> None:
    artifact_file = tmp_path / "archive.json"
    artifact_file.write_text(json.dumps(_safe_archive(), sort_keys=True))

    manifest = build_scoped_runtime_archive_chain_integrity_manifest(tmp_path)
    data = manifest.to_dict()

    assert data["kind"] == "scoped_runtime_archive_chain_integrity_manifest"
    assert data["manifest_status"] == "created-local-archive-chain-integrity-manifest-no-execution"
    assert data["manifest_state"] == "integrity_manifest_local_only"
    assert data["artifact_count"] == 1
    assert data["accepted_count"] == 1
    assert data["blocked_count"] == 0
    assert data["batch_validation_status"] == "validated-local-archive-chain-batch-no-execution"
    assert data["records"][0]["filename"] == "archive.json"
    assert len(data["records"][0]["sha256"]) == 64
    assert data["records"][0]["json_load_status"] == "loaded"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["blocking_findings"] == []


def test_archive_chain_integrity_verification_recomputes_hashes(tmp_path: Path) -> None:
    artifact_file = tmp_path / "archive.json"
    artifact_file.write_text(json.dumps(_safe_archive(), sort_keys=True))
    manifest = build_scoped_runtime_archive_chain_integrity_manifest(tmp_path)

    verification = verify_scoped_runtime_archive_chain_integrity_manifest(
        manifest.to_dict(),
        artifact_dir=tmp_path,
    )
    data = verification.to_dict()

    assert data["kind"] == "scoped_runtime_archive_chain_integrity_verification"
    assert data["verification_status"] == "verified-local-archive-chain-integrity-manifest-no-execution"
    assert data["verification_state"] == "integrity_verified_local_only"
    assert data["artifact_count"] == 1
    assert data["verified_count"] == 1
    assert data["missing_count"] == 0
    assert data["mismatch_count"] == 0
    assert data["recomputed_from_files"] is True
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["blocking_findings"] == []


def test_archive_chain_integrity_verification_blocks_hash_mismatch(tmp_path: Path) -> None:
    artifact_file = tmp_path / "archive.json"
    artifact_file.write_text(json.dumps(_safe_archive(), sort_keys=True))
    manifest = build_scoped_runtime_archive_chain_integrity_manifest(tmp_path)

    artifact_file.write_text(json.dumps({**_safe_archive(), "archive_state": "tampered"}, sort_keys=True))

    data = verify_scoped_runtime_archive_chain_integrity_manifest(
        manifest.to_dict(),
        artifact_dir=tmp_path,
    ).to_dict()

    assert data["verification_status"] == "blocked-local-archive-chain-integrity-verification"
    assert data["verified_count"] == 0
    assert data["mismatch_count"] == 1
    assert any("hash mismatch" in item for item in data["blocking_findings"])


def test_archive_chain_integrity_markdown_is_human_readable_and_safe(tmp_path: Path) -> None:
    artifact_file = tmp_path / "archive.json"
    artifact_file.write_text(json.dumps(_safe_archive(), sort_keys=True))

    markdown = build_scoped_runtime_archive_chain_integrity_manifest(tmp_path).to_markdown()

    assert "# Scoped Runtime Archive Chain Integrity Manifest" in markdown
    assert "Manifest status: `created-local-archive-chain-integrity-manifest-no-execution`" in markdown
    assert "Artifact count: `1`" in markdown
    assert "Network requests allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "does not execute curl" in markdown
