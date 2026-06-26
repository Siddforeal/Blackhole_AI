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
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_request import (
    export_case_intake_brain_handoff_scoped_adapter_execution_request,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_scope_review import (
    export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_safety_review import (
    export_case_intake_brain_handoff_scoped_adapter_safety_review,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_final_execution_gate import (
    record_case_intake_brain_handoff_scoped_adapter_final_execution_gate,
)
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet import (
    record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _runtime_confirmation() -> dict:
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
    confirmation = record_case_intake_brain_handoff_adapter_final_confirmation(
        preview,
        decision="confirmed",
        confirmed_by="human-reviewer",
        reason="Final human review confirms dry-run preview is ready for future scoped adapter only.",
    ).to_dict()
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        confirmation,
        request_purpose="future-scoped-curl-adapter-review",
    ).to_dict()
    runtime_review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(
        request,
        allowed_host="example-program.test",
        allowed_scheme="https",
        allowed_method="GET",
    ).to_dict()
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()
    final_gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        safety_review,
        decision="approved",
        decided_by="human-reviewer",
        reason="Approved for future adapter execution path only after separate explicit runtime confirmation.",
    ).to_dict()
    return record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        final_gate,
        confirmed_by="human-reviewer",
        confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.",
    ).to_dict()


def test_execution_plan_cli_writes_json_and_markdown(tmp_path) -> None:
    runtime_confirmation_file = tmp_path / "scoped-adapter-runtime-confirmation.json"
    json_output = tmp_path / "scoped-adapter-execution-plan.json"
    markdown_output = tmp_path / "scoped-adapter-execution-plan.md"

    runtime_confirmation_file.write_text(json.dumps(_runtime_confirmation()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-plan",
            str(runtime_confirmation_file),
            "--planned-by",
            "human-reviewer",
            "--plan-purpose",
            "Prepare a future scoped adapter execution plan without executing anything.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Scoped Adapter Execution Plan Packet" in result.output
    assert "Saved case intake brain scoped adapter execution plan JSON" in result.output
    assert "Saved case intake brain scoped adapter execution plan Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_execution_plan_packet"
    assert data["execution_plan_id"] == "SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["execution_plan_status"] == "planned-for-future-scoped-adapter-execution-no-execution"
    assert data["execution_plan_state"] == "planned_local_only"
    assert data["planned_by"] == "human-reviewer"
    assert data["execution_plan_steps"]
    assert data["adapter_execution_state"] == "not_executed"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["execution_plan_allows_execution"] is False
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
    assert "# Case Intake Brain Scoped Adapter Execution Plan Packet" in markdown
    assert "## Reviewed Command" in markdown
    assert "No command execution" in markdown


def test_execution_plan_cli_rejects_missing_runtime_confirmation_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-plan",
            str(missing),
            "--plan-purpose",
            "Prepare plan.",
        ],
    )

    assert result.exit_code != 0
    assert "scoped adapter runtime confirmation file does not exist" in result.output


def test_execution_plan_cli_blocks_missing_plan_purpose(tmp_path) -> None:
    runtime_confirmation_file = tmp_path / "scoped-adapter-runtime-confirmation.json"
    json_output = tmp_path / "scoped-adapter-execution-plan.json"

    runtime_confirmation_file.write_text(json.dumps(_runtime_confirmation()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-execution-plan",
            str(runtime_confirmation_file),
            "--plan-purpose",
            "",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Execution plan purpose is required" in data["block_reason"]
    assert data["can_execute_now"] is False
