"""Batch validation for scoped runtime archive-chain artifacts.

This module is local-only and deterministic. It does not execute curl, call
subprocess, send network requests, launch browsers, call providers, collect
evidence, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
    ScopedRuntimeArchiveChainValidationResult,
    validate_scoped_runtime_archive_chain_artifact,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata


ARCHIVE_CHAIN_KIND_RULES: dict[str, dict[str, Any]] = {
    "scoped_runtime_execution_gate_artifact": {
        "required_fields": ("gate_id", "request_id", "gate_status", "gate_mode"),
        "expected_statuses": {},
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_verification_artifact": {
        "required_fields": ("gate_id", "request_id", "verification_status", "bundle_mode"),
        "expected_statuses": {
            "verification_status": "verified-local-bundle-no-execution",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_review_packet": {
        "required_fields": ("review_packet_id", "gate_id", "request_id", "review_status", "bundle_mode"),
        "expected_statuses": {
            "review_status": "accepted-local-bundle-verification-no-execution",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_packet": {
        "required_fields": ("handoff_packet_id", "review_packet_id", "gate_id", "request_id", "handoff_status", "handoff_state"),
        "expected_statuses": {
            "handoff_status": "ready-local-bundle-handoff-no-execution",
            "handoff_state": "handoff_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_checklist": {
        "required_fields": ("checklist_id", "handoff_packet_id", "gate_id", "request_id", "checklist_status", "checklist_state"),
        "expected_statuses": {
            "checklist_status": "passed-local-bundle-handoff-checklist-no-execution",
            "checklist_state": "checked_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_checklist_summary": {
        "required_fields": ("summary_id", "checklist_id", "handoff_packet_id", "gate_id", "request_id", "summary_status", "summary_state"),
        "expected_statuses": {
            "summary_status": "summarized-local-bundle-handoff-checklist-no-execution",
            "summary_state": "summarized_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt": {
        "required_fields": ("receipt_id", "summary_id", "checklist_id", "handoff_packet_id", "gate_id", "request_id", "receipt_status", "receipt_state"),
        "expected_statuses": {
            "receipt_status": "accepted-local-bundle-handoff-checklist-summary-receipt-no-execution",
            "receipt_state": "receipt_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest": {
        "required_fields": ("archive_manifest_id", "receipt_id", "summary_id", "checklist_id", "handoff_packet_id", "gate_id", "request_id", "archive_status", "archive_state"),
        "expected_statuses": {
            "archive_status": "archived-local-bundle-handoff-receipt-manifest-no-execution",
            "archive_state": "archive_manifest_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": True,
    },
    "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification": {
        "required_fields": ("verification_id", "archive_manifest_id", "receipt_id", "gate_id", "request_id", "verification_status", "verification_state"),
        "expected_statuses": {
            "verification_status": "verified-local-bundle-handoff-receipt-archive-manifest-no-execution",
            "verification_state": "verified_archive_manifest_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
    "scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification_review_packet": {
        "required_fields": ("review_packet_id", "verification_id", "archive_manifest_id", "receipt_id", "gate_id", "request_id", "review_status", "review_state"),
        "expected_statuses": {
            "review_status": "accepted-local-bundle-handoff-receipt-archive-manifest-verification-review-no-execution",
            "review_state": "reviewed_archive_manifest_verification_local_only",
            "bundle_mode": "local_files_only_no_execution",
        },
        "expect_default_archive_chain": False,
    },
}


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainBatchItem:
    artifact_path: str
    artifact_kind: str
    validation: ScopedRuntimeArchiveChainValidationResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "artifact_kind": self.artifact_kind,
            "validation": self.validation.to_dict(),
        }


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainBatchValidationReport:
    batch_id: str
    batch_status: str
    batch_state: str
    input_dir: str
    artifact_count: int
    accepted_count: int
    blocked_count: int
    kind_counts: dict[str, int]
    items: tuple[ScopedRuntimeArchiveChainBatchItem, ...]
    batch_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-archive-chain-batch-validation"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_archive_chain_batch_validation_report",
            "source": self.source,
            "batch_id": self.batch_id,
            "batch_status": self.batch_status,
            "batch_state": self.batch_state,
            "input_dir": self.input_dir,
            "artifact_count": self.artifact_count,
            "accepted_count": self.accepted_count,
            "blocked_count": self.blocked_count,
            "kind_counts": dict(self.kind_counts),
            "items": [item.to_dict() for item in self.items],
            "batch_findings": list(self.batch_findings),
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
            "# Scoped Runtime Archive Chain Batch Validation",
            "",
            "## Summary",
            "",
            f"- Batch ID: `{self.batch_id}`",
            f"- Batch status: `{self.batch_status}`",
            f"- Batch state: `{self.batch_state}`",
            f"- Input directory: `{self.input_dir}`",
            f"- Artifact count: `{self.artifact_count}`",
            f"- Accepted count: `{self.accepted_count}`",
            f"- Blocked count: `{self.blocked_count}`",
            "",
            "## Kind counts",
            "",
        ]

        if self.kind_counts:
            for kind, count in sorted(self.kind_counts.items()):
                lines.append(f"- {kind}: `{count}`")
        else:
            lines.append("- none")

        lines.extend(
            [
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
                "## Batch findings",
                "",
            ]
        )

        if self.batch_findings:
            lines.extend(f"- {finding}" for finding in self.batch_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Blocking findings", ""])
        if self.blocking_findings:
            lines.extend(f"- {finding}" for finding in self.blocking_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Items", ""])
        if self.items:
            for item in self.items:
                validation = item.validation
                lines.append(f"- `{item.artifact_path}` — `{item.artifact_kind}` — `{validation.validation_status}`")
        else:
            lines.append("- none")

        lines.extend(["", "## Safety statement", ""])
        lines.append("This batch validation is local-only, deterministic, planning-only, and dry-run-only.")
        lines.append("")
        lines.append(
            "It does not execute curl, call subprocess, send network requests, execute tools, "
            "launch browsers, call providers, collect evidence, mutate targets, submit reports, "
            "or confirm vulnerabilities."
        )
        lines.append("")
        return "\n".join(lines)


def _load_json_object(path: Path) -> tuple[dict[str, Any], tuple[str, ...]]:
    try:
        data = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive parse failure
        return {}, (f"{path.name} could not be read as JSON: {exc}",)

    if not isinstance(data, dict):
        return {}, (f"{path.name} did not contain a JSON object.",)

    return data, ()


def _validate_one_artifact(path: Path) -> ScopedRuntimeArchiveChainBatchItem:
    artifact, load_findings = _load_json_object(path)
    artifact_kind = str(artifact.get("kind") or "unknown")

    rule = ARCHIVE_CHAIN_KIND_RULES.get(artifact_kind, {})
    required_fields = tuple(rule.get("required_fields") or ())
    expected_statuses = dict(rule.get("expected_statuses") or {})
    expected_chain = EXPECTED_ARCHIVE_CHAIN if rule.get("expect_default_archive_chain") else None

    validation = validate_scoped_runtime_archive_chain_artifact(
        artifact,
        expected_kind=artifact_kind if artifact_kind != "unknown" else "",
        required_fields=required_fields,
        expected_statuses=expected_statuses,
        expected_upstream_chain=expected_chain,
        validated_by="batch-validator",
        validation_note=f"Batch validation for {path.name}; no execution authorized.",
    )

    if load_findings:
        validation = ScopedRuntimeArchiveChainValidationResult(
            artifact_kind=artifact_kind,
            validation_status="blocked-local-archive-chain-artifact-validation",
            validation_state="validated_archive_chain_local_only",
            validated_by="batch-validator",
            validation_note=f"Batch validation for {path.name}; no execution authorized.",
            expected_kind="",
            required_fields=(),
            missing_field_findings=(),
            expected_statuses={},
            status_findings=(),
            upstream_artifact_count=0,
            expected_upstream_artifact_count=0,
            upstream_chain_findings=(),
            no_execution_findings=(),
            safety_findings=(),
            blocking_findings=load_findings,
        )

    return ScopedRuntimeArchiveChainBatchItem(
        artifact_path=str(path),
        artifact_kind=artifact_kind,
        validation=validation,
    )


def validate_scoped_runtime_archive_chain_directory(
    artifact_dir: Path | str,
    *,
    recursive: bool = False,
) -> ScopedRuntimeArchiveChainBatchValidationReport:
    """Validate all local JSON archive-chain artifacts in a directory without execution."""
    root = Path(artifact_dir)
    blocking: list[str] = []

    if not root.exists():
        blocking.append("Artifact directory does not exist.")
        artifact_paths: tuple[Path, ...] = ()
    elif not root.is_dir():
        blocking.append("Artifact path is not a directory.")
        artifact_paths = ()
    else:
        iterator = root.rglob("*.json") if recursive else root.glob("*.json")
        artifact_paths = tuple(sorted(path for path in iterator if path.is_file()))

    items = tuple(_validate_one_artifact(path) for path in artifact_paths)
    item_blockers = [
        f"{Path(item.artifact_path).name}: {finding}"
        for item in items
        for finding in item.validation.blocking_findings
    ]
    blocking.extend(item_blockers)

    kind_counts: dict[str, int] = {}
    for item in items:
        kind_counts[item.artifact_kind] = kind_counts.get(item.artifact_kind, 0) + 1

    accepted_count = sum(
        1
        for item in items
        if item.validation.validation_status == "validated-local-archive-chain-artifact-no-execution"
    )
    blocked_count = len(items) - accepted_count

    if not items and not blocking:
        blocking.append("Artifact directory contained no JSON files.")

    batch_status = (
        "blocked-local-archive-chain-batch-validation"
        if blocking
        else "validated-local-archive-chain-batch-no-execution"
    )

    batch_findings = (
        "Archive-chain batch validation inspected local JSON files only.",
        "Archive-chain batch validation applied shared artifact rules, no-execution flags, and safety metadata checks.",
        "Archive-chain batch validation preserves not_executed state and false execution flags.",
        "Archive-chain batch validation does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeArchiveChainBatchValidationReport(
        batch_id=f"SREG-ARCHIVE-CHAIN-BATCH-{root.name or 'ROOT'}",
        batch_status=batch_status,
        batch_state="batch_validated_archive_chain_local_only",
        input_dir=str(root),
        artifact_count=len(items),
        accepted_count=accepted_count,
        blocked_count=blocked_count,
        kind_counts=kind_counts,
        items=items,
        batch_findings=batch_findings,
        blocking_findings=tuple(blocking),
    )
