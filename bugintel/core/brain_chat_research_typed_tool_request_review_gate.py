"""Review gate for research typed tool-request manifests.

This module validates a planning-only typed tool-request manifest before a
future exact-action runtime-approval template may be created.

It verifies:

- manifest structure and readiness
- deterministic request and manifest digests
- request identity, ordering, profiles, and adapter contracts
- focus-endpoint requirements
- execution-gate input and preview consistency
- fail-closed packet, request, and safety flags

It does not generate commands or payloads, install software, execute tools,
send requests, interact with targets, collect evidence, validate findings,
mutate state, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_research_approved_action_packet import (
    ACTION_PROFILES,
)
from bugintel.core.brain_chat_research_typed_tool_request_manifest import (
    ADAPTER_CONTRACTS,
)
from bugintel.core.tool_execution_gate import (
    build_tool_execution_gate,
)


EXPECTED_KIND = (
    "brain_chat_research_typed_tool_request_manifest"
)
EXPECTED_STATUS = (
    "ready-for-tool-execution-gate-review"
)
READY_STATUS = "ready-for-runtime-approval-template"

REQUEST_ID_PATTERN = re.compile(r"^RTR-[0-9]{3}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

PACKET_FALSE_FLAGS: tuple[str, ...] = (
    "command_generation_allowed",
    "payload_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

REQUEST_FALSE_FLAGS: tuple[str, ...] = (
    "command_generated",
    "payload_generated",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
)

SAFETY_TRUE_FLAGS: tuple[str, ...] = (
    "local_only",
    "planning_only",
    "typed_requests_only",
    "source_human_approval_required",
    "execution_gate_required",
)

SAFETY_FALSE_FLAGS: tuple[str, ...] = (
    "network_interaction",
    "target_mutation",
    "command_generation",
    "payload_generation",
    "tool_execution",
    "browser_execution",
    "curl_execution",
    "kali_execution",
    "burp_execution",
    "provider_execution",
    "package_installation",
    "target_interaction",
    "evidence_collection",
    "validation_execution",
    "runtime_execution_allowed",
    "state_mutation",
    "report_submission",
    "vulnerability_confirmation",
)

REQUIRED_REQUEST_FIELDS: tuple[str, ...] = (
    "request_id",
    "action_id",
    "hypothesis_id",
    "hypothesis_type",
    "action_type",
    "request_kind",
    "name",
    "purpose",
    "manual_order",
    "tool_family",
    "adapter_family",
    "risk_level",
    "risk_reasons",
    "decision_reason",
    "expected_artifact",
    "requires_human_approval",
    "requires_scope_confirmation",
    "requires_controlled_assets",
    "requires_runtime_gate",
    "requires_focus_endpoint",
    "requires_redaction_review",
    "requires_observation_capture",
    "approval_state",
    "request_state",
    "manifest_eligible",
    "allowed_inputs",
    "required_outputs",
    "prohibited_operations",
    "blocked_by",
    "request_digest",
)

REVIEW_SAFETY: dict[str, bool] = {
    "local_only": True,
    "planning_only": True,
    "integrity_review_only": True,
    "runtime_approval_template_required": True,
    "exact_action_approval_required": True,
    "network_interaction": False,
    "target_mutation": False,
    "command_generation": False,
    "payload_generation": False,
    "tool_execution": False,
    "browser_execution": False,
    "curl_execution": False,
    "kali_execution": False,
    "burp_execution": False,
    "provider_execution": False,
    "package_installation": False,
    "target_interaction": False,
    "evidence_collection": False,
    "validation_execution": False,
    "runtime_execution_allowed": False,
    "state_mutation": False,
    "report_submission": False,
    "vulnerability_confirmation": False,
}


def load_json_object(path: str | Path) -> dict[str, Any]:
    source = Path(path)

    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {source}")

    return value


def write_json(
    path: str | Path,
    value: dict[str, Any],
) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_markdown(path: str | Path, text: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def build_research_typed_tool_request_review_gate(
    manifest: dict[str, Any],
    source: str = (
        "brain-chat-research-typed-tool-request-review-gate"
    ),
) -> dict[str, Any]:
    source_manifest = copy.deepcopy(manifest)
    requests = _object_list(
        source_manifest.get("typed_requests")
    )

    manifest_findings = _manifest_findings(
        source_manifest,
        requests,
    )
    request_findings = _request_findings(
        requests,
        focus_endpoint=_optional_text(
            source_manifest.get("focus_endpoint")
        ),
    )
    gate_findings = _gate_findings(
        source_manifest,
        requests,
    )

    findings = (
        manifest_findings
        + request_findings
        + gate_findings
    )

    review_status = _review_status(
        manifest_findings=manifest_findings,
        request_findings=request_findings,
        gate_findings=gate_findings,
        request_count=len(requests),
    )
    review_ready = review_status == READY_STATUS

    request_reviews = [
        _request_review(
            request,
            findings=[
                finding
                for finding in request_findings
                if finding.get("subject")
                == f"typed_requests[{index}]"
            ],
            review_ready=review_ready,
        )
        for index, request in enumerate(requests)
    ]

    high_findings = [
        finding
        for finding in findings
        if finding.get("severity") == "high"
    ]
    medium_findings = [
        finding
        for finding in findings
        if finding.get("severity") == "medium"
    ]

    return {
        "kind": (
            "brain_chat_research_typed_tool_request_review_gate"
        ),
        "source": source,
        "target_name": _text(
            source_manifest.get("target_name"),
            "unknown-target",
        ),
        "focus_endpoint": _optional_text(
            source_manifest.get("focus_endpoint")
        ),
        "review_status": review_status,
        "summary": _summary(
            review_status,
            len(requests),
        ),
        "review_ready": review_ready,
        "runtime_approval_template_ready": review_ready,
        "runtime_execution_allowed": False,
        "source_manifest_kind": _text(
            source_manifest.get("kind"),
            "unknown",
        ),
        "source_manifest_status": _text(
            source_manifest.get("manifest_status"),
            "unknown",
        ),
        "source_manifest_ready": bool(
            source_manifest.get("manifest_ready")
        ),
        "source_manifest_digest": _text(
            source_manifest.get("manifest_digest")
        ),
        "source_approved_action_packet_digest": _text(
            source_manifest.get(
                "approved_action_packet_digest"
            )
        ),
        "typed_request_count": len(requests),
        "request_reviews": request_reviews,
        "manifest_findings": manifest_findings,
        "request_findings": request_findings,
        "gate_findings": gate_findings,
        "counts": {
            "typed_requests": len(requests),
            "request_reviews": len(request_reviews),
            "manifest_findings": len(
                manifest_findings
            ),
            "request_findings": len(
                request_findings
            ),
            "gate_findings": len(gate_findings),
            "high_findings": len(high_findings),
            "medium_findings": len(
                medium_findings
            ),
            "ready_requests": sum(
                bool(item.get("review_ready"))
                for item in request_reviews
            ),
            "blocked_requests": sum(
                not bool(item.get("review_ready"))
                for item in request_reviews
            ),
        },
        "allowed_next_steps": _allowed_next_steps(
            review_status,
            len(requests),
        ),
        "rejected_next_steps": [
            "Do not execute requests from this review gate.",
            "Do not generate commands or payloads.",
            "Do not install software or invoke tools.",
            "Do not send requests or interact with targets.",
            "Do not collect evidence or validate findings.",
            "Do not mutate state or submit reports.",
            "Do not treat planning approval as runtime approval.",
        ],
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": dict(REVIEW_SAFETY),
    }


def build_review_gate_from_file(
    manifest_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    manifest = load_json_object(manifest_file)
    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_typed_tool_request_review_gate_markdown(
                review
            ),
        )

    if json_output is not None:
        write_json(json_output, review)

    return review


def render_research_typed_tool_request_review_gate_markdown(
    review: dict[str, Any],
) -> str:
    lines = [
        "# Research Typed Tool Request Review Gate",
        "",
        "## Review Status",
        "",
        f"- target_name: `{review.get('target_name', '')}`",
        (
            "- focus_endpoint: "
            f"`{review.get('focus_endpoint') or 'none'}`"
        ),
        (
            "- review_status: "
            f"`{review.get('review_status', '')}`"
        ),
        (
            "- review_ready: "
            f"`{_bool_text(review.get('review_ready'))}`"
        ),
        (
            "- runtime_approval_template_ready: "
            f"`{_bool_text(review.get('runtime_approval_template_ready'))}`"
        ),
        (
            "- runtime_execution_allowed: "
            f"`{_bool_text(review.get('runtime_execution_allowed'))}`"
        ),
        f"- summary: {review.get('summary', '')}",
        "",
        "## Request Reviews",
        "",
        (
            "| Request ID | Action ID | Tool Family | Adapter | "
            "Risk | Review Status |"
        ),
        "|---|---|---|---|---|---|",
    ]

    for item in _object_list(
        review.get("request_reviews")
    ):
        lines.append(
            "| "
            f"`{item.get('request_id', '')}` | "
            f"`{item.get('action_id', '')}` | "
            f"`{item.get('tool_family', '')}` | "
            f"`{item.get('adapter_family', '')}` | "
            f"`{item.get('risk_level', '')}` | "
            f"`{item.get('review_status', '')}` |"
        )

    for heading, key in (
        ("Manifest Findings", "manifest_findings"),
        ("Request Findings", "request_findings"),
        ("Execution-Gate Findings", "gate_findings"),
    ):
        lines.extend(["", f"## {heading}", ""])
        lines.extend(_render_findings(review.get(key)))

    lines.extend(["", "## Allowed Next Steps", ""])
    lines.extend(
        [
            f"- {item}"
            for item in _list_of_text(
                review.get("allowed_next_steps")
            )
        ]
        or ["- none"]
    )

    lines.extend(["", "## Safety", ""])
    lines.extend(
        [
            "- This artifact performs integrity and safety review only.",
            "- Command generation allowed: `false`",
            "- Payload generation allowed: `false`",
            "- Package installation allowed: `false`",
            "- Runtime execution allowed: `false`",
            "- Network interaction allowed: `false`",
            "- Target interaction allowed: `false`",
            "- Evidence collection allowed: `false`",
            "- A later exact-action runtime approval is required.",
            "",
        ]
    )

    return "\n".join(lines)


def _manifest_findings(
    manifest: dict[str, Any],
    requests: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if manifest.get("kind") != EXPECTED_KIND:
        findings.append(
            _finding(
                "manifest-schema",
                "high",
                f"kind must be {EXPECTED_KIND}.",
                "kind",
            )
        )

    if (
        _text(manifest.get("manifest_status"))
        != EXPECTED_STATUS
    ):
        findings.append(
            _finding(
                "manifest-readiness",
                "high",
                f"manifest_status must be {EXPECTED_STATUS}.",
                "manifest_status",
            )
        )

    for field in (
        "manifest_ready",
        "execution_gate_input_ready",
        "execution_gate_review_ready",
        "existing_tool_execution_gate_compatible",
    ):
        if not bool(manifest.get(field)):
            findings.append(
                _finding(
                    "manifest-readiness",
                    "high",
                    f"{field} must be true.",
                    field,
                )
            )

    if not _text(manifest.get("target_name")):
        findings.append(
            _finding(
                "manifest-schema",
                "high",
                "target_name must not be empty.",
                "target_name",
            )
        )

    declared_count = _int(
        manifest.get("typed_request_count")
    )
    if declared_count != len(requests):
        findings.append(
            _finding(
                "manifest-consistency",
                "high",
                (
                    "typed_request_count does not match "
                    f"typed_requests: {declared_count} != "
                    f"{len(requests)}."
                ),
                "typed_request_count",
            )
        )

    source_digest = _text(
        manifest.get("approved_action_packet_digest")
    )
    if not SHA256_PATTERN.fullmatch(source_digest):
        findings.append(
            _finding(
                "manifest-integrity",
                "high",
                (
                    "approved_action_packet_digest must be a "
                    "lowercase SHA-256 digest."
                ),
                "approved_action_packet_digest",
            )
        )

    manifest_digest = _text(
        manifest.get("manifest_digest")
    )
    expected_digest = _manifest_digest(manifest)

    if not SHA256_PATTERN.fullmatch(manifest_digest):
        findings.append(
            _finding(
                "manifest-integrity",
                "high",
                (
                    "manifest_digest must be a lowercase "
                    "SHA-256 digest."
                ),
                "manifest_digest",
            )
        )
    elif manifest_digest != expected_digest:
        findings.append(
            _finding(
                "manifest-integrity",
                "high",
                "manifest_digest does not match manifest data.",
                "manifest_digest",
            )
        )

    for field in PACKET_FALSE_FLAGS:
        if bool(manifest.get(field)):
            findings.append(
                _finding(
                    "manifest-safety",
                    "high",
                    f"{field} must remain false.",
                    field,
                )
            )

    if not bool(manifest.get("planning_only")):
        findings.append(
            _finding(
                "manifest-safety",
                "high",
                "planning_only must be true.",
                "planning_only",
            )
        )

    if (
        _text(manifest.get("execution_state"))
        != "not_executed"
    ):
        findings.append(
            _finding(
                "manifest-safety",
                "high",
                "execution_state must be not_executed.",
                "execution_state",
            )
        )

    safety = manifest.get("safety")
    if not isinstance(safety, dict):
        findings.append(
            _finding(
                "manifest-safety",
                "high",
                "safety must be an object.",
                "safety",
            )
        )
        return findings

    for field in SAFETY_TRUE_FLAGS:
        if not bool(safety.get(field)):
            findings.append(
                _finding(
                    "manifest-safety",
                    "high",
                    f"safety.{field} must be true.",
                    f"safety.{field}",
                )
            )

    for field in SAFETY_FALSE_FLAGS:
        if bool(safety.get(field)):
            findings.append(
                _finding(
                    "manifest-safety",
                    "high",
                    f"safety.{field} must remain false.",
                    f"safety.{field}",
                )
            )

    return findings


def _request_findings(
    requests: list[dict[str, Any]],
    focus_endpoint: str | None,
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    request_ids: set[str] = set()
    action_ids: set[str] = set()
    orders: set[int] = set()

    for index, request in enumerate(requests):
        subject = f"typed_requests[{index}]"

        for field in REQUIRED_REQUEST_FIELDS:
            if field not in request:
                findings.append(
                    _finding(
                        "request-schema",
                        "high",
                        f"Required field is missing: {field}.",
                        subject,
                    )
                )

        request_id = _text(request.get("request_id"))
        action_id = _text(request.get("action_id"))
        order = _int(request.get("manual_order"))

        if not REQUEST_ID_PATTERN.fullmatch(request_id):
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    f"Invalid request_id: {request_id or 'missing'}.",
                    subject,
                )
            )
        elif request_id in request_ids:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    f"Duplicate request_id: {request_id}.",
                    subject,
                )
            )

        if not action_id:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    "action_id must not be empty.",
                    subject,
                )
            )
        elif action_id in action_ids:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    f"Duplicate action_id: {action_id}.",
                    subject,
                )
            )

        if order <= 0:
            findings.append(
                _finding(
                    "request-order",
                    "high",
                    "manual_order must be positive.",
                    subject,
                )
            )
        elif order in orders:
            findings.append(
                _finding(
                    "request-order",
                    "high",
                    f"Duplicate manual_order: {order}.",
                    subject,
                )
            )

        expected_id = f"RTR-{index + 1:03d}"
        if request_id and request_id != expected_id:
            findings.append(
                _finding(
                    "request-order",
                    "high",
                    (
                        f"request_id must be {expected_id} "
                        "for deterministic ordering."
                    ),
                    subject,
                )
            )

        request_ids.add(request_id)
        action_ids.add(action_id)
        orders.add(order)

        action_type = _text(request.get("action_type"))
        profile = ACTION_PROFILES.get(action_type)

        if profile is None:
            findings.append(
                _finding(
                    "request-profile",
                    "high",
                    (
                        "Unsupported action_type: "
                        f"{action_type or 'missing'}."
                    ),
                    subject,
                )
            )
        else:
            expected_values = {
                "tool_family": profile["tool_family"],
                "adapter_family": profile[
                    "adapter_family"
                ],
                "request_kind": profile["request_kind"],
                "risk_level": profile["risk_level"],
                "requires_scope_confirmation": profile[
                    "requires_scope_confirmation"
                ],
                "requires_controlled_assets": profile[
                    "requires_controlled_assets"
                ],
                "requires_runtime_gate": profile[
                    "requires_runtime_gate"
                ],
            }

            for field, expected in expected_values.items():
                if request.get(field) != expected:
                    findings.append(
                        _finding(
                            "request-profile",
                            "high",
                            (
                                f"{field} mismatch: "
                                f"{request.get(field)!r} != "
                                f"{expected!r}."
                            ),
                            subject,
                        )
                    )

        adapter = _text(
            request.get("adapter_family")
        )
        contract = ADAPTER_CONTRACTS.get(adapter)

        if contract is None:
            findings.append(
                _finding(
                    "request-contract",
                    "high",
                    (
                        "Unsupported adapter_family: "
                        f"{adapter or 'missing'}."
                    ),
                    subject,
                )
            )
        else:
            for field in (
                "allowed_inputs",
                "required_outputs",
                "prohibited_operations",
            ):
                expected = list(contract[field])
                actual = request.get(field)

                if actual != expected:
                    findings.append(
                        _finding(
                            "request-contract",
                            "high",
                            f"{field} does not match adapter contract.",
                            subject,
                        )
                    )

        if not bool(
            request.get("requires_human_approval")
        ):
            findings.append(
                _finding(
                    "request-safety",
                    "high",
                    "requires_human_approval must be true.",
                    subject,
                )
            )

        if not bool(request.get("manifest_eligible")):
            findings.append(
                _finding(
                    "request-readiness",
                    "high",
                    "manifest_eligible must be true.",
                    subject,
                )
            )

        if (
            _text(request.get("approval_state"))
            != "human-approved-for-planning"
        ):
            findings.append(
                _finding(
                    "request-safety",
                    "high",
                    (
                        "approval_state must be "
                        "human-approved-for-planning."
                    ),
                    subject,
                )
            )

        if (
            _text(request.get("request_state"))
            != "typed-request-not-executable"
        ):
            findings.append(
                _finding(
                    "request-safety",
                    "high",
                    (
                        "request_state must be "
                        "typed-request-not-executable."
                    ),
                    subject,
                )
            )

        if (
            bool(request.get("requires_focus_endpoint"))
            and not focus_endpoint
        ):
            findings.append(
                _finding(
                    "focus-endpoint",
                    "high",
                    (
                        "A focus endpoint is required before "
                        "runtime approval preparation."
                    ),
                    subject,
                )
            )

        for field in REQUEST_FALSE_FLAGS:
            if bool(request.get(field)):
                findings.append(
                    _finding(
                        "request-safety",
                        "high",
                        f"{field} must remain false.",
                        subject,
                    )
                )

        digest = _text(request.get("request_digest"))
        expected_digest = _request_digest(request)

        if not SHA256_PATTERN.fullmatch(digest):
            findings.append(
                _finding(
                    "request-integrity",
                    "high",
                    (
                        "request_digest must be a lowercase "
                        "SHA-256 digest."
                    ),
                    subject,
                )
            )
        elif digest != expected_digest:
            findings.append(
                _finding(
                    "request-integrity",
                    "high",
                    "request_digest does not match request data.",
                    subject,
                )
            )

    return findings


def _gate_findings(
    manifest: dict[str, Any],
    requests: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    gate_input = manifest.get("execution_gate_input")
    stored_preview = manifest.get("execution_gate_preview")

    if not isinstance(gate_input, dict):
        return [
            _finding(
                "gate-consistency",
                "high",
                "execution_gate_input must be an object.",
                "execution_gate_input",
            )
        ]

    if not isinstance(stored_preview, dict):
        return [
            _finding(
                "gate-consistency",
                "high",
                "execution_gate_preview must be an object.",
                "execution_gate_preview",
            )
        ]

    if (
        _text(gate_input.get("target_name"))
        != _text(manifest.get("target_name"))
    ):
        findings.append(
            _finding(
                "gate-consistency",
                "high",
                "Execution-gate target does not match manifest.",
                "execution_gate_input.target_name",
            )
        )

    if (
        _optional_text(gate_input.get("focus_endpoint"))
        != _optional_text(manifest.get("focus_endpoint"))
    ):
        findings.append(
            _finding(
                "gate-consistency",
                "high",
                (
                    "Execution-gate focus endpoint does not "
                    "match manifest."
                ),
                "execution_gate_input.focus_endpoint",
            )
        )

    gate_requests = _object_list(
        gate_input.get("requests")
    )
    if len(gate_requests) != len(requests):
        findings.append(
            _finding(
                "gate-consistency",
                "high",
                (
                    "Execution-gate request count does not "
                    "match typed requests."
                ),
                "execution_gate_input.requests",
            )
        )

    rebuilt = build_tool_execution_gate(
        gate_input
    ).to_dict()
    rebuilt.pop("markdown", None)

    if rebuilt != stored_preview:
        findings.append(
            _finding(
                "gate-consistency",
                "high",
                (
                    "execution_gate_preview does not match "
                    "the current execution_gate_input."
                ),
                "execution_gate_preview",
            )
        )

    if bool(stored_preview.get("execution_allowed")):
        findings.append(
            _finding(
                "gate-safety",
                "high",
                (
                    "Execution-gate preview must keep "
                    "execution_allowed false."
                ),
                "execution_gate_preview.execution_allowed",
            )
        )

    expected_decision = (
        "blocked-manifest-execution-disabled"
        if _optional_text(manifest.get("focus_endpoint"))
        else "blocked-missing-focus-endpoint"
    )

    if (
        _text(stored_preview.get("gate_decision"))
        != expected_decision
    ):
        findings.append(
            _finding(
                "gate-consistency",
                "high",
                (
                    "Unexpected fail-closed gate decision: "
                    f"expected {expected_decision}."
                ),
                "execution_gate_preview.gate_decision",
            )
        )

    return findings


def _request_review(
    request: dict[str, Any],
    findings: list[dict[str, str]],
    review_ready: bool,
) -> dict[str, Any]:
    high = any(
        item.get("severity") == "high"
        for item in findings
    )
    ready = review_ready and not high

    return {
        "request_id": _text(request.get("request_id")),
        "action_id": _text(request.get("action_id")),
        "tool_family": _text(
            request.get("tool_family")
        ),
        "adapter_family": _text(
            request.get("adapter_family")
        ),
        "risk_level": _text(
            request.get("risk_level")
        ),
        "request_digest": _text(
            request.get("request_digest")
        ),
        "review_status": (
            "ready-for-runtime-approval-template"
            if ready
            else "blocked"
        ),
        "review_ready": ready,
        "runtime_execution_allowed": False,
        "finding_count": len(findings),
    }


def _review_status(
    manifest_findings: list[dict[str, str]],
    request_findings: list[dict[str, str]],
    gate_findings: list[dict[str, str]],
    request_count: int,
) -> str:
    all_findings = (
        manifest_findings
        + request_findings
        + gate_findings
    )
    high = [
        item
        for item in all_findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category") in {
            "manifest-safety",
            "request-safety",
            "gate-safety",
        }
        for item in high
    ):
        return "blocked-unsafe-manifest"

    if any(
        item.get("category") == "focus-endpoint"
        for item in high
    ):
        return "blocked-missing-focus-endpoint"

    if any(
        item.get("category") == "manifest-readiness"
        for item in high
    ):
        return "blocked-manifest-not-ready"

    if not request_count:
        return "blocked-no-typed-requests"

    if high:
        return "blocked-invalid-typed-tool-requests"

    return READY_STATUS


def _summary(status: str, count: int) -> str:
    if status == READY_STATUS:
        return (
            f"{count} typed request(s) passed integrity, "
            "contract, safety, focus-endpoint, and execution-"
            "gate consistency review. Runtime execution "
            "remains disabled."
        )

    return (
        "The typed tool-request manifest is blocked from "
        f"runtime-approval preparation: {status}."
    )


def _allowed_next_steps(
    status: str,
    count: int,
) -> list[str]:
    if status != READY_STATUS:
        return []

    return [
        (
            f"Create an exact-action runtime approval template "
            f"for the {count} reviewed request(s)."
        ),
        (
            "Bind every approval entry to the manifest digest, "
            "request digest, focus endpoint, adapter, risk, and "
            "expected artifact."
        ),
        (
            "Keep execution disabled until the later runtime "
            "approval packet and execution adapter review."
        ),
    ]


def _manifest_digest(manifest: dict[str, Any]) -> str:
    material = {
        "target_name": manifest.get("target_name"),
        "focus_endpoint": _optional_text(
            manifest.get("focus_endpoint")
        ),
        "typed_requests": _object_list(
            manifest.get("typed_requests")
        ),
        "source_digest": manifest.get(
            "approved_action_packet_digest"
        ),
    }
    return _sha256(material)


def _request_digest(request: dict[str, Any]) -> str:
    material = copy.deepcopy(request)
    material.pop("request_digest", None)
    return _sha256(material)


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finding(
    category: str,
    severity: str,
    message: str,
    subject: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "subject": subject,
        "required_action": (
            "Correct the source manifest and regenerate the "
            "typed request review gate."
        ),
    }


def _render_findings(value: Any) -> list[str]:
    findings = value if isinstance(value, list) else []
    lines: list[str] = []

    for item in findings:
        if not isinstance(item, dict):
            continue

        lines.append(
            "- "
            f"[{item.get('severity', 'unknown')}] "
            f"{item.get('category', 'finding')} / "
            f"{item.get('subject', 'unknown')}: "
            f"{item.get('message', '')}"
        )

    return lines or ["- none"]


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def _list_of_text(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if not isinstance(value, list):
        return []

    return [
        _text(item)
        for item in value
        if _text(item)
    ]


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text if text else None


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bool_text(value: Any) -> str:
    return str(bool(value)).lower()


__all__ = [
    "EXPECTED_KIND",
    "EXPECTED_STATUS",
    "READY_STATUS",
    "build_research_typed_tool_request_review_gate",
    "build_review_gate_from_file",
    "load_json_object",
    "render_research_typed_tool_request_review_gate_markdown",
    "write_json",
    "write_markdown",
]
