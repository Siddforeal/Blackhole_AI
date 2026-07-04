from __future__ import annotations

import json
from pathlib import Path

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
)
from bugintel.adapters.scoped_runtime.archive_chain_audit_pack import (
    build_scoped_runtime_archive_chain_audit_pack,
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


def test_archive_chain_audit_pack_writes_expected_files_and_preserves_safety(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    output_dir = tmp_path / "audit"
    artifact_dir.mkdir()
    (artifact_dir / "archive.json").write_text(json.dumps(_safe_archive(), sort_keys=True))

    audit_pack = build_scoped_runtime_archive_chain_audit_pack(artifact_dir, output_dir)
    data = audit_pack.to_dict()

    assert data["kind"] == "scoped_runtime_archive_chain_audit_pack"
    assert data["audit_pack_status"] == "created-local-archive-chain-audit-pack-no-execution"
    assert data["audit_pack_state"] == "audit_pack_local_only"
    assert data["artifact_count"] == 1
    assert data["accepted_count"] == 1
    assert data["blocked_count"] == 0
    assert data["integrity_record_count"] == 1
    assert data["integrity_verified_count"] == 1
    assert data["integrity_missing_count"] == 0
    assert data["integrity_mismatch_count"] == 0
    assert data["batch_validation_status"] == "validated-local-archive-chain-batch-no-execution"
    assert data["integrity_manifest_status"] == "created-local-archive-chain-integrity-manifest-no-execution"
    assert data["integrity_verification_status"] == "verified-local-archive-chain-integrity-manifest-no-execution"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["blocking_findings"] == []

    for filename in (
        "batch-validation.json",
        "batch-validation.md",
        "integrity-manifest.json",
        "integrity-manifest.md",
        "integrity-verification.json",
        "integrity-verification.md",
        "audit-pack.json",
        "audit-pack.md",
        "manifest.json",
    ):
        assert (output_dir / filename).exists()


def test_archive_chain_audit_pack_blocks_invalid_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    output_dir = tmp_path / "audit"
    artifact_dir.mkdir()

    bad = _safe_archive()
    bad["archive_status"] = "blocked"
    bad["network_requests_allowed"] = True
    bad["safety"]["network_requests"] = True
    (artifact_dir / "archive.json").write_text(json.dumps(bad, sort_keys=True))

    data = build_scoped_runtime_archive_chain_audit_pack(artifact_dir, output_dir).to_dict()

    assert data["audit_pack_status"] == "blocked-local-archive-chain-audit-pack"
    assert data["artifact_count"] == 1
    assert data["accepted_count"] == 0
    assert data["blocked_count"] == 1
    assert any("archive_status" in item for item in data["blocking_findings"])
    assert any("network_requests_allowed" in item for item in data["blocking_findings"])


def test_archive_chain_audit_pack_markdown_is_human_readable_and_safe(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    output_dir = tmp_path / "audit"
    artifact_dir.mkdir()
    (artifact_dir / "archive.json").write_text(json.dumps(_safe_archive(), sort_keys=True))

    markdown = build_scoped_runtime_archive_chain_audit_pack(artifact_dir, output_dir).to_markdown()

    assert "# Scoped Runtime Archive Chain Audit Pack" in markdown
    assert "Audit pack status: `created-local-archive-chain-audit-pack-no-execution`" in markdown
    assert "Artifact count: `1`" in markdown
    assert "Integrity verified count: `1`" in markdown
    assert "Network requests allowed: `false`" in markdown
    assert "Tool execution allowed: `false`" in markdown
    assert "does not execute curl" in markdown
