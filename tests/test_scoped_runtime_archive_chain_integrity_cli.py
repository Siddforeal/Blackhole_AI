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


def test_archive_chain_integrity_manifest_and_verify_cli_write_json_and_markdown(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "archive.json").write_text(json.dumps(_safe_archive(), sort_keys=True))

    manifest_json = tmp_path / "integrity.json"
    manifest_md = tmp_path / "integrity.md"
    verify_json = tmp_path / "verify.json"
    verify_md = tmp_path / "verify.md"

    manifest_result = runner.invoke(
        app,
        [
            "scoped-runtime-archive-chain-integrity-manifest",
            str(artifact_dir),
            "--json-output",
            str(manifest_json),
            "--output-file",
            str(manifest_md),
        ],
    )

    assert manifest_result.exit_code == 0
    assert manifest_json.exists()
    assert manifest_md.exists()

    manifest_data = json.loads(manifest_json.read_text())
    assert manifest_data["manifest_status"] == "created-local-archive-chain-integrity-manifest-no-execution"
    assert manifest_data["artifact_count"] == 1
    assert manifest_data["accepted_count"] == 1
    assert manifest_data["blocked_count"] == 0

    verify_result = runner.invoke(
        app,
        [
            "scoped-runtime-archive-chain-integrity-verify",
            str(manifest_json),
            "--artifact-dir",
            str(artifact_dir),
            "--json-output",
            str(verify_json),
            "--output-file",
            str(verify_md),
        ],
    )

    assert verify_result.exit_code == 0
    assert verify_json.exists()
    assert verify_md.exists()

    verify_data = json.loads(verify_json.read_text())
    verify_markdown = verify_md.read_text()
    normalized_stdout = " ".join(verify_result.stdout.split())

    assert verify_data["verification_status"] == "verified-local-archive-chain-integrity-manifest-no-execution"
    assert verify_data["verified_count"] == 1
    assert verify_data["mismatch_count"] == 0
    assert verify_data["network_requests_allowed"] is False
    assert verify_data["tool_execution_allowed"] is False
    assert "# Scoped Runtime Archive Chain Integrity Verification" in verify_markdown
    assert "Saved scoped runtime archive-chain integrity verification JSON" in normalized_stdout
    assert "Saved scoped runtime archive-chain integrity verification Markdown" in normalized_stdout
