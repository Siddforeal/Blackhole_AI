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


def test_scoped_runtime_archive_chain_batch_validate_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    artifact_dir.mkdir()
    (artifact_dir / "archive.json").write_text(json.dumps(_safe_archive()))

    output_json = tmp_path / "batch.json"
    output_markdown = tmp_path / "batch.md"

    result = runner.invoke(
        app,
        [
            "scoped-runtime-archive-chain-batch-validate",
            str(artifact_dir),
            "--json-output",
            str(output_json),
            "--output-file",
            str(output_markdown),
        ],
    )

    assert result.exit_code == 0
    assert output_json.exists()
    assert output_markdown.exists()

    data = json.loads(output_json.read_text())
    markdown = output_markdown.read_text()
    normalized_stdout = " ".join(result.stdout.split())

    assert data["kind"] == "scoped_runtime_archive_chain_batch_validation_report"
    assert data["batch_status"] == "validated-local-archive-chain-batch-no-execution"
    assert data["batch_state"] == "batch_validated_archive_chain_local_only"
    assert data["artifact_count"] == 1
    assert data["accepted_count"] == 1
    assert data["blocked_count"] == 0
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Archive Chain Batch Validation" in markdown
    assert "Saved scoped runtime archive-chain batch validation JSON" in normalized_stdout
    assert "Saved scoped runtime archive-chain batch validation Markdown" in normalized_stdout
