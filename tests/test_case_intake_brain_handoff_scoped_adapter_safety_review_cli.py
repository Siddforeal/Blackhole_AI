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
from tests.test_case_intake_brain_handoff_answerer import _handoff


def _runtime_scope_review() -> dict:
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
    return export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(
        request,
        allowed_host="example-program.test",
        allowed_scheme="https",
        allowed_method="GET",
    ).to_dict()


def test_adapter_safety_review_cli_writes_json_and_markdown(tmp_path) -> None:
    runtime_review_file = tmp_path / "scoped-adapter-runtime-scope-review.json"
    json_output = tmp_path / "scoped-adapter-safety-review.json"
    markdown_output = tmp_path / "scoped-adapter-safety-review.md"

    runtime_review_file.write_text(json.dumps(_runtime_scope_review()))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-safety-review",
            str(runtime_review_file),
            "--json-output",
            str(json_output),
            "--output-file",
            str(markdown_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Case Intake Brain Scoped Adapter Safety Review" in result.output
    assert "Saved case intake brain scoped adapter safety review JSON" in result.output
    assert "Saved case intake brain scoped adapter safety review Markdown" in result.output

    data = json.loads(json_output.read_text())
    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_safety_review"
    assert data["safety_review_id"] == "ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert data["adapter_safety_review_status"] == "passed-local-adapter-safety-review-no-execution"
    assert data["adapter_safety_state"] == "reviewed_local_only"
    assert data["adapter_execution_state"] == "not_executed"
    assert data["reviewed_method"] == "GET"
    assert data["missing_safe_flags"] == []
    assert data["blocked_flags_seen"] == []
    assert data["shell_control_patterns_seen"] == []
    assert data["dry_run_only"] is True
    assert data["can_execute_now"] is False
    assert data["adapter_safety_review_allows_execution"] is False
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
    assert "# Case Intake Brain Scoped Adapter Safety Review" in markdown
    assert "## Reviewed Command" in markdown
    assert "No command execution" in markdown


def test_adapter_safety_review_cli_rejects_missing_runtime_scope_review_file(tmp_path) -> None:
    missing = tmp_path / "missing.json"

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-safety-review",
            str(missing),
        ],
    )

    assert result.exit_code != 0
    assert "scoped adapter runtime scope review file does not exist" in result.output


def test_adapter_safety_review_cli_blocks_unsafe_flag(tmp_path) -> None:
    runtime_review_file = tmp_path / "scoped-adapter-runtime-scope-review.json"
    json_output = tmp_path / "scoped-adapter-safety-review.json"

    data = _runtime_scope_review()
    data["reviewed_command"] = data["reviewed_command"] + " --retry 3"
    runtime_review_file.write_text(json.dumps(data))

    result = CliRunner().invoke(
        app,
        [
            "case-intake-brain-scoped-adapter-safety-review",
            str(runtime_review_file),
            "--json-output",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    data = json.loads(json_output.read_text())
    assert data["blocked"] is True
    assert "--retry" in data["blocked_flags_seen"]
    assert "blocked curl flags" in data["block_reason"]
    assert data["can_execute_now"] is False
