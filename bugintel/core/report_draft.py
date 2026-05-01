"""
Report draft builder for Blackhole AI Workbench.

This module creates a safe, planning-only vulnerability report skeleton from
orchestration JSON. It does not send requests, execute shell commands, launch
browsers, call LLM providers, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ReportDraftSection:
    title: str
    content: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportDraft:
    title: str
    target_name: str
    endpoint_count: int
    sections: tuple[ReportDraftSection, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "target_name": self.target_name,
            "endpoint_count": self.endpoint_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "sections": [section.to_dict() for section in self.sections],
            "markdown": render_report_draft_markdown(self),
        }


def build_report_draft(orchestration_data: dict[str, Any]) -> ReportDraft:
    """Build a report draft skeleton from orchestration JSON."""
    target_name = str(orchestration_data.get("target_name") or "unknown-target")
    endpoints = list(orchestration_data.get("endpoints") or [])
    priorities = list(orchestration_data.get("endpoint_priorities") or [])
    attack_surface_map = orchestration_data.get("attack_surface_map") or {}
    evidence_plan = orchestration_data.get("evidence_requirement_plan") or {}

    title = f"Blackhole Report Draft: {target_name}"

    sections = (
        ReportDraftSection(
            title="Summary",
            content=_summary_section(target_name, endpoints, priorities),
        ),
        ReportDraftSection(
            title="Scope and Authorization",
            content=_scope_section(),
        ),
        ReportDraftSection(
            title="Priority Triage",
            content=_priority_section(priorities),
        ),
        ReportDraftSection(
            title="Attack Surface Grouping",
            content=_attack_surface_section(attack_surface_map),
        ),
        ReportDraftSection(
            title="Evidence Requirements",
            content=_evidence_section(evidence_plan),
        ),
        ReportDraftSection(
            title="Validation Notes",
            content=_validation_section(),
        ),
        ReportDraftSection(
            title="Impact",
            content=_impact_section(),
        ),
        ReportDraftSection(
            title="Steps to Reproduce",
            content=_steps_section(),
        ),
        ReportDraftSection(
            title="Evidence References",
            content=_evidence_references_section(evidence_plan),
        ),
        ReportDraftSection(
            title="Safety and Redaction Checklist",
            content=_safety_section(),
        ),
    )

    return ReportDraft(
        title=title,
        target_name=target_name,
        endpoint_count=len(endpoints),
        sections=sections,
    )


def render_report_draft_markdown(draft: ReportDraft) -> str:
    """Render a report draft as Markdown."""
    lines = [
        f"# {draft.title}",
        "",
        "> Planning-only report draft. Fill this with manually validated evidence before submission.",
        "",
        f"- Target: `{draft.target_name}`",
        f"- Endpoints in orchestration plan: `{draft.endpoint_count}`",
        f"- Execution state: `{draft.execution_state}`",
        "",
    ]

    for section in draft.sections:
        lines.append(f"## {section.title}")
        lines.append("")
        lines.append(section.content.rstrip())
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _summary_section(target_name: str, endpoints: list[Any], priorities: list[dict[str, Any]]) -> str:
    top = priorities[0] if priorities else {}
    top_endpoint = top.get("endpoint", "TBD")
    top_score = top.get("score", "TBD")
    top_band = top.get("band", "TBD")

    return "\n".join(
        [
            f"This draft summarizes a Blackhole-assisted review of `{target_name}`.",
            "",
            f"- Total endpoints considered: `{len(endpoints)}`",
            f"- Highest-priority endpoint: `{top_endpoint}`",
            f"- Highest-priority score: `{top_score}`",
            f"- Highest-priority band: `{top_band}`",
            "",
            "Replace this section with a concise validated finding summary after evidence is collected.",
        ]
    )


def _scope_section() -> str:
    return "\n".join(
        [
            "- [ ] Confirm the target is in the program scope.",
            "- [ ] Confirm the accounts, projects, tenants, files, or objects used are controlled test data.",
            "- [ ] Confirm no real customer data is included.",
            "- [ ] Confirm all active testing was explicitly authorized and non-destructive.",
        ]
    )


def _priority_section(priorities: list[dict[str, Any]]) -> str:
    if not priorities:
        return "No endpoint priority data was present in the orchestration JSON."

    lines = ["| Score | Band | Endpoint | Top Signals |", "|---:|---|---|---|"]

    for item in priorities:
        signals = item.get("signals") or []
        top_signals = ", ".join(signal.get("name", "") for signal in signals[:3]) or "none"
        lines.append(
            f"| {item.get('score', 0)} | {item.get('band', 'info')} | `{item.get('endpoint', '')}` | {top_signals} |"
        )

    return "\n".join(lines)


def _attack_surface_section(attack_surface_map: dict[str, Any]) -> str:
    groups = attack_surface_map.get("groups") or []

    if not groups:
        return "No attack-surface group data was present in the orchestration JSON."

    lines = ["| Group | Count | Max Score | Priority Hint |", "|---|---:|---:|---|"]

    for group in groups:
        lines.append(
            f"| {group.get('name', '')} | {group.get('count', 0)} | {group.get('max_score', 0)} | {group.get('priority_hint', '')} |"
        )

    return "\n".join(lines)


def _evidence_section(evidence_plan: dict[str, Any]) -> str:
    endpoint_plans = evidence_plan.get("endpoint_plans") or []

    if not endpoint_plans:
        return "No evidence requirement plan was present in the orchestration JSON."

    lines = []

    for endpoint_plan in endpoint_plans:
        endpoint = endpoint_plan.get("endpoint", "unknown-endpoint")
        score = endpoint_plan.get("priority_score", 0)
        band = endpoint_plan.get("priority_band", "info")
        requirements = endpoint_plan.get("requirements") or []

        lines.append(f"### `{endpoint}`")
        lines.append("")
        lines.append(f"- Priority: `{band}` / `{score}`")
        lines.append("- Requirements:")
        for requirement in requirements:
            name = requirement.get("name", "unknown-requirement")
            artifact = requirement.get("artifact_type", "artifact")
            redact = "yes" if requirement.get("redaction_required") else "no"
            approval = "yes" if requirement.get("human_approval_required") else "no"
            lines.append(f"  - [ ] `{name}` — artifact: `{artifact}`, redact: `{redact}`, approval: `{approval}`")
        lines.append("")

    return "\n".join(lines).rstrip()


def _validation_section() -> str:
    return "\n".join(
        [
            "Use this section only after manual validation.",
            "",
            "- Observed behavior:",
            "  - TBD",
            "- Expected behavior:",
            "  - TBD",
            "- Security boundary crossed:",
            "  - TBD",
            "- Why this is not intended behavior:",
            "  - TBD",
        ]
    )


def _impact_section() -> str:
    return "\n".join(
        [
            "Describe confirmed impact only.",
            "",
            "- Affected role/account/object:",
            "  - TBD",
            "- Data or action exposed:",
            "  - TBD",
            "- Business/security consequence:",
            "  - TBD",
            "- Severity rationale:",
            "  - TBD",
        ]
    )


def _steps_section() -> str:
    return "\n".join(
        [
            "Replace placeholders with safe, reproducible, authorized steps.",
            "",
            "1. Log in with a controlled test account.",
            "2. Navigate to the relevant feature or prepare the approved request.",
            "3. Perform the non-destructive validation step.",
            "4. Observe the redacted response or UI behavior.",
            "5. Compare against expected authorization or data boundary behavior.",
        ]
    )


def _evidence_references_section(evidence_plan: dict[str, Any]) -> str:
    endpoint_plans = evidence_plan.get("endpoint_plans") or []

    if not endpoint_plans:
        return "- TBD"

    lines = []

    for index, endpoint_plan in enumerate(endpoint_plans, start=1):
        endpoint = endpoint_plan.get("endpoint", "unknown-endpoint")
        lines.append(f"- Endpoint {index}: `{endpoint}`")
        lines.append("  - Request sample: `TBD`")
        lines.append("  - Response sample: `TBD`")
        lines.append("  - Screenshot: `TBD`")
        lines.append("  - Notes: `TBD`")

    return "\n".join(lines)


def _safety_section() -> str:
    return "\n".join(
        [
            "- [ ] Tokens/cookies/API keys redacted.",
            "- [ ] Emails/user identifiers redacted where needed.",
            "- [ ] No customer/private data included.",
            "- [ ] Screenshots reviewed before sharing.",
            "- [ ] All requests/responses are safe and non-destructive.",
            "- [ ] Report text does not include exploit escalation beyond validated scope.",
        ]
    )
