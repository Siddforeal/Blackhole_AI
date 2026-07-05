"""Audit-pack export for scoped runtime archive-chain artifacts.

This module is local-only and deterministic. It does not execute curl, call
subprocess, send network requests, launch browsers, call providers, collect
evidence, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.adapters.scoped_runtime.archive_chain_batch import (
    validate_scoped_runtime_archive_chain_directory,
)
from bugintel.adapters.scoped_runtime.archive_chain_integrity import (
    build_scoped_runtime_archive_chain_integrity_manifest,
    verify_scoped_runtime_archive_chain_integrity_manifest,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainAuditPackFile:
    filename: str
    kind: str
    description: str

    def to_dict(self) -> dict[str, str]:
        return {
            "filename": self.filename,
            "kind": self.kind,
            "description": self.description,
        }


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainAuditPack:
    audit_pack_id: str
    audit_pack_status: str
    audit_pack_state: str
    artifact_dir: str
    output_dir: str
    recursive: bool
    generated_files: tuple[ScopedRuntimeArchiveChainAuditPackFile, ...]
    batch_validation_status: str
    integrity_manifest_status: str
    integrity_verification_status: str
    artifact_count: int
    accepted_count: int
    blocked_count: int
    integrity_record_count: int
    integrity_verified_count: int
    integrity_missing_count: int
    integrity_mismatch_count: int
    pack_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-archive-chain-audit-pack"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_archive_chain_audit_pack",
            "source": self.source,
            "audit_pack_id": self.audit_pack_id,
            "audit_pack_status": self.audit_pack_status,
            "audit_pack_state": self.audit_pack_state,
            "artifact_dir": self.artifact_dir,
            "output_dir": self.output_dir,
            "recursive": self.recursive,
            "generated_files": [item.to_dict() for item in self.generated_files],
            "batch_validation_status": self.batch_validation_status,
            "integrity_manifest_status": self.integrity_manifest_status,
            "integrity_verification_status": self.integrity_verification_status,
            "artifact_count": self.artifact_count,
            "accepted_count": self.accepted_count,
            "blocked_count": self.blocked_count,
            "integrity_record_count": self.integrity_record_count,
            "integrity_verified_count": self.integrity_verified_count,
            "integrity_missing_count": self.integrity_missing_count,
            "integrity_mismatch_count": self.integrity_mismatch_count,
            "pack_findings": list(self.pack_findings),
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
            "# Scoped Runtime Archive Chain Audit Pack",
            "",
            "## Summary",
            "",
            f"- Audit pack ID: `{self.audit_pack_id}`",
            f"- Audit pack status: `{self.audit_pack_status}`",
            f"- Audit pack state: `{self.audit_pack_state}`",
            f"- Artifact directory: `{self.artifact_dir}`",
            f"- Output directory: `{self.output_dir}`",
            f"- Recursive: `{str(self.recursive).lower()}`",
            f"- Batch validation status: `{self.batch_validation_status}`",
            f"- Integrity manifest status: `{self.integrity_manifest_status}`",
            f"- Integrity verification status: `{self.integrity_verification_status}`",
            f"- Artifact count: `{self.artifact_count}`",
            f"- Accepted count: `{self.accepted_count}`",
            f"- Blocked count: `{self.blocked_count}`",
            f"- Integrity record count: `{self.integrity_record_count}`",
            f"- Integrity verified count: `{self.integrity_verified_count}`",
            f"- Integrity missing count: `{self.integrity_missing_count}`",
            f"- Integrity mismatch count: `{self.integrity_mismatch_count}`",
            "",
            "## Generated files",
            "",
        ]

        if self.generated_files:
            for item in self.generated_files:
                lines.append(f"- `{item.filename}` — `{item.kind}` — {item.description}")
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
                "## Pack findings",
                "",
            ]
        )

        if self.pack_findings:
            lines.extend(f"- {finding}" for finding in self.pack_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Blocking findings", ""])
        if self.blocking_findings:
            lines.extend(f"- {finding}" for finding in self.blocking_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Safety statement", ""])
        lines.append("This audit pack is local-only, deterministic, planning-only, and dry-run-only.")
        lines.append("")
        lines.append(
            "It does not execute curl, call subprocess, send network requests, execute tools, "
            "launch browsers, call providers, collect evidence, mutate targets, submit reports, "
            "or confirm vulnerabilities."
        )
        lines.append("")
        return "\n".join(lines)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def _pack_file(filename: str, kind: str, description: str) -> ScopedRuntimeArchiveChainAuditPackFile:
    return ScopedRuntimeArchiveChainAuditPackFile(
        filename=filename,
        kind=kind,
        description=description,
    )


def build_scoped_runtime_archive_chain_audit_pack(
    artifact_dir: Path | str,
    output_dir: Path | str,
    *,
    recursive: bool = False,
) -> ScopedRuntimeArchiveChainAuditPack:
    """Create a local audit pack from archive-chain artifacts without execution."""
    artifact_path = Path(artifact_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    batch = validate_scoped_runtime_archive_chain_directory(artifact_path, recursive=recursive)
    integrity_manifest = build_scoped_runtime_archive_chain_integrity_manifest(
        artifact_path,
        recursive=recursive,
    )
    integrity_verification = verify_scoped_runtime_archive_chain_integrity_manifest(
        integrity_manifest.to_dict(),
        artifact_dir=artifact_path,
    )

    generated_files = (
        _pack_file("batch-validation.json", "scoped_runtime_archive_chain_batch_validation_report_json", "Machine-readable archive-chain batch validation report."),
        _pack_file("batch-validation.md", "scoped_runtime_archive_chain_batch_validation_report_markdown", "Human-readable archive-chain batch validation report."),
        _pack_file("integrity-manifest.json", "scoped_runtime_archive_chain_integrity_manifest_json", "Machine-readable SHA-256 integrity manifest."),
        _pack_file("integrity-manifest.md", "scoped_runtime_archive_chain_integrity_manifest_markdown", "Human-readable SHA-256 integrity manifest."),
        _pack_file("integrity-verification.json", "scoped_runtime_archive_chain_integrity_verification_json", "Machine-readable integrity verification report."),
        _pack_file("integrity-verification.md", "scoped_runtime_archive_chain_integrity_verification_markdown", "Human-readable integrity verification report."),
        _pack_file("audit-pack.json", "scoped_runtime_archive_chain_audit_pack_json", "Machine-readable audit pack index."),
        _pack_file("audit-pack.md", "scoped_runtime_archive_chain_audit_pack_markdown", "Human-readable audit pack index."),
        _pack_file("manifest.json", "scoped_runtime_archive_chain_audit_pack_file_manifest", "Machine-readable audit pack file manifest."),
    )

    blocking: list[str] = []
    blocking.extend(batch.blocking_findings)
    blocking.extend(integrity_manifest.blocking_findings)
    blocking.extend(integrity_verification.blocking_findings)

    if batch.batch_status != "validated-local-archive-chain-batch-no-execution":
        blocking.append("Audit pack batch validation is not validated-local-archive-chain-batch-no-execution.")

    if integrity_manifest.manifest_status != "created-local-archive-chain-integrity-manifest-no-execution":
        blocking.append("Audit pack integrity manifest is not created-local-archive-chain-integrity-manifest-no-execution.")

    if integrity_verification.verification_status != "verified-local-archive-chain-integrity-manifest-no-execution":
        blocking.append("Audit pack integrity verification is not verified-local-archive-chain-integrity-manifest-no-execution.")

    audit_pack_status = (
        "blocked-local-archive-chain-audit-pack"
        if blocking
        else "created-local-archive-chain-audit-pack-no-execution"
    )

    pack_findings = (
        "Audit pack generated local batch validation, integrity manifest, and integrity verification artifacts.",
        "Audit pack wrote JSON and Markdown files under the requested output directory.",
        "Audit pack preserves not_executed state and false execution flags.",
        "Audit pack does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    audit_pack = ScopedRuntimeArchiveChainAuditPack(
        audit_pack_id=f"SREG-ARCHIVE-CHAIN-AUDIT-PACK-{artifact_path.name or 'ROOT'}",
        audit_pack_status=audit_pack_status,
        audit_pack_state="audit_pack_local_only",
        artifact_dir=str(artifact_path),
        output_dir=str(output_path),
        recursive=recursive,
        generated_files=generated_files,
        batch_validation_status=batch.batch_status,
        integrity_manifest_status=integrity_manifest.manifest_status,
        integrity_verification_status=integrity_verification.verification_status,
        artifact_count=batch.artifact_count,
        accepted_count=batch.accepted_count,
        blocked_count=batch.blocked_count,
        integrity_record_count=integrity_manifest.artifact_count,
        integrity_verified_count=integrity_verification.verified_count,
        integrity_missing_count=integrity_verification.missing_count,
        integrity_mismatch_count=integrity_verification.mismatch_count,
        pack_findings=pack_findings,
        blocking_findings=tuple(blocking),
    )

    _write_json(output_path / "batch-validation.json", batch.to_dict())
    (output_path / "batch-validation.md").write_text(batch.to_markdown())

    _write_json(output_path / "integrity-manifest.json", integrity_manifest.to_dict())
    (output_path / "integrity-manifest.md").write_text(integrity_manifest.to_markdown())

    _write_json(output_path / "integrity-verification.json", integrity_verification.to_dict())
    (output_path / "integrity-verification.md").write_text(integrity_verification.to_markdown())

    _write_json(output_path / "audit-pack.json", audit_pack.to_dict())
    (output_path / "audit-pack.md").write_text(audit_pack.to_markdown())

    _write_json(
        output_path / "manifest.json",
        {
            "kind": "scoped_runtime_archive_chain_audit_pack_file_manifest",
            "source": "scoped-runtime-archive-chain-audit-pack",
            "audit_pack_id": audit_pack.audit_pack_id,
            "audit_pack_status": audit_pack.audit_pack_status,
            "artifact_dir": audit_pack.artifact_dir,
            "output_dir": audit_pack.output_dir,
            "generated_files": [item.to_dict() for item in generated_files],
            "adapter_execution_state": "not_executed",
            "can_execute_now": False,
            "execution_allowed": False,
            "validation_allowed": False,
            "runtime_execution_allowed": False,
            "tool_execution_allowed": False,
            "browser_execution_allowed": False,
            "network_requests_allowed": False,
            "evidence_collection_allowed": False,
            "target_mutation_allowed": False,
            "report_submission_allowed": False,
            "vulnerability_confirmation_allowed": False,
            "planning_only": True,
            "dry_run_only": True,
            "safety": safety_metadata(),
        },
    )

    return audit_pack
