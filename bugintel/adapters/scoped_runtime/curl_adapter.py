"""Non-executing scoped curl adapter skeleton.

This module provides a local preview-only adapter wrapper around the scoped
runtime contracts and preview renderer.

It does not execute curl, call subprocess, send network requests, launch
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
from bugintel.adapters.scoped_runtime.preview_renderer import (
    ScopedRuntimePreviewArtifact,
    render_scoped_runtime_preview,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata


@dataclass(frozen=True)
class ScopedCurlAdapterPreview:
    adapter_name: str
    request_id: str
    implementation_blueprint_id: str
    render_status: str
    render_mode: str
    preview_artifact: dict[str, Any]
    prepared_command: dict[str, Any]
    redacted_preview_command: str
    adapter_findings: tuple[str, ...]
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
    source: str = "scoped-curl-adapter-skeleton"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_curl_adapter_preview",
            "source": self.source,
            "adapter_name": self.adapter_name,
            "request_id": self.request_id,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "render_status": self.render_status,
            "render_mode": self.render_mode,
            "preview_artifact": self.preview_artifact,
            "prepared_command": self.prepared_command,
            "redacted_preview_command": self.redacted_preview_command,
            "adapter_findings": list(self.adapter_findings),
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


@dataclass(frozen=True)
class ScopedCurlAdapter:
    adapter_name: str = "scoped-curl-adapter-skeleton"
    adapter_family: str = "curl"
    command_family: str = "curl"
    render_mode: str = "preview_only"
    adapter_execution_state: str = "not_executed"
    can_execute_now: bool = False
    execution_allowed: bool = False
    tool_execution_allowed: bool = False
    network_requests_allowed: bool = False
    evidence_collection_allowed: bool = False
    target_mutation_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    dry_run_only: bool = True

    def prepare_request(self, request: ScopedAdapterRequest) -> ScopedAdapterPreparedCommand:
        """Prepare a preview-only command contract.

        This method creates data only. It intentionally does not call curl,
        subprocess, network, browser, provider, evidence, mutation, report, or
        vulnerability-confirmation paths.
        """
        return ScopedAdapterPreparedCommand.from_request(request)

    def render_preview(self, request: ScopedAdapterRequest) -> ScopedCurlAdapterPreview:
        """Render a local preview artifact through the preview renderer.

        This method is still non-executing. It wraps
        render_scoped_runtime_preview(...) and preserves all false execution
        flags.
        """
        prepared = self.prepare_request(request)
        artifact = render_scoped_runtime_preview(request)
        artifact_data = artifact.to_dict()
        render_status = (
            "adapter-preview-rendered-local-only-no-execution"
            if artifact.render_status != "blocked"
            else "blocked"
        )

        findings = (
            "Scoped curl adapter skeleton rendered a local preview only.",
            "Scoped curl adapter skeleton did not execute curl or subprocess.",
            "Scoped curl adapter skeleton did not send network requests or collect evidence.",
            "Scoped curl adapter skeleton preserved not_executed state and false execution flags.",
        )

        return ScopedCurlAdapterPreview(
            adapter_name=self.adapter_name,
            request_id=request.request_id,
            implementation_blueprint_id=request.implementation_blueprint_id,
            render_status=render_status,
            render_mode=self.render_mode,
            preview_artifact=artifact_data,
            prepared_command=prepared.to_dict(),
            redacted_preview_command=artifact.redacted_preview_command,
            adapter_findings=findings,
            blocking_findings=tuple(artifact.blocking_findings),
        )


def render_scoped_curl_adapter_preview(request: ScopedAdapterRequest) -> ScopedCurlAdapterPreview:
    """Render a scoped curl adapter preview using the skeleton adapter."""
    return ScopedCurlAdapter().render_preview(request)
