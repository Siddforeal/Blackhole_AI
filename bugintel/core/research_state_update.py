"""
Research state update planner for Blackhole AI Workbench.

This module creates planning-only update plans for research-state JSON after a
human validation result. It does not call LLM providers, send requests, execute
shell commands, launch browsers, use Kali tools, mutate targets, or bypass
authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


VALIDATION_RESULTS = {
    "supported",
    "rejected",
    "needs-more-evidence",
    "deprioritize",
}


@dataclass(frozen=True)
class ResearchStateUpdateAction:
    path: str
    old_value: str | int | bool | None
    new_value: str | int | bool | None
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchStateUpdatePlan:
    target_name: str
    endpoint: str
    validation_result: str
    actions: tuple[ResearchStateUpdateAction, ...]
    required_human_review: bool = True
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "endpoint": self.endpoint,
            "validation_result": self.validation_result,
            "actions": [action.to_dict() for action in self.actions],
            "required_human_review": self.required_human_review,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_research_state_update_plan_markdown(self),
        }


def build_research_state_update_plan(
    research_state_data: dict[str, Any],
    endpoint: str,
    validation_result: str,
    note: str = "",
) -> ResearchStateUpdatePlan:
    """Build a safe update plan for one endpoint in research-state JSON."""
    if validation_result not in VALIDATION_RESULTS:
        raise ValueError(
            "validation_result must be one of: " + ", ".join(sorted(VALIDATION_RESULTS))
        )

    target_name = str(research_state_data.get("target_name") or "unknown-target")
    endpoint_state = _find_endpoint_state(research_state_data, endpoint)

    actions = _actions_for_result(endpoint_state, endpoint, validation_result, note)

    return ResearchStateUpdatePlan(
        target_name=target_name,
        endpoint=endpoint,
        validation_result=validation_result,
        actions=tuple(actions),
    )


def render_research_state_update_plan_markdown(plan: ResearchStateUpdatePlan) -> str:
    """Render a research-state update plan as Markdown."""
    lines = [
        f"# Blackhole Research State Update Plan: {plan.target_name}",
        "",
        "> Planning-only update plan. Review before applying to any case memory.",
        "",
        f"- Endpoint: `{plan.endpoint}`",
        f"- Validation result: `{plan.validation_result}`",
        f"- Human review required: `{plan.required_human_review}`",
        f"- Execution state: `{plan.execution_state}`",
        "",
        "## Proposed Updates",
        "",
        "| # | Path | Old | New | Reason |",
        "|---:|---|---|---|---|",
    ]

    for index, action in enumerate(plan.actions, start=1):
        lines.append(
            f"| {index} | `{action.path}` | `{action.old_value}` | `{action.new_value}` | {action.reason} |"
        )

    lines.extend(
        [
            "",
            "## Safety Notes",
            "",
            "- Do not apply this update unless manual validation evidence supports it.",
            "- Do not mark a finding reportable without redacted evidence and human review.",
            "- Keep provider, network, browser, shell, and Kali execution disabled unless separately approved.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _find_endpoint_state(research_state_data: dict[str, Any], endpoint: str) -> dict[str, Any]:
    for item in research_state_data.get("endpoints") or []:
        if item.get("endpoint") == endpoint:
            return item
    return {
        "endpoint": endpoint,
        "triage_state": "unknown",
        "hypotheses": [],
        "artifacts": [],
    }


def _actions_for_result(
    endpoint_state: dict[str, Any],
    endpoint: str,
    validation_result: str,
    note: str,
) -> list[ResearchStateUpdateAction]:
    old_triage = str(endpoint_state.get("triage_state") or "unknown")
    actions: list[ResearchStateUpdateAction] = []

    if validation_result == "supported":
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].triage_state",
                old_value=old_triage,
                new_value="report-candidate",
                reason="Manual validation supports a security finding candidate.",
            )
        )
        hypothesis_status = "supported"
        artifact_status = "attached-to-report"
    elif validation_result == "rejected":
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].triage_state",
                old_value=old_triage,
                new_value="deprioritized",
                reason="Manual validation rejected the hypothesis or found expected behavior.",
            )
        )
        hypothesis_status = "rejected"
        artifact_status = "rejected"
    elif validation_result == "needs-more-evidence":
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].triage_state",
                old_value=old_triage,
                new_value="needs-more-evidence",
                reason="Manual validation was inconclusive and more safe evidence is required.",
            )
        )
        hypothesis_status = "needs-more-evidence"
        artifact_status = "planned"
    else:
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].triage_state",
                old_value=old_triage,
                new_value="deprioritized",
                reason="Researcher explicitly chose to deprioritize this endpoint.",
            )
        )
        hypothesis_status = "deprioritized"
        artifact_status = "planned"

    hypotheses = endpoint_state.get("hypotheses") or []
    for index, hypothesis in enumerate(hypotheses):
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].hypotheses[{index}].status",
                old_value=str(hypothesis.get("status") or "open"),
                new_value=hypothesis_status,
                reason="Align hypothesis status with manual validation result.",
            )
        )

    artifacts = endpoint_state.get("artifacts") or []
    for index, artifact in enumerate(artifacts):
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].artifacts[{index}].status",
                old_value=str(artifact.get("status") or "planned"),
                new_value=artifact_status,
                reason="Align artifact status with manual validation result.",
            )
        )

    if note:
        actions.append(
            ResearchStateUpdateAction(
                path=f"endpoints[{endpoint}].validation_note",
                old_value=None,
                new_value=note,
                reason="Record human validation note.",
            )
        )

    return actions
