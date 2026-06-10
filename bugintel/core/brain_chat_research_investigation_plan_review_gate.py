"""Research investigation plan review gate.

v1.11.0 milestone:
local research investigation plan packet -> local-only human review gate.

This module only reviews a local JSON packet. It does not browse, generate
commands, execute tools, launch browsers, use Kali tools, send requests,
collect evidence, validate a finding, confirm a vulnerability, submit reports,
or mutate state.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_KIND = "brain_chat_research_investigation_plan_packet"

REQUIRED_PACKET_FIELDS: tuple[str, ...] = (
    "kind",
    "target_name",
    "packet_status",
    "selection_status",
    "investigation_plan_status",
    "selected_count",
    "plan_count",
    "primary_hypothesis_id",
    "hypothesis_plan_ids",
    "plans",
    "rejected_actions",
    "safety_flags",
)

REQUIRED_PLAN_FIELDS: tuple[str, ...] = (
    "hypothesis_id",
    "hypothesis_type",
    "title",
    "priority",
    "confidence",
    "focus",
    "plan_status",
    "investigation_allowed",
    "validation_allowed",
    "evidence_collection_allowed",
    "vulnerability_confirmation_allowed",
    "investigation_phases",
    "review_questions",
    "evidence_requirements",
    "local_only_checks",
    "blocked_until_later_gate",
)

REQUIRED_BLOCKED_GATES: tuple[str, ...] = (
    "runtime validation",
    "target interaction",
    "command generation",
    "browser execution",
    "curl execution",
    "Kali execution",
    "Burp execution",
    "evidence collection",
    "vulnerability confirmation",
    "report submission",
)

FALSE_SAFETY_FLAGS: tuple[str, ...] = (
    "web_browsing",
    "network_interaction",
    "command_generation",
    "tool_execution",
    "browser_execution",
    "curl_execution",
    "kali_execution",
    "burp_execution",
    "target_interaction",
    "evidence_collection",
    "validation_execution",
    "report_submission",
    "vulnerability_confirmation",
)

SAFETY: dict[str, bool] = {
    "local_only": True,
    "planning_only": True,
    "human_approval_required": True,
    "state_mutation": False,
    "case_memory_write": False,
    "research_state_write": False,
    "network_interaction": False,
    "target_mutation": False,
    "tool_execution": False,
    "browser_execution": False,
    "curl_execution": False,
    "kali_execution": False,
    "burp_execution": False,
    "llm_provider_calls": False,
    "provider_execution": False,
    "evidence_collection": False,
    "validation_execution": False,
    "runtime_execution_allowed": False,
    "report_submission": False,
    "vulnerability_confirmation": False,
}

REJECTED_ACTIONS: tuple[str, ...] = (
    "Do not execute investigation plans from this review gate.",
    "Do not generate shell, curl, browser, Burp, Kali, scanner, or exploitation commands from this review gate.",
    "Do not browse, fetch, crawl, send requests, or interact with targets from this review gate.",
    "Do not collect evidence from this review gate.",
    "Do not validate exploitability from this review gate.",
    "Do not confirm vulnerabilities from this review gate.",
    "Do not submit or prepare a final report as confirmed from this review gate.",
    "Do not write case memory or research state from this review gate.",
)


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return data


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    """Write deterministic JSON output."""

    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, text: str) -> None:
    """Write markdown output."""

    Path(path).write_text(text, encoding="utf-8")


def build_research_investigation_plan_review_gate(
    packet: dict[str, Any],
    source: str = "brain-chat-research-investigation-plan-review-gate",
) -> dict[str, Any]:
    """Build a local-only review gate for a research investigation plan packet."""

    schema_findings = _schema_findings(packet)
    safety_findings = _safety_findings(packet)
    plan_findings = _plan_findings(packet)

    plans = packet.get("plans")
    plans_list = plans if isinstance(plans, list) else []
    plan_count = len([item for item in plans_list if isinstance(item, dict)])

    high_findings = [
        item
        for item in schema_findings + safety_findings + plan_findings
        if item.get("severity") == "high"
    ]

    if schema_findings and any(item.get("severity") == "high" for item in schema_findings):
        review_status = "blocked-invalid-packet"
        review_ready = False
        recommendation = "Fix investigation plan packet schema before human review."
    elif plan_count == 0:
        review_status = "blocked-no-investigation-plans"
        review_ready = False
        recommendation = "Provide at least one selected investigation plan before human review."
    elif high_findings:
        review_status = "blocked-unsafe-plan"
        review_ready = False
        recommendation = "Resolve unsafe flags or missing safety gates before human review."
    else:
        review_status = "needs-human-review"
        review_ready = True
        recommendation = "Investigation plan is structurally reviewable by a human. This gate does not approve validation or execution."

    human_review_items = _human_review_items(packet, schema_findings, safety_findings, plan_findings)

    return {
        "kind": "brain_chat_research_investigation_plan_review_gate",
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "review_status": review_status,
        "recommendation": recommendation,
        "packet_kind": _text(packet.get("kind"), ""),
        "packet_status": _text(packet.get("packet_status"), "unknown"),
        "selection_status": _text(packet.get("selection_status"), "unknown"),
        "investigation_plan_status": _text(packet.get("investigation_plan_status"), "unknown"),
        "selected_count": _int(packet.get("selected_count")),
        "plan_count": plan_count,
        "review_ready": review_ready,
        "validation_allowed": False,
        "runtime_execution_allowed": False,
        "evidence_collection_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "schema_findings": schema_findings,
        "safety_findings": safety_findings,
        "plan_findings": plan_findings,
        "counts": {
            "schema_findings": len(schema_findings),
            "safety_findings": len(safety_findings),
            "plan_findings": len(plan_findings),
            "human_review_items": len(human_review_items),
            "rejected_actions": len(REJECTED_ACTIONS),
            "high_findings": len(high_findings),
        },
        "human_review_items": human_review_items,
        "rejected_actions": list(REJECTED_ACTIONS),
        "planning_only": True,
        "execution_state": "not_executed",
        "gate_state": "reviewed_not_used",
        "safety": dict(SAFETY),
    }


def render_research_investigation_plan_review_gate_markdown(review_gate: dict[str, Any]) -> str:
    """Render a human-readable investigation plan review gate."""

    lines: list[str] = [
        "# Research Investigation Plan Review Gate",
        "",
        "## Review Status",
        "",
        f"- kind: `{review_gate.get('kind', '')}`",
        f"- target_name: `{review_gate.get('target_name', '')}`",
        f"- review_status: `{review_gate.get('review_status', '')}`",
        f"- recommendation: {review_gate.get('recommendation', '')}",
        f"- packet_status: `{review_gate.get('packet_status', '')}`",
        f"- investigation_plan_status: `{review_gate.get('investigation_plan_status', '')}`",
        f"- selected_count: `{review_gate.get('selected_count', 0)}`",
        f"- plan_count: `{review_gate.get('plan_count', 0)}`",
        f"- review_ready: `{str(bool(review_gate.get('review_ready'))).lower()}`",
        f"- validation_allowed: `{str(bool(review_gate.get('validation_allowed'))).lower()}`",
        f"- runtime_execution_allowed: `{str(bool(review_gate.get('runtime_execution_allowed'))).lower()}`",
        f"- evidence_collection_allowed: `{str(bool(review_gate.get('evidence_collection_allowed'))).lower()}`",
        f"- report_submission_allowed: `{str(bool(review_gate.get('report_submission_allowed'))).lower()}`",
        f"- vulnerability_confirmation_allowed: `{str(bool(review_gate.get('vulnerability_confirmation_allowed'))).lower()}`",
        "",
        "## Schema Findings",
        "",
    ]

    lines.extend(_render_findings(review_gate.get("schema_findings")))
    lines.extend(["", "## Safety Findings", ""])
    lines.extend(_render_findings(review_gate.get("safety_findings")))
    lines.extend(["", "## Plan Findings", ""])
    lines.extend(_render_findings(review_gate.get("plan_findings")))

    lines.extend(["", "## Human Review Items", ""])
    human_review_items = _list_of_text(review_gate.get("human_review_items"))
    if human_review_items:
        for item in human_review_items:
            lines.append(f"- [ ] {item}")
    else:
        lines.append("- none")

    lines.extend(["", "## Rejected Actions", ""])
    for item in _list_of_text(review_gate.get("rejected_actions")):
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- This review gate is local and planning-only.",
            "- It does not execute investigation plans, generate commands, browse, send requests, collect evidence, validate findings, submit reports, or confirm vulnerabilities.",
            "- Human approval is still required before any later validation or evidence collection workflow.",
            "",
        ]
    )

    return "\n".join(lines)


def build_review_gate_from_file(
    plan_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Load an investigation plan packet, build the review gate, and optionally write outputs."""

    packet = load_json(plan_file)
    review_gate = build_research_investigation_plan_review_gate(packet)

    if output_file is not None:
        write_markdown(output_file, render_research_investigation_plan_review_gate_markdown(review_gate))

    if json_output is not None:
        write_json(json_output, review_gate)

    return review_gate


def _schema_findings(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_KIND:
        findings.append(
            _finding(
                category="schema",
                severity="high",
                message=f"Packet kind must be {EXPECTED_KIND}.",
                subject="kind",
                required_action="Build a valid research investigation plan packet before review.",
            )
        )

    for field in REQUIRED_PACKET_FIELDS:
        if field not in packet:
            findings.append(
                _finding(
                    category="schema",
                    severity="high",
                    message=f"Required packet field is missing: {field}.",
                    subject=field,
                    required_action="Regenerate the investigation plan packet with all required fields.",
                )
            )

    plans = packet.get("plans")
    if "plans" in packet and not isinstance(plans, list):
        findings.append(
            _finding(
                category="schema",
                severity="high",
                message="plans must be a list.",
                subject="plans",
                required_action="Regenerate the packet with plans as a list of objects.",
            )
        )

    if isinstance(plans, list):
        selected_count = _int(packet.get("selected_count"))
        declared_plan_count = _int(packet.get("plan_count"))
        actual_plan_count = len([item for item in plans if isinstance(item, dict)])

        if selected_count != actual_plan_count:
            findings.append(
                _finding(
                    category="schema",
                    severity="medium",
                    message=f"selected_count does not match actual plan count: {selected_count} != {actual_plan_count}.",
                    subject="selected_count",
                    required_action="Review count consistency before relying on this packet.",
                )
            )

        if declared_plan_count != actual_plan_count:
            findings.append(
                _finding(
                    category="schema",
                    severity="medium",
                    message=f"plan_count does not match actual plan count: {declared_plan_count} != {actual_plan_count}.",
                    subject="plan_count",
                    required_action="Review count consistency before relying on this packet.",
                )
            )

    packet_status = _text(packet.get("packet_status"))
    investigation_status = _text(packet.get("investigation_plan_status"))
    allowed_statuses = {"ready-for-human-review", "blocked-no-selected-hypotheses"}

    if packet_status and packet_status not in allowed_statuses:
        findings.append(
            _finding(
                category="schema",
                severity="medium",
                message=f"Unexpected packet_status: {packet_status}.",
                subject="packet_status",
                required_action="Review whether this packet was produced by the expected investigation plan builder.",
            )
        )

    if investigation_status and investigation_status not in allowed_statuses:
        findings.append(
            _finding(
                category="schema",
                severity="medium",
                message=f"Unexpected investigation_plan_status: {investigation_status}.",
                subject="investigation_plan_status",
                required_action="Review whether this packet is ready for this review gate.",
            )
        )

    return findings


def _safety_findings(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    safety_flags = packet.get("safety_flags")
    if not isinstance(safety_flags, dict):
        return [
            _finding(
                category="safety",
                severity="high",
                message="safety_flags must be present as an object.",
                subject="safety_flags",
                required_action="Regenerate the investigation plan packet with explicit false safety flags.",
            )
        ]

    for flag in FALSE_SAFETY_FLAGS:
        if flag not in safety_flags:
            findings.append(
                _finding(
                    category="safety",
                    severity="medium",
                    message=f"Safety flag is missing: {flag}.",
                    subject=f"safety_flags.{flag}",
                    required_action="Regenerate the packet with complete safety metadata.",
                )
            )
            continue

        if bool(safety_flags.get(flag)) is not False:
            findings.append(
                _finding(
                    category="safety",
                    severity="high",
                    message=f"Safety flag must remain false: {flag}.",
                    subject=f"safety_flags.{flag}",
                    required_action="Block this packet until all execution, target interaction, validation, evidence, report, and confirmation flags are false.",
                )
            )

    return findings


def _plan_findings(packet: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    plans = packet.get("plans")

    if not isinstance(plans, list):
        return findings

    for index, plan in enumerate(plans, start=1):
        subject_prefix = f"plans[{index - 1}]"

        if not isinstance(plan, dict):
            findings.append(
                _finding(
                    category="plan",
                    severity="high",
                    message=f"Plan item {index} must be an object.",
                    subject=subject_prefix,
                    required_action="Regenerate plans as JSON objects.",
                )
            )
            continue

        hypothesis_id = _text(plan.get("hypothesis_id"), f"plan-{index}")
        subject = f"{subject_prefix}:{hypothesis_id}"

        for field in REQUIRED_PLAN_FIELDS:
            if field not in plan:
                findings.append(
                    _finding(
                        category="plan",
                        severity="high",
                        message=f"Required plan field is missing: {field}.",
                        subject=subject,
                        required_action="Regenerate the investigation plan with complete per-plan review fields.",
                    )
                )

        if _text(plan.get("plan_status")) != "ready-for-human-review":
            findings.append(
                _finding(
                    category="plan",
                    severity="medium",
                    message=f"Plan status should be ready-for-human-review, got {_text(plan.get('plan_status'), 'missing')}.",
                    subject=subject,
                    required_action="Review plan state before relying on it.",
                )
            )

        if bool(plan.get("validation_allowed")) is not False:
            findings.append(
                _finding(
                    category="plan-safety",
                    severity="high",
                    message="validation_allowed must be false.",
                    subject=subject,
                    required_action="Block this plan until validation is moved to a later approval gate.",
                )
            )

        if bool(plan.get("evidence_collection_allowed")) is not False:
            findings.append(
                _finding(
                    category="plan-safety",
                    severity="high",
                    message="evidence_collection_allowed must be false.",
                    subject=subject,
                    required_action="Block this plan until evidence collection is moved to a later approval gate.",
                )
            )

        if bool(plan.get("vulnerability_confirmation_allowed")) is not False:
            findings.append(
                _finding(
                    category="plan-safety",
                    severity="high",
                    message="vulnerability_confirmation_allowed must be false.",
                    subject=subject,
                    required_action="Block this plan until confirmation is supported by later evidence-backed review.",
                )
            )

        blocked_until_later = _list_of_text(plan.get("blocked_until_later_gate"))
        if not blocked_until_later:
            findings.append(
                _finding(
                    category="plan-safety",
                    severity="high",
                    message="blocked_until_later_gate must list deferred unsafe actions.",
                    subject=subject,
                    required_action="Regenerate the plan with explicit deferred execution, validation, evidence, confirmation, and reporting gates.",
                )
            )
        else:
            normalized = {item.lower() for item in blocked_until_later}
            for required in REQUIRED_BLOCKED_GATES:
                if required.lower() not in normalized:
                    findings.append(
                        _finding(
                            category="plan-safety",
                            severity="medium",
                            message=f"blocked_until_later_gate is missing: {required}.",
                            subject=subject,
                            required_action="Review the blocked gate list for complete deferral of unsafe actions.",
                        )
                    )

        for list_field in ("investigation_phases", "review_questions", "evidence_requirements", "local_only_checks"):
            if list_field in plan and not _list_of_text(plan.get(list_field)):
                findings.append(
                    _finding(
                        category="plan",
                        severity="medium",
                        message=f"{list_field} should contain at least one item.",
                        subject=subject,
                        required_action="Add human-reviewable planning material before review.",
                    )
                )

    return findings


def _human_review_items(
    packet: dict[str, Any],
    schema_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    plan_findings: list[dict[str, str]],
) -> list[str]:
    items = [
        "Confirm this packet is only used for local human review.",
        "Confirm target scope and authorization before any later validation workflow.",
        "Confirm no command, browser, curl, Kali, Burp, scanner, or target interaction is generated from this review gate.",
        "Confirm evidence collection remains blocked until a separate approval workflow.",
        "Confirm validation remains blocked until a separate approval workflow.",
        "Confirm no vulnerability is treated as confirmed or reportable from this review gate.",
        "Confirm report submission remains blocked.",
    ]

    if schema_findings:
        items.append("Review schema findings and regenerate the packet if required fields or counts are wrong.")

    if safety_findings:
        items.append("Review safety findings and block progression until all execution and confirmation flags are false.")

    if plan_findings:
        items.append("Review plan findings for missing fields, incomplete blocked gates, or unsafe per-plan flags.")

    plans = packet.get("plans")
    if isinstance(plans, list) and plans:
        items.append("Review each investigation phase, review question, and evidence requirement for scope alignment.")

    return _dedupe(items)


def _render_findings(value: Any) -> list[str]:
    findings = value if isinstance(value, list) else []

    if not findings:
        return ["- none"]

    lines: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        lines.append(
            "- "
            f"[{finding.get('severity', 'unknown')}] "
            f"{finding.get('category', 'finding')} / {finding.get('subject', 'unknown')}: "
            f"{finding.get('message', '')} "
            f"Required action: {finding.get('required_action', '')}"
        )

    return lines or ["- none"]


def _finding(
    category: str,
    severity: str,
    message: str,
    subject: str,
    required_action: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "subject": subject,
        "required_action": required_action,
    }


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return 0


def _list_of_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []

    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)

    return output


__all__ = [
    "EXPECTED_KIND",
    "REJECTED_ACTIONS",
    "SAFETY",
    "build_research_investigation_plan_review_gate",
    "build_review_gate_from_file",
    "load_json",
    "render_research_investigation_plan_review_gate_markdown",
    "write_json",
    "write_markdown",
]
