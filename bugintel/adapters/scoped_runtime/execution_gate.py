"""Scoped runtime execution gate.

This module records whether a scoped runtime adapter request remains blocked or
has future runtime authorization recorded.

It does not execute curl, call subprocess, send network requests, launch
browsers, call providers, collect evidence, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
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
class ScopedRuntimeExecutionGateBundleVerificationArtifact:
    bundle_dir: str
    verification_status: str
    bundle_mode: str
    expected_files: tuple[str, ...]
    present_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    artifact_files_declared: tuple[str, ...]
    gate_kind: str
    manifest_kind: str
    gate_id: str
    manifest_gate_id: str
    request_id: str
    manifest_request_id: str
    gate_status: str
    manifest_gate_status: str
    markdown_has_title: bool
    markdown_has_unredacted_secret: bool
    markdown_has_redacted_placeholder: bool
    verification_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-verification"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_verification_artifact",
            "source": self.source,
            "bundle_dir": self.bundle_dir,
            "verification_status": self.verification_status,
            "bundle_mode": self.bundle_mode,
            "expected_files": list(self.expected_files),
            "present_files": list(self.present_files),
            "missing_files": list(self.missing_files),
            "unexpected_files": list(self.unexpected_files),
            "artifact_files_declared": list(self.artifact_files_declared),
            "gate_kind": self.gate_kind,
            "manifest_kind": self.manifest_kind,
            "gate_id": self.gate_id,
            "manifest_gate_id": self.manifest_gate_id,
            "request_id": self.request_id,
            "manifest_request_id": self.manifest_request_id,
            "gate_status": self.gate_status,
            "manifest_gate_status": self.manifest_gate_status,
            "markdown_has_title": self.markdown_has_title,
            "markdown_has_unredacted_secret": self.markdown_has_unredacted_secret,
            "markdown_has_redacted_placeholder": self.markdown_has_redacted_placeholder,
            "verification_findings": list(self.verification_findings),
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
        lines = [
            "# Scoped Runtime Execution Gate Bundle Verification",
            "",
            "## Summary",
            "",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Files",
            "",
            f"- Expected files: `{', '.join(self.expected_files)}`",
            f"- Present files: `{', '.join(self.present_files) or 'none'}`",
            f"- Missing files: `{', '.join(self.missing_files) or 'none'}`",
            f"- Unexpected files: `{', '.join(self.unexpected_files) or 'none'}`",
            f"- Manifest-declared files: `{', '.join(self.artifact_files_declared) or 'none'}`",
            "",
            "## Redaction checks",
            "",
            f"- Markdown has title: `{str(self.markdown_has_title).lower()}`",
            f"- Markdown has unredacted secret placeholder: `{str(self.markdown_has_unredacted_secret).lower()}`",
            f"- Markdown has redacted placeholder: `{str(self.markdown_has_redacted_placeholder).lower()}`",
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
            "",
            "## Verification findings",
            "",
        ]

        if self.verification_findings:
            lines.extend(f"- {finding}" for finding in self.verification_findings)
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
                "This verification is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def verify_scoped_runtime_execution_gate_bundle(
    bundle_dir: Path | str,
) -> ScopedRuntimeExecutionGateBundleVerificationArtifact:
    """Verify a scoped runtime execution gate bundle using local files only."""
    bundle_path = Path(bundle_dir)
    expected_files = ("gate.json", "gate.md", "manifest.json")
    blocking: list[str] = []

    if not bundle_path.exists():
        blocking.append("Bundle directory does not exist.")
        present_files: tuple[str, ...] = ()
    elif not bundle_path.is_dir():
        blocking.append("Bundle path is not a directory.")
        present_files = ()
    else:
        present_files = tuple(sorted(path.name for path in bundle_path.iterdir() if path.is_file()))

    missing_files = tuple(filename for filename in expected_files if filename not in present_files)
    unexpected_files = tuple(filename for filename in present_files if filename not in expected_files)

    if missing_files:
        blocking.append(f"Bundle is missing expected files: {', '.join(missing_files)}.")

    if unexpected_files:
        blocking.append(f"Bundle contains unexpected files: {', '.join(unexpected_files)}.")

    gate = _load_bundle_json(bundle_path / "gate.json", blocking, "gate.json") if "gate.json" in present_files else {}
    manifest = (
        _load_bundle_json(bundle_path / "manifest.json", blocking, "manifest.json")
        if "manifest.json" in present_files
        else {}
    )
    markdown = _load_bundle_text(bundle_path / "gate.md", blocking, "gate.md") if "gate.md" in present_files else ""

    artifact_files_declared = tuple(
        str(item.get("filename") or "")
        for item in manifest.get("artifact_files", [])
        if isinstance(item, dict) and str(item.get("filename") or "").strip()
    )

    gate_kind = str(gate.get("kind") or "")
    manifest_kind = str(manifest.get("kind") or "")
    gate_id = str(gate.get("gate_id") or "")
    manifest_gate_id = str(manifest.get("gate_id") or "")
    request_id = str(gate.get("request_id") or "")
    manifest_request_id = str(manifest.get("request_id") or "")
    gate_status = str(gate.get("gate_status") or "")
    manifest_gate_status = str(manifest.get("gate_status") or "")
    bundle_mode = str(manifest.get("bundle_mode") or "")

    if gate and gate_kind != "scoped_runtime_execution_gate_artifact":
        blocking.append("gate.json has unexpected artifact kind.")

    if manifest and manifest_kind != "scoped_runtime_execution_gate_bundle_manifest":
        blocking.append("manifest.json has unexpected artifact kind.")

    if manifest and bundle_mode != "local_files_only_no_execution":
        blocking.append("manifest.json does not record local_files_only_no_execution bundle mode.")

    if manifest and artifact_files_declared != expected_files:
        blocking.append("manifest.json artifact file list does not match expected bundle files.")

    for field in (
        "gate_id",
        "request_id",
        "implementation_blueprint_id",
        "readiness_review_id",
        "execution_plan_id",
        "gate_status",
        "gate_mode",
    ):
        if gate and manifest and str(gate.get(field) or "") != str(manifest.get(field) or ""):
            blocking.append(f"gate.json and manifest.json disagree on {field}.")

    execution_flags = (
        "can_execute_now",
        "execution_allowed",
        "validation_allowed",
        "runtime_execution_allowed",
        "tool_execution_allowed",
        "browser_execution_allowed",
        "network_requests_allowed",
        "evidence_collection_allowed",
        "target_mutation_allowed",
        "report_submission_allowed",
        "vulnerability_confirmation_allowed",
    )

    for label, data in (("gate.json", gate), ("manifest.json", manifest)):
        if not data:
            continue
        for flag in execution_flags:
            if data.get(flag) is not False:
                blocking.append(f"{label} does not keep {flag} false.")

        safety = data.get("safety")
        if isinstance(safety, dict):
            for safety_key in (
                "network_requests",
                "tool_execution",
                "evidence_collection",
                "validation_execution",
                "report_submission",
                "vulnerability_confirmation",
            ):
                if safety.get(safety_key) is not False:
                    blocking.append(f"{label} safety metadata does not keep {safety_key} false.")
        else:
            blocking.append(f"{label} is missing safety metadata.")

    redacted_preview_command = str(gate.get("redacted_preview_command") or "")
    if gate and "CONTROLLED_TOKEN_ONLY" in redacted_preview_command:
        blocking.append("gate.json redacted_preview_command contains the unredacted token placeholder.")

    if gate and "REDACTED_CONTROLLED_TOKEN" not in redacted_preview_command:
        blocking.append("gate.json redacted_preview_command is missing the redacted token placeholder.")

    markdown_has_title = "# Scoped Runtime Execution Gate" in markdown
    markdown_has_unredacted_secret = "CONTROLLED_TOKEN_ONLY" in markdown
    markdown_has_redacted_placeholder = "REDACTED_CONTROLLED_TOKEN" in markdown

    if markdown and not markdown_has_title:
        blocking.append("gate.md is missing the expected Markdown title.")

    if markdown and markdown_has_unredacted_secret:
        blocking.append("gate.md contains the unredacted token placeholder.")

    if markdown and not markdown_has_redacted_placeholder:
        blocking.append("gate.md is missing the redacted token placeholder.")

    verification_status = (
        "blocked-bundle-verification-failed"
        if blocking
        else "verified-local-bundle-no-execution"
    )

    verification_findings = (
        "Bundle verification inspected local files only.",
        "Bundle verification checked expected files, manifest file list, IDs, gate status, redaction, and safety flags.",
        "Bundle verification did not execute curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleVerificationArtifact(
        bundle_dir=str(bundle_path),
        verification_status=verification_status,
        bundle_mode=bundle_mode,
        expected_files=expected_files,
        present_files=present_files,
        missing_files=missing_files,
        unexpected_files=unexpected_files,
        artifact_files_declared=artifact_files_declared,
        gate_kind=gate_kind,
        manifest_kind=manifest_kind,
        gate_id=gate_id,
        manifest_gate_id=manifest_gate_id,
        request_id=request_id,
        manifest_request_id=manifest_request_id,
        gate_status=gate_status,
        manifest_gate_status=manifest_gate_status,
        markdown_has_title=markdown_has_title,
        markdown_has_unredacted_secret=markdown_has_unredacted_secret,
        markdown_has_redacted_placeholder=markdown_has_redacted_placeholder,
        verification_findings=verification_findings,
        blocking_findings=tuple(blocking),
    )


def _load_bundle_json(path: Path, blocking: list[str], label: str) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive parse failure branch
        blocking.append(f"{label} could not be read as JSON: {exc}")
        return {}
    if not isinstance(data, dict):
        blocking.append(f"{label} did not contain a JSON object.")
        return {}
    return data


def _load_bundle_text(path: Path, blocking: list[str], label: str) -> str:
    try:
        return path.read_text()
    except Exception as exc:  # pragma: no cover - defensive read failure branch
        blocking.append(f"{label} could not be read: {exc}")
        return ""


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
