import json

from typer.testing import CliRunner

from bugintel.cli import app
from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import export_case_intake_brain_handoff_adapter_dry_run_preview
from bugintel.core.case_intake_brain_handoff_adapter_final_confirmation_packet import record_case_intake_brain_handoff_adapter_final_confirmation
from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import record_case_intake_brain_handoff_approval_decision
from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import export_case_intake_brain_handoff_approval_packet
from bugintel.core.case_intake_brain_handoff_execution_approval_gate import record_case_intake_brain_handoff_execution_approval_gate
from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import export_case_intake_brain_handoff_manual_validation_plan
from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import export_case_intake_brain_handoff_read_only_command_proposal
from bugintel.core.case_intake_brain_handoff_runtime_safety_manifest import export_case_intake_brain_handoff_runtime_safety_manifest
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_request import export_case_intake_brain_handoff_scoped_adapter_execution_request
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_scope_review import export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review
from bugintel.core.case_intake_brain_handoff_scoped_adapter_safety_review import export_case_intake_brain_handoff_scoped_adapter_safety_review
from bugintel.core.case_intake_brain_handoff_scoped_adapter_final_execution_gate import record_case_intake_brain_handoff_scoped_adapter_final_execution_gate
from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet import record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_plan_packet import export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet
from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_readiness_review import review_case_intake_brain_handoff_scoped_adapter_execution_readiness
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _readiness_review() -> dict:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()
    packet = export_case_intake_brain_handoff_approval_packet(plan, endpoint="/api/admin/users/{id}/permissions").to_dict()
    decision = record_case_intake_brain_handoff_approval_decision(packet, decision="approved", decided_by="human-reviewer", reason="Approved read-only planning only with controlled accounts.").to_dict()
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(decision, command_family="curl").to_dict()
    gate = record_case_intake_brain_handoff_execution_approval_gate(proposal, decision="approved", decided_by="human-reviewer", reason="Approved only for future controlled read-only execution adapter preview.").to_dict()
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(gate, adapter_family="curl").to_dict()
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(manifest, target_base_url="https://example-program.test", controlled_account_token_placeholder="CONTROLLED_TOKEN_ONLY", path_parameters=["id=SYNTHETIC_USER_ID"]).to_dict()
    confirmation = record_case_intake_brain_handoff_adapter_final_confirmation(preview, decision="confirmed", confirmed_by="human-reviewer", reason="Final human review confirms dry-run preview is ready for future scoped adapter only.").to_dict()
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(confirmation, request_purpose="future-scoped-curl-adapter-review").to_dict()
    runtime_review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(request, allowed_host="example-program.test", allowed_scheme="https", allowed_method="GET").to_dict()
    safety_review = export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()
    final_gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(safety_review, decision="approved", decided_by="human-reviewer", reason="Approved for future adapter execution path only after separate explicit runtime confirmation.").to_dict()
    runtime_confirmation = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(final_gate, confirmed_by="human-reviewer", confirmation_text="I confirm the exact scoped adapter context was reviewed for a future runtime path only.").to_dict()
    execution_plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(runtime_confirmation, planned_by="human-reviewer", plan_purpose="Prepare a future scoped adapter execution plan without executing anything.").to_dict()
    return review_case_intake_brain_handoff_scoped_adapter_execution_readiness(execution_plan, reviewed_by="human-reviewer", readiness_note="Reviewed for future scoped adapter implementation readiness only; no execution authorized.").to_dict()


def test_implementation_blueprint_cli_writes_json_and_markdown(tmp_path) -> None:
    readiness_file = tmp_path / "scoped-adapter-execution-readiness.json"
    json_output = tmp_path / "scoped-adapter-implementation-blueprint.json"
    markdown_output = tmp_path / "scoped-adapter-implementation-blueprint.md"

    readiness_file.write_text(json.dumps(_readiness_review()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-implementation-blueprint",
            str(readiness_file),
            "--blueprinted-by",
            "human-reviewer",
            "--blueprint-note",
            "Define future scoped adapter implementation files and interfaces only; no execution authorized.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Scoped Adapter Implementation Blueprint" in result.output
    assert "Saved case intake brain scoped adapter implementation blueprint JSON" in result.output
    assert "Saved case intake brain scoped adapter implementation blueprint Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_implementation_blueprint"
    assert data["implementation_blueprint_id"] == "SIB-ERR-SEP-RCP-FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["implementation_blueprint_status"] == "blueprinted-for-future-scoped-adapter-implementation-no-execution"
    assert data["implementation_blueprint_state"] == "blueprinted_local_only"
    assert data["blueprinted_by"] == "human-reviewer"
    assert data["proposed_module_files"]
    assert data["proposed_interfaces"]
    assert data["proposed_dataclasses"]
    assert data["proposed_validation_guards"]
    assert data["proposed_test_files"]
    assert data["blueprint_findings"]
    assert data["adapter_execution_state"] == "not_executed"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["implementation_blueprint_allows_execution"] is False
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
    assert "# Case Intake Brain Scoped Adapter Implementation Blueprint" in markdown
    assert "## Reviewed Command" in markdown
    assert "No command execution" in markdown


def test_implementation_blueprint_cli_rejects_missing_readiness_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-implementation-blueprint",
            str(missing),
            "--blueprint-note",
            "Blueprint.",
        ],
    )

    assert result.exit_code != 0
    assert "scoped adapter execution readiness file does not exist" in result.output


def test_implementation_blueprint_cli_blocks_missing_blueprint_note(tmp_path) -> None:
    readiness_file = tmp_path / "scoped-adapter-execution-readiness.json"
    json_output = tmp_path / "scoped-adapter-implementation-blueprint.json"

    readiness_file.write_text(json.dumps(_readiness_review()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-implementation-blueprint",
            str(readiness_file),
            "--blueprint-note",
            "",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "Implementation blueprint note is required" in data["block_reason"]
    assert data["can_execute_now"] is False
