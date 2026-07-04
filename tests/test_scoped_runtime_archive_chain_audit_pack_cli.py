from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
)
from bugintel.cli import app

runner = CliRunner()


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


def test_archive_chain_audit_pack_cli_writes_audit_directory(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    output_dir = tmp_path / "audit"
    artifact_dir.mkdir()
    (artifact_dir / "archive.json").write_text(json.dumps(_safe_archive(), sort_keys=True))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-archive-chain-audit-pack",
            str(artifact_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert output_dir.exists()

    audit_pack = json.loads((output_dir / "audit-pack.json").read_text())
    audit_markdown = (output_dir / "audit-pack.md").read_text()
    normalized_stdout = " ".join(result.stdout.split())

    assert audit_pack["audit_pack_status"] == "created-local-archive-chain-audit-pack-no-execution"
    assert audit_pack["audit_pack_state"] == "audit_pack_local_only"
    assert audit_pack["artifact_count"] == 1
    assert audit_pack["accepted_count"] == 1
    assert audit_pack["blocked_count"] == 0
    assert audit_pack["integrity_verified_count"] == 1
    assert audit_pack["network_requests_allowed"] is False
    assert audit_pack["tool_execution_allowed"] is False
    assert "# Scoped Runtime Archive Chain Audit Pack" in audit_markdown
    assert "Saved scoped runtime archive-chain audit pack" in normalized_stdout

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
