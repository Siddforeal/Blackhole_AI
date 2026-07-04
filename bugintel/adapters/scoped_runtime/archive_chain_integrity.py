"""Integrity manifests for scoped runtime archive-chain artifacts.

This module is local-only and deterministic. It does not execute curl, call
subprocess, send network requests, launch browsers, call providers, collect
evidence, mutate targets, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.adapters.scoped_runtime.archive_chain import (
    no_execution_flag_findings,
    safety_metadata_findings,
)
from bugintel.adapters.scoped_runtime.archive_chain_batch import (
    validate_scoped_runtime_archive_chain_directory,
)
from bugintel.adapters.scoped_runtime.result_types import safety_metadata


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainIntegrityRecord:
    artifact_path: str
    relative_path: str
    filename: str
    artifact_kind: str
    sha256: str
    size_bytes: int
    json_load_status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "relative_path": self.relative_path,
            "filename": self.filename,
            "artifact_kind": self.artifact_kind,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "json_load_status": self.json_load_status,
        }


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainIntegrityManifest:
    manifest_id: str
    manifest_status: str
    manifest_state: str
    input_dir: str
    recursive: bool
    artifact_count: int
    accepted_count: int
    blocked_count: int
    kind_counts: dict[str, int]
    records: tuple[ScopedRuntimeArchiveChainIntegrityRecord, ...]
    batch_validation_status: str
    batch_validation_blocking_findings: tuple[str, ...]
    integrity_findings: tuple[str, ...]
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
    source: str = "scoped-runtime-archive-chain-integrity-manifest"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_archive_chain_integrity_manifest",
            "source": self.source,
            "manifest_id": self.manifest_id,
            "manifest_status": self.manifest_status,
            "manifest_state": self.manifest_state,
            "input_dir": self.input_dir,
            "recursive": self.recursive,
            "artifact_count": self.artifact_count,
            "accepted_count": self.accepted_count,
            "blocked_count": self.blocked_count,
            "kind_counts": dict(self.kind_counts),
            "records": [record.to_dict() for record in self.records],
            "batch_validation_status": self.batch_validation_status,
            "batch_validation_blocking_findings": list(self.batch_validation_blocking_findings),
            "integrity_findings": list(self.integrity_findings),
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
            "# Scoped Runtime Archive Chain Integrity Manifest",
            "",
            "## Summary",
            "",
            f"- Manifest ID: `{self.manifest_id}`",
            f"- Manifest status: `{self.manifest_status}`",
            f"- Manifest state: `{self.manifest_state}`",
            f"- Input directory: `{self.input_dir}`",
            f"- Recursive: `{str(self.recursive).lower()}`",
            f"- Artifact count: `{self.artifact_count}`",
            f"- Accepted count: `{self.accepted_count}`",
            f"- Blocked count: `{self.blocked_count}`",
            f"- Batch validation status: `{self.batch_validation_status}`",
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
                "## Integrity records",
                "",
            ]
        )

        if self.records:
            for record in self.records:
                lines.append(
                    f"- `{record.relative_path}` — `{record.artifact_kind}` — "
                    f"`{record.sha256}` — `{record.size_bytes}` bytes"
                )
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
                "## Integrity findings",
                "",
            ]
        )

        if self.integrity_findings:
            lines.extend(f"- {finding}" for finding in self.integrity_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Blocking findings", ""])
        if self.blocking_findings:
            lines.extend(f"- {finding}" for finding in self.blocking_findings)
        else:
            lines.append("- none")

        lines.extend(["", "## Safety statement", ""])
        lines.append("This integrity manifest is local-only, deterministic, planning-only, and dry-run-only.")
        lines.append("")
        lines.append(
            "It does not execute curl, call subprocess, send network requests, execute tools, "
            "launch browsers, call providers, collect evidence, mutate targets, submit reports, "
            "or confirm vulnerabilities."
        )
        lines.append("")
        return "\n".join(lines)


@dataclass(frozen=True)
class ScopedRuntimeArchiveChainIntegrityVerification:
    verification_id: str
    manifest_id: str
    verification_status: str
    verification_state: str
    manifest_status: str
    manifest_state: str
    artifact_count: int
    verified_count: int
    missing_count: int
    mismatch_count: int
    recomputed_from_files: bool
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
    source: str = "scoped-runtime-archive-chain-integrity-verification"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "scoped_runtime_archive_chain_integrity_verification",
            "source": self.source,
            "verification_id": self.verification_id,
            "manifest_id": self.manifest_id,
            "verification_status": self.verification_status,
            "verification_state": self.verification_state,
            "manifest_status": self.manifest_status,
            "manifest_state": self.manifest_state,
            "artifact_count": self.artifact_count,
            "verified_count": self.verified_count,
            "missing_count": self.missing_count,
            "mismatch_count": self.mismatch_count,
            "recomputed_from_files": self.recomputed_from_files,
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
            "# Scoped Runtime Archive Chain Integrity Verification",
            "",
            "## Summary",
            "",
            f"- Verification ID: `{self.verification_id}`",
            f"- Manifest ID: `{self.manifest_id}`",
            f"- Verification status: `{self.verification_status}`",
            f"- Verification state: `{self.verification_state}`",
            f"- Manifest status: `{self.manifest_status}`",
            f"- Manifest state: `{self.manifest_state}`",
            f"- Artifact count: `{self.artifact_count}`",
            f"- Verified count: `{self.verified_count}`",
            f"- Missing count: `{self.missing_count}`",
            f"- Mismatch count: `{self.mismatch_count}`",
            f"- Recomputed from files: `{str(self.recomputed_from_files).lower()}`",
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

        lines.extend(["", "## Safety statement", ""])
        lines.append("This integrity verification is local-only, deterministic, planning-only, and dry-run-only.")
        lines.append("")
        lines.append(
            "It does not execute curl, call subprocess, send network requests, execute tools, "
            "launch browsers, call providers, collect evidence, mutate targets, submit reports, "
            "or confirm vulnerabilities."
        )
        lines.append("")
        return "\n".join(lines)


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_kind(path: Path) -> tuple[str, str]:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return "unknown", "failed"

    if not isinstance(data, dict):
        return "unknown", "failed"

    return str(data.get("kind") or "unknown"), "loaded"


def build_scoped_runtime_archive_chain_integrity_manifest(
    artifact_dir: Path | str,
    *,
    recursive: bool = False,
) -> ScopedRuntimeArchiveChainIntegrityManifest:
    """Build a local SHA-256 integrity manifest for archive-chain artifacts."""
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

    if not artifact_paths and not blocking:
        blocking.append("Artifact directory contained no JSON files.")

    records: list[ScopedRuntimeArchiveChainIntegrityRecord] = []
    for path in artifact_paths:
        kind, load_status = _artifact_kind(path)
        records.append(
            ScopedRuntimeArchiveChainIntegrityRecord(
                artifact_path=str(path),
                relative_path=str(path.relative_to(root)),
                filename=path.name,
                artifact_kind=kind,
                sha256=_hash_file(path),
                size_bytes=path.stat().st_size,
                json_load_status=load_status,
            )
        )
        if load_status != "loaded":
            blocking.append(f"{path.name} could not be loaded as a JSON object.")

    batch = validate_scoped_runtime_archive_chain_directory(root, recursive=recursive)
    blocking.extend(batch.blocking_findings)

    kind_counts: dict[str, int] = {}
    for record in records:
        kind_counts[record.artifact_kind] = kind_counts.get(record.artifact_kind, 0) + 1

    manifest_status = (
        "blocked-local-archive-chain-integrity-manifest"
        if blocking
        else "created-local-archive-chain-integrity-manifest-no-execution"
    )

    integrity_findings = (
        "Integrity manifest hashed local JSON artifact files only.",
        "Integrity manifest included batch validation status and SHA-256 records.",
        "Integrity manifest preserves not_executed state and false execution flags.",
        "Integrity manifest does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeArchiveChainIntegrityManifest(
        manifest_id=f"SREG-ARCHIVE-CHAIN-INTEGRITY-{root.name or 'ROOT'}",
        manifest_status=manifest_status,
        manifest_state="integrity_manifest_local_only",
        input_dir=str(root),
        recursive=recursive,
        artifact_count=len(records),
        accepted_count=batch.accepted_count,
        blocked_count=batch.blocked_count,
        kind_counts=kind_counts,
        records=tuple(records),
        batch_validation_status=batch.batch_status,
        batch_validation_blocking_findings=tuple(batch.blocking_findings),
        integrity_findings=integrity_findings,
        blocking_findings=tuple(blocking),
    )


def verify_scoped_runtime_archive_chain_integrity_manifest(
    manifest: dict[str, Any],
    *,
    artifact_dir: Path | str | None = None,
) -> ScopedRuntimeArchiveChainIntegrityVerification:
    """Verify a local archive-chain integrity manifest without execution."""
    blocking = list(manifest.get("blocking_findings") or [])

    if manifest.get("kind") != "scoped_runtime_archive_chain_integrity_manifest":
        blocking.append("Integrity verification input has unexpected artifact kind.")

    if manifest.get("manifest_status") != "created-local-archive-chain-integrity-manifest-no-execution":
        blocking.append("Integrity manifest is not created-local-archive-chain-integrity-manifest-no-execution.")

    if manifest.get("manifest_state") != "integrity_manifest_local_only":
        blocking.append("Integrity manifest is not in integrity_manifest_local_only state.")

    if int(manifest.get("artifact_count") or 0) <= 0:
        blocking.append("Integrity manifest does not record any artifacts.")

    blocking.extend(no_execution_flag_findings(manifest, label="Integrity manifest"))
    blocking.extend(safety_metadata_findings(manifest, label="Integrity manifest"))

    records = manifest.get("records")
    if not isinstance(records, list):
        blocking.append("Integrity manifest records field is missing or not a list.")
        records = []

    verified_count = 0
    missing_count = 0
    mismatch_count = 0
    recomputed = artifact_dir is not None
    root = Path(artifact_dir) if artifact_dir is not None else None

    if recomputed:
        for record in records:
            if not isinstance(record, dict):
                blocking.append("Integrity manifest contains a non-object record.")
                continue

            relative_path = str(record.get("relative_path") or "")
            expected_hash = str(record.get("sha256") or "")
            if not relative_path or not expected_hash:
                blocking.append("Integrity manifest record is missing relative_path or sha256.")
                continue

            path = root / relative_path  # type: ignore[operator]
            if not path.exists() or not path.is_file():
                missing_count += 1
                blocking.append(f"Integrity manifest referenced missing file: {relative_path}.")
                continue

            actual_hash = _hash_file(path)
            if actual_hash != expected_hash:
                mismatch_count += 1
                blocking.append(f"Integrity manifest hash mismatch for: {relative_path}.")
                continue

            verified_count += 1

    verification_status = (
        "blocked-local-archive-chain-integrity-verification"
        if blocking
        else "verified-local-archive-chain-integrity-manifest-no-execution"
    )

    verification_findings = (
        "Integrity verification inspected local manifest metadata only." if not recomputed else "Integrity verification recomputed local SHA-256 hashes only.",
        "Integrity verification preserves not_executed state and false execution flags.",
        "Integrity verification does not call curl, subprocess, network, browser, provider, evidence, mutation, report, or vulnerability-confirmation paths.",
    )

    return ScopedRuntimeArchiveChainIntegrityVerification(
        verification_id=f"SREG-ARCHIVE-CHAIN-INTEGRITY-VERIFY-{manifest.get('manifest_id') or 'UNKNOWN'}",
        manifest_id=str(manifest.get("manifest_id") or ""),
        verification_status=verification_status,
        verification_state="integrity_verified_local_only",
        manifest_status=str(manifest.get("manifest_status") or ""),
        manifest_state=str(manifest.get("manifest_state") or ""),
        artifact_count=int(manifest.get("artifact_count") or 0),
        verified_count=verified_count,
        missing_count=missing_count,
        mismatch_count=mismatch_count,
        recomputed_from_files=recomputed,
        verification_findings=verification_findings,
        blocking_findings=tuple(blocking),
    )
