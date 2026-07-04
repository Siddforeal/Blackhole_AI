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


def _safe_artifact() -> dict:
    artifact = {
        "kind": "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
        "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
        "archive_state": "archive_manifest_local_only",
        "gate_id": "SREG-TEST",
        "request_id": "REQ-TEST",
        "archive_manifest_id": "ARCHIVE-TEST",
        "upstream_artifact_chain": list(EXPECTED_ARCHIVE_CHAIN),
        "safety": {key: False for key in SAFETY_FALSE_KEYS},
    }
    artifact.update({flag: False for flag in NO_EXECUTION_FLAGS})
    return artifact


def test_scoped_runtime_archive_chain_validate_cli_writes_json_and_markdown(tmp_path: Path) -> None:
    artifact_file = tmp_path / "artifact.json"
    output_json = tmp_path / "validation.json"
    output_markdown = tmp_path / "validation.md"
    artifact_file.write_text(json.dumps(_safe_artifact()))

    result = runner.invoke(
        app,
        [
            "scoped-runtime-archive-chain-validate",
            str(artifact_file),
            "--expected-kind",
            "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
            "--required-field",
            "gate_id",
            "--required-field",
            "request_id",
            "--required-field",
            "archive_manifest_id",
            "--expect-status",
            "archive_status=archived-local-bundle-handoff-receipt-manifest-no-execution",
            "--expect-status",
            "archive_state=archive_manifest_local_only",
            "--expect-default-archive-chain",
            "--validated-by",
            "human-reviewer",
            "--validation-note",
            "Validated local archive-chain artifact only; no execution authorized.",
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

    assert data["kind"] == "scoped_runtime_archive_chain_validation_result"
    assert data["validation_status"] == "validated-local-archive-chain-artifact-no-execution"
    assert data["validation_state"] == "validated_archive_chain_local_only"
    assert data["validated_by"] == "human-reviewer"
    assert data["upstream_artifact_count"] == 7
    assert data["expected_upstream_artifact_count"] == 7
    assert data["can_execute_now"] is False
    assert data["network_requests_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert "# Scoped Runtime Archive Chain Validation" in markdown
    assert "Saved scoped runtime archive-chain validation JSON" in normalized_stdout
    assert "Saved scoped runtime archive-chain validation Markdown" in normalized_stdout
