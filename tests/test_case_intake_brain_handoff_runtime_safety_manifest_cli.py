import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
    record_case_intake_brain_handoff_approval_decision,
)
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
    export_case_intake_brain_handoff_approval_packet,
)
from bugintel.core.case_intake_brain_handoff_execution_approval_gate import (
    record_case_intake_brain_handoff_execution_approval_gate,
)
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import (
    export_case_intake_brain_handoff_read_only_command_proposal,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _execution_gate() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    approval_decision = record_case_intake_brain_handoff_approval_decision(
        packet,
        decision="approved",
        decided_by="sidd",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()
    command_proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()
    return record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision="approved",
        decided_by="sidd",
        reason="Approved only for future controlled read-only execution adapter preview.",
    ).to_dict()


def test_runtime_safety_manifest_cli_writes_json_and_markdown(tmp_path) -> None:
    gate_file = tmp_path / "execution-approval.json"
    json_output = tmp_path / "runtime-safety-manifest.json"
    markdown_output = tmp_path / "runtime-safety-manifest.md"

    gate_file.write_text(json.dumps(_execution_gate()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-runtime-safety-manifest",
            str(gate_file),
            "--adapter-family",
            "curl",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Runtime Safety Manifest" in result.output
    assert "Saved case intake brain runtime safety manifest JSON" in result.output
    assert "Saved case intake brain runtime safety manifest Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_runtime_safety_manifest"
    assert data["manifest_id"] == "RSM-EG-CP-AD-AP-001"
    assert data["adapter_family"] == "curl"
    assert data["runtime_manifest_status"] == "ready-for-future-adapter-review-no-execution"
    assert data["can_execute_now"] is False
    assert data["manifest_allows_execution"] is False
    assert data["execution_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False

    markdown = markdown_output.read_text()
    assert "# Case Intake Brain Runtime Safety Manifest" in markdown
    assert "## Runtime Scope Check Requirements" in markdown
    assert "No command execution" in markdown


def test_runtime_safety_manifest_cli_rejects_missing_gate_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-runtime-safety-manifest",
            str(missing),
            "--adapter-family",
            "curl",
        ],
    )

    assert result.exit_code != 0
    assert "execution approval gate file does not exist" in result.output


def test_runtime_safety_manifest_cli_blocks_unsupported_adapter(tmp_path) -> None:
    gate_file = tmp_path / "execution-approval.json"
    json_output = tmp_path / "runtime-safety-manifest.json"

    gate_file.write_text(json.dumps(_execution_gate()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-runtime-safety-manifest",
            str(gate_file),
            "--adapter-family",
            "burp",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Unsupported adapter family" in data["block_reason"]
    assert data["can_execute_now"] is False
