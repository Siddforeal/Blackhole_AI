import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import (
    export_case_intake_brain_handoff_adapter_dry_run_preview,
)
from bugintel.core.case_intake_brain_handoff_adapter_final_confirmation_packet import (
    record_case_intake_brain_handoff_adapter_final_confirmation,
)
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
from bugintel.core.case_intake_brain_handoff_runtime_safety_manifest import (
    export_case_intake_brain_handoff_runtime_safety_manifest,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _final_confirmation() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(
        plan,
        endpoint="/api/admin/users/{id}/permissions",
    ).to_dict()
    approval_decision = record_case_intake_brain_handoff_approval_decision(
        packet,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved read-only planning only with controlled accounts.",
    ).to_dict()
    command_proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family="curl",
    ).to_dict()
    execution_gate = record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved only for future controlled read-only execution adapter preview.",
    ).to_dict()
    runtime_manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        execution_gate,
        adapter_family="curl",
    ).to_dict()
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        runtime_manifest,
        target_base_url="https://example-program.test",
        controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY",
        path_parameters=["id=SYNTHETIC_USER_ID"],
    ).to_dict()
    return record_case_intake_brain_handoff_adapter_final_confirmation(
        preview,
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview is ready for future scoped adapter only.",
    ).to_dict()


def test_scoped_adapter_execution_request_cli_writes_json_and_markdown(tmp_path) -> None:
    confirmation_file = tmp_path / "adapter-final-confirmation.json"
    json_output = tmp_path / "scoped-adapter-execution-request.json"
    markdown_output = tmp_path / "scoped-adapter-execution-request.md"

    confirmation_file.write_text(json.dumps(_final_confirmation()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-request",
            str(confirmation_file),
            "--request-purpose",
            "future-scoped-curl-adapter-review",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Scoped Adapter Execution Request" in result.output
    assert "Saved case intake brain scoped adapter execution request JSON" in result.output
    assert "Saved case intake brain scoped adapter execution request Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_execution_request"
    assert data["request_id"] == "SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["request_status"] == "ready-for-future-scoped-adapter-review-no-execution"
    assert data["request_purpose"] == "future-scoped-curl-adapter-review"
    assert data["scope_validation_state"] == "not_performed"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["confirmed_by"] == "human-reviewer"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["execution_request_allows_execution"] is False
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
    assert "# Case Intake Brain Scoped Adapter Execution Request" in markdown
    assert "## Reviewed Command Packaged for Future Adapter" in markdown
    assert "No command execution" in markdown


def test_scoped_adapter_execution_request_cli_rejects_missing_confirmation_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-request",
            str(missing),
            "--request-purpose",
            "future-scoped-curl-adapter-review",
        ],
    )

    assert result.exit_code != 0
    assert "adapter final confirmation file does not exist" in result.output


def test_scoped_adapter_execution_request_cli_blocks_empty_purpose(tmp_path) -> None:
    confirmation_file = tmp_path / "adapter-final-confirmation.json"
    json_output = tmp_path / "scoped-adapter-execution-request.json"

    confirmation_file.write_text(json.dumps(_final_confirmation()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-request",
            str(confirmation_file),
            "--request-purpose",
            "",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Request purpose is required" in data["block_reason"]
    assert data["can_execute_now"] is False
