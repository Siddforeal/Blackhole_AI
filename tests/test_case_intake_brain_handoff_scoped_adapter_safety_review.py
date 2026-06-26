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


def test_adapter_safety_review_passes_without_execution() -> None:
    review = export_case_intake_brain_handoff_scoped_adapter_safety_review(
        _runtime_scope_review(),
    )

    assert review.safety_review_id == "ASR-RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert review.runtime_scope_review_id == "RSR-SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert review.request_id == "SAER-AFC-ADP-RSM-EG-CP-AD-AP-001"
    assert review.adapter_safety_review_status == "passed-local-adapter-safety-review-no-execution"
    assert review.adapter_safety_state == "reviewed_local_only"
    assert review.adapter_execution_state == "not_executed"
    assert review.reviewed_method == "GET"
    assert "--max-time" in review.present_safe_flags
    assert "--silent" in review.present_safe_flags
    assert "--show-error" in review.present_safe_flags
    assert "--fail-with-body" in review.present_safe_flags
    assert review.missing_safe_flags == ()
    assert review.blocked_flags_seen == ()
    assert review.shell_control_patterns_seen == ()
    assert review.safe_command_findings
    assert review.blocked is False
    assert review.dry_run_only is True
    assert review.can_execute_now is False
    assert review.adapter_safety_review_allows_execution is False
    assert review.execution_allowed is False
    assert review.validation_allowed is False
    assert review.runtime_execution_allowed is False
    assert review.tool_execution_allowed is False
    assert review.browser_execution_allowed is False
    assert review.network_requests_allowed is False
    assert review.evidence_collection_allowed is False
    assert review.target_mutation_allowed is False
    assert review.report_submission_allowed is False
    assert review.vulnerability_confirmation_allowed is False


def test_adapter_safety_review_blocks_redirect_flag() -> None:
    data = _runtime_scope_review()
    data["reviewed_command"] = data["reviewed_command"] + " --location"

    review = export_case_intake_brain_handoff_scoped_adapter_safety_review(data)

    assert review.blocked is True
    assert "blocked curl flags" in review.block_reason
    assert "--location" in review.blocked_flags_seen
    assert review.can_execute_now is False


def test_adapter_safety_review_blocks_missing_safe_flag() -> None:
    data = _runtime_scope_review()
    data["reviewed_command"] = data["reviewed_command"].replace(" --fail-with-body", "")

    review = export_case_intake_brain_handoff_scoped_adapter_safety_review(data)

    assert review.blocked is True
    assert "missing required safe curl flags" in review.block_reason
    assert "--fail-with-body" in review.missing_safe_flags
    assert review.can_execute_now is False


def test_adapter_safety_review_blocks_shell_control_operator() -> None:
    data = _runtime_scope_review()
    data["reviewed_command"] = data["reviewed_command"] + " && curl https://evil.test"

    review = export_case_intake_brain_handoff_scoped_adapter_safety_review(data)

    assert review.blocked is True
    assert "shell control patterns" in review.block_reason
    assert "&&" in review.shell_control_patterns_seen
    assert review.can_execute_now is False


def test_adapter_safety_review_blocks_invalid_input() -> None:
    review = export_case_intake_brain_handoff_scoped_adapter_safety_review({"kind": "wrong"})

    assert review.blocked is True
    assert "not a case_intake_brain_handoff_scoped_adapter_runtime_scope_review" in review.block_reason
    assert review.can_execute_now is False


def test_adapter_safety_review_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_scoped_adapter_safety_review(
        _runtime_scope_review(),
    ).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_scoped_adapter_safety_review"
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
    assert data["safety"]["dry_run_only"] is True
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_adapter_safety_review_markdown_contains_review_and_safety() -> None:
    markdown = export_case_intake_brain_handoff_scoped_adapter_safety_review(
        _runtime_scope_review(),
    ).to_markdown()

    assert "# Case Intake Brain Scoped Adapter Safety Review" in markdown
    assert "## Reviewed Command" in markdown
    assert "Adapter safety review allows execution" in markdown
    assert "No command execution" in markdown
    assert "Required Safe Flags" in markdown
