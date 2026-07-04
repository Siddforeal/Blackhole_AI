from bugintel.adapters.scoped_runtime.archive_chain import (
    EXPECTED_ARCHIVE_CHAIN,
    NO_EXECUTION_FLAGS,
    SAFETY_FALSE_KEYS,
    ScopedRuntimeArchiveChainValidationResult,
    missing_required_field_findings,
    no_execution_flag_findings,
    safety_metadata_findings,
    status_mismatch_findings,
    upstream_chain_findings,
    validate_scoped_runtime_archive_chain_artifact,
)
"""Scoped runtime adapter contracts.

This package currently defines local deterministic contracts only. It does not
send requests, execute tools, launch browsers, call providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.
"""

from bugintel.adapters.scoped_runtime.archive_chain_batch import (
    ARCHIVE_CHAIN_KIND_RULES,
    ScopedRuntimeArchiveChainBatchItem,
    ScopedRuntimeArchiveChainBatchValidationReport,
    validate_scoped_runtime_archive_chain_directory,
)
from bugintel.adapters.scoped_runtime.archive_chain_integrity import (
    ScopedRuntimeArchiveChainIntegrityManifest,
    ScopedRuntimeArchiveChainIntegrityRecord,
    ScopedRuntimeArchiveChainIntegrityVerification,
    build_scoped_runtime_archive_chain_integrity_manifest,
    verify_scoped_runtime_archive_chain_integrity_manifest,
)
from bugintel.adapters.scoped_runtime.contracts import (
    ScopedAdapterPreparedCommand,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.result_types import (
    ScopedAdapterResult,
    ScopedAdapterScopeGuardResult,
)
from bugintel.adapters.scoped_runtime.scope_guard import validate_scoped_adapter_request
from bugintel.adapters.scoped_runtime.preview_renderer import (
    ScopedRuntimePreviewArtifact,
    render_scoped_runtime_preview,
)
from bugintel.adapters.scoped_runtime.curl_adapter import (
    ScopedCurlAdapter,
    ScopedCurlAdapterPreview,
    render_scoped_curl_adapter_preview,
)
from bugintel.adapters.scoped_runtime.execution_gate import (
    ScopedRuntimeExecutionGate,
    ScopedRuntimeExecutionGateArtifact,
    ScopedRuntimeExecutionGateBundleHandoffChecklist,
    ScopedRuntimeExecutionGateBundleHandoffChecklistSummary,
    ScopedRuntimeExecutionGateBundleHandoffChecklistSummaryReceipt,
    ScopedRuntimeExecutionGateBundleHandoffPacket,
    ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifest,
    ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifestVerification,
    ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifestVerificationReviewPacket,
    ScopedRuntimeExecutionGateBundleReviewPacket,
    ScopedRuntimeExecutionGateBundleVerificationArtifact,
    build_scoped_runtime_execution_gate_bundle_handoff_checklist,
    build_scoped_runtime_execution_gate_bundle_handoff_packet,
    build_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt,
    build_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest,
    verify_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest,
    review_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification,
    evaluate_scoped_runtime_execution_gate,
    review_scoped_runtime_execution_gate_bundle_verification,
    summarize_scoped_runtime_execution_gate_bundle_handoff_checklist,
    verify_scoped_runtime_execution_gate_bundle,
)

__all__ = [
    "verify_scoped_runtime_archive_chain_integrity_manifest",
    "build_scoped_runtime_archive_chain_integrity_manifest",
    "ScopedRuntimeArchiveChainIntegrityVerification",
    "ScopedRuntimeArchiveChainIntegrityRecord",
    "ScopedRuntimeArchiveChainIntegrityManifest",
    "validate_scoped_runtime_archive_chain_directory",
    "ScopedRuntimeArchiveChainBatchValidationReport",
    "ScopedRuntimeArchiveChainBatchItem",
    "ARCHIVE_CHAIN_KIND_RULES",
    "validate_scoped_runtime_archive_chain_artifact",
    "upstream_chain_findings",
    "status_mismatch_findings",
    "safety_metadata_findings",
    "no_execution_flag_findings",
    "missing_required_field_findings",
    "ScopedRuntimeArchiveChainValidationResult",
    "SAFETY_FALSE_KEYS",
    "NO_EXECUTION_FLAGS",
    "EXPECTED_ARCHIVE_CHAIN",
    "ScopedAdapterPreparedCommand",
    "ScopedAdapterRequest",
    "ScopedAdapterResult",
    "ScopedAdapterScopeGuardResult",
    "validate_scoped_adapter_request",
    "ScopedRuntimePreviewArtifact",
    "render_scoped_runtime_preview",
    "ScopedCurlAdapter",
    "ScopedCurlAdapterPreview",
    "render_scoped_curl_adapter_preview",
    "ScopedRuntimeExecutionGate",
    "ScopedRuntimeExecutionGateArtifact",
    "ScopedRuntimeExecutionGateBundleHandoffChecklist",
    "ScopedRuntimeExecutionGateBundleHandoffChecklistSummary",
    "ScopedRuntimeExecutionGateBundleHandoffChecklistSummaryReceipt",
    "ScopedRuntimeExecutionGateBundleHandoffPacket",
    "ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifest",
    "ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifestVerification",
    "ScopedRuntimeExecutionGateBundleHandoffReceiptArchiveManifestVerificationReviewPacket",
    "ScopedRuntimeExecutionGateBundleReviewPacket",
    "ScopedRuntimeExecutionGateBundleVerificationArtifact",
    "build_scoped_runtime_execution_gate_bundle_handoff_checklist",
    "build_scoped_runtime_execution_gate_bundle_handoff_packet",
    "build_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt",
    "build_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
    "verify_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest",
    "review_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification",
    "evaluate_scoped_runtime_execution_gate",
    "review_scoped_runtime_execution_gate_bundle_verification",
    "summarize_scoped_runtime_execution_gate_bundle_handoff_checklist",
    "verify_scoped_runtime_execution_gate_bundle",
]
