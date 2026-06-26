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
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _safety_review() -> dict:
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
    return export_case_intake_brain_handoff_scoped_adapter_safety_review(runtime_review).to_dict()


def test_final_execution_gate_cli_writes_json_and_markdown(tmp_path) -> None:
    safety_review_file = tmp_path / "scoped-adapter-safety-review.json"
    json_output = tmp_path / "scoped-adapter-final-execution-gate.json"
    markdown_output = tmp_path / "scoped-adapter-final-execution-gate.md"

    safety_review_file.write_text(json.dumps(_safety_review()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-final-execution-gate",
            str(safety_review_file),
            "--decision",
            "approved",
            "--decided-by",
            "human-reviewer",
            "--reason",
            "Approved for future adapter execution path only after separate explicit runtime confirmation.",
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Scoped Adapter Final Execution Gate" in result.output
    assert "Saved case intake brain scoped adapter final execution gate JSON" in result.output
    assert "Saved case intake brain scoped adapter final execution gate Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_final_execution_gate"
    assert data["final_gate_id"] == "FEG-ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["final_execution_gate_decision"] == "approved"
    assert data["final_execution_gate_status"] == "approved-for-future-adapter-path-no-execution"
    assert data["decided_by"] == "human-reviewer"
    assert data["human_final_execution_gate_recorded"] is True
    assert data["final_go_no_go"] == "go-recorded-for-future-adapter-path-only"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["final_execution_gate_allows_execution"] is False
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
    assert "# Case Intake Brain Scoped Adapter Final Execution Gate" in markdown
    assert "## Reviewed Command" in markdown
    assert "No command execution" in markdown


def test_final_execution_gate_cli_rejects_missing_safety_review_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-final-execution-gate",
            str(missing),
            "--decision",
            "approved",
            "--reason",
            "Approved.",
        ],
    )

    assert result.exit_code != 0
    assert "scoped adapter safety review file does not exist" in result.output


def test_final_execution_gate_cli_blocks_denied_decision(tmp_path) -> None:
    safety_review_file = tmp_path / "scoped-adapter-safety-review.json"
    json_output = tmp_path / "scoped-adapter-final-execution-gate.json"

    safety_review_file.write_text(json.dumps(_safety_review()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-final-execution-gate",
            str(safety_review_file),
            "--decision",
            "denied",
            "--reason",
            "Human reviewer denied the final gate.",
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert data["final_execution_gate_decision"] == "denied"
    assert data["final_go_no_go"] == "no-go-denied-by-human"
    assert data["can_execute_now"] is False
