"""Local preview renderer for scoped runtime adapter requests.

This module renders a preview artifact from a ScopedAdapterRequest. It is local,
deterministic, preview-only, and dry-run-only.

It does not execute curl, execute subprocesses, send network requests, launch
browsers, call providers, collect evidence, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.adapters.scoped_runtime.contracts import (
    ScopedAdapterPreparedCommand,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata
from bugintel.adapters.scoped_runtime.scope_guard import validate_scoped_adapter_request


@dataclass(frozen=True)
class ScopedRuntimePreviewArtifact:
    preview_id: str
    request_id: str
    implementation_blueprint_id: str
    readiness_review_id: str
    execution_plan_id: str
    target_name: str
    endpoint: str
    adapter_family: str
    command_family: str
    reviewed_method: str
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    resolved_target_url: str
    render_status: str
    render_mode: str
    scope_guard: dict[str, Any]
    prepared_command: dict[str, Any]
    preview_command: str
    redacted_preview_command: str
    renderer_findings: tuple[str, ...]
    blocking_findings: tuple[str, ...]
    adapter_execution_state: str = "not_executed"
    can_execute_now: bool = False
    execution_allowed: bool = False
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    tool_execution_allowed: bool = False
    browser_execution_allowed: bool = False
    network_requests_allowed: bool = False
    evidence_collection_allowed: bool = False
    target_mutation_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    dry_run_only: bool = True
    source: str = "scoped-runtime-preview-renderer"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_preview_artifact",
            "source": self.source,
            "preview_id": self.preview_id,
            "request_id": self.request_id,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "readiness_review_id": self.readiness_review_id,
            "execution_plan_id": self.execution_plan_id,
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "adapter_family": self.adapter_family,
            "command_family": self.command_family,
            "reviewed_method": self.reviewed_method,
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "resolved_target_url": self.resolved_target_url,
            "render_status": self.render_status,
            "render_mode": self.render_mode,
            "scope_guard": self.scope_guard,
            "prepared_command": self.prepared_command,
            "preview_command": self.preview_command,
            "redacted_preview_command": self.redacted_preview_command,
            "renderer_findings": list(self.renderer_findings),
            "blocking_findings": list(self.blocking_findings),
            "adapter_execution_state": self.adapter_execution_state,
            "can_execute_now": self.can_execute_now,
            "execution_allowed": self.execution_allowed,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "tool_execution_allowed": self.tool_execution_allowed,
            "browser_execution_allowed": self.browser_execution_allowed,
            "network_requests_allowed": self.network_requests_allowed,
            "evidence_collection_allowed": self.evidence_collection_allowed,
            "target_mutation_allowed": self.target_mutation_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "dry_run_only": self.dry_run_only,
            "safety": safety_metadata(),
        }


def render_scoped_runtime_preview(request: ScopedAdapterRequest) -> ScopedRuntimePreviewArtifact:
    """Render a local preview artifact from a scoped adapter request.

    The returned artifact is a preview only. This function intentionally performs
    no subprocess calls, no network requests, and no target interaction.
    """
    guard = validate_scoped_adapter_request(request)
    prepared = ScopedAdapterPreparedCommand.from_request(request)

    renderer_findings = (
        "Scoped adapter request was rendered locally without execution.",
        "Preview renderer preserved preview_only render mode.",
        "Preview renderer did not call subprocess, curl, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    if not guard.allowed:
        return ScopedRuntimePreviewArtifact(
            preview_id=f"SRP-BLOCKED-{request.implementation_blueprint_id}",
            request_id=request.request_id,
            implementation_blueprint_id=request.implementation_blueprint_id,
            readiness_review_id=request.readiness_review_id,
            execution_plan_id=request.execution_plan_id,
            target_name=request.target_name,
            endpoint=request.endpoint,
            adapter_family=request.adapter_family,
            command_family=request.command_family,
            reviewed_method=request.reviewed_method,
            reviewed_scheme=request.reviewed_scheme,
            reviewed_host=request.reviewed_host,
            reviewed_path=request.reviewed_path,
            resolved_target_url=request.resolved_target_url,
            render_status="blocked",
            render_mode="preview_only",
            scope_guard=guard.to_dict(),
            prepared_command=prepared.to_dict(),
            preview_command="",
            redacted_preview_command="",
            renderer_findings=renderer_findings,
            blocking_findings=guard.blocking_findings,
        )

    preview_command = prepared.reviewed_command
    return ScopedRuntimePreviewArtifact(
        preview_id=f"SRP-{request.implementation_blueprint_id}",
        request_id=request.request_id,
        implementation_blueprint_id=request.implementation_blueprint_id,
        readiness_review_id=request.readiness_review_id,
        execution_plan_id=request.execution_plan_id,
        target_name=request.target_name,
        endpoint=request.endpoint,
        adapter_family=request.adapter_family,
        command_family=request.command_family,
        reviewed_method=request.reviewed_method,
        reviewed_scheme=request.reviewed_scheme,
        reviewed_host=request.reviewed_host,
        reviewed_path=request.reviewed_path,
        resolved_target_url=request.resolved_target_url,
        render_status="rendered-local-preview-only-no-execution",
        render_mode=prepared.render_mode,
        scope_guard=guard.to_dict(),
        prepared_command=prepared.to_dict(),
        preview_command=preview_command,
        redacted_preview_command=_redact_preview_command(preview_command),
        renderer_findings=renderer_findings,
        blocking_findings=(),
    )


def _redact_preview_command(command: str) -> str:
    redacted = str(command or "")
    replacements = {
        "CONTROLLED_TOKEN_ONLY": "REDACTED_CONTROLLED_TOKEN",
        "Bearer CONTROLLED_TOKEN_ONLY": "Bearer REDACTED_CONTROLLED_TOKEN",
        "Authorization: Bearer CONTROLLED_TOKEN_ONLY": "Authorization: Bearer REDACTED_CONTROLLED_TOKEN",
    }
    for old, new in replacements.items():
        redacted = redacted.replace(old, new)
    return redacted
