"""Contracts for future scoped runtime adapters.

These contracts are local deterministic data models only. They do not execute
curl, Burp, browser, terminal, providers, network requests, evidence collection,
target mutation, report submission, or vulnerability confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SAFE_BLUEPRINT_STATUS = "blueprinted-for-future-scoped-adapter-implementation-no-execution"
SAFE_BLUEPRINT_STATE = "blueprinted_local_only"
SAFE_ADAPTER_EXECUTION_STATE = "not_executed"


@dataclass(frozen=True)
class ScopedAdapterRequest:
    request_id: str
    implementation_blueprint_id: str
    readiness_review_id: str
    execution_plan_id: str
    target_name: str
    endpoint: str
    adapter_family: str
    command_family: str
    resolved_target_url: str
    reviewed_command: str
    reviewed_method: str
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    implementation_blueprint_status: str
    implementation_blueprint_state: str
    source_adapter_execution_state: str
    blueprint_artifact_kind: str
    blueprint_note: str
    proposed_validation_guards: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    scope_check_requirements: tuple[str, ...]
    placeholder_check_requirements: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    unresolved_placeholders: tuple[str, ...]
    missing_safe_flags: tuple[str, ...]
    blocked_flags_seen: tuple[str, ...]
    shell_control_patterns_seen: tuple[str, ...]
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

    @classmethod
    def from_blueprint_artifact(cls, artifact: dict[str, Any]) -> "ScopedAdapterRequest":
        data = artifact if isinstance(artifact, dict) else {}
        return cls(
            request_id=str(data.get("request_id") or "SAER-UNKNOWN"),
            implementation_blueprint_id=str(data.get("implementation_blueprint_id") or "SIB-UNKNOWN"),
            readiness_review_id=str(data.get("readiness_review_id") or "ERR-UNKNOWN"),
            execution_plan_id=str(data.get("execution_plan_id") or "SEP-UNKNOWN"),
            target_name=str(data.get("target_name") or "bug-bounty-target"),
            endpoint=str(data.get("endpoint") or "unknown-endpoint"),
            adapter_family=str(data.get("adapter_family") or "unknown").strip().lower(),
            command_family=str(data.get("command_family") or "unknown").strip().lower(),
            resolved_target_url=str(data.get("resolved_target_url") or ""),
            reviewed_command=str(data.get("reviewed_command") or ""),
            reviewed_method=str(data.get("reviewed_method") or ""),
            reviewed_scheme=str(data.get("reviewed_scheme") or ""),
            reviewed_host=str(data.get("reviewed_host") or ""),
            reviewed_path=str(data.get("reviewed_path") or ""),
            implementation_blueprint_status=str(data.get("implementation_blueprint_status") or ""),
            implementation_blueprint_state=str(data.get("implementation_blueprint_state") or ""),
            source_adapter_execution_state=str(data.get("adapter_execution_state") or ""),
            blueprint_artifact_kind=str(data.get("kind") or "unknown"),
            blueprint_note=str(data.get("blueprint_note") or ""),
            proposed_validation_guards=tuple(_strings(data.get("proposed_validation_guards"))),
            required_preconditions=tuple(_strings(data.get("required_preconditions"))),
            scope_check_requirements=tuple(_strings(data.get("scope_check_requirements"))),
            placeholder_check_requirements=tuple(_strings(data.get("placeholder_check_requirements"))),
            redaction_requirements=tuple(_strings(data.get("redaction_requirements"))),
            stop_conditions=tuple(_strings(data.get("stop_conditions"))),
            unresolved_placeholders=tuple(_strings(data.get("unresolved_placeholders"))),
            missing_safe_flags=tuple(_strings(data.get("missing_safe_flags"))),
            blocked_flags_seen=tuple(_strings(data.get("blocked_flags_seen"))),
            shell_control_patterns_seen=tuple(_strings(data.get("shell_control_patterns_seen"))),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "readiness_review_id": self.readiness_review_id,
            "execution_plan_id": self.execution_plan_id,
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "adapter_family": self.adapter_family,
            "command_family": self.command_family,
            "resolved_target_url": self.resolved_target_url,
            "reviewed_command": self.reviewed_command,
            "reviewed_method": self.reviewed_method,
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "implementation_blueprint_status": self.implementation_blueprint_status,
            "implementation_blueprint_state": self.implementation_blueprint_state,
            "source_adapter_execution_state": self.source_adapter_execution_state,
            "blueprint_artifact_kind": self.blueprint_artifact_kind,
            "blueprint_note": self.blueprint_note,
            "proposed_validation_guards": list(self.proposed_validation_guards),
            "required_preconditions": list(self.required_preconditions),
            "scope_check_requirements": list(self.scope_check_requirements),
            "placeholder_check_requirements": list(self.placeholder_check_requirements),
            "redaction_requirements": list(self.redaction_requirements),
            "stop_conditions": list(self.stop_conditions),
            "unresolved_placeholders": list(self.unresolved_placeholders),
            "missing_safe_flags": list(self.missing_safe_flags),
            "blocked_flags_seen": list(self.blocked_flags_seen),
            "shell_control_patterns_seen": list(self.shell_control_patterns_seen),
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
        }


@dataclass(frozen=True)
class ScopedAdapterPreparedCommand:
    request_id: str
    adapter_family: str
    command_family: str
    reviewed_command: str
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

    @classmethod
    def from_request(cls, request: ScopedAdapterRequest) -> "ScopedAdapterPreparedCommand":
        return cls(
            request_id=request.request_id,
            adapter_family=request.adapter_family,
            command_family=request.command_family,
            reviewed_command=request.reviewed_command,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "adapter_family": self.adapter_family,
            "command_family": self.command_family,
            "reviewed_command": self.reviewed_command,
            "render_mode": self.render_mode,
            "adapter_execution_state": self.adapter_execution_state,
            "can_execute_now": self.can_execute_now,
            "execution_allowed": self.execution_allowed,
            "tool_execution_allowed": self.tool_execution_allowed,
            "network_requests_allowed": self.network_requests_allowed,
            "evidence_collection_allowed": self.evidence_collection_allowed,
            "target_mutation_allowed": self.target_mutation_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "dry_run_only": self.dry_run_only,
        }


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
