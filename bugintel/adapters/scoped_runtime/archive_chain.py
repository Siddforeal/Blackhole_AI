"""Shared scoped runtime archive-chain validation helpers.

This module is local-only and deterministic. It does not execute curl, call
subprocess, send network requests, launch browsers, call providers, collect
evidence, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.adapters.scoped_runtime.result_types import safety_metadata


NO_EXECUTION_FLAGS: tuple[str, ...] = (
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

SAFETY_FALSE_KEYS: tuple[str, ...] = (
    "network_requests",
    "tool_execution",
    "evidence_collection",
    "validation_execution",
    "report_submission",
    "vulnerability_confirmation",
)

EXPECTED_ARCHIVE_CHAIN: tuple[str, ...] = (
    "scoped_runtime_execution_gate_artifact",
    "scoped_runtime_execution_gate_bundle_verification_artifact",
    "scoped_runtime_execution_gate_bundle_review_packet",
    "scoped_runtime_execution_gate_bundle_handoff_packet",
    "scoped_runtime_execution_gate_bundle_handoff_checklist",
    "scoped_runtime_execution_gate_bundle_handoff_checklist_summary",
    "scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt",
)


def no_execution_flag_findings(artifact: dict[str, Any], *, label: str = "artifact") -> tuple[str, ...]:
    """Return findings for execution-like flags that are missing or not false."""
    findings: list[str] = []
    for flag in NO_EXECUTION_FLAGS:
        if artifact.get(flag) is not False:
            findings.append(f"{label} does not keep {flag} false.")
    return tuple(findings)


def safety_metadata_findings(artifact: dict[str, Any], *, label: str = "artifact") -> tuple[str, ...]:
    """Return findings for safety metadata that is missing or not false."""
    safety = artifact.get("safety")
    findings: list[str] = []

    if not isinstance(safety, dict):
        return (f"{label} is missing safety metadata.",)

    for key in SAFETY_FALSE_KEYS:
        if safety.get(key) is not False:
            findings.append(f"{label} safety metadata does not keep {key} false.")
    return tuple(findings)


def missing_required_field_findings(
    artifact: dict[str, Any],
    required_fields: tuple[str, ...],
    *,
    label: str = "artifact",
) -> tuple[str, ...]:
    """Return findings for required fields that are absent or empty."""
    findings: list[str] = []
    for field in required_fields:
        if artifact.get(field) in (None, "", [], {}):
            findings.append(f"{label} is missing {field}.")
    return tuple(findings)


def status_mismatch_findings(
    artifact: dict[str, Any],
    expected_statuses: dict[str, str],
    *,
    label: str = "artifact",
) -> tuple[str, ...]:
    """Return findings for status fields that do not match expected values."""
    findings: list[str] = []
    for field, expected in expected_statuses.items():
        actual = str(artifact.get(field) or "")
        if actual != expected:
            findings.append(f"{label} {field} is `{actual}`; expected `{expected}`.")
    return tuple(findings)


def upstream_chain_findings(
    artifact: dict[str, Any],
    expected_chain: tuple[str, ...] | None = None,
    *,
    label: str = "artifact",
) -> tuple[str, ...]:
    """Return findings for upstream artifact chain mismatches."""
    if expected_chain is None:
        return ()

    actual = tuple(artifact.get("upstream_artifact_chain") or ())
    if actual != expected_chain:
        return (f"{label} upstream artifact chain does not match expected chain.",)
    return ()


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainValidationResult:
    artifact_kind: str
    validation_status: str
    validation_state: str
    validated_by: str
    validation_note: str
    expected_kind: str
    required_fields: tuple[str, ...]
    missing_field_findings: tuple[str, ...]
    expected_statuses: dict[str, str]
    status_findings: tuple[str, ...]
    upstream_artifact_count: int
    expected_upstream_artifact_count: int
    upstream_chain_findings: tuple[str, ...]
    no_execution_findings: tuple[str, ...]
    safety_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-archive-chain-shared-framework"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_archive_chain_validation_result",
            "source": self.source,
            "artifact_kind": self.artifact_kind,
            "validation_status": self.validation_status,
            "validation_state": self.validation_state,
            "validated_by": self.validated_by,
            "validation_note": self.validation_note,
            "expected_kind": self.expected_kind,
            "required_fields": list(self.required_fields),
            "missing_field_findings": list(self.missing_field_findings),
            "expected_statuses": dict(self.expected_statuses),
            "status_findings": list(self.status_findings),
            "upstream_artifact_count": self.upstream_artifact_count,
            "expected_upstream_artifact_count": self.expected_upstream_artifact_count,
            "upstream_chain_findings": list(self.upstream_chain_findings),
            "no_execution_findings": list(self.no_execution_findings),
            "safety_findings": list(self.safety_findings),
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
            "# Scoped Runtime Archive Chain Validation",
            "",
            "## Summary",
            "",
            f"- Artifact kind: `{self.artifact_kind}`",
            f"- Validation status: `{self.validation_status}`",
            f"- Validation state: `{self.validation_state}`",
            f"- Validated by: `{self.validated_by}`",
            f"- Expected kind: `{self.expected_kind or 'none'}`",
            f"- Upstream artifact count: `{self.upstream_artifact_count}`",
            f"- Expected upstream artifact count: `{self.expected_upstream_artifact_count}`",
            "",
            "## Validation note",
            "",
            self.validation_note or "none",
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
            "## Blocking findings",
            "",
        ]

        if self.blocking_findings:
            lines.extend(f"- {finding}" for finding in self.blocking_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Safety statement", ""])
        lines.append("This validation is local-only, deterministic, planning-only, and dry-run-only.")
        lines.append("")
        lines.append(
            "It does not execute curl, call subprocess, send network requests, execute tools, "
            "launch browsers, call providers, collect evidence, mutate targets, submit reports, "
            "or confirm vulnerabilities."
        )
        lines.append("")
        return "\n".join(lines)


def validate_scoped_runtime_archive_chain_artifact(
    artifact: dict[str, Any],
    *,
    expected_kind: str = "",
    required_fields: tuple[str, ...] = (),
    expected_statuses: dict[str, str] | None = None,
    expected_upstream_chain: tuple[str, ...] | None = None,
    validated_by: str = "human-reviewer",
    validation_note: str = "",
) -> ScopedRuntimeArchiveChainValidationResult:
    """Validate a local scoped runtime archive-chain artifact without execution."""
    expected_statuses = expected_statuses or {}
    artifact_kind = str(artifact.get("kind") or "")
    blocking: list[str] = []

    if expected_kind and artifact_kind != expected_kind:
        blocking.append(f"artifact kind is `{artifact_kind}`; expected `{expected_kind}`.")

    missing_findings = missing_required_field_findings(artifact, required_fields)
    status_findings = status_mismatch_findings(artifact, expected_statuses)
    chain_findings = upstream_chain_findings(artifact, expected_upstream_chain)
    execution_findings = no_execution_flag_findings(artifact)
    safety_findings = safety_metadata_findings(artifact)

    blocking.extend(missing_findings)
    blocking.extend(status_findings)
    blocking.extend(chain_findings)
    blocking.extend(execution_findings)
    blocking.extend(safety_findings)

    upstream_chain = tuple(artifact.get("upstream_artifact_chain") or ())
    expected_chain_count = len(expected_upstream_chain or ())

    validation_status = (
        "blocked-local-archive-chain-artifact-validation"
        if blocking
        else "validated-local-archive-chain-artifact-no-execution"
    )

    return ScopedRuntimeArchiveChainValidationResult(
        artifact_kind=artifact_kind,
        validation_status=validation_status,
        validation_state="validated_archive_chain_local_only",
        validated_by=validated_by,
        validation_note=validation_note,
        expected_kind=expected_kind,
        required_fields=required_fields,
        missing_field_findings=missing_findings,
        expected_statuses=expected_statuses,
        status_findings=status_findings,
        upstream_artifact_count=len(upstream_chain),
        expected_upstream_artifact_count=expected_chain_count,
        upstream_chain_findings=chain_findings,
        no_execution_findings=execution_findings,
        safety_findings=safety_findings,
        blocking_findings=tuple(blocking),
    )
