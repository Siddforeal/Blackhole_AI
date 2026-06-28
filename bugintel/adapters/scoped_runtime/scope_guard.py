"""Scope guard contracts for future scoped runtime adapters.

The guard validates local request metadata only. It does not execute commands,
send requests, open browsers, call providers, collect evidence, mutate targets,
submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from bugintel.adapters.scoped_runtime.contracts import (
    SAFE_ADAPTER_EXECUTION_STATE,
    SAFE_BLUEPRINT_STATE,
    SAFE_BLUEPRINT_STATUS,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.result_types import ScopedAdapterScopeGuardResult


def validate_scoped_adapter_request(request: ScopedAdapterRequest) -> ScopedAdapterScopeGuardResult:
    blocking: list[str] = []

    if request.blueprint_artifact_kind != "case_intake_brain_handoff_scoped_adapter_implementation_blueprint":
        blocking.append("Request must come from a scoped adapter implementation blueprint artifact.")

    if request.implementation_blueprint_status != SAFE_BLUEPRINT_STATUS:
        blocking.append("Implementation blueprint status is not safe for future implementation planning.")

    if request.implementation_blueprint_state != SAFE_BLUEPRINT_STATE:
        blocking.append("Implementation blueprint state must be blueprinted_local_only.")

    if request.source_adapter_execution_state != SAFE_ADAPTER_EXECUTION_STATE:
        blocking.append("Source adapter execution state must be not_executed.")

    if request.adapter_execution_state != SAFE_ADAPTER_EXECUTION_STATE:
        blocking.append("Request adapter execution state must be not_executed.")

    if request.can_execute_now:
        blocking.append("Request cannot be executable now.")

    if any(
        (
            request.execution_allowed,
            request.validation_allowed,
            request.runtime_execution_allowed,
            request.tool_execution_allowed,
            request.browser_execution_allowed,
            request.network_requests_allowed,
            request.evidence_collection_allowed,
            request.target_mutation_allowed,
            request.report_submission_allowed,
            request.vulnerability_confirmation_allowed,
        )
    ):
        blocking.append("Request contains an unsafe execution/evidence/mutation/report/vulnerability flag.")

    if request.adapter_family != "curl":
        blocking.append("Only the planned curl adapter family may be represented by this contract.")

    if request.command_family != "curl":
        blocking.append("Only the planned curl command family may be represented by this contract.")

    if request.reviewed_scheme != "https":
        blocking.append("Reviewed scheme must be https.")

    if request.reviewed_method not in {"GET", "HEAD", "OPTIONS"}:
        blocking.append("Reviewed method must be read-only.")

    if not request.reviewed_host:
        blocking.append("Reviewed host is required.")

    if not request.reviewed_path.startswith("/"):
        blocking.append("Reviewed path must start with /.")

    if not request.resolved_target_url.startswith("https://"):
        blocking.append("Resolved target URL must be https.")

    if request.unresolved_placeholders:
        blocking.append("Unresolved placeholders must be empty.")

    if request.missing_safe_flags:
        blocking.append("Missing safe flags must be empty.")

    if request.blocked_flags_seen:
        blocking.append("Blocked flags must be empty.")

    if request.shell_control_patterns_seen:
        blocking.append("Shell control patterns must be empty.")

    findings = (
        "Request was checked locally without execution.",
        "Scope guard preserves not_executed adapter state.",
        "Scope guard does not authorize network, browser, tool, provider, evidence, mutation, report, or vulnerability-confirmation work.",
    )

    if blocking:
        return ScopedAdapterScopeGuardResult(
            allowed=False,
            status="blocked",
            findings=findings,
            blocking_findings=tuple(blocking),
        )

    return ScopedAdapterScopeGuardResult(
        allowed=True,
        status="valid-for-future-implementation-contract-only-no-execution",
        findings=findings,
        blocking_findings=(),
    )
