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
class ScopedRuntimeExecutionGateBundleReviewPacket:
    review_packet_id: str
    verification_status: str
    review_status: str
    review_state: str
    reviewed_by: str
    review_note: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    present_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    verification_findings: tuple[str, ...]
    review_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-review-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_review_packet",
            "source": self.source,
            "review_packet_id": self.review_packet_id,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "review_state": self.review_state,
            "reviewed_by": self.reviewed_by,
            "review_note": self.review_note,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "present_files": list(self.present_files),
            "missing_files": list(self.missing_files),
            "unexpected_files": list(self.unexpected_files),
            "verification_findings": list(self.verification_findings),
            "review_findings": list(self.review_findings),
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
            "# Scoped Runtime Execution Gate Bundle Review Packet",
            "",
            "## Summary",
            "",
            f"- Review packet ID: `{self.review_packet_id}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Review state: `{self.review_state}`",
            f"- Reviewed by: `{self.reviewed_by}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Review note",
            "",
            self.review_note or "none",
            "",
            "## Files",
            "",
            f"- Present files: `{', '.join(self.present_files) or 'none'}`",
            f"- Missing files: `{', '.join(self.missing_files) or 'none'}`",
            f"- Unexpected files: `{', '.join(self.unexpected_files) or 'none'}`",
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

        lines.extend(["", "## Review findings", ""])
        if self.review_findings:
            lines.extend(f"- {finding}" for finding in self.review_findings)
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
                "This review packet is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def review_scoped_runtime_execution_gate_bundle_verification(
    verification_artifact: dict[str, Any],
    *,
    reviewed_by: str = "human-reviewer",
    review_note: str = "",
) -> ScopedRuntimeExecutionGateBundleReviewPacket:
    """Create a human-reviewable packet from a bundle verification artifact without execution."""
    blocking = list(verification_artifact.get("blocking_findings") or [])

    if verification_artifact.get("kind") != "scoped_runtime_execution_gate_bundle_verification_artifact":
        blocking.append("Verification input has unexpected artifact kind.")

    if verification_artifact.get("verification_status") != "verified-local-bundle-no-execution":
        blocking.append("Bundle verification is not in verified-local-bundle-no-execution status.")

    if verification_artifact.get("bundle_mode") != "local_files_only_no_execution":
        blocking.append("Bundle verification does not record local_files_only_no_execution mode.")

    if verification_artifact.get("missing_files"):
        blocking.append("Bundle verification still reports missing files.")

    if verification_artifact.get("unexpected_files"):
        blocking.append("Bundle verification still reports unexpected files.")

    if verification_artifact.get("markdown_has_unredacted_secret") is not False:
        blocking.append("Bundle verification did not confirm absence of unredacted secret placeholder.")

    if verification_artifact.get("markdown_has_redacted_placeholder") is not True:
        blocking.append("Bundle verification did not confirm the redacted token placeholder.")

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
    for flag in execution_flags:
        if verification_artifact.get(flag) is not False:
            blocking.append(f"Verification artifact does not keep {flag} false.")

    safety = verification_artifact.get("safety")
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
                blocking.append(f"Verification safety metadata does not keep {safety_key} false.")
    else:
        blocking.append("Verification artifact is missing safety metadata.")

    review_status = (
        "blocked-local-bundle-verification-review"
        if blocking
        else "accepted-local-bundle-verification-no-execution"
    )

    gate_id = str(verification_artifact.get("gate_id") or "UNKNOWN")
    request_id = str(verification_artifact.get("request_id") or "UNKNOWN")

    review_findings = (
        "Review packet inspected a local bundle verification artifact only.",
        "Review packet records human review metadata without allowing execution.",
        "Review packet preserves not_executed state and false execution flags.",
        "Review packet does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleReviewPacket(
        review_packet_id=f"SREG-BUNDLE-REVIEW-{gate_id}",
        verification_status=str(verification_artifact.get("verification_status") or ""),
        review_status=review_status,
        review_state="reviewed_local_only",
        reviewed_by=reviewed_by,
        review_note=review_note,
        bundle_dir=str(verification_artifact.get("bundle_dir") or ""),
        bundle_mode=str(verification_artifact.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=request_id,
        gate_status=str(verification_artifact.get("gate_status") or ""),
        present_files=tuple(verification_artifact.get("present_files") or ()),
        missing_files=tuple(verification_artifact.get("missing_files") or ()),
        unexpected_files=tuple(verification_artifact.get("unexpected_files") or ()),
        verification_findings=tuple(verification_artifact.get("verification_findings") or ()),
        review_findings=review_findings,
        blocking_findings=tuple(blocking),
    )



@dataclass(frozen=True)
class ScopedRuntimeExecutionGateBundleHandoffPacket:
    handoff_packet_id: str
    review_packet_id: str
    verification_status: str
    review_status: str
    handoff_status: str
    handoff_state: str
    reviewed_by: str
    handoff_to: str
    handoff_note: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    present_files: tuple[str, ...]
    missing_files: tuple[str, ...]
    unexpected_files: tuple[str, ...]
    verification_findings: tuple[str, ...]
    review_findings: tuple[str, ...]
    handoff_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-handoff-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_handoff_packet",
            "source": self.source,
            "handoff_packet_id": self.handoff_packet_id,
            "review_packet_id": self.review_packet_id,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "handoff_status": self.handoff_status,
            "handoff_state": self.handoff_state,
            "reviewed_by": self.reviewed_by,
            "handoff_to": self.handoff_to,
            "handoff_note": self.handoff_note,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "present_files": list(self.present_files),
            "missing_files": list(self.missing_files),
            "unexpected_files": list(self.unexpected_files),
            "verification_findings": list(self.verification_findings),
            "review_findings": list(self.review_findings),
            "handoff_findings": list(self.handoff_findings),
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
            "# Scoped Runtime Execution Gate Bundle Handoff Packet",
            "",
            "## Summary",
            "",
            f"- Handoff packet ID: `{self.handoff_packet_id}`",
            f"- Review packet ID: `{self.review_packet_id}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Handoff state: `{self.handoff_state}`",
            f"- Reviewed by: `{self.reviewed_by}`",
            f"- Handoff to: `{self.handoff_to}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Handoff note",
            "",
            self.handoff_note or "none",
            "",
            "## Files",
            "",
            f"- Present files: `{', '.join(self.present_files) or 'none'}`",
            f"- Missing files: `{', '.join(self.missing_files) or 'none'}`",
            f"- Unexpected files: `{', '.join(self.unexpected_files) or 'none'}`",
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

        lines.extend(["", "## Review findings", ""])
        if self.review_findings:
            lines.extend(f"- {finding}" for finding in self.review_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Handoff findings", ""])
        if self.handoff_findings:
            lines.extend(f"- {finding}" for finding in self.handoff_findings)
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
                "This handoff packet is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def build_scoped_runtime_execution_gate_bundle_handoff_packet(
    review_packet: dict[str, Any],
    *,
    handoff_to: str = "future-reviewer",
    handoff_note: str = "",
) -> ScopedRuntimeExecutionGateBundleHandoffPacket:
    """Create a handoff packet from a bundle review packet without execution."""
    blocking = list(review_packet.get("blocking_findings") or [])

    if review_packet.get("kind") != "scoped_runtime_execution_gate_bundle_review_packet":
        blocking.append("Review packet input has unexpected artifact kind.")

    if review_packet.get("verification_status") != "verified-local-bundle-no-execution":
        blocking.append("Review packet does not reference a verified local bundle verification artifact.")

    if review_packet.get("review_status") != "accepted-local-bundle-verification-no-execution":
        blocking.append("Review packet is not accepted-local-bundle-verification-no-execution.")

    if review_packet.get("bundle_mode") != "local_files_only_no_execution":
        blocking.append("Review packet does not record local_files_only_no_execution mode.")

    if review_packet.get("missing_files"):
        blocking.append("Review packet still reports missing files.")

    if review_packet.get("unexpected_files"):
        blocking.append("Review packet still reports unexpected files.")

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
    for flag in execution_flags:
        if review_packet.get(flag) is not False:
            blocking.append(f"Review packet does not keep {flag} false.")

    safety = review_packet.get("safety")
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
                blocking.append(f"Review packet safety metadata does not keep {safety_key} false.")
    else:
        blocking.append("Review packet is missing safety metadata.")

    handoff_status = (
        "blocked-local-bundle-handoff"
        if blocking
        else "ready-local-bundle-handoff-no-execution"
    )

    gate_id = str(review_packet.get("gate_id") or "UNKNOWN")
    review_packet_id = str(review_packet.get("review_packet_id") or "UNKNOWN")

    handoff_findings = (
        "Handoff packet inspected a local bundle review packet only.",
        "Handoff packet summarizes verification, review, bundle, gate, and safety metadata for a future reviewer or operator.",
        "Handoff packet preserves not_executed state and false execution flags.",
        "Handoff packet does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleHandoffPacket(
        handoff_packet_id=f"SREG-BUNDLE-HANDOFF-{gate_id}",
        review_packet_id=review_packet_id,
        verification_status=str(review_packet.get("verification_status") or ""),
        review_status=str(review_packet.get("review_status") or ""),
        handoff_status=handoff_status,
        handoff_state="handoff_local_only",
        reviewed_by=str(review_packet.get("reviewed_by") or ""),
        handoff_to=handoff_to,
        handoff_note=handoff_note,
        bundle_dir=str(review_packet.get("bundle_dir") or ""),
        bundle_mode=str(review_packet.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=str(review_packet.get("request_id") or ""),
        gate_status=str(review_packet.get("gate_status") or ""),
        present_files=tuple(review_packet.get("present_files") or ()),
        missing_files=tuple(review_packet.get("missing_files") or ()),
        unexpected_files=tuple(review_packet.get("unexpected_files") or ()),
        verification_findings=tuple(review_packet.get("verification_findings") or ()),
        review_findings=tuple(review_packet.get("review_findings") or ()),
        handoff_findings=handoff_findings,
        blocking_findings=tuple(blocking),
    )



@dataclass(frozen=True)
class ScopedRuntimeExecutionGateBundleHandoffChecklist:
    checklist_id: str
    handoff_packet_id: str
    handoff_status: str
    checklist_status: str
    checklist_state: str
    checked_by: str
    checklist_note: str
    handoff_to: str
    verification_status: str
    review_status: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    required_checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    failed_checks: tuple[str, ...]
    handoff_findings: tuple[str, ...]
    checklist_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-handoff-checklist"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_handoff_checklist",
            "source": self.source,
            "checklist_id": self.checklist_id,
            "handoff_packet_id": self.handoff_packet_id,
            "handoff_status": self.handoff_status,
            "checklist_status": self.checklist_status,
            "checklist_state": self.checklist_state,
            "checked_by": self.checked_by,
            "checklist_note": self.checklist_note,
            "handoff_to": self.handoff_to,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "required_checks": list(self.required_checks),
            "passed_checks": list(self.passed_checks),
            "failed_checks": list(self.failed_checks),
            "handoff_findings": list(self.handoff_findings),
            "checklist_findings": list(self.checklist_findings),
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
            "# Scoped Runtime Execution Gate Bundle Handoff Checklist",
            "",
            "## Summary",
            "",
            f"- Checklist ID: `{self.checklist_id}`",
            f"- Handoff packet ID: `{self.handoff_packet_id}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Checklist status: `{self.checklist_status}`",
            f"- Checklist state: `{self.checklist_state}`",
            f"- Checked by: `{self.checked_by}`",
            f"- Handoff to: `{self.handoff_to}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Checklist note",
            "",
            self.checklist_note or "none",
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
            "## Required checks",
            "",
        ]

        if self.required_checks:
            lines.extend(f"- {item}" for item in self.required_checks)
        else:
            lines.append("- none")

        lines.extend(["", "## Passed checks", ""])
        if self.passed_checks:
            lines.extend(f"- {item}" for item in self.passed_checks)
        else:
            lines.append("- none")

        lines.extend(["", "## Failed checks", ""])
        if self.failed_checks:
            lines.extend(f"- {item}" for item in self.failed_checks)
        else:
            lines.append("- none")

        lines.extend(["", "## Handoff findings", ""])
        if self.handoff_findings:
            lines.extend(f"- {finding}" for finding in self.handoff_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Checklist findings", ""])
        if self.checklist_findings:
            lines.extend(f"- {finding}" for finding in self.checklist_findings)
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
                "This checklist is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def build_scoped_runtime_execution_gate_bundle_handoff_checklist(
    handoff_packet: dict[str, Any],
    *,
    checked_by: str = "human-reviewer",
    checklist_note: str = "",
) -> ScopedRuntimeExecutionGateBundleHandoffChecklist:
    """Create a local checklist from a bundle handoff packet without execution."""
    blocking = list(handoff_packet.get("blocking_findings") or [])

    required_checks = (
        "Input kind is scoped_runtime_execution_gate_bundle_handoff_packet.",
        "Handoff status is ready-local-bundle-handoff-no-execution.",
        "Handoff state is handoff_local_only.",
        "Verification status is verified-local-bundle-no-execution.",
        "Review status is accepted-local-bundle-verification-no-execution.",
        "Bundle mode is local_files_only_no_execution.",
        "Gate ID, request ID, and handoff packet ID are present.",
        "No missing files are reported.",
        "No unexpected files are reported.",
        "Execution and runtime flags remain false.",
        "Safety metadata keeps execution-like capabilities false.",
    )

    passed: list[str] = []
    failed: list[str] = []

    def record(condition: bool, check: str, finding: str) -> None:
        if condition:
            passed.append(check)
        else:
            failed.append(check)
            blocking.append(finding)

    record(
        handoff_packet.get("kind") == "scoped_runtime_execution_gate_bundle_handoff_packet",
        required_checks[0],
        "Handoff checklist input has unexpected artifact kind.",
    )
    record(
        handoff_packet.get("handoff_status") == "ready-local-bundle-handoff-no-execution",
        required_checks[1],
        "Handoff packet is not ready-local-bundle-handoff-no-execution.",
    )
    record(
        handoff_packet.get("handoff_state") == "handoff_local_only",
        required_checks[2],
        "Handoff packet is not in handoff_local_only state.",
    )
    record(
        handoff_packet.get("verification_status") == "verified-local-bundle-no-execution",
        required_checks[3],
        "Handoff packet does not reference a verified local bundle verification artifact.",
    )
    record(
        handoff_packet.get("review_status") == "accepted-local-bundle-verification-no-execution",
        required_checks[4],
        "Handoff packet does not reference an accepted local bundle review packet.",
    )
    record(
        handoff_packet.get("bundle_mode") == "local_files_only_no_execution",
        required_checks[5],
        "Handoff packet does not record local_files_only_no_execution mode.",
    )
    record(
        bool(handoff_packet.get("gate_id")) and bool(handoff_packet.get("request_id")) and bool(handoff_packet.get("handoff_packet_id")),
        required_checks[6],
        "Handoff packet is missing gate_id, request_id, or handoff_packet_id.",
    )
    record(
        not handoff_packet.get("missing_files"),
        required_checks[7],
        "Handoff packet still reports missing files.",
    )
    record(
        not handoff_packet.get("unexpected_files"),
        required_checks[8],
        "Handoff packet still reports unexpected files.",
    )

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
    execution_flags_ok = all(handoff_packet.get(flag) is False for flag in execution_flags)
    record(
        execution_flags_ok,
        required_checks[9],
        "Handoff packet does not keep every execution and runtime flag false.",
    )

    safety = handoff_packet.get("safety")
    safety_keys = (
        "network_requests",
        "tool_execution",
        "evidence_collection",
        "validation_execution",
        "report_submission",
        "vulnerability_confirmation",
    )
    safety_ok = isinstance(safety, dict) and all(safety.get(key) is False for key in safety_keys)
    record(
        safety_ok,
        required_checks[10],
        "Handoff packet safety metadata does not keep every execution-like capability false.",
    )

    checklist_status = (
        "blocked-local-bundle-handoff-checklist"
        if blocking
        else "passed-local-bundle-handoff-checklist-no-execution"
    )

    gate_id = str(handoff_packet.get("gate_id") or "UNKNOWN")
    handoff_packet_id = str(handoff_packet.get("handoff_packet_id") or "UNKNOWN")

    checklist_findings = (
        "Checklist inspected a local bundle handoff packet only.",
        "Checklist confirmed required handoff, verification, review, bundle, gate, and safety metadata.",
        "Checklist preserves not_executed state and false execution flags.",
        "Checklist does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleHandoffChecklist(
        checklist_id=f"SREG-BUNDLE-HANDOFF-CHECKLIST-{gate_id}",
        handoff_packet_id=handoff_packet_id,
        handoff_status=str(handoff_packet.get("handoff_status") or ""),
        checklist_status=checklist_status,
        checklist_state="checked_local_only",
        checked_by=checked_by,
        checklist_note=checklist_note,
        handoff_to=str(handoff_packet.get("handoff_to") or ""),
        verification_status=str(handoff_packet.get("verification_status") or ""),
        review_status=str(handoff_packet.get("review_status") or ""),
        bundle_dir=str(handoff_packet.get("bundle_dir") or ""),
        bundle_mode=str(handoff_packet.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=str(handoff_packet.get("request_id") or ""),
        gate_status=str(handoff_packet.get("gate_status") or ""),
        required_checks=required_checks,
        passed_checks=tuple(passed),
        failed_checks=tuple(failed),
        handoff_findings=tuple(handoff_packet.get("handoff_findings") or ()),
        checklist_findings=checklist_findings,
        blocking_findings=tuple(blocking),
    )



@dataclass(frozen=True)
class ScopedRuntimeExecutionGateBundleHandoffChecklistSummary:
    summary_id: str
    checklist_id: str
    handoff_packet_id: str
    checklist_status: str
    summary_status: str
    summary_state: str
    summarized_by: str
    summary_note: str
    checked_by: str
    handoff_status: str
    handoff_to: str
    verification_status: str
    review_status: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    required_check_count: int
    passed_check_count: int
    failed_check_count: int
    failed_checks: tuple[str, ...]
    checklist_findings: tuple[str, ...]
    summary_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-handoff-checklist-summary"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_handoff_checklist_summary",
            "source": self.source,
            "summary_id": self.summary_id,
            "checklist_id": self.checklist_id,
            "handoff_packet_id": self.handoff_packet_id,
            "checklist_status": self.checklist_status,
            "summary_status": self.summary_status,
            "summary_state": self.summary_state,
            "summarized_by": self.summarized_by,
            "summary_note": self.summary_note,
            "checked_by": self.checked_by,
            "handoff_status": self.handoff_status,
            "handoff_to": self.handoff_to,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "required_check_count": self.required_check_count,
            "passed_check_count": self.passed_check_count,
            "failed_check_count": self.failed_check_count,
            "failed_checks": list(self.failed_checks),
            "checklist_findings": list(self.checklist_findings),
            "summary_findings": list(self.summary_findings),
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
            "# Scoped Runtime Execution Gate Bundle Handoff Checklist Summary",
            "",
            "## Summary",
            "",
            f"- Summary ID: `{self.summary_id}`",
            f"- Checklist ID: `{self.checklist_id}`",
            f"- Handoff packet ID: `{self.handoff_packet_id}`",
            f"- Checklist status: `{self.checklist_status}`",
            f"- Summary status: `{self.summary_status}`",
            f"- Summary state: `{self.summary_state}`",
            f"- Summarized by: `{self.summarized_by}`",
            f"- Checked by: `{self.checked_by}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Handoff to: `{self.handoff_to}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Summary note",
            "",
            self.summary_note or "none",
            "",
            "## Check counts",
            "",
            f"- Required checks: `{self.required_check_count}`",
            f"- Passed checks: `{self.passed_check_count}`",
            f"- Failed checks: `{self.failed_check_count}`",
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
            "## Failed checks",
            "",
        ]

        if self.failed_checks:
            lines.extend(f"- {item}" for item in self.failed_checks)
        else:
            lines.append("- none")

        lines.extend(["", "## Checklist findings", ""])
        if self.checklist_findings:
            lines.extend(f"- {finding}" for finding in self.checklist_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Summary findings", ""])
        if self.summary_findings:
            lines.extend(f"- {finding}" for finding in self.summary_findings)
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
                "This summary is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def summarize_scoped_runtime_execution_gate_bundle_handoff_checklist(
    checklist: dict[str, Any],
    *,
    summarized_by: str = "human-reviewer",
    summary_note: str = "",
) -> ScopedRuntimeExecutionGateBundleHandoffChecklistSummary:
    """Create a compact summary from a bundle handoff checklist without execution."""
    blocking = list(checklist.get("blocking_findings") or [])

    if checklist.get("kind") != "scoped_runtime_execution_gate_bundle_handoff_checklist":
        blocking.append("Checklist summary input has unexpected artifact kind.")

    if checklist.get("checklist_status") != "passed-local-bundle-handoff-checklist-no-execution":
        blocking.append("Checklist is not passed-local-bundle-handoff-checklist-no-execution.")

    if checklist.get("checklist_state") != "checked_local_only":
        blocking.append("Checklist is not in checked_local_only state.")

    if checklist.get("handoff_status") != "ready-local-bundle-handoff-no-execution":
        blocking.append("Checklist does not reference a ready handoff packet.")

    required_checks = tuple(checklist.get("required_checks") or ())
    passed_checks = tuple(checklist.get("passed_checks") or ())
    failed_checks = tuple(checklist.get("failed_checks") or ())

    if failed_checks:
        blocking.append("Checklist still reports failed checks.")

    if len(required_checks) != len(passed_checks) or failed_checks:
        blocking.append("Checklist check counts do not show all required checks passed.")

    if checklist.get("bundle_mode") != "local_files_only_no_execution":
        blocking.append("Checklist does not record local_files_only_no_execution mode.")

    if not checklist.get("gate_id") or not checklist.get("request_id") or not checklist.get("checklist_id"):
        blocking.append("Checklist is missing gate_id, request_id, or checklist_id.")

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
    for flag in execution_flags:
        if checklist.get(flag) is not False:
            blocking.append(f"Checklist does not keep {flag} false.")

    safety = checklist.get("safety")
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
                blocking.append(f"Checklist safety metadata does not keep {safety_key} false.")
    else:
        blocking.append("Checklist is missing safety metadata.")

    summary_status = (
        "blocked-local-bundle-handoff-checklist-summary"
        if blocking
        else "summarized-local-bundle-handoff-checklist-no-execution"
    )

    gate_id = str(checklist.get("gate_id") or "UNKNOWN")
    checklist_id = str(checklist.get("checklist_id") or "UNKNOWN")

    summary_findings = (
        "Checklist summary inspected a local bundle handoff checklist only.",
        "Checklist summary records pass/block status, check counts, failed checks, blockers, and safety metadata.",
        "Checklist summary preserves not_executed state and false execution flags.",
        "Checklist summary does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleHandoffChecklistSummary(
        summary_id=f"SREG-BUNDLE-HANDOFF-CHECKLIST-SUMMARY-{gate_id}",
        checklist_id=checklist_id,
        handoff_packet_id=str(checklist.get("handoff_packet_id") or ""),
        checklist_status=str(checklist.get("checklist_status") or ""),
        summary_status=summary_status,
        summary_state="summarized_local_only",
        summarized_by=summarized_by,
        summary_note=summary_note,
        checked_by=str(checklist.get("checked_by") or ""),
        handoff_status=str(checklist.get("handoff_status") or ""),
        handoff_to=str(checklist.get("handoff_to") or ""),
        verification_status=str(checklist.get("verification_status") or ""),
        review_status=str(checklist.get("review_status") or ""),
        bundle_dir=str(checklist.get("bundle_dir") or ""),
        bundle_mode=str(checklist.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=str(checklist.get("request_id") or ""),
        gate_status=str(checklist.get("gate_status") or ""),
        required_check_count=len(required_checks),
        passed_check_count=len(passed_checks),
        failed_check_count=len(failed_checks),
        failed_checks=failed_checks,
        checklist_findings=tuple(checklist.get("checklist_findings") or ()),
        summary_findings=summary_findings,
        blocking_findings=tuple(blocking),
    )



@dataclass(frozen=True)
class ScopedRuntimeExecutionGateBundleHandoffChecklistSummaryReceipt:
    receipt_id: str
    summary_id: str
    checklist_id: str
    handoff_packet_id: str
    summary_status: str
    receipt_status: str
    receipt_state: str
    received_by: str
    receipt_note: str
    summarized_by: str
    checked_by: str
    checklist_status: str
    handoff_status: str
    handoff_to: str
    verification_status: str
    review_status: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    required_check_count: int
    passed_check_count: int
    failed_check_count: int
    final_handoff_outcome: str
    summary_findings: tuple[str, ...]
    receipt_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-handoff-checklist-summary-receipt"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt",
            "source": self.source,
            "receipt_id": self.receipt_id,
            "summary_id": self.summary_id,
            "checklist_id": self.checklist_id,
            "handoff_packet_id": self.handoff_packet_id,
            "summary_status": self.summary_status,
            "receipt_status": self.receipt_status,
            "receipt_state": self.receipt_state,
            "received_by": self.received_by,
            "receipt_note": self.receipt_note,
            "summarized_by": self.summarized_by,
            "checked_by": self.checked_by,
            "checklist_status": self.checklist_status,
            "handoff_status": self.handoff_status,
            "handoff_to": self.handoff_to,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "required_check_count": self.required_check_count,
            "passed_check_count": self.passed_check_count,
            "failed_check_count": self.failed_check_count,
            "final_handoff_outcome": self.final_handoff_outcome,
            "summary_findings": list(self.summary_findings),
            "receipt_findings": list(self.receipt_findings),
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
            "# Scoped Runtime Execution Gate Bundle Handoff Checklist Summary Receipt",
            "",
            "## Summary",
            "",
            f"- Receipt ID: `{self.receipt_id}`",
            f"- Summary ID: `{self.summary_id}`",
            f"- Checklist ID: `{self.checklist_id}`",
            f"- Handoff packet ID: `{self.handoff_packet_id}`",
            f"- Summary status: `{self.summary_status}`",
            f"- Receipt status: `{self.receipt_status}`",
            f"- Receipt state: `{self.receipt_state}`",
            f"- Received by: `{self.received_by}`",
            f"- Summarized by: `{self.summarized_by}`",
            f"- Checked by: `{self.checked_by}`",
            f"- Checklist status: `{self.checklist_status}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Handoff to: `{self.handoff_to}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            f"- Final handoff outcome: `{self.final_handoff_outcome}`",
            "",
            "## Receipt note",
            "",
            self.receipt_note or "none",
            "",
            "## Check counts",
            "",
            f"- Required checks: `{self.required_check_count}`",
            f"- Passed checks: `{self.passed_check_count}`",
            f"- Failed checks: `{self.failed_check_count}`",
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
            "## Summary findings",
            "",
        ]

        if self.summary_findings:
            lines.extend(f"- {finding}" for finding in self.summary_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Receipt findings", ""])
        if self.receipt_findings:
            lines.extend(f"- {finding}" for finding in self.receipt_findings)
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
                "This receipt is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def build_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt(
    summary: dict[str, Any],
    *,
    received_by: str = "human-reviewer",
    receipt_note: str = "",
) -> ScopedRuntimeExecutionGateBundleHandoffChecklistSummaryReceipt:
    """Create a final local receipt from a bundle handoff checklist summary without execution."""
    blocking = list(summary.get("blocking_findings") or [])

    if summary.get("kind") != "scoped_runtime_execution_gate_bundle_handoff_checklist_summary":
        blocking.append("Summary receipt input has unexpected artifact kind.")

    if summary.get("summary_status") != "summarized-local-bundle-handoff-checklist-no-execution":
        blocking.append("Summary is not summarized-local-bundle-handoff-checklist-no-execution.")

    if summary.get("summary_state") != "summarized_local_only":
        blocking.append("Summary is not in summarized_local_only state.")

    if summary.get("checklist_status") != "passed-local-bundle-handoff-checklist-no-execution":
        blocking.append("Summary does not reference a passed local handoff checklist.")

    if summary.get("handoff_status") != "ready-local-bundle-handoff-no-execution":
        blocking.append("Summary does not reference a ready local handoff packet.")

    if summary.get("bundle_mode") != "local_files_only_no_execution":
        blocking.append("Summary does not record local_files_only_no_execution mode.")

    required_count = int(summary.get("required_check_count") or 0)
    passed_count = int(summary.get("passed_check_count") or 0)
    failed_count = int(summary.get("failed_check_count") or 0)

    if required_count <= 0:
        blocking.append("Summary does not record any required checks.")

    if required_count != passed_count or failed_count != 0:
        blocking.append("Summary check counts do not show all required checks passed.")

    if not summary.get("gate_id") or not summary.get("request_id") or not summary.get("summary_id"):
        blocking.append("Summary is missing gate_id, request_id, or summary_id.")

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
    for flag in execution_flags:
        if summary.get(flag) is not False:
            blocking.append(f"Summary does not keep {flag} false.")

    safety = summary.get("safety")
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
                blocking.append(f"Summary safety metadata does not keep {safety_key} false.")
    else:
        blocking.append("Summary is missing safety metadata.")

    receipt_status = (
        "blocked-local-bundle-handoff-checklist-summary-receipt"
        if blocking
        else "accepted-local-bundle-handoff-checklist-summary-receipt-no-execution"
    )

    final_handoff_outcome = (
        "blocked-local-bundle-handoff-checklist-summary-receipt"
        if blocking
        else "ready-for-future-local-review-no-execution"
    )

    gate_id = str(summary.get("gate_id") or "UNKNOWN")
    summary_id = str(summary.get("summary_id") or "UNKNOWN")

    receipt_findings = (
        "Receipt inspected a local bundle handoff checklist summary only.",
        "Receipt records final local handoff outcome without allowing execution.",
        "Receipt preserves not_executed state and false execution flags.",
        "Receipt does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleHandoffChecklistSummaryReceipt(
        receipt_id=f"SREG-BUNDLE-HANDOFF-CHECKLIST-SUMMARY-RECEIPT-{gate_id}",
        summary_id=summary_id,
        checklist_id=str(summary.get("checklist_id") or ""),
        handoff_packet_id=str(summary.get("handoff_packet_id") or ""),
        summary_status=str(summary.get("summary_status") or ""),
        receipt_status=receipt_status,
        receipt_state="receipt_local_only",
        received_by=received_by,
        receipt_note=receipt_note,
        summarized_by=str(summary.get("summarized_by") or ""),
        checked_by=str(summary.get("checked_by") or ""),
        checklist_status=str(summary.get("checklist_status") or ""),
        handoff_status=str(summary.get("handoff_status") or ""),
        handoff_to=str(summary.get("handoff_to") or ""),
        verification_status=str(summary.get("verification_status") or ""),
        review_status=str(summary.get("review_status") or ""),
        bundle_dir=str(summary.get("bundle_dir") or ""),
        bundle_mode=str(summary.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=str(summary.get("request_id") or ""),
        gate_status=str(summary.get("gate_status") or ""),
        required_check_count=required_count,
        passed_check_count=passed_count,
        failed_check_count=failed_count,
        final_handoff_outcome=final_handoff_outcome,
        summary_findings=tuple(summary.get("summary_findings") or ()),
        receipt_findings=receipt_findings,
        blocking_findings=tuple(blocking),
    )



@dataclass(frozen=True)
class ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifest:
    archive_manifest_id: str
    receipt_id: str
    summary_id: str
    checklist_id: str
    handoff_packet_id: str
    archive_status: str
    archive_state: str
    archived_by: str
    archive_note: str
    receipt_status: str
    receipt_state: str
    final_handoff_outcome: str
    summary_status: str
    checklist_status: str
    handoff_status: str
    verification_status: str
    review_status: str
    bundle_dir: str
    bundle_mode: str
    gate_id: str
    request_id: str
    gate_status: str
    upstream_artifact_chain: tuple[str, ...]
    archived_artifact_ids: dict[str, str]
    required_check_count: int
    passed_check_count: int
    failed_check_count: int
    receipt_findings: tuple[str, ...]
    archive_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-execution-gate-bundle-handoff-receipt-archive-manifest"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
            "source": self.source,
            "archive_manifest_id": self.archive_manifest_id,
            "receipt_id": self.receipt_id,
            "summary_id": self.summary_id,
            "checklist_id": self.checklist_id,
            "handoff_packet_id": self.handoff_packet_id,
            "archive_status": self.archive_status,
            "archive_state": self.archive_state,
            "archived_by": self.archived_by,
            "archive_note": self.archive_note,
            "receipt_status": self.receipt_status,
            "receipt_state": self.receipt_state,
            "final_handoff_outcome": self.final_handoff_outcome,
            "summary_status": self.summary_status,
            "checklist_status": self.checklist_status,
            "handoff_status": self.handoff_status,
            "verification_status": self.verification_status,
            "review_status": self.review_status,
            "bundle_dir": self.bundle_dir,
            "bundle_mode": self.bundle_mode,
            "gate_id": self.gate_id,
            "request_id": self.request_id,
            "gate_status": self.gate_status,
            "upstream_artifact_chain": list(self.upstream_artifact_chain),
            "archived_artifact_ids": dict(self.archived_artifact_ids),
            "required_check_count": self.required_check_count,
            "passed_check_count": self.passed_check_count,
            "failed_check_count": self.failed_check_count,
            "receipt_findings": list(self.receipt_findings),
            "archive_findings": list(self.archive_findings),
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
            "# Scoped Runtime Execution Gate Bundle Handoff Receipt Archive Manifest",
            "",
            "## Summary",
            "",
            f"- Archive manifest ID: `{self.archive_manifest_id}`",
            f"- Receipt ID: `{self.receipt_id}`",
            f"- Summary ID: `{self.summary_id}`",
            f"- Checklist ID: `{self.checklist_id}`",
            f"- Handoff packet ID: `{self.handoff_packet_id}`",
            f"- Archive status: `{self.archive_status}`",
            f"- Archive state: `{self.archive_state}`",
            f"- Archived by: `{self.archived_by}`",
            f"- Receipt status: `{self.receipt_status}`",
            f"- Receipt state: `{self.receipt_state}`",
            f"- Final handoff outcome: `{self.final_handoff_outcome}`",
            f"- Summary status: `{self.summary_status}`",
            f"- Checklist status: `{self.checklist_status}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Review status: `{self.review_status}`",
            f"- Bundle directory: `{self.bundle_dir}`",
            f"- Bundle mode: `{self.bundle_mode}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Request ID: `{self.request_id}`",
            f"- Gate status: `{self.gate_status}`",
            "",
            "## Archive note",
            "",
            self.archive_note or "none",
            "",
            "## Upstream artifact chain",
            "",
        ]

        if self.upstream_artifact_chain:
            lines.extend(f"- {item}" for item in self.upstream_artifact_chain)
        else:
            lines.append("- none")

        lines.extend(["", "## Archived artifact IDs", ""])
        if self.archived_artifact_ids:
            for key, value in self.archived_artifact_ids.items():
                lines.append(f"- {key}: `{value}`")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Check counts",
                "",
                f"- Required checks: `{self.required_check_count}`",
                f"- Passed checks: `{self.passed_check_count}`",
                f"- Failed checks: `{self.failed_check_count}`",
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
                "## Receipt findings",
                "",
            ]
        )

        if self.receipt_findings:
            lines.extend(f"- {finding}" for finding in self.receipt_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Archive findings", ""])
        if self.archive_findings:
            lines.extend(f"- {finding}" for finding in self.archive_findings)
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
                "This archive manifest is local-only, deterministic, planning-only, and dry-run-only.",
                "",
                "It does not execute curl, call subprocess, send network requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )
        return "\n".join(lines)


def build_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest(
    receipt: dict[str, Any],
    *,
    archived_by: str = "human-reviewer",
    archive_note: str = "",
) -> ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifest:
    """Create a final local archive manifest from a bundle handoff receipt without execution."""
    blocking = list(receipt.get("blocking_findings") or [])

    if receipt.get("kind") != "scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt":
        blocking.append("Archive manifest input has unexpected artifact kind.")

    if receipt.get("receipt_status") != "accepted-local-bundle-handoff-checklist-summary-receipt-no-execution":
        blocking.append("Receipt is not accepted-local-bundle-handoff-checklist-summary-receipt-no-execution.")

    if receipt.get("receipt_state") != "receipt_local_only":
        blocking.append("Receipt is not in receipt_local_only state.")

    if receipt.get("final_handoff_outcome") != "ready-for-future-local-review-no-execution":
        blocking.append("Receipt does not record ready-for-future-local-review-no-execution outcome.")

    if receipt.get("summary_status") != "summarized-local-bundle-handoff-checklist-no-execution":
        blocking.append("Receipt does not reference a summarized local checklist summary.")

    if receipt.get("checklist_status") != "passed-local-bundle-handoff-checklist-no-execution":
        blocking.append("Receipt does not reference a passed local handoff checklist.")

    if receipt.get("handoff_status") != "ready-local-bundle-handoff-no-execution":
        blocking.append("Receipt does not reference a ready local handoff packet.")

    if receipt.get("bundle_mode") != "local_files_only_no_execution":
        blocking.append("Receipt does not record local_files_only_no_execution mode.")

    required_count = int(receipt.get("required_check_count") or 0)
    passed_count = int(receipt.get("passed_check_count") or 0)
    failed_count = int(receipt.get("failed_check_count") or 0)

    if required_count <= 0:
        blocking.append("Receipt does not record any required checks.")

    if required_count != passed_count or failed_count != 0:
        blocking.append("Receipt check counts do not show all required checks passed.")

    for field in ("gate_id", "request_id", "receipt_id", "summary_id", "checklist_id", "handoff_packet_id"):
        if not receipt.get(field):
            blocking.append(f"Receipt is missing {field}.")

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
    for flag in execution_flags:
        if receipt.get(flag) is not False:
            blocking.append(f"Receipt does not keep {flag} false.")

    safety = receipt.get("safety")
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
                blocking.append(f"Receipt safety metadata does not keep {safety_key} false.")
    else:
        blocking.append("Receipt is missing safety metadata.")

    archive_status = (
        "blocked-local-bundle-handoff-receipt-archive-manifest"
        if blocking
        else "archived-local-bundle-handoff-receipt-manifest-no-execution"
    )

    gate_id = str(receipt.get("gate_id") or "UNKNOWN")

    upstream_artifact_chain = (
        "scoped_runtime_execution_gate_artifact",
        "scoped_runtime_execution_gate_bundle_verification_artifact",
        "scoped_runtime_execution_gate_bundle_review_packet",
        "scoped_runtime_execution_gate_bundle_handoff_packet",
        "scoped_runtime_execution_gate_bundle_handoff_checklist",
        "scoped_runtime_execution_gate_bundle_handoff_checklist_summary",
        "scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt",
    )

    archived_artifact_ids = {
        "receipt_id": str(receipt.get("receipt_id") or ""),
        "summary_id": str(receipt.get("summary_id") or ""),
        "checklist_id": str(receipt.get("checklist_id") or ""),
        "handoff_packet_id": str(receipt.get("handoff_packet_id") or ""),
        "gate_id": gate_id,
        "request_id": str(receipt.get("request_id") or ""),
    }

    archive_findings = (
        "Archive manifest inspected a local bundle handoff receipt only.",
        "Archive manifest records final receipt, upstream artifact chain, IDs, check counts, and safety metadata.",
        "Archive manifest preserves not_executed state and false execution flags.",
        "Archive manifest does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifest(
        archive_manifest_id=f"SREG-BUNDLE-HANDOFF-RECEIPT-ARCHIVE-{gate_id}",
        receipt_id=str(receipt.get("receipt_id") or ""),
        summary_id=str(receipt.get("summary_id") or ""),
        checklist_id=str(receipt.get("checklist_id") or ""),
        handoff_packet_id=str(receipt.get("handoff_packet_id") or ""),
        archive_status=archive_status,
        archive_state="archive_manifest_local_only",
        archived_by=archived_by,
        archive_note=archive_note,
        receipt_status=str(receipt.get("receipt_status") or ""),
        receipt_state=str(receipt.get("receipt_state") or ""),
        final_handoff_outcome=str(receipt.get("final_handoff_outcome") or ""),
        summary_status=str(receipt.get("summary_status") or ""),
        checklist_status=str(receipt.get("checklist_status") or ""),
        handoff_status=str(receipt.get("handoff_status") or ""),
        verification_status=str(receipt.get("verification_status") or ""),
        review_status=str(receipt.get("review_status") or ""),
        bundle_dir=str(receipt.get("bundle_dir") or ""),
        bundle_mode=str(receipt.get("bundle_mode") or ""),
        gate_id=gate_id,
        request_id=str(receipt.get("request_id") or ""),
        gate_status=str(receipt.get("gate_status") or ""),
        upstream_artifact_chain=upstream_artifact_chain,
        archived_artifact_ids=archived_artifact_ids,
        required_check_count=required_count,
        passed_check_count=passed_count,
        failed_check_count=failed_count,
        receipt_findings=tuple(receipt.get("receipt_findings") or ()),
        archive_findings=archive_findings,
        blocking_findings=tuple(blocking),
    )


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
