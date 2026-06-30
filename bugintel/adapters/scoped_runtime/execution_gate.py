"""Scoped runtime execution gate.

This module records whether a scoped runtime adapter request remains blocked or
has future runtime authorization recorded.

It does not execute curl, call subprocess, send network requests, launch
browsers, call providers, collect evidence, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.adapters.scoped_runtime.contracts import ScopedAdapterRequest
from bugintel.adapters.scoped_runtime.curl_adapter import (
    ScopedCurlAdapter,
    ScopedCurlAdapterPreview,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata


@dataclass(frozen=True)
class ScopedRuntimeExecutionGateArtifact:
    gate_id: str
    request_id: str
    implementation_blueprint_id: str
    readiness_review_id: str
    execution_plan_id: str
    target_name: str
    endpoint: str
    gate_status: str
    gate_mode: str
    future_authorization_requested: bool
    human_authorization_recorded: bool
    controlled_account_recorded: bool
    scope_review_recorded: bool
    adapter_preview: dict[str, Any]
    redacted_preview_command: str
    gate_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_artifact",
            "source": self.source,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "readiness_review_id": self.readiness_review_id,
            "execution_plan_id": self.execution_plan_id,
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "gate_status": self.gate_status,
            "gate_mode": self.gate_mode,
            "future_authorization_requested": self.future_authorization_requested,
            "human_authorization_recorded": self.human_authorization_recorded,
            "controlled_account_recorded": self.controlled_account_recorded,
            "scope_review_recorded": self.scope_review_recorded,
            "adapter_preview": self.adapter_preview,
            "redacted_preview_command": self.redacted_preview_command,
            "gate_findings": list(self.gate_findings),
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

    def to_markdown(self) -> str:
        """Render a human-readable Markdown execution gate artifact."""
        data = self.to_dict()
        safety = data["safety"]

        lines = [
            "# Scoped Runtime Execution Gate",
            "",
            "## Summary",
            "",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Implementation blueprint ID: `{self.implementation_blueprint_id}`",
            f"- Readiness review ID: `{self.readiness_review_id}`",
            f"- Execution plan ID: `{self.execution_plan_id}`",
            f"- Target: `{self.target_name}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Gate mode: `{self.gate_mode}`",
            "",
            "## Authorization metadata",
            "",
            f"- Future authorization requested: `{str(self.future_authorization_requested).lower()}`",
            f"- Human authorization recorded: `{str(self.human_authorization_recorded).lower()}`",
            f"- Controlled account recorded: `{str(self.controlled_account_recorded).lower()}`",
            f"- Scope review recorded: `{str(self.scope_review_recorded).lower()}`",
            "",
            "## Execution state",
            "",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Can execute now: `{str(self.can_execute_now).lower()}`",
            f"- Execution allowed: `{str(self.execution_allowed).lower()}`",
            f"- Validation allowed: `{str(self.validation_allowed).lower()}`",
            f"- Runtime execution allowed: `{str(self.runtime_execution_allowed).lower()}`",
            f"- Tool execution allowed: `{str(self.tool_execution_allowed).lower()}`",
            f"- Browser execution allowed: `{str(self.browser_execution_allowed).lower()}`",
            f"- Network requests allowed: `{str(self.network_requests_allowed).lower()}`",
            f"- Evidence collection allowed: `{str(self.evidence_collection_allowed).lower()}`",
            f"- Target mutation allowed: `{str(self.target_mutation_allowed).lower()}`",
            f"- Report submission allowed: `{str(self.report_submission_allowed).lower()}`",
            f"- Vulnerability confirmation allowed: `{str(self.vulnerability_confirmation_allowed).lower()}`",
            f"- Planning only: `{str(self.planning_only).lower()}`",
            f"- Dry-run only: `{str(self.dry_run_only).lower()}`",
            "",
            "## Safety",
            "",
            f"- Network requests: `{str(safety['network_requests']).lower()}`",
            f"- Tool execution: `{str(safety['tool_execution']).lower()}`",
            f"- Evidence collection: `{str(safety['evidence_collection']).lower()}`",
            f"- Validation execution: `{str(safety['validation_execution']).lower()}`",
            f"- Report submission: `{str(safety['report_submission']).lower()}`",
            f"- Vulnerability confirmation: `{str(safety['vulnerability_confirmation']).lower()}`",
            "",
            "## Adapter preview",
            "",
            f"- Preview kind: `{self.adapter_preview.get('kind', 'unknown')}`",
            f"- Preview status: `{self.adapter_preview.get('render_status', 'unknown')}`",
            f"- Preview mode: `{self.adapter_preview.get('render_mode', 'unknown')}`",
            f"- Adapter execution state: `{self.adapter_preview.get('adapter_execution_state', 'unknown')}`",
            "",
            "## Redacted preview command",
            "",
            "```bash",
            self.redacted_preview_command,
            "```",
            "",
            "## Gate findings",
            "",
        ]

        if self.gate_findings:
            lines.extend(f"- {finding}" for finding in self.gate_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Blocking findings", ""])
        if self.blocking_findings:
            lines.extend(f"- {finding}" for finding in self.blocking_findings)
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety statement",
                "",
                "This artifact is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)

    def to_bundle_manifest(self) -> dict[str, Any]:
        """Render a local bundle manifest for JSON and Markdown exports."""
        return {
            "kind": "scoped_runtime_execution_gate_bundle_manifest",
            "source": "scoped-runtime-execution-gate-bundle-export",
            "bundle_id": f"SREG-BUNDLE-{self.gate_id}",
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "readiness_review_id": self.readiness_review_id,
            "execution_plan_id": self.execution_plan_id,
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "gate_status": self.gate_status,
            "gate_mode": self.gate_mode,
            "artifact_files": [
                {
                    "filename": "gate.json",
                    "kind": "scoped_runtime_execution_gate_artifact_json",
                    "description": "Machine-readable scoped runtime execution gate artifact.",
                },
                {
                    "filename": "gate.md",
                    "kind": "scoped_runtime_execution_gate_artifact_markdown",
                    "description": "Human-readable scoped runtime execution gate artifact.",
                },
                {
                    "filename": "manifest.json",
                    "kind": "scoped_runtime_execution_gate_bundle_manifest",
                    "description": "Machine-readable local bundle manifest.",
                },
            ],
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
            "bundle_mode": "local_files_only_no_execution",
            "safety": safety_metadata(),
        }


@dataclass(frozen=True)
class ScopedRuntimeExecutionGate:
    gate_name: str = "scoped-runtime-execution-gate"
    gate_mode: str = "record_only_no_execution"
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

    def evaluate(
        self,
        request: ScopedAdapterRequest,
        *,
        future_authorization_requested: bool = False,
        human_authorization_recorded: bool = False,
        controlled_account_recorded: bool = False,
        scope_review_recorded: bool = False,
    ) -> ScopedRuntimeExecutionGateArtifact:
        """Evaluate the execution gate without executing anything."""
        adapter_preview = ScopedCurlAdapter().render_preview(request)
        preview_data = adapter_preview.to_dict()
        blocking = list(adapter_preview.blocking_findings)

        if adapter_preview.render_status == "blocked":
            blocking.append("Adapter preview is blocked, so runtime execution remains blocked.")

        if not future_authorization_requested:
            blocking.append("Future runtime authorization was not requested.")

        if future_authorization_requested and not human_authorization_recorded:
            blocking.append("Human authorization was not recorded.")

        if future_authorization_requested and not controlled_account_recorded:
            blocking.append("Controlled account precondition was not recorded.")

        if future_authorization_requested and not scope_review_recorded:
            blocking.append("Scope review confirmation was not recorded.")

        gate_findings = (
            "Execution gate evaluated request metadata locally without execution.",
            "Execution gate did not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
            "Execution gate preserved not_executed state and false execution flags.",
        )

        if blocking:
            gate_status = "blocked-runtime-execution-not-authorized"
        else:
            gate_status = "future-runtime-authorization-recorded-no-execution"

        return ScopedRuntimeExecutionGateArtifact(
            gate_id=f"SREG-{request.implementation_blueprint_id}",
            request_id=request.request_id,
            implementation_blueprint_id=request.implementation_blueprint_id,
            readiness_review_id=request.readiness_review_id,
            execution_plan_id=request.execution_plan_id,
            target_name=request.target_name,
            endpoint=request.endpoint,
            gate_status=gate_status,
            gate_mode=self.gate_mode,
            future_authorization_requested=future_authorization_requested,
            human_authorization_recorded=human_authorization_recorded,
            controlled_account_recorded=controlled_account_recorded,
            scope_review_recorded=scope_review_recorded,
            adapter_preview=preview_data,
            redacted_preview_command=adapter_preview.redacted_preview_command,
            gate_findings=gate_findings,
            blocking_findings=tuple(blocking),
        )


def evaluate_scoped_runtime_execution_gate(
    request: ScopedAdapterRequest,
    *,
    future_authorization_requested: bool = False,
    human_authorization_recorded: bool = False,
    controlled_account_recorded: bool = False,
    scope_review_recorded: bool = False,
) -> ScopedRuntimeExecutionGateArtifact:
    """Evaluate the scoped runtime execution gate without execution."""
    return ScopedRuntimeExecutionGate().evaluate(
        request,
        future_authorization_requested=future_authorization_requested,
        human_authorization_recorded=human_authorization_recorded,
        controlled_account_recorded=controlled_account_recorded,
        scope_review_recorded=scope_review_recorded,
    )
