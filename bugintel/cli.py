"""
Blackhole AI Workbench CLI.

Commands:
- version
- scope-check
- mine-endpoints
- compare-responses
- build-tree
- plan-curl
- run-curl
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table
from rich.markup import escape
from bugintel.ui.intro import IntroConfig, show_intro

from bugintel.agents.report_agent import save_evidence_report
from bugintel.agents.recon_agent import analyze_html
from bugintel.agents.web_recon_agent import run_website_recon
from bugintel.agents.js_agent import collect_js_sources
from bugintel.agents.ios_agent import analyze_ios_plist
from bugintel.agents.android_agent import analyze_android_manifest
from bugintel.analyzers.endpoint_miner import mine_endpoints
from bugintel.analyzers.http_parser import parse_http_response
from bugintel.analyzers.response_diff import compare_responses, summarize_response
from bugintel.core.evidence_store import EvidenceStore
from bugintel.core.scope_guard import load_scope_from_dict
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.endpoint_investigation import build_endpoint_investigation_profile
from bugintel.core.endpoint_priority import prioritize_endpoints, score_endpoint
from bugintel.core.attack_surface import build_attack_surface_map
from bugintel.core.evidence_requirements import build_evidence_requirement_plan
from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow
from bugintel.core.bug_bounty_case_intake_brain_handoff import build_case_intake_brain_handoff
from bugintel.core.case_intake_brain_handoff_answerer import answer_case_intake_brain_handoff_question
from bugintel.core.evidence_workspace import build_evidence_workspace_manifest, materialize_evidence_workspace
from bugintel.core.report_draft import build_report_draft, render_report_draft_markdown
from bugintel.core.validation_runbook import build_validation_runbook, render_validation_runbook_markdown
from bugintel.core.research_state import build_research_state_from_orchestration, render_research_state_markdown
from bugintel.core.research_state_update import build_research_state_update_plan, render_research_state_update_plan_markdown
from bugintel.core.result_interpreter import interpret_validation_result
from bugintel.core.result_evidence import import_result_evidence, import_result_evidence_batch, review_result_evidence_batch
from bugintel.core.result_evidence_report import render_result_evidence_review_report
from bugintel.core.result_evidence_finding_draft import render_result_evidence_finding_draft
from bugintel.core.result_evidence_finding_package import build_result_evidence_finding_package
from bugintel.core.result_evidence_hypothesis import generate_result_evidence_hypotheses
from bugintel.core.result_evidence_validation_plan import build_result_evidence_validation_plan
from bugintel.core.result_evidence_case_summary import build_result_evidence_case_summary
from bugintel.core.result_evidence_chat import answer_case_question
from bugintel.core.result_evidence_chat_session import append_case_chat_turn_to_file
from bugintel.core.result_evidence_priority_ranking import build_result_evidence_priority_ranking
from bugintel.core.result_evidence_multi_agent_review import build_result_evidence_multi_agent_review_plan
from bugintel.core.result_evidence_report_assistant import build_case_report_assistant_draft
from bugintel.core.result_evidence_chat_context import answer_case_context_question
from bugintel.core.result_evidence_grounding import build_grounded_answer
from bugintel.core.result_evidence_case_memory import build_result_evidence_case_memory
from bugintel.core.result_evidence_chat_prompt import build_case_chat_prompt_package, render_case_chat_prompt_package_markdown
from bugintel.core.result_evidence_chat_provider_gate import build_case_chat_provider_gate
from bugintel.core.result_evidence_chat_provider_dry_run import build_case_chat_provider_dry_run
from bugintel.core.result_evidence_chat_provider_result import import_case_chat_provider_result
from bugintel.core.result_evidence_chat_provider_result_review import review_case_chat_provider_result
from bugintel.core.result_evidence_provider_action_plan import build_provider_suggestion_action_plan
from bugintel.core.result_evidence_action_plan_apply_preview import build_provider_suggestion_action_plan_apply_preview
from bugintel.core.result_evidence_action_plan_apply_preview_review import build_action_plan_apply_preview_review
from bugintel.core.result_evidence_reviewed_apply_packet import build_reviewed_apply_packet
from bugintel.core.result_evidence_reviewed_apply_packet_export_bundle import (build_bundle_artifact_from_path, build_reviewed_apply_packet_export_bundle)
from bugintel.core.result_evidence_export_bundle_review_gate import build_export_bundle_review_gate
from bugintel.core.result_evidence_export_bundle_report_readiness import build_export_bundle_report_readiness_review
from bugintel.core.result_evidence_report_readiness_finding_draft_packet import build_report_readiness_finding_draft_packet
from bugintel.core.result_evidence_finding_draft_packet_review_gate import build_finding_draft_packet_review_gate
from bugintel.core.result_evidence_human_report_skeleton_packet import build_human_report_skeleton_packet
from bugintel.core.result_evidence_human_report_skeleton_review_gate import build_human_report_skeleton_review_gate
from bugintel.core.result_evidence_chat_router import route_chat_context
from bugintel.core.result_update_bridge import build_update_plan_from_interpretation
from bugintel.core.result_flow import build_result_flow
from bugintel.core.research_state_apply import apply_research_state_update_plan
from bugintel.core.case_timeline import build_case_timeline, render_case_timeline_markdown
from bugintel.core.case_summary import build_case_summary, render_case_summary_markdown
from bugintel.core.ai_brain import build_ai_brain_plan, render_ai_brain_plan_markdown
from bugintel.core.brain_prompt import build_brain_prompt_package, render_brain_prompt_package_markdown
from bugintel.core.brain_review import build_brain_review, render_brain_review_markdown
from bugintel.core.brain_decision import build_brain_decision_gate, render_brain_decision_gate_markdown
from bugintel.core.brain_approval import build_brain_approval_packet, render_brain_approval_packet_markdown
from bugintel.core.tool_request_manifest import build_tool_request_manifest, render_tool_request_manifest_markdown
from bugintel.core.tool_execution_gate import build_tool_execution_gate, render_tool_execution_gate_markdown
from bugintel.core.brain_chat import build_brain_chat_reply
from bugintel.core.brain_state_export import build_brain_state_export
from bugintel.core.brain_chat_demo_flow import run_brain_chat_demo_flow
from bugintel.core.brain_chat_session import append_brain_chat_turn, load_brain_chat_session, render_brain_chat_session_summary, save_brain_chat_session, summarize_brain_chat_session
from bugintel.core.brain_chat_session_next_step import build_brain_chat_session_next_step_plan
from bugintel.core.brain_chat_case_dashboard import build_brain_chat_case_dashboard
from bugintel.core.brain_chat_case_dashboard_review_packet import build_brain_chat_case_dashboard_review_packet
from bugintel.core.brain_chat_evidence_checklist import build_brain_chat_evidence_checklist
from bugintel.core.brain_chat_evidence_checklist_status_importer import import_evidence_checklist_status_file
from bugintel.core.brain_chat_evidence_checklist_review_gate import build_evidence_checklist_review_gate
from bugintel.core.brain_chat_evidence_approval_request import build_evidence_approval_request
from bugintel.core.brain_chat_evidence_approval_decision_importer import import_evidence_approval_decision_file
from bugintel.core.brain_chat_evidence_approved_validation_plan import build_evidence_approved_validation_plan
from bugintel.core.brain_chat_validation_plan_step_review_gate import build_validation_plan_step_review_gate
from bugintel.core.brain_chat_validation_step_approval_request import build_validation_step_approval_request
from bugintel.core.brain_chat_validation_step_approval_decision_importer import import_validation_step_approval_decision_file
from bugintel.core.brain_chat_validation_step_execution_gate_proposal import build_validation_step_execution_gate_proposal
from bugintel.core.brain_chat_execution_gate_proposal_review_packet import build_execution_gate_proposal_review_packet
from bugintel.core.brain_chat_case_intelligence_status_summary import build_case_intelligence_status_summary
from bugintel.core.brain_chat_case_intelligence_question_answerer import answer_case_intelligence_question
from bugintel.core.brain_chat_case_intelligence_question_set_runner import run_case_intelligence_question_set
from bugintel.core.brain_chat_case_intelligence_briefing_export import build_case_intelligence_briefing_export
from bugintel.core.brain_chat_case_intelligence_briefing_review_gate import build_case_intelligence_briefing_review_gate
from bugintel.core.brain_chat_case_intelligence_human_review_request import build_case_intelligence_human_review_request
from bugintel.core.brain_chat_case_intelligence_human_review_decision_importer import import_case_intelligence_human_review_decision_file
from bugintel.core.brain_chat_case_intelligence_human_review_decision_gate import build_case_intelligence_human_review_decision_gate
from bugintel.core.brain_chat_human_case_review_packet import build_human_case_review_packet
from bugintel.core.brain_chat_human_case_review_packet_review_gate import build_human_case_review_packet_review_gate
from bugintel.core.brain_chat_human_case_review_decision_request import build_human_case_review_decision_request
from bugintel.core.brain_chat_human_case_review_decision_importer import import_human_case_review_decision_file
from bugintel.core.brain_chat_human_case_review_decision_gate import build_human_case_review_decision_gate
from bugintel.core.task_tree import build_endpoint_task_tree, render_tree
from bugintel.core.research_planner import build_research_plan_from_browser_evidence, render_research_plan_markdown, ResearchPlan, ResearchHypothesis, ResearchRecommendation, EvidenceReference
from bugintel.core.llm_prompt import LLMPromptPackage, build_llm_prompt_package_from_research_plan, render_llm_prompt_package_markdown
from bugintel.core.llm_provider import run_disabled_llm_provider
from bugintel.core.llm_provider_config import LLMProviderConfig, validate_provider_config
from bugintel.core.llm_safety import audit_llm_prompt_package, render_llm_prompt_safety_markdown
from bugintel.integrations.kali_runner import build_curl_plan, execute_curl_plan
from bugintel.integrations.playwright_runner import (
    BrowserAction,
    BrowserCaptureResult,
    BrowserExecutionConfig,
    BrowserPlan,
    PlaywrightArtifactPlan,
    PlaywrightExecutionRequest,
    PlaywrightExecutionSafetyError,
    build_browser_plan,
    build_playwright_adapter_context,
    build_playwright_execution_preview,
    build_playwright_execution_request,
    execute_playwright_plan,
    load_browser_capture_result_from_artifacts,
)
from bugintel.integrations.web_fetcher import fetch_web_page
from bugintel.integrations.har_importer import load_har
from bugintel.core.brain_chat_research_hypothesis_feedback_packet import (
    build_feedback_packet_from_files as build_research_hypothesis_feedback_packet_from_files,
)
from bugintel.core.brain_chat_research_hypothesis_feedback_decision_packet import (
    build_decision_packet_from_files as build_research_hypothesis_feedback_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_hypothesis_confidence_update_packet import (
    build_confidence_update_packet_from_files as build_research_hypothesis_confidence_update_packet_from_files,
)
from bugintel.core.brain_chat_research_state_transition_review_gate import (
    build_review_gate_from_file as build_research_state_transition_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_transition_decision_template import (
    build_decision_template_from_file as build_research_state_transition_decision_template_from_file,
)
from bugintel.core.brain_chat_research_state_transition_decision_packet import (
    build_decision_packet_from_files as build_research_state_transition_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_state_transition_packet import (
    build_transition_packet_from_file as build_research_state_transition_packet_from_file,
)
from bugintel.core.brain_chat_research_state_transition_apply_review_gate import (
    build_apply_review_gate_from_file as build_research_state_transition_apply_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_transition_apply_decision_packet import (
    build_apply_decision_packet_from_files as build_research_state_transition_apply_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_state_transition_apply_preview import (
    build_apply_preview_from_file as build_research_state_transition_apply_preview_from_file,
)
from bugintel.core.brain_chat_research_state_persistence_write_review_gate import (
    build_persistence_write_review_gate_from_file as build_research_state_persistence_write_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_persistence_write_decision_packet import (
    build_persistence_write_decision_packet_from_files as build_research_state_persistence_write_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_state_local_write_packet_preview import (
    build_local_write_packet_preview_from_file as build_research_state_local_write_packet_preview_from_file,
)
from bugintel.core.brain_chat_research_state_write_execution_review_gate import (
    build_write_execution_review_gate_from_file as build_research_state_write_execution_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_write_execution_decision_packet import (
    build_write_execution_decision_packet_from_files as build_research_state_write_execution_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_state_local_write_execution_packet import (
    build_local_write_execution_packet_from_file as build_research_state_local_write_execution_packet_from_file,
)
from bugintel.core.brain_chat_research_state_final_persistence_apply_review_gate import (
    build_final_persistence_apply_review_gate_from_file as build_research_state_final_persistence_apply_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_human_final_apply_decision_packet import (
    build_human_final_apply_decision_packet_from_files as build_research_state_human_final_apply_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_state_final_local_apply_preview import (
    build_final_local_apply_preview_from_file as build_research_state_final_local_apply_preview_from_file,
)
from bugintel.core.brain_chat_research_state_final_apply_execution_review_gate import (
    build_final_apply_execution_review_gate_from_file as build_research_state_final_apply_execution_review_gate_from_file,
)
from bugintel.core.brain_chat_research_state_human_final_apply_execution_decision_packet import (
    build_human_final_apply_execution_decision_packet_from_files as build_research_state_human_final_apply_execution_decision_packet_from_files,
)
from bugintel.core.brain_chat_research_hypothesis_feedback_decision_template import (
    build_research_hypothesis_feedback_decision_template,
    load_json_object as load_research_hypothesis_feedback_decision_template_json,
    write_json as write_research_hypothesis_feedback_decision_template_json,
)
from bugintel.core.brain_chat_research_observation_review_gate import (
    build_review_gate_from_file as build_research_observation_review_gate_from_file,
)
from bugintel.core.brain_chat_research_observation_packet import (
    build_observation_packet_from_file as build_research_observation_packet_from_file,
)
from bugintel.core.brain_chat_research_source_packet import build_research_source_packet
from bugintel.core.brain_chat_research_hypothesis_packet import build_research_hypothesis_packet
from bugintel.core.brain_chat_research_hypothesis_selection_packet import build_research_hypothesis_selection_packet
from bugintel.core.brain_chat_research_typed_tool_request_review_gate import (
    build_review_gate_from_file as build_research_typed_tool_request_review_gate_from_file,
)
from bugintel.core.brain_chat_research_typed_tool_request_manifest import (
    build_typed_manifest_from_file as build_research_typed_tool_request_manifest_from_file,
)
from bugintel.core.brain_chat_research_approved_action_packet import (
    build_approved_action_packet_from_file as build_research_approved_action_packet_from_file,
)
from bugintel.core.brain_chat_research_action_decision_packet import (
    build_decision_packet_from_files as build_research_action_decision_packet_from_files,
    build_research_action_decision_template,
    load_json_object as load_research_action_decision_json,
    write_json as write_research_action_decision_json,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    build_review_gate_from_file as build_research_action_proposal_review_gate_from_file,
)
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_packet_from_files as build_research_action_proposal_packet_from_files,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_review_gate_from_file as build_research_investigation_plan_review_gate_from_file,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_packet_from_file as build_research_investigation_plan_packet_from_file,
)

app = typer.Typer(
    name="bugintel",
    help="Blackhole AI Workbench: human-in-the-loop vulnerability discovery and bug intelligence.",
no_args_is_help=False,
)

console = Console()





def _print_evidence_requirements_table(evidence_requirement_plan, title: str = "Evidence Requirements") -> None:
    """Print evidence requirement counts when an orchestration plan includes them."""
    if evidence_requirement_plan is None or not evidence_requirement_plan.endpoint_plans:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Requirements", justify="right")
    table.add_column("Redaction", justify="right")
    table.add_column("Approval", justify="right")

    for index, endpoint_plan in enumerate(evidence_requirement_plan.endpoint_plans, start=1):
        redaction_count = sum(1 for requirement in endpoint_plan.requirements if requirement.redaction_required)
        approval_count = sum(1 for requirement in endpoint_plan.requirements if requirement.human_approval_required)

        table.add_row(
            str(index),
            endpoint_plan.endpoint,
            str(len(endpoint_plan.requirements)),
            str(redaction_count),
            str(approval_count),
        )

    console.print(table)

def _print_attack_surface_table(attack_surface_map, title: str = "Attack Surface Groups") -> None:
    """Print attack-surface groups when an orchestration plan includes them."""
    if attack_surface_map is None or not attack_surface_map.groups:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Group")
    table.add_column("Count", justify="right")
    table.add_column("Max Score", justify="right")
    table.add_column("Priority Hint")

    for index, group in enumerate(attack_surface_map.groups, start=1):
        table.add_row(
            str(index),
            group.spec.name,
            str(group.count),
            str(group.max_score),
            group.spec.priority_hint,
        )

    console.print(table)

def _endpoint_values_from_text(text: str) -> list[str]:
    """Extract endpoints from mined text plus plain endpoint-list lines."""
    mined = [endpoint.value for endpoint in mine_endpoints(text)]
    line_candidates = []

    for line in text.splitlines():
        value = line.strip()

        if not value or value.startswith("#"):
            continue

        if value.startswith("/") or value.startswith("http://") or value.startswith("https://"):
            line_candidates.append(value)

    return sorted(set(mined + line_candidates))

def _print_endpoint_priority_table(priorities, title: str = "Endpoint Priorities") -> None:
    """Print endpoint priority scores when an orchestration plan includes them."""
    if not priorities:
        return

    table = Table(title=title)
    table.add_column("#", justify="right")
    table.add_column("Score", justify="right")
    table.add_column("Band")
    table.add_column("Endpoint")
    table.add_column("Top Signals")

    for index, item in enumerate(priorities, start=1):
        top_signals = ", ".join(signal.name for signal in item.signals[:3])
        table.add_row(
            str(index),
            str(item.score),
            item.band,
            item.endpoint,
            top_signals or "none",
        )

    console.print(table)




@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Blackhole AI Workbench."""
    if ctx.invoked_subcommand is None:
        show_intro(
            config=IntroConfig(
                version="1.79.0",
                force=True,
            )
        )
        raise typer.Exit()


@app.command("intro")
def intro_command():
    """Show the Blackhole startup intro."""
    show_intro(
        config=IntroConfig(
            version="1.79.0",
            force=True,
        )
    )


@app.command()
def version():
    """Show Blackhole version."""
    console.print("[bold green]Blackhole AI Workbench[/bold green] version 1.79.0")


@app.command("scope-check")
def scope_check(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to check against scope."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method to check."),
):
    """Check whether a URL and HTTP method are allowed by the target scope."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    decision = scope.is_url_allowed(url, method)

    table = Table(title="Scope Guard Decision")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if decision.allowed else "NO")
    table.add_row("Reason", decision.reason)

    console.print(table)

    if not decision.allowed:
        raise typer.Exit(code=2)


@app.command("mine-endpoints")
def mine_endpoints_command(
    input_file: Path = typer.Argument(..., help="File to scan for endpoints."),
):
    """Extract API-like endpoints from JavaScript, HTML, HAR text, logs, or Burp exports."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoints = mine_endpoints(text)

    table = Table(title=f"Endpoint Mining Results: {input_file}")
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Category")
    table.add_column("Source")

    for index, endpoint in enumerate(endpoints, start=1):
        table.add_row(str(index), endpoint.value, endpoint.category, endpoint.source)

    console.print(table)
    console.print(f"[bold]Total endpoints:[/bold] {len(endpoints)}")


@app.command("compare-responses")
def compare_responses_command(
    baseline_file: Path = typer.Argument(..., help="Baseline response JSON file."),
    candidate_file: Path = typer.Argument(..., help="Candidate response JSON file."),
):
    """Compare two HTTP response records for security-relevant differences."""
    if not baseline_file.exists():
        console.print(f"[bold red]Baseline file not found:[/bold red] {baseline_file}")
        raise typer.Exit(code=1)

    if not candidate_file.exists():
        console.print(f"[bold red]Candidate file not found:[/bold red] {candidate_file}")
        raise typer.Exit(code=1)

    baseline_data = json.loads(baseline_file.read_text(encoding="utf-8"))
    candidate_data = json.loads(candidate_file.read_text(encoding="utf-8"))

    baseline = summarize_response(
        baseline_data.get("status_code"),
        baseline_data.get("headers", {}),
        baseline_data.get("body", ""),
    )

    candidate = summarize_response(
        candidate_data.get("status_code"),
        candidate_data.get("headers", {}),
        candidate_data.get("body", ""),
    )

    comparison = compare_responses(baseline, candidate)

    table = Table(title="Response Diff Analysis")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Baseline status", str(comparison.baseline_status))
    table.add_row("Candidate status", str(comparison.candidate_status))
    table.add_row("Same status", str(comparison.same_status))
    table.add_row("Size delta", str(comparison.size_delta))
    table.add_row("Size ratio", str(comparison.size_ratio))
    table.add_row("JSON key overlap", str(comparison.json_key_overlap))
    table.add_row("Signals", ", ".join(comparison.signals) if comparison.signals else "none")
    table.add_row("Verdict", comparison.verdict)

    console.print(table)


@app.command("build-tree")
def build_tree_command(
    input_file: Path = typer.Argument(..., help="File containing JS/HTML/HAR/log text to mine endpoints from."),
    target_name: str = typer.Option("demo-lab", "--target", "-t", help="Target/workspace name."),
    output_file: Path | None = typer.Option(None, "--output", "-o", help="Optional output file for rendered tree."),
):
    """Build a research task tree from discovered endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)

    root = build_endpoint_task_tree(target_name=target_name, endpoints=endpoint_values)
    rendered = render_tree(root)

    console.print(f"[bold green]Built task tree for:[/bold green] {target_name}")
    console.print(f"[bold]Endpoints discovered:[/bold] {len(endpoint_values)}")
    console.print()
    console.print(rendered)

    if output_file:
        output_file.write_text(rendered, encoding="utf-8")
        console.print()
        console.print(f"[bold green]Saved tree to:[/bold green] {output_file}")



@app.command("endpoint-investigation")
def endpoint_investigation_command(
    endpoint: str = typer.Argument(..., help="Endpoint path or URL to classify and expand into investigation tasks."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save endpoint investigation profile JSON.",
    ),
):
    """Build a planning-only endpoint investigation profile."""
    profile = build_endpoint_investigation_profile(endpoint)
    data = profile.to_dict()

    summary = Table(title="Endpoint Investigation Profile")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", profile.endpoint)
    summary.add_row("Normalized path", profile.normalized_path)
    summary.add_row("Categories", ", ".join(profile.categories))
    summary.add_row("Planned tasks", str(len(profile.tasks)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    console.print("[bold]Task types:[/bold] " + ", ".join(task.task_type for task in profile.tasks))

    task_table = Table(title="Planned Investigation Tasks")
    task_table.add_column("#", justify="right")
    task_table.add_column("Task")
    task_table.add_column("Type")
    task_table.add_column("Priority")
    task_table.add_column("Agent")
    task_table.add_column("Human Approval")

    for index, task in enumerate(profile.tasks, start=1):
        task_table.add_row(
            str(index),
            task.title,
            task.task_type,
            task.priority,
            task.agent_hint,
            "YES" if task.requires_human_approval else "NO",
        )

    console.print(task_table)
    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a reviewable plan. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved endpoint investigation JSON:[/bold green] {json_output}")


















@app.command("bug-bounty-case-intake")
def bug_bounty_case_intake_command(
    input_file: Path = typer.Argument(..., help="HAR, Burp export, JS, endpoint list, or notes to intake."),
    target_name: str = typer.Option("bug-bounty-target", "--target", "-t", help="Target or case name."),
    top: int = typer.Option(10, "--top", help="Number of top endpoints to include."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save the intake workflow JSON.",
    ),
):
    """Build a P1/P2-focused bug bounty case intake workflow."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    workflow = build_bug_bounty_case_intake_workflow(
        text,
        target_name=target_name,
        top_n=top,
    )
    data = workflow.to_dict()

    summary = Table(title="Bug Bounty Case Intake")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", workflow.target_name)
    summary.add_row("Status", workflow.status)
    summary.add_row("Endpoints discovered", str(workflow.endpoint_count))
    summary.add_row("Endpoints selected", str(workflow.selected_endpoint_count))
    summary.add_row("P1 potential", str(workflow.lane_counts.get("p1-potential-review", 0)))
    summary.add_row("P2 potential", str(workflow.lane_counts.get("p2-potential-review", 0)))
    summary.add_row("Execution", "planning-only; no requests, browser, provider, or tool execution")
    console.print(summary)

    endpoint_table = Table(title="P1/P2-Focused Endpoint Plan")
    endpoint_table.add_column("#", justify="right")
    endpoint_table.add_column("Endpoint")
    endpoint_table.add_column("Lane")
    endpoint_table.add_column("Score", justify="right")
    endpoint_table.add_column("Band")
    endpoint_table.add_column("Categories")

    for index, endpoint in enumerate(workflow.top_endpoints, start=1):
        endpoint_table.add_row(
            str(index),
            endpoint.endpoint,
            endpoint.p1_p2_lane,
            str(endpoint.priority_score),
            endpoint.priority_band,
            ", ".join(endpoint.categories),
        )

    console.print(endpoint_table)

    console.print("[bold]Manual testing plan:[/bold]")
    for index, step in enumerate(workflow.manual_testing_plan, start=1):
        console.print(f"{index}. {step}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved bug bounty case intake JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local planning workflow. "
        "It does not send requests, execute tools, launch browsers, call providers, collect evidence, "
        "submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-handoff")
def case_intake_brain_handoff_command(
    intake_file: Path = typer.Argument(..., help="Path to bug-bounty-case-intake JSON output."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save brain handoff JSON.",
    ),
):
    """Convert a bug bounty case intake workflow into brain-readable context."""
    if not intake_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {intake_file}")
        raise typer.Exit(code=1)

    intake = json.loads(intake_file.read_text(encoding="utf-8"))
    handoff = build_case_intake_brain_handoff(intake)
    data = handoff.to_dict()

    summary = Table(title="Case Intake Brain Handoff")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", handoff.target_name)
    summary.add_row("Status", handoff.status)
    summary.add_row("Focus endpoints", str(handoff.focus_endpoint_count))
    summary.add_row("Deferred endpoints", str(handoff.deferred_endpoint_count))
    summary.add_row("Evidence gaps", str(len(handoff.evidence_gaps)))
    summary.add_row("Execution", "planning-only; no requests, browser, provider, or tool execution")
    console.print(summary)

    focus_table = Table(title="Brain Focus Endpoints")
    focus_table.add_column("#", justify="right")
    focus_table.add_column("Endpoint")
    focus_table.add_column("Lane")
    focus_table.add_column("Score", justify="right")
    focus_table.add_column("Why focus")

    for index, endpoint in enumerate(handoff.focus_endpoints, start=1):
        focus_table.add_row(
            str(index),
            endpoint.endpoint,
            endpoint.lane,
            str(endpoint.priority_score),
            "; ".join(endpoint.why_focus[:2]),
        )

    console.print(focus_table)

    console.print("[bold]Brain questions:[/bold]")
    for index, question in enumerate(handoff.brain_questions, start=1):
        console.print(f"{index}. {question}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intake brain handoff JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only converts intake output into local brain context. "
        "It does not send requests, execute tools, launch browsers, call providers, collect evidence, "
        "submit reports, or confirm vulnerabilities."
    )


@app.command("case-intake-brain-answer")
def case_intake_brain_answer_command(
    handoff_file: Path = typer.Argument(..., help="Path to case-intake-brain-handoff JSON output."),
    question: str = typer.Argument(..., help="Local question to answer from the brain handoff."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Answer a local deterministic question from a case intake brain handoff."""
    if not handoff_file.exists():
        console.print(f"[bold red]Handoff file not found:[/bold red] {handoff_file}")
        raise typer.Exit(code=1)

    try:
        handoff = json.loads(handoff_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid handoff JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    answer = answer_case_intake_brain_handoff_question(handoff, question)
    markdown = answer.to_markdown()
    data = answer.to_dict()

    table = Table(title="Case Intake Brain Handoff Answer")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Question", answer.question)
    table.add_row("Route", answer.route)
    table.add_row("Target", answer.target_name)
    table.add_row("Focus endpoint", answer.focus_endpoint or "none")
    table.add_row("Handoff status", answer.handoff_status)
    table.add_row("Blocked", str(answer.blocked))
    table.add_row("Focus endpoints", str(answer.focus_endpoint_count))
    table.add_row("Deferred endpoints", str(answer.deferred_endpoint_count))
    table.add_row("Evidence gaps", str(answer.evidence_gap_count))
    table.add_row("Validation allowed", str(answer.validation_allowed))
    table.add_row("Runtime execution allowed", str(answer.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(answer.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(answer.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    console.print("[bold yellow]Answer:[/bold yellow]")
    console.print(answer.answer)

    if answer.supporting_points:
        console.print("[bold yellow]Supporting points:[/bold yellow]")
        for item in answer.supporting_points:
            console.print(f"- {item}")

    console.print("[bold yellow]Recommended next action:[/bold yellow]")
    console.print(answer.recommended_next_action)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case intake brain answer Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intake brain answer JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers local deterministic handoff questions. "
        "It does not send requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, "
        "submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-demo-flow")
def brain_chat_demo_flow_command(
    endpoints_file: Path = typer.Argument(..., help="Path to endpoints.txt for the demo case."),
    target_name: str = typer.Option("demo.local", "--target", "-t", help="Target/workspace name."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Directory to write the demo case artifacts."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Run a local planning-only demo flow from endpoints.txt to brain-chat state."""
    try:
        flow = run_brain_chat_demo_flow(
            endpoints_file=endpoints_file,
            target_name=target_name,
            output_dir=output_dir,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid brain chat demo flow input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    flow_data = flow.to_dict()
    markdown = flow.to_markdown()

    table = Table(title="Brain Chat Demo Flow")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", flow.target_name)
    table.add_row("Output dir", flow.output_dir)
    table.add_row("Brain state dir", flow.brain_state_dir)
    table.add_row("Focus endpoint", flow.focus_endpoint or "none")
    table.add_row("Recommendation", flow.recommendation)
    table.add_row("Artifacts", str(len(flow.artifacts)))
    table.add_row("Tool execution", "false")
    table.add_row("Provider execution", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat demo flow Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(flow_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat demo flow JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local planning artifacts and a brain-chat state directory. "
        "It does not execute tools, send requests, call providers, launch browsers, or confirm vulnerabilities."
    )


@app.command("brain-state-export")
def brain_state_export_command(
    ai_brain_file: Path = typer.Option(..., "--ai-brain", help="Path to ai-brain JSON."),
    brain_decision_file: Path = typer.Option(..., "--brain-decision", help="Path to brain-decision JSON."),
    brain_approval_file: Path = typer.Option(..., "--brain-approval", help="Path to brain-approval JSON."),
    tool_execution_gate_file: Path = typer.Option(..., "--tool-execution-gate", help="Path to tool-execution-gate JSON."),
    output_dir: Path = typer.Option(..., "--output-dir", help="Directory to write brain-chat state files."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Export generated brain artifacts into the numbered state-dir format expected by brain-chat."""
    try:
        export = build_brain_state_export(
            ai_brain=ai_brain_file,
            brain_decision=brain_decision_file,
            brain_approval=brain_approval_file,
            tool_execution_gate=tool_execution_gate_file,
            output_dir=output_dir,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid brain state export input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    export_data = export.to_dict()
    markdown = export.to_markdown()

    table = Table(title="Brain State Export")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Output dir", export.output_dir)
    table.add_row("Recommendation", export.recommendation)
    table.add_row("Exported files", str(len(export.exported_items)))
    table.add_row("File copy only", "true")
    table.add_row("Tool execution", "false")
    table.add_row("Provider execution", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    for item in export.exported_items:
        console.print(f"[bold green]Exported {item.role}:[/bold green] {item.output_path}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain state export Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(export_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain state export JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only copies local brain artifacts into the brain-chat state layout. "
        "It does not execute tools, send requests, call providers, or confirm vulnerabilities."
    )


def _looks_like_brain_chat_state_dir(path: Path) -> bool:
    return all(
        (path / filename).exists()
        for filename in (
            "03-ai-brain.json",
            "06-brain-decision.json",
            "07-brain-approval.json",
            "09-tool-execution-gate.json",
        )
    )


def _resolve_brain_chat_state_dir(state_dir: Path | None, case_dir: Path | None) -> Path:
    if state_dir is not None:
        return state_dir

    if case_dir is not None:
        case_brain_dir = case_dir / "brain"
        if _looks_like_brain_chat_state_dir(case_brain_dir):
            return case_brain_dir
        if _looks_like_brain_chat_state_dir(case_dir):
            return case_dir
        return case_brain_dir

    cwd = Path(".")
    if _looks_like_brain_chat_state_dir(cwd / "brain"):
        return cwd / "brain"

    return cwd


def _resolve_brain_chat_session_path(
    session: Path | None,
    state_dir: Path | None,
    case_dir: Path | None,
    resolved_state_dir: Path,
) -> Path | None:
    if session is not None:
        return session

    if state_dir is not None:
        return None

    if case_dir is not None:
        return case_dir / "brain-chat-session.json"

    cwd = Path(".")
    if resolved_state_dir == cwd / "brain":
        return cwd / "brain-chat-session.json"

    return None


@app.command("brain-chat-human-case-review-decision-gate")
def brain_chat_human_case_review_decision_gate_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human case-review decision to gate."),
    human_review_decision_file: Path = typer.Option(..., "--human-review-decision-file", "--human-review-decision", help="Local JSON file containing the upstream human review decision used to build the decision request."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review an imported human case-review decision gate."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human case review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if not human_review_decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {human_review_decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        upstream_decision = import_case_intelligence_human_review_decision_file(
            request,
            human_review_decision_file,
        )
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    decision_gate = build_case_intelligence_human_review_decision_gate(upstream_decision)
    packet = build_human_case_review_packet(decision_gate)
    packet_review_gate = build_human_case_review_packet_review_gate(packet)
    decision_request = build_human_case_review_decision_request(packet_review_gate)

    try:
        imported = import_human_case_review_decision_file(decision_request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    gate = build_human_case_review_decision_gate(imported)

    markdown = gate.to_markdown()
    data = gate.to_dict()

    table = Table(title="Brain Chat Human Case Review Decision Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", gate.decision)
    table.add_row("Decision request status", gate.decision_request_status)
    table.add_row("Decision import status", gate.decision_import_status)
    table.add_row("Decision gate status", gate.decision_gate_status)
    table.add_row("Human case review decision ready", str(gate.human_case_review_decision_ready))
    table.add_row("Human case review ready", str(gate.human_case_review_ready))
    table.add_row("Effective human review approval", str(gate.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(gate.approval_granted))
    table.add_row("Effective next local planning approval", str(gate.effective_next_local_planning_approval_granted))
    table.add_row("Next local planning gate ready", str(gate.next_local_planning_gate_ready))
    table.add_row("Decision effective", str(gate.decision_effective))
    table.add_row("Decision blockers", str(len(gate.decision_blockers)))
    table.add_row("Packet blockers", str(len(gate.packet_blockers)))
    table.add_row("Missing evidence checklist", str(len(gate.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(gate.blockers_checklist)))
    table.add_row("Required human checks", str(len(gate.required_human_checks)))
    table.add_row("Allowed local next steps", str(len(gate.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(gate.rejected_actions)))
    table.add_row("Validation allowed", str(gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(gate.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(gate.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(gate.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Decision gate status:[/bold yellow] {gate.decision_gate_status}")

    if gate.decision_blockers:
        console.print("[bold yellow]Decision blockers:[/bold yellow]")
        for item in gate.decision_blockers:
            console.print(f"- {item}")

    if gate.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in gate.allowed_local_next_steps:
            console.print(f"- {item}")

    if gate.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in gate.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local deterministic human case-review decision gate. "
        "It does not grant runtime execution, validation execution, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-human-case-review-decision-import")
def brain_chat_human_case_review_decision_import_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human case-review decision to import."),
    human_review_decision_file: Path = typer.Option(..., "--human-review-decision-file", "--human-review-decision", help="Local JSON file containing the upstream human review decision used to build the decision request."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import a local deterministic human case-review decision."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human case review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if not human_review_decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {human_review_decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        upstream_decision = import_case_intelligence_human_review_decision_file(
            request,
            human_review_decision_file,
        )
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    decision_gate = build_case_intelligence_human_review_decision_gate(upstream_decision)
    packet = build_human_case_review_packet(decision_gate)
    packet_review_gate = build_human_case_review_packet_review_gate(packet)
    decision_request = build_human_case_review_decision_request(packet_review_gate)

    try:
        imported = import_human_case_review_decision_file(decision_request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = imported.to_markdown()
    data = imported.to_dict()

    table = Table(title="Brain Chat Human Case Review Decision Import")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", imported.decision)
    table.add_row("Reviewer", imported.reviewer or "unknown")
    table.add_row("Decision request status", imported.decision_request_status)
    table.add_row("Decision import status", imported.decision_import_status)
    table.add_row("Human case review decision ready", str(imported.human_case_review_decision_ready))
    table.add_row("Human case review ready", str(imported.human_case_review_ready))
    table.add_row("Effective human review approval", str(imported.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(imported.approval_granted))
    table.add_row("Effective next local planning approval", str(imported.effective_next_local_planning_approval_granted))
    table.add_row("Decision effective", str(imported.decision_effective))
    table.add_row("Decision options", str(len(imported.requested_human_decision_options)))
    table.add_row("Required human checks", str(len(imported.required_human_checks)))
    table.add_row("Packet blockers", str(len(imported.packet_blockers)))
    table.add_row("Decision blockers", str(len(imported.decision_blockers)))
    table.add_row("Missing evidence checklist", str(len(imported.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(imported.blockers_checklist)))
    table.add_row("Allowed local next steps", str(len(imported.allowed_local_next_steps)))
    table.add_row("Rejected next steps", str(len(imported.rejected_next_steps)))
    table.add_row("Validation allowed", str(imported.validation_allowed))
    table.add_row("Runtime execution allowed", str(imported.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(imported.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(imported.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Decision import status:[/bold yellow] {imported.decision_import_status}")

    if imported.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in imported.allowed_local_next_steps:
            console.print(f"- {item}")

    if imported.rejected_next_steps:
        console.print("[bold yellow]Rejected next steps:[/bold yellow]")
        for item in imported.rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision import Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision import JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports a local deterministic human case-review decision. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-human-case-review-decision-request")
def brain_chat_human_case_review_decision_request_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human review decision."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic human case-review decision request."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        decision = import_case_intelligence_human_review_decision_file(request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    decision_gate = build_case_intelligence_human_review_decision_gate(decision)
    packet = build_human_case_review_packet(decision_gate)
    packet_review_gate = build_human_case_review_packet_review_gate(packet)
    decision_request = build_human_case_review_decision_request(packet_review_gate)

    markdown = decision_request.to_markdown()
    data = decision_request.to_dict()

    table = Table(title="Brain Chat Human Case Review Decision Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", decision_request.decision)
    table.add_row("Decision gate status", decision_request.decision_gate_status)
    table.add_row("Case review packet status", decision_request.case_review_packet_status)
    table.add_row("Packet review status", decision_request.packet_review_status)
    table.add_row("Decision request status", decision_request.decision_request_status)
    table.add_row("Human case review decision ready", str(decision_request.human_case_review_decision_ready))
    table.add_row("Human case review ready", str(decision_request.human_case_review_ready))
    table.add_row("Effective approval granted", str(decision_request.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(decision_request.approval_granted))
    table.add_row("Blocked", str(decision_request.blocked))
    table.add_row("Decision options", str(len(decision_request.requested_human_decision_options)))
    table.add_row("Reviewer instructions", str(len(decision_request.reviewer_instructions)))
    table.add_row("Required human checks", str(len(decision_request.required_human_checks)))
    table.add_row("Packet blockers", str(len(decision_request.packet_blockers)))
    table.add_row("Decision blockers", str(len(decision_request.decision_blockers)))
    table.add_row("Missing evidence checklist", str(len(decision_request.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(decision_request.blockers_checklist)))
    table.add_row("Allowed local next steps", str(len(decision_request.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(decision_request.rejected_actions)))
    table.add_row("Validation allowed", str(decision_request.validation_allowed))
    table.add_row("Runtime execution allowed", str(decision_request.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(decision_request.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(decision_request.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Decision request status:[/bold yellow] {decision_request.decision_request_status}")

    console.print("[bold yellow]Requested human decision options:[/bold yellow]")
    for item in decision_request.requested_human_decision_options:
        console.print(f"- {item}")

    if decision_request.reviewer_instructions:
        console.print("[bold yellow]Reviewer instructions:[/bold yellow]")
        for item in decision_request.reviewer_instructions:
            console.print(f"- {item}")

    if decision_request.packet_blockers:
        console.print("[bold yellow]Packet blockers:[/bold yellow]")
        for item in decision_request.packet_blockers:
            console.print(f"- {item}")

    if decision_request.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in decision_request.allowed_local_next_steps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in decision_request.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision request Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human case review decision request JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic human case-review decision request. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-human-case-review-packet-review-gate")
def brain_chat_human_case_review_packet_review_gate_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human review decision."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a local deterministic human case-review packet."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        decision = import_case_intelligence_human_review_decision_file(request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    decision_gate = build_case_intelligence_human_review_decision_gate(decision)
    packet = build_human_case_review_packet(decision_gate)
    packet_review_gate = build_human_case_review_packet_review_gate(packet)

    markdown = packet_review_gate.to_markdown()
    data = packet_review_gate.to_dict()

    table = Table(title="Brain Chat Human Case Review Packet Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", packet_review_gate.decision)
    table.add_row("Decision gate status", packet_review_gate.decision_gate_status)
    table.add_row("Case review packet status", packet_review_gate.case_review_packet_status)
    table.add_row("Packet review status", packet_review_gate.packet_review_status)
    table.add_row("Human case review ready", str(packet_review_gate.human_case_review_ready))
    table.add_row("Effective approval granted", str(packet_review_gate.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(packet_review_gate.approval_granted))
    table.add_row("Blocked", str(packet_review_gate.blocked))
    table.add_row("Packet blockers", str(len(packet_review_gate.packet_blockers)))
    table.add_row("Review scope", str(len(packet_review_gate.review_scope)))
    table.add_row("Human review tasks", str(len(packet_review_gate.human_review_tasks)))
    table.add_row("Decision blockers", str(len(packet_review_gate.decision_blockers)))
    table.add_row("Missing evidence checklist", str(len(packet_review_gate.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(packet_review_gate.blockers_checklist)))
    table.add_row("Required human checks", str(len(packet_review_gate.required_human_checks)))
    table.add_row("Allowed local next steps", str(len(packet_review_gate.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(packet_review_gate.rejected_actions)))
    table.add_row("Validation allowed", str(packet_review_gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(packet_review_gate.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(packet_review_gate.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(packet_review_gate.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Packet review status:[/bold yellow] {packet_review_gate.packet_review_status}")

    if packet_review_gate.packet_blockers:
        console.print("[bold yellow]Packet blockers:[/bold yellow]")
        for item in packet_review_gate.packet_blockers:
            console.print(f"- {item}")

    if packet_review_gate.human_review_tasks:
        console.print("[bold yellow]Human review tasks:[/bold yellow]")
        for item in packet_review_gate.human_review_tasks:
            console.print(f"- [ ] {item}")

    if packet_review_gate.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in packet_review_gate.allowed_local_next_steps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in packet_review_gate.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human case review packet review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human case review packet review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local deterministic human case-review packet. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-human-case-review-packet")
def brain_chat_human_case_review_packet_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human review decision."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic human case-review packet."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        decision = import_case_intelligence_human_review_decision_file(request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    decision_gate = build_case_intelligence_human_review_decision_gate(decision)
    packet = build_human_case_review_packet(decision_gate)

    markdown = packet.to_markdown()
    data = packet.to_dict()

    table = Table(title="Brain Chat Human Case Review Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", packet.decision)
    table.add_row("Decision gate status", packet.decision_gate_status)
    table.add_row("Packet status", packet.case_review_packet_status)
    table.add_row("Human case review ready", str(packet.human_case_review_ready))
    table.add_row("Effective approval granted", str(packet.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(packet.approval_granted))
    table.add_row("Request status", packet.request_status)
    table.add_row("Review status", packet.review_status)
    table.add_row("Briefing status", packet.briefing_status)
    table.add_row("Blocked", str(packet.blocked))
    table.add_row("Human review tasks", str(len(packet.human_review_tasks)))
    table.add_row("Decision blockers", str(len(packet.decision_blockers)))
    table.add_row("Missing evidence checklist", str(len(packet.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(packet.blockers_checklist)))
    table.add_row("Required human checks", str(len(packet.required_human_checks)))
    table.add_row("Allowed local next steps", str(len(packet.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(packet.rejected_actions)))
    table.add_row("Validation allowed", str(packet.validation_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(packet.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(packet.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Packet status:[/bold yellow] {packet.case_review_packet_status}")

    console.print("[bold yellow]Review objective:[/bold yellow]")
    console.print(packet.review_objective)

    if packet.human_review_tasks:
        console.print("[bold yellow]Human review tasks:[/bold yellow]")
        for item in packet.human_review_tasks:
            console.print(f"- [ ] {item}")

    if packet.decision_blockers:
        console.print("[bold yellow]Decision blockers:[/bold yellow]")
        for item in packet.decision_blockers:
            console.print(f"- {item}")

    if packet.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in packet.allowed_local_next_steps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in packet.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human case review packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human case review packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic human case-review packet. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-human-review-decision-gate")
def brain_chat_case_intelligence_human_review_decision_gate_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human review decision."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review an imported case-intelligence human-review decision."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    review_gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(review_gate)

    try:
        decision = import_case_intelligence_human_review_decision_file(request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    gate = build_case_intelligence_human_review_decision_gate(decision)

    markdown = gate.to_markdown()
    data = gate.to_dict()

    table = Table(title="Brain Chat Case Intelligence Human Review Decision Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", gate.decision)
    table.add_row("Decision gate status", gate.decision_gate_status)
    table.add_row("Human case review ready", str(gate.human_case_review_ready))
    table.add_row("Effective approval granted", str(gate.effective_human_review_approval_granted))
    table.add_row("Approval granted", str(gate.approval_granted))
    table.add_row("Request status", gate.request_status)
    table.add_row("Review status", gate.review_status)
    table.add_row("Briefing status", gate.briefing_status)
    table.add_row("Human review request ready", str(gate.human_review_request_ready))
    table.add_row("Case review ready", str(gate.case_review_ready))
    table.add_row("Blocked", str(gate.blocked))
    table.add_row("Validation allowed", str(gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(gate.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(gate.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(gate.vulnerability_confirmation_allowed))
    table.add_row("Decision blockers", str(len(gate.decision_blockers)))
    table.add_row("Allowed local next steps", str(len(gate.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(gate.rejected_actions)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if gate.decision_blockers:
        console.print("[bold yellow]Decision blockers:[/bold yellow]")
        for item in gate.decision_blockers:
            console.print(f"- {item}")

    if gate.allowed_local_next_steps:
        console.print("[bold yellow]Allowed local next steps:[/bold yellow]")
        for item in gate.allowed_local_next_steps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in gate.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human review decision gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human review decision gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local deterministic human-review decision. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-human-review-decision-import")
def brain_chat_case_intelligence_human_review_decision_import_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the human review decision."),
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import a local deterministic case-intelligence human-review decision."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if not decision_file.exists():
            console.print(f"[bold red]Human review decision JSON not found:[/bold red] {decision_file}")
            raise typer.Exit(code=1)

        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(gate)

    try:
        decision = import_case_intelligence_human_review_decision_file(request, decision_file)
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = decision.to_markdown()
    data = decision.to_dict()

    table = Table(title="Brain Chat Case Intelligence Human Review Decision")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Decision", decision.decision)
    table.add_row("Reviewer", decision.reviewer)
    table.add_row("Request status", decision.request_status)
    table.add_row("Review status", decision.review_status)
    table.add_row("Briefing status", decision.briefing_status)
    table.add_row("Human review request ready", str(decision.human_review_request_ready))
    table.add_row("Case review ready", str(decision.case_review_ready))
    table.add_row("Approval granted", str(decision.approval_granted))
    table.add_row("Effective approval granted", str(decision.effective_human_review_approval_granted))
    table.add_row("Blocked", str(decision.blocked))
    table.add_row("Validation allowed", str(decision.validation_allowed))
    table.add_row("Runtime execution allowed", str(decision.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(decision.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(decision.vulnerability_confirmation_allowed))
    table.add_row("Missing evidence checklist", str(len(decision.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(decision.blockers_checklist)))
    table.add_row("Required human checks", str(len(decision.required_human_checks)))
    table.add_row("Allowed next steps", str(len(decision.allowed_next_steps)))
    table.add_row("Rejected next steps", str(len(decision.rejected_next_steps)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if decision.reason:
        console.print("[bold yellow]Reason:[/bold yellow]")
        console.print(decision.reason)

    if decision.allowed_next_steps:
        console.print("[bold yellow]Allowed next steps:[/bold yellow]")
        for item in decision.allowed_next_steps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected next steps:[/bold yellow]")
    for item in decision.rejected_next_steps:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human review decision Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human review decision JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports a local deterministic human-review decision. "
        "It does not grant side-effectful approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-human-review-request")
def brain_chat_case_intelligence_human_review_request_command(
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic case-intelligence human-review request."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    gate = build_case_intelligence_briefing_review_gate(briefing)
    request = build_case_intelligence_human_review_request(gate)

    markdown = request.to_markdown()
    data = request.to_dict()

    table = Table(title="Brain Chat Case Intelligence Human Review Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", request.target_name)
    table.add_row("Focus endpoint", request.focus_endpoint or "none")
    table.add_row("Current stage", request.current_stage)
    table.add_row("Current status", request.current_status)
    table.add_row("Briefing status", request.briefing_status)
    table.add_row("Review status", request.review_status)
    table.add_row("Request status", request.request_status)
    table.add_row("Human review request ready", str(request.human_review_request_ready))
    table.add_row("Case review ready", str(request.case_review_ready))
    table.add_row("Approval granted", str(request.approval_granted))
    table.add_row("Blocked", str(request.blocked))
    table.add_row("Validation allowed", str(request.validation_allowed))
    table.add_row("Runtime execution allowed", str(request.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(request.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(request.vulnerability_confirmation_allowed))
    table.add_row("Missing evidence checklist", str(len(request.missing_evidence_checklist)))
    table.add_row("Blockers checklist", str(len(request.blockers_checklist)))
    table.add_row("Human review items", str(len(request.human_review_items)))
    table.add_row("Required human checks", str(len(request.required_human_checks)))
    table.add_row("Decision options", str(len(request.requested_human_decision_options)))
    table.add_row("Questions answered", str(request.question_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if request.human_review_items:
        console.print("[bold yellow]Human review items:[/bold yellow]")
        for item in request.human_review_items:
            console.print(f"- {item}")

    if request.missing_evidence_checklist:
        console.print("[bold yellow]Missing evidence checklist:[/bold yellow]")
        for item in request.missing_evidence_checklist:
            console.print(f"- [ ] {item}")

    if request.blockers_checklist:
        console.print("[bold yellow]Blockers checklist:[/bold yellow]")
        for item in request.blockers_checklist:
            console.print(f"- [ ] {item}")

    if request.required_human_checks:
        console.print("[bold yellow]Required human checks:[/bold yellow]")
        for item in request.required_human_checks:
            console.print(f"- [ ] {item}")

    console.print("[bold yellow]Requested human decision options:[/bold yellow]")
    for item in request.requested_human_decision_options:
        console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in request.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved human review request Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human review request JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic human-review request. "
        "It does not grant approval, call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-briefing-review-gate")
def brain_chat_case_intelligence_briefing_review_gate_command(
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a local deterministic case-intelligence briefing packet."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)
    gate = build_case_intelligence_briefing_review_gate(briefing)

    markdown = gate.to_markdown()
    data = gate.to_dict()

    table = Table(title="Brain Chat Case Intelligence Briefing Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate.target_name)
    table.add_row("Focus endpoint", gate.focus_endpoint or "none")
    table.add_row("Current stage", gate.current_stage)
    table.add_row("Current status", gate.current_status)
    table.add_row("Briefing status", gate.briefing_status)
    table.add_row("Review status", gate.review_status)
    table.add_row("Case review ready", str(gate.case_review_ready))
    table.add_row("Blocked", str(gate.blocked))
    table.add_row("Validation allowed", str(gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(gate.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(gate.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(gate.vulnerability_confirmation_allowed))
    table.add_row("Missing evidence", str(len(gate.missing_evidence)))
    table.add_row("Blockers", str(len(gate.blockers)))
    table.add_row("Human review items", str(len(gate.human_review_items)))
    table.add_row("Required human checks", str(len(gate.required_human_checks)))
    table.add_row("Questions answered", str(gate.question_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if gate.missing_evidence:
        console.print("[bold yellow]Missing evidence:[/bold yellow]")
        for item in gate.missing_evidence:
            console.print(f"- {item}")

    if gate.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in gate.blockers:
            console.print(f"- {item}")

    if gate.human_review_items:
        console.print("[bold yellow]Human review items:[/bold yellow]")
        for item in gate.human_review_items:
            console.print(f"- {item}")

    if gate.required_human_checks:
        console.print("[bold yellow]Required human checks:[/bold yellow]")
        for item in gate.required_human_checks:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in gate.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved briefing review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved briefing review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local deterministic briefing. "
        "It does not call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-briefing-export")
def brain_chat_case_intelligence_briefing_export_command(
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Export a local deterministic case-intelligence briefing packet."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)
    briefing = build_case_intelligence_briefing_export(summary, question_set=question_set)

    markdown = briefing.to_markdown()
    data = briefing.to_dict()

    table = Table(title="Brain Chat Case Intelligence Briefing Export")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", briefing.target_name)
    table.add_row("Focus endpoint", briefing.focus_endpoint or "none")
    table.add_row("Current stage", briefing.current_stage)
    table.add_row("Current status", briefing.current_status)
    table.add_row("Briefing status", briefing.briefing_status)
    table.add_row("Blocked", str(briefing.blocked))
    table.add_row("Validation allowed", str(briefing.validation_allowed))
    table.add_row("Runtime execution allowed", str(briefing.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(briefing.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(briefing.vulnerability_confirmation_allowed))
    table.add_row("Missing evidence", str(len(briefing.missing_evidence)))
    table.add_row("Blockers", str(len(briefing.blockers)))
    table.add_row("Questions answered", str(briefing.question_set.question_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    console.print("[bold yellow]Briefing summary:[/bold yellow]")
    console.print(briefing.briefing_summary)

    console.print("[bold yellow]Safest next action:[/bold yellow]")
    console.print(briefing.safest_next_action)

    if briefing.missing_evidence:
        console.print("[bold yellow]Missing evidence:[/bold yellow]")
        for item in briefing.missing_evidence:
            console.print(f"- {item}")

    if briefing.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in briefing.blockers:
            console.print(f"- {item}")

    console.print("[bold yellow]Question set answers:[/bold yellow]")
    for index, answer in enumerate(briefing.question_set.answers, start=1):
        console.print(f"{index}. {answer.question}")
        console.print(f"   Route: {answer.route}")
        console.print(f"   Answer: {answer.answer}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence briefing Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence briefing JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only exports a local deterministic case-intelligence briefing. "
        "It does not call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-question-set")
def brain_chat_case_intelligence_question_set_command(
    questions_file: Path | None = typer.Option(None, "--questions-file", "--questions", help="Optional local JSON file containing a list of questions."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Run a local deterministic case-intelligence question set."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)

        questions = None
        if questions_file is not None:
            if not questions_file.exists():
                console.print(f"[bold red]Questions JSON not found:[/bold red] {questions_file}")
                raise typer.Exit(code=1)
            raw_questions = json.loads(questions_file.read_text(encoding="utf-8"))
            if isinstance(raw_questions, dict):
                raw_questions = raw_questions.get("questions")
            if not isinstance(raw_questions, list) or not all(isinstance(item, str) for item in raw_questions):
                console.print("[bold red]Questions JSON must be a list of strings or an object with a questions list.[/bold red]")
                raise typer.Exit(code=1)
            questions = tuple(raw_questions)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    question_set = run_case_intelligence_question_set(summary, questions=questions)

    markdown = question_set.to_markdown()
    data = question_set.to_dict()

    table = Table(title="Brain Chat Case Intelligence Question Set")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", question_set.target_name)
    table.add_row("Focus endpoint", question_set.focus_endpoint or "none")
    table.add_row("Current stage", question_set.current_stage)
    table.add_row("Current status", question_set.current_status)
    table.add_row("Blocked", str(question_set.blocked))
    table.add_row("Validation allowed", str(question_set.validation_allowed))
    table.add_row("Runtime execution allowed", str(question_set.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(question_set.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(question_set.vulnerability_confirmation_allowed))
    table.add_row("Questions answered", str(question_set.question_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    for index, answer in enumerate(question_set.answers, start=1):
        console.print(f"[bold yellow]{index}. {answer.question}[/bold yellow]")
        console.print(f"Route: {answer.route}")
        console.print(f"Answer: {answer.answer}")
        if answer.supporting_points:
            console.print("Supporting points:")
            for item in answer.supporting_points:
                console.print(f"- {item}")
        console.print(f"Recommended next action: {answer.recommended_next_action}")
        console.print("")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence question set Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence question set JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only runs local deterministic case-intelligence questions. "
        "It does not call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-answer")
def brain_chat_case_intelligence_answer_command(
    question: str = typer.Argument(..., help="Local case-intelligence question to answer."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Answer a local deterministic question from case intelligence status."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )
    answer = answer_case_intelligence_question(summary, question)

    markdown = answer.to_markdown()
    data = answer.to_dict()

    table = Table(title="Brain Chat Case Intelligence Answer")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Question", answer.question)
    table.add_row("Route", answer.route)
    table.add_row("Target", answer.target_name)
    table.add_row("Focus endpoint", answer.focus_endpoint or "none")
    table.add_row("Current stage", answer.current_stage)
    table.add_row("Current status", answer.current_status)
    table.add_row("Blocked", str(answer.blocked))
    table.add_row("Validation allowed", str(answer.validation_allowed))
    table.add_row("Runtime execution allowed", str(answer.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(answer.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(answer.vulnerability_confirmation_allowed))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    console.print("[bold yellow]Answer:[/bold yellow]")
    console.print(answer.answer)

    if answer.supporting_points:
        console.print("[bold yellow]Supporting points:[/bold yellow]")
        for item in answer.supporting_points:
            console.print(f"- {item}")

    console.print("[bold yellow]Recommended next action:[/bold yellow]")
    console.print(answer.recommended_next_action)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence answer Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence answer JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers local case-intelligence questions. "
        "It does not call providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-intelligence-status")
def brain_chat_case_intelligence_status_command(
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    approval_decision_file: Path | None = typer.Option(None, "--approval-decision-file", "--approval-decision", help="Optional local JSON file containing evidence approval decision metadata."),
    step_decision_file: Path | None = typer.Option(None, "--step-decision-file", "--step-decision", help="Optional local JSON file containing validation step approval decision metadata."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Summarize local case intelligence status across the review chain."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    session = None
    checklist = None
    evidence_gate = None
    approval_request = None
    approval_decision = None
    validation_plan = None
    step_gate = None
    step_approval_request = None
    step_approval_decision = None
    execution_proposal = None
    execution_review = None

    try:
        if resolved_session_file.exists():
            session = load_brain_chat_session(resolved_session_file)

            if status_file is not None:
                if not status_file.exists():
                    console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                    raise typer.Exit(code=1)
                import_result = import_evidence_checklist_status_file(session, status_file)
                checklist = import_result.checklist
            else:
                checklist = build_brain_chat_evidence_checklist(session)

            evidence_gate = build_evidence_checklist_review_gate(checklist)
            approval_request = build_evidence_approval_request(evidence_gate)

            if approval_decision_file is not None:
                if not approval_decision_file.exists():
                    console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
                    raise typer.Exit(code=1)
                approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
                validation_plan = build_evidence_approved_validation_plan(approval_decision)
                step_gate = build_validation_plan_step_review_gate(validation_plan)
                step_approval_request = build_validation_step_approval_request(step_gate)

                if step_decision_file is not None:
                    if not step_decision_file.exists():
                        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
                        raise typer.Exit(code=1)
                    step_approval_decision = import_validation_step_approval_decision_file(
                        step_approval_request,
                        step_decision_file,
                    )
                    execution_proposal = build_validation_step_execution_gate_proposal(step_approval_decision)
                    execution_review = build_execution_gate_proposal_review_packet(execution_proposal)
        else:
            if session_file is not None:
                console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
                raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    summary = build_case_intelligence_status_summary(
        session=session,
        checklist=checklist,
        evidence_review_gate=evidence_gate,
        approval_request=approval_request,
        approval_decision=approval_decision,
        validation_plan=validation_plan,
        step_review_gate=step_gate,
        step_approval_request=step_approval_request,
        step_approval_decision=step_approval_decision,
        execution_gate_proposal=execution_proposal,
        execution_gate_review_packet=execution_review,
    )

    markdown = summary.to_markdown()
    data = summary.to_dict()

    table = Table(title="Brain Chat Case Intelligence Status Summary")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file) if session else "none")
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Approval decision file", str(approval_decision_file) if approval_decision_file else "none")
    table.add_row("Step decision file", str(step_decision_file) if step_decision_file else "none")
    table.add_row("Target", summary.target_name)
    table.add_row("Focus endpoint", summary.focus_endpoint or "none")
    table.add_row("Current stage", summary.current_stage)
    table.add_row("Current status", summary.current_status)
    table.add_row("Blocked", str(summary.blocked))
    table.add_row("Validation allowed", str(summary.validation_allowed))
    table.add_row("Runtime execution allowed", str(summary.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(summary.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(summary.vulnerability_confirmation_allowed))
    table.add_row("Missing evidence", str(len(summary.missing_evidence)))
    table.add_row("Blockers", str(len(summary.blockers)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    console.print("[bold yellow]Safest next action:[/bold yellow]")
    console.print(summary.safest_next_action)

    if summary.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in summary.blockers:
            console.print(f"- {item}")

    if summary.missing_evidence:
        console.print("[bold yellow]Missing evidence:[/bold yellow]")
        for item in summary.missing_evidence:
            console.print(f"- {item}")

    if summary.chain_position:
        console.print("[bold yellow]Chain position:[/bold yellow]")
        for item in summary.chain_position:
            console.print(f"- {item.stage}: {item.status} ready={item.ready}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case intelligence summary JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only summarizes local case intelligence. "
        "It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-execution-gate-proposal-review-packet")
def brain_chat_execution_gate_proposal_review_packet_command(
    step_decision_file: Path = typer.Argument(..., help="Local JSON file containing the validation step approval decision."),
    approval_decision_file: Path = typer.Option(..., "--approval-decision-file", "--approval-decision", help="Local JSON file containing the earlier evidence approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a local execution-gate proposal before any future gate design."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not approval_decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
        raise typer.Exit(code=1)

    if not step_decision_file.exists():
        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
        plan = build_evidence_approved_validation_plan(approval_decision)
        step_gate = build_validation_plan_step_review_gate(plan)
        step_approval_request = build_validation_step_approval_request(step_gate)
        step_decision = import_validation_step_approval_decision_file(step_approval_request, step_decision_file)
        proposal = build_validation_step_execution_gate_proposal(step_decision)
        review_packet = build_execution_gate_proposal_review_packet(proposal)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = review_packet.to_markdown()
    data = review_packet.to_dict()

    table = Table(title="Brain Chat Execution Gate Proposal Review Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Evidence approval decision file", str(approval_decision_file))
    table.add_row("Step decision file", str(step_decision_file))
    table.add_row("Target", review_packet.target_name)
    table.add_row("Focus endpoint", review_packet.focus_endpoint or "none")
    table.add_row("Review status", review_packet.review_status)
    table.add_row("Proposal status", review_packet.proposal_status)
    table.add_row("Effective step approval granted", str(review_packet.effective_step_approval_granted))
    table.add_row("Execution gate proposal ready", str(review_packet.execution_gate_proposal_ready))
    table.add_row("Runtime execution allowed", str(review_packet.runtime_execution_allowed))
    table.add_row("Design review ready", str(review_packet.design_review_ready))
    table.add_row("Approved steps", str(len(review_packet.approved_steps)))
    table.add_row("Proposal requirements", str(len(review_packet.proposal_requirements)))
    table.add_row("Runtime guards", str(len(review_packet.runtime_guards)))
    table.add_row("Blockers", str(len(review_packet.blockers)))
    table.add_row("Human review items", str(len(review_packet.human_review_items)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Execution gate created", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if review_packet.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in review_packet.blockers:
            console.print(f"- {item}")

    if review_packet.human_review_items:
        console.print("[bold yellow]Human review items:[/bold yellow]")
        for item in review_packet.human_review_items:
            console.print(f"- {item}")

    if review_packet.proposal_requirements:
        console.print("[bold yellow]Proposal requirements:[/bold yellow]")
        for item in review_packet.proposal_requirements:
            console.print(f"- {item}")

    if review_packet.runtime_guards:
        console.print("[bold yellow]Runtime guards:[/bold yellow]")
        for item in review_packet.runtime_guards:
            console.print(f"- {item}")

    if review_packet.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in review_packet.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved execution gate proposal review packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved execution gate proposal review packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local execution-gate proposal. "
        "It does not create an execution gate, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-validation-step-execution-gate-proposal")
def brain_chat_validation_step_execution_gate_proposal_command(
    step_decision_file: Path = typer.Argument(..., help="Local JSON file containing the validation step approval decision."),
    approval_decision_file: Path = typer.Option(..., "--approval-decision-file", "--approval-decision", help="Local JSON file containing the earlier evidence approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local proposal for what a future execution gate would require."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not approval_decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
        raise typer.Exit(code=1)

    if not step_decision_file.exists():
        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
        plan = build_evidence_approved_validation_plan(approval_decision)
        step_gate = build_validation_plan_step_review_gate(plan)
        step_approval_request = build_validation_step_approval_request(step_gate)
        step_decision = import_validation_step_approval_decision_file(step_approval_request, step_decision_file)
        proposal = build_validation_step_execution_gate_proposal(step_decision)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = proposal.to_markdown()
    data = proposal.to_dict()

    table = Table(title="Brain Chat Validation Step Execution Gate Proposal")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Evidence approval decision file", str(approval_decision_file))
    table.add_row("Step decision file", str(step_decision_file))
    table.add_row("Target", proposal.target_name)
    table.add_row("Focus endpoint", proposal.focus_endpoint or "none")
    table.add_row("Proposal status", proposal.proposal_status)
    table.add_row("Decision", proposal.decision)
    table.add_row("Effective step approval granted", str(proposal.effective_step_approval_granted))
    table.add_row("Execution gate proposal ready", str(proposal.execution_gate_proposal_ready))
    table.add_row("Runtime execution allowed", str(proposal.runtime_execution_allowed))
    table.add_row("Approved steps", str(len(proposal.approved_steps)))
    table.add_row("Proposed requirements", str(len(proposal.proposed_execution_gate_requirements)))
    table.add_row("Runtime guards", str(len(proposal.proposed_runtime_guards)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Execution gate created", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if proposal.approved_steps:
        console.print("[bold yellow]Approved steps:[/bold yellow]")
        for item in proposal.approved_steps:
            console.print(f"- {item}")

    if proposal.proposed_execution_gate_requirements:
        console.print("[bold yellow]Proposed execution gate requirements:[/bold yellow]")
        for item in proposal.proposed_execution_gate_requirements:
            console.print(f"- {item}")

    if proposal.proposed_runtime_guards:
        console.print("[bold yellow]Proposed runtime guards:[/bold yellow]")
        for item in proposal.proposed_runtime_guards:
            console.print(f"- {item}")

    if proposal.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in proposal.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation step execution gate proposal Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation step execution gate proposal JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local execution-gate proposal. "
        "It does not create an execution gate, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-validation-step-approval-decision-import")
def brain_chat_validation_step_approval_decision_import_command(
    step_decision_file: Path = typer.Argument(..., help="Local JSON file containing the validation step approval decision."),
    approval_decision_file: Path = typer.Option(..., "--approval-decision-file", "--approval-decision", help="Local JSON file containing the earlier evidence approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import a local human decision for validation-step approval."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not approval_decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {approval_decision_file}")
        raise typer.Exit(code=1)

    if not step_decision_file.exists():
        console.print(f"[bold red]Validation step approval decision JSON not found:[/bold red] {step_decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        approval_decision = import_evidence_approval_decision_file(approval_request, approval_decision_file)
        plan = build_evidence_approved_validation_plan(approval_decision)
        step_gate = build_validation_plan_step_review_gate(plan)
        step_approval_request = build_validation_step_approval_request(step_gate)
        step_decision = import_validation_step_approval_decision_file(step_approval_request, step_decision_file)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = step_decision.to_markdown()
    data = step_decision.to_dict()

    table = Table(title="Brain Chat Validation Step Approval Decision")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Evidence approval decision file", str(approval_decision_file))
    table.add_row("Step decision file", str(step_decision_file))
    table.add_row("Decision", step_decision.decision)
    table.add_row("Reviewer", step_decision.reviewer or "unspecified")
    table.add_row("Request status", step_decision.request_status)
    table.add_row("Gate status", step_decision.gate_status)
    table.add_row("Step review ready", str(step_decision.step_review_ready))
    table.add_row("Validation allowed", str(step_decision.validation_allowed))
    table.add_row("Effective step approval granted", str(step_decision.effective_step_approval_granted))
    table.add_row("Approved steps", str(len(step_decision.approved_steps)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Step approval side effects", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if step_decision.reason:
        console.print("[bold yellow]Reason:[/bold yellow]")
        console.print(step_decision.reason)

    if step_decision.approved_steps:
        console.print("[bold yellow]Approved steps:[/bold yellow]")
        for item in step_decision.approved_steps:
            console.print(f"- {item}")

    if step_decision.allowed_next_steps:
        console.print("[bold yellow]Allowed next steps:[/bold yellow]")
        for item in step_decision.allowed_next_steps:
            console.print(f"- {item}")

    if step_decision.rejected_next_steps:
        console.print("[bold yellow]Rejected next steps:[/bold yellow]")
        for item in step_decision.rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation step approval decision Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation step approval decision JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports local validation step approval metadata. "
        "It does not grant side-effectful approval, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-validation-step-approval-request")
def brain_chat_validation_step_approval_request_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the reviewer approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local human approval-request packet for reviewed validation steps."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        decision = import_evidence_approval_decision_file(approval_request, decision_file)
        plan = build_evidence_approved_validation_plan(decision)
        step_gate = build_validation_plan_step_review_gate(plan)
        step_approval_request = build_validation_step_approval_request(step_gate)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = step_approval_request.to_markdown()
    data = step_approval_request.to_dict()

    table = Table(title="Brain Chat Validation Step Approval Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Decision file", str(decision_file))
    table.add_row("Target", step_approval_request.target_name)
    table.add_row("Focus endpoint", step_approval_request.focus_endpoint or "none")
    table.add_row("Request status", step_approval_request.request_status)
    table.add_row("Gate status", step_approval_request.gate_status)
    table.add_row("Step review ready", str(step_approval_request.step_review_ready))
    table.add_row("Validation allowed", str(step_approval_request.validation_allowed))
    table.add_row("Reviewed step count", str(step_approval_request.reviewed_step_count))
    table.add_row("Blockers", str(len(step_approval_request.blockers)))
    table.add_row("Steps for approval", str(len(step_approval_request.steps_for_human_approval)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Step approval granted", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if step_approval_request.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in step_approval_request.blockers:
            console.print(f"- {item}")

    if step_approval_request.steps_for_human_approval:
        console.print("[bold yellow]Steps for human approval:[/bold yellow]")
        for item in step_approval_request.steps_for_human_approval:
            console.print(f"- {item}")

    if step_approval_request.required_human_checks:
        console.print("[bold yellow]Required human checks:[/bold yellow]")
        for item in step_approval_request.required_human_checks:
            console.print(f"- {item}")

    if step_approval_request.rejected_without_approval:
        console.print("[bold yellow]Rejected without approval:[/bold yellow]")
        for item in step_approval_request.rejected_without_approval:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation step approval request Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation step approval request JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local validation step approval-request packet. "
        "It does not grant approval, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-validation-plan-step-review-gate")
def brain_chat_validation_plan_step_review_gate_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the reviewer approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review local validation-plan steps before any execution layer exists."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        decision = import_evidence_approval_decision_file(approval_request, decision_file)
        plan = build_evidence_approved_validation_plan(decision)
        step_gate = build_validation_plan_step_review_gate(plan)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = step_gate.to_markdown()
    data = step_gate.to_dict()

    table = Table(title="Brain Chat Validation Plan Step Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Decision file", str(decision_file))
    table.add_row("Target", step_gate.target_name)
    table.add_row("Focus endpoint", step_gate.focus_endpoint or "none")
    table.add_row("Gate status", step_gate.gate_status)
    table.add_row("Plan status", step_gate.plan_status)
    table.add_row("Validation allowed", str(step_gate.validation_allowed))
    table.add_row("Step review ready", str(step_gate.step_review_ready))
    table.add_row("Total steps", str(step_gate.total_steps))
    table.add_row("Allowed for manual review", str(step_gate.allowed_count))
    table.add_row("Needs scope check", str(step_gate.needs_scope_check_count))
    table.add_row("Rejected unsafe", str(step_gate.rejected_unsafe_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if step_gate.reviewed_steps:
        console.print("[bold yellow]Reviewed steps:[/bold yellow]")
        for index, item in enumerate(step_gate.reviewed_steps, start=1):
            console.print(f"{index}. \\[{item.status}] {item.step}")
            console.print(f"   Reason: {item.reason}")

    if step_gate.blocking_reasons:
        console.print("[bold yellow]Blocking reasons:[/bold yellow]")
        for item in step_gate.blocking_reasons:
            console.print(f"- {item}")

    if step_gate.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in step_gate.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation plan step review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation plan step review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews local validation-plan steps. "
        "It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-approved-validation-plan")
def brain_chat_evidence_approved_validation_plan_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the reviewer approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local validation-plan packet from an effective approval decision."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        decision = import_evidence_approval_decision_file(approval_request, decision_file)
        plan = build_evidence_approved_validation_plan(decision)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = plan.to_markdown()
    data = plan.to_dict()

    table = Table(title="Brain Chat Evidence Approved Validation Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Decision file", str(decision_file))
    table.add_row("Target", plan.target_name)
    table.add_row("Focus endpoint", plan.focus_endpoint or "none")
    table.add_row("Plan status", plan.plan_status)
    table.add_row("Decision", plan.decision)
    table.add_row("Effective approval granted", str(plan.effective_approval_granted))
    table.add_row("Validation allowed", str(plan.validation_allowed))
    table.add_row("Planned validation steps", str(len(plan.planned_validation_steps)))
    table.add_row("Runtime guards", str(len(plan.required_runtime_guards)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if plan.planned_validation_steps:
        console.print("[bold yellow]Planned validation steps:[/bold yellow]")
        for item in plan.planned_validation_steps:
            console.print(f"- {item}")

    if plan.required_runtime_guards:
        console.print("[bold yellow]Required runtime guards:[/bold yellow]")
        for item in plan.required_runtime_guards:
            console.print(f"- {item}")

    if plan.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in plan.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved approved validation plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved approved validation plan JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local validation-plan packet. "
        "It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-approval-decision-import")
def brain_chat_evidence_approval_decision_import_command(
    decision_file: Path = typer.Argument(..., help="Local JSON file containing the reviewer approval decision."),
    status_file: Path | None = typer.Option(None, "--status-file", "--status", help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import a local human approval decision for an evidence approval request."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(f"[bold red]Evidence approval decision JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
        decision = import_evidence_approval_decision_file(approval_request, decision_file)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = decision.to_markdown()
    data = decision.to_dict()

    table = Table(title="Brain Chat Evidence Approval Decision")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Decision file", str(decision_file))
    table.add_row("Decision", decision.decision)
    table.add_row("Reviewer", decision.reviewer or "unspecified")
    table.add_row("Approval request status", decision.approval_request_status)
    table.add_row("Gate status", decision.gate_status)
    table.add_row("Effective approval granted", str(decision.effective_approval_granted))
    table.add_row("Target", decision.target_name)
    table.add_row("Focus endpoint", decision.focus_endpoint or "none")
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Approval side effects", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if decision.reason:
        console.print("[bold yellow]Reason:[/bold yellow]")
        console.print(decision.reason)

    if decision.allowed_next_steps:
        console.print("[bold yellow]Allowed next steps:[/bold yellow]")
        for item in decision.allowed_next_steps:
            console.print(f"- {item}")

    if decision.rejected_next_steps:
        console.print("[bold yellow]Rejected next steps:[/bold yellow]")
        for item in decision.rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved evidence approval decision Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved evidence approval decision JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports local approval decision metadata. "
        "It does not grant side-effectful approval, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-approval-request")
def brain_chat_evidence_approval_request_command(
    status_file: Path | None = typer.Argument(None, help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local human approval-request packet from an evidence checklist review gate."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
        approval_request = build_evidence_approval_request(gate)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = approval_request.to_markdown()
    data = approval_request.to_dict()

    table = Table(title="Brain Chat Evidence Approval Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Target", approval_request.target_name)
    table.add_row("Focus endpoint", approval_request.focus_endpoint or "none")
    table.add_row("Approval status", approval_request.approval_status)
    table.add_row("Gate status", approval_request.gate_status)
    table.add_row("Validation approval ready", str(approval_request.validation_approval_ready))
    table.add_row("Requested action", approval_request.requested_action)
    table.add_row("Blockers", str(len(approval_request.blockers)))
    table.add_row("Required human checks", str(len(approval_request.required_human_checks)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Approval granted", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if approval_request.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in approval_request.blockers:
            console.print(f"- {item}")

    if approval_request.required_human_checks:
        console.print("[bold yellow]Required human checks:[/bold yellow]")
        for item in approval_request.required_human_checks:
            console.print(f"- {item}")

    if approval_request.rejected_without_approval:
        console.print("[bold yellow]Rejected without approval:[/bold yellow]")
        for item in approval_request.rejected_without_approval:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved evidence approval request Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved evidence approval request JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local human approval-request packet. "
        "It does not grant approval, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-checklist-review-gate")
def brain_chat_evidence_checklist_review_gate_command(
    status_file: Path | None = typer.Argument(None, help="Optional local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a local evidence checklist and decide validation-approval readiness."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        if status_file is not None:
            if not status_file.exists():
                console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
                raise typer.Exit(code=1)
            import_result = import_evidence_checklist_status_file(session, status_file)
            checklist = import_result.checklist
        else:
            checklist = build_brain_chat_evidence_checklist(session)

        gate = build_evidence_checklist_review_gate(checklist)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    markdown = gate.to_markdown()
    data = gate.to_dict()

    table = Table(title="Brain Chat Evidence Checklist Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file) if status_file else "none")
    table.add_row("Target", gate.target_name)
    table.add_row("Focus endpoint", gate.focus_endpoint or "none")
    table.add_row("Gate status", gate.gate_status)
    table.add_row("Recommendation", gate.recommendation)
    table.add_row("Checklist complete", str(gate.checklist_complete))
    table.add_row("Validation approval ready", str(gate.validation_approval_ready))
    table.add_row("Total items", str(gate.total_items))
    table.add_row("Missing", str(gate.missing_count))
    table.add_row("Collected", str(gate.collected_count))
    table.add_row("Review needed", str(gate.review_needed_count))
    table.add_row("Blocked", str(gate.blocked_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if gate.blocking_reasons:
        console.print("[bold yellow]Blocking reasons:[/bold yellow]")
        for item in gate.blocking_reasons:
            console.print(f"- {item}")

    if gate.review_reasons:
        console.print("[bold yellow]Review reasons:[/bold yellow]")
        for item in gate.review_reasons:
            console.print(f"- {item}")

    if gate.approval_requirements:
        console.print("[bold yellow]Approval requirements:[/bold yellow]")
        for item in gate.approval_requirements:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved evidence checklist review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved evidence checklist review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews local checklist readiness. "
        "It does not collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-checklist-import-status")
def brain_chat_evidence_checklist_import_status_command(
    status_file: Path = typer.Argument(..., help="Local JSON file containing evidence checklist statuses."),
    session_file: Path | None = typer.Option(None, "--session-file", "--session", help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import local evidence checklist statuses from JSON."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    if not status_file.exists():
        console.print(f"[bold red]Evidence checklist status JSON not found:[/bold red] {status_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)

    try:
        result = import_evidence_checklist_status_file(session, status_file)
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=1) from exc

    checklist = result.checklist
    markdown = checklist.to_markdown()
    data = result.to_dict()

    table = Table(title="Brain Chat Evidence Checklist Status Import")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Status file", str(status_file))
    table.add_row("Target", checklist.target_name)
    table.add_row("Focus endpoint", checklist.focus_endpoint or "none")
    table.add_row("Complete", str(checklist.complete))
    table.add_row("Total items", str(len(checklist.items)))
    table.add_row("Missing", str(checklist.missing_count))
    table.add_row("Collected", str(checklist.collected_count))
    table.add_row("Review needed", str(checklist.review_needed_count))
    table.add_row("Blocked", str(checklist.blocked_count))
    table.add_row("Unmatched labels", str(len(result.imported.unmatched_labels)))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if checklist.items:
        console.print("[bold yellow]Evidence checklist:[/bold yellow]")
        for index, item in enumerate(checklist.items, start=1):
            console.print(f"{index}. \\[{item.status}] {item.label}")

    if result.imported.unmatched_labels:
        console.print("[bold yellow]Unmatched labels:[/bold yellow]")
        for label in result.imported.unmatched_labels:
            console.print(f"- {label}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved imported evidence checklist Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved imported evidence checklist JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports local checklist status metadata. "
        "It does not collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-evidence-checklist")
def brain_chat_evidence_checklist_command(
    session_file: Path | None = typer.Argument(None, help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local evidence checklist from a brain-chat dashboard review packet."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)
    checklist = build_brain_chat_evidence_checklist(session)
    markdown = checklist.to_markdown()
    data = checklist.to_dict()

    table = Table(title="Brain Chat Evidence Checklist")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Target", checklist.target_name)
    table.add_row("Focus endpoint", checklist.focus_endpoint or "none")
    table.add_row("Review status", checklist.review_status)
    table.add_row("Reportable", str(checklist.reportable))
    table.add_row("Execution allowed", str(checklist.execution_allowed))
    table.add_row("Complete", str(checklist.complete))
    table.add_row("Total items", str(len(checklist.items)))
    table.add_row("Missing", str(checklist.missing_count))
    table.add_row("Collected", str(checklist.collected_count))
    table.add_row("Review needed", str(checklist.review_needed_count))
    table.add_row("Blocked", str(checklist.blocked_count))
    table.add_row("Tool execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if checklist.items:
        console.print("[bold yellow]Evidence checklist:[/bold yellow]")
        for index, item in enumerate(checklist.items, start=1):
            console.print(f"{index}. \\[{item.status}] {item.label}")

    if checklist.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in checklist.blockers:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain chat evidence checklist Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat evidence checklist JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local evidence checklist. "
        "It does not collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-dashboard-review-packet")
def brain_chat_case_dashboard_review_packet_command(
    session_file: Path | None = typer.Argument(None, help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local review packet from a brain-chat case dashboard."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)
    packet = build_brain_chat_case_dashboard_review_packet(session)
    markdown = packet.to_markdown()
    data = packet.to_dict()

    table = Table(title="Brain Chat Case Dashboard Review Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Target", packet.target_name)
    table.add_row("Focus endpoint", packet.focus_endpoint or "none")
    table.add_row("Review status", packet.review_status)
    table.add_row("Reportable", str(packet.reportable))
    table.add_row("Execution allowed", str(packet.execution_allowed))
    table.add_row("Blockers", str(len(packet.blockers)))
    table.add_row("Required evidence", str(len(packet.required_evidence)))
    table.add_row("Safe next action", packet.safe_next_action)
    table.add_row("Tool execution", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if packet.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in packet.blockers:
            console.print(f"- {item}")

    if packet.required_evidence:
        console.print("[bold yellow]Required evidence:[/bold yellow]")
        for item in packet.required_evidence:
            console.print(f"- {item}")

    if packet.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in packet.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain chat case dashboard review packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat case dashboard review packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local dashboard review packet. "
        "It does not call providers, execute tools, send requests, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-case-dashboard")
def brain_chat_case_dashboard_command(
    session_file: Path | None = typer.Argument(None, help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Show a local case dashboard from a brain-chat session."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)
    dashboard = build_brain_chat_case_dashboard(session)
    markdown = dashboard.to_markdown()
    data = dashboard.to_dict()

    table = Table(title="Brain Chat Case Dashboard")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Target", dashboard.target_name)
    table.add_row("Focus endpoint", dashboard.focus_endpoint or "none")
    table.add_row("Turns", str(dashboard.turn_count))
    table.add_row("Latest question", dashboard.latest_question or "none")
    table.add_row("Decision", dashboard.decision)
    table.add_row("Approval status", dashboard.approval_status)
    table.add_row("Execution gate", dashboard.execution_gate)
    table.add_row("Execution allowed", str(dashboard.execution_allowed))
    table.add_row("Reportable", str(dashboard.reportable))
    table.add_row("Recommendation", dashboard.recommendation)
    table.add_row("Next question", dashboard.next_question)
    console.print(table)

    if dashboard.next_evidence:
        console.print("[bold yellow]Next evidence:[/bold yellow]")
        for item in dashboard.next_evidence:
            console.print(f"- {item}")

    if dashboard.repeated_questions:
        console.print("[bold yellow]Repeated questions:[/bold yellow]")
        for item in dashboard.repeated_questions:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain chat case dashboard Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat case dashboard JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only summarizes local brain-chat case state. "
        "It does not call providers, execute tools, send requests, or confirm vulnerabilities."
    )


@app.command("brain-chat-session-next-step")
def brain_chat_session_next_step_command(
    session_file: Path | None = typer.Argument(None, help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a planning-only next-step plan from a local brain-chat session."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)
    plan = build_brain_chat_session_next_step_plan(session)
    markdown = plan.to_markdown()
    data = plan.to_dict()

    table = Table(title="Brain Chat Session Next-Step Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Recommendation", plan.recommendation)
    table.add_row("Focus endpoint", plan.current_focus_endpoint or "none")
    table.add_row("Current blocker", plan.current_blocker)
    table.add_row("Next question", plan.next_question)
    table.add_row("Next evidence items", str(len(plan.next_evidence)))
    table.add_row("Do-not-do items", str(len(plan.do_not_do_yet)))
    table.add_row("Tool execution", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if plan.next_evidence:
        console.print("[bold yellow]Next evidence:[/bold yellow]")
        for item in plan.next_evidence:
            console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain chat next-step Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat next-step JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local planning packet from chat history. "
        "It does not call providers, execute tools, send requests, or confirm vulnerabilities."
    )


@app.command("brain-chat-session-summary")
def brain_chat_session_summary_command(
    session_file: Path | None = typer.Argument(None, help="Path to brain-chat-session JSON. Defaults to ./brain-chat-session.json."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Summarize a local brain-chat session JSON file."""
    resolved_session_file = session_file or Path("brain-chat-session.json")

    if not resolved_session_file.exists():
        console.print(f"[bold red]Brain chat session JSON not found:[/bold red] {resolved_session_file}")
        raise typer.Exit(code=1)

    session = load_brain_chat_session(resolved_session_file)
    summary = summarize_brain_chat_session(session)
    markdown = render_brain_chat_session_summary(session)
    data = summary.to_dict()

    table = Table(title="Brain Chat Session Summary")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Session", str(resolved_session_file))
    table.add_row("Turns", str(summary.turn_count))
    table.add_row("Latest question", summary.latest_question or "none")
    table.add_row("Latest focus endpoint", summary.latest_focus_endpoint or "none")
    table.add_row("Latest decision", summary.latest_decision)
    table.add_row("Latest approval status", summary.latest_approval_status)
    table.add_row("Latest execution gate", summary.latest_execution_gate)
    table.add_row("Execution allowed", str(summary.latest_execution_allowed))
    table.add_row("Repeated questions", str(len(summary.repeated_questions)))
    table.add_row("Suggested next question", summary.suggested_next_question)
    console.print(table)

    if summary.repeated_questions:
        console.print("[bold yellow]Repeated questions:[/bold yellow]")
        for question in summary.repeated_questions:
            console.print(f"- {question}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain chat session summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat session summary JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only summarizes local brain-chat session history. "
        "It does not call providers, execute tools, send requests, or confirm vulnerabilities."
    )


@app.command("brain-chat")
def brain_chat_command(
    question: str = typer.Argument(..., help="Question to ask the local deterministic brain."),
    state_dir: Path | None = typer.Option(
        None,
        "--state-dir",
        help="Directory containing generated Blackhole brain artifacts.",
    ),
    case_dir: Path | None = typer.Option(
        None,
        "--case-dir",
        help="Case directory containing a brain/ state directory.",
    ),
    session: Path | None = typer.Option(
        None,
        "--session",
        help="Optional session JSON file to append this brain-chat turn.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain-chat reply.",
    ),
):
    """Ask the local planning-only brain state a deterministic question."""
    resolved_state_dir = _resolve_brain_chat_state_dir(state_dir=state_dir, case_dir=case_dir)
    resolved_session = _resolve_brain_chat_session_path(
        session=session,
        state_dir=state_dir,
        case_dir=case_dir,
        resolved_state_dir=resolved_state_dir,
    )
    reply = build_brain_chat_reply(question, resolved_state_dir)
    data = reply.to_dict()

    console.print("[bold green]Blackhole:[/bold green]")
    console.print(reply.answer)

    if resolved_session:
        current_session = load_brain_chat_session(resolved_session)
        updated_session = append_brain_chat_turn(current_session, reply)
        save_brain_chat_session(updated_session, resolved_session)
        console.print(
            f"[bold green]Saved brain chat session:[/bold green] {resolved_session} "
            f"({len(updated_session.turns)} turn(s))"
        )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] brain-chat is local and planning-only. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("tool-execution-gate")
def tool_execution_gate_command(
    tool_request_manifest_json: Path = typer.Argument(..., help="Path to tool-request-manifest JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the tool execution gate.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured tool execution gate.",
    ),
):
    """Build a planning-only tool execution gate from tool-request-manifest JSON."""
    if not tool_request_manifest_json.exists():
        console.print(f"[bold red]Tool request manifest JSON not found:[/bold red] {tool_request_manifest_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(tool_request_manifest_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid tool request manifest JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Tool request manifest JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    gate = build_tool_execution_gate(data)
    markdown = render_tool_execution_gate_markdown(gate)
    gate_data = gate.to_dict()

    summary = Table(title="Tool Execution Gate")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", gate.target_name)
    summary.add_row("Focus endpoint", gate.focus_endpoint or "none")
    summary.add_row("Gate decision", gate.gate_decision)
    summary.add_row("Execution allowed", str(gate.execution_allowed))
    summary.add_row("Gate items", str(len(gate.gate_items)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no tool, curl, browser, network, Kali, shell, or LLM execution")
    console.print(summary)

    items_table = Table(title="Execution Gate Items")
    items_table.add_column("#", justify="right")
    items_table.add_column("Family")
    items_table.add_column("Request")
    items_table.add_column("Gate Status")

    for index, item in enumerate(gate.gate_items, start=1):
        items_table.add_row(
            str(index),
            item.tool_family,
            item.request_name,
            item.gate_status,
        )

    console.print(items_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved tool execution gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved tool execution gate JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only execution gate. "
        "It does not execute tools, send requests, run shell commands, launch browsers, call LLM providers, or use Kali tools."
    )


@app.command("tool-request-manifest")
def tool_request_manifest_command(
    brain_approval_json: Path = typer.Argument(..., help="Path to brain-approval JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the tool request manifest.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured tool request manifest.",
    ),
):
    """Build a planning-only tool request manifest from brain-approval JSON."""
    if not brain_approval_json.exists():
        console.print(f"[bold red]Brain approval JSON not found:[/bold red] {brain_approval_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_approval_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain approval JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain approval JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    manifest = build_tool_request_manifest(data)
    markdown = render_tool_request_manifest_markdown(manifest)
    manifest_data = manifest.to_dict()

    summary = Table(title="Tool Request Manifest")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", manifest.target_name)
    summary.add_row("Focus endpoint", manifest.focus_endpoint or "none")
    summary.add_row("Source approval status", manifest.source_approval_status)
    summary.add_row("Tool requests", str(len(manifest.requests)))
    summary.add_row("Execution allowed", str(manifest.execution_allowed))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no tool, curl, browser, network, Kali, shell, or LLM execution")
    console.print(summary)

    requests_table = Table(title="Tool Requests")
    requests_table.add_column("#", justify="right")
    requests_table.add_column("Family")
    requests_table.add_column("Request")
    requests_table.add_column("Approval")
    requests_table.add_column("Execution")

    for index, request in enumerate(manifest.requests, start=1):
        requests_table.add_row(
            str(index),
            request.tool_family,
            request.name,
            "YES" if request.requires_human_approval else "NO",
            "YES" if request.execution_allowed else "NO",
        )

    console.print(requests_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved tool request manifest Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(manifest_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved tool request manifest JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only tool request manifest. "
        "It does not execute tools, send requests, run shell commands, launch browsers, call LLM providers, or use Kali tools."
    )


@app.command("brain-approval")
def brain_approval_command(
    brain_decision_json: Path = typer.Argument(..., help="Path to brain-decision JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the human approval packet.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured human approval packet.",
    ),
):
    """Build a planning-only human approval packet from brain-decision JSON."""
    if not brain_decision_json.exists():
        console.print(f"[bold red]Brain decision JSON not found:[/bold red] {brain_decision_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_decision_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain decision JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain decision JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    packet = build_brain_approval_packet(data)
    markdown = render_brain_approval_packet_markdown(packet)
    packet_data = packet.to_dict()

    summary = Table(title="Human Approval Packet")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", packet.target_name)
    summary.add_row("Focus endpoint", packet.focus_endpoint or "none")
    summary.add_row("Source decision", packet.source_decision)
    summary.add_row("Approval status", packet.approval_status)
    summary.add_row("Approval required", str(packet.approval_required))
    summary.add_row("Reportable", str(packet.reportable))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    items_table = Table(title="Approval Items")
    items_table.add_column("#", justify="right")
    items_table.add_column("Category")
    items_table.add_column("Item")
    items_table.add_column("Required")
    items_table.add_column("Source")

    for index, item in enumerate(packet.approval_items, start=1):
        items_table.add_row(
            str(index),
            item.category,
            item.name,
            str(item.required),
            item.source_blocker or "manual",
        )

    console.print(items_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain approval Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(packet_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain approval JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only human approval packet. "
        "It does not confirm vulnerabilities, call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-decision")
def brain_decision_command(
    brain_review_json: Path = typer.Argument(..., help="Path to brain-review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the brain decision gate.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain decision gate.",
    ),
):
    """Build a planning-only decision gate from brain-review JSON."""
    if not brain_review_json.exists():
        console.print(f"[bold red]Brain review JSON not found:[/bold red] {brain_review_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_review_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    gate = build_brain_decision_gate(data)
    markdown = render_brain_decision_gate_markdown(gate)
    gate_data = gate.to_dict()

    summary = Table(title="Brain Decision Gate")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", gate.target_name)
    summary.add_row("Focus endpoint", gate.focus_endpoint or "none")
    summary.add_row("Decision", gate.decision)
    summary.add_row("Reportable", str(gate.reportable))
    summary.add_row("Blockers", str(len(gate.blockers)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    blockers_table = Table(title="Decision Blockers")
    blockers_table.add_column("#", justify="right")
    blockers_table.add_column("Blocker")
    blockers_table.add_column("Severity")
    blockers_table.add_column("Reason")

    for index, blocker in enumerate(gate.blockers, start=1):
        blockers_table.add_row(str(index), blocker.name, blocker.severity, blocker.reason)

    console.print(blockers_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain decision Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain decision JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only decision gate. "
        "It does not confirm vulnerabilities, call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-review")
def brain_review_command(
    brain_prompt_json: Path = typer.Argument(..., help="Path to brain-prompt JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the brain review.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured brain review.",
    ),
):
    """Build a planning-only reasoning review from brain-prompt JSON."""
    if not brain_prompt_json.exists():
        console.print(f"[bold red]Brain prompt JSON not found:[/bold red] {brain_prompt_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(brain_prompt_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid brain prompt JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Brain prompt JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    review = build_brain_review(data)
    markdown = render_brain_review_markdown(review)
    review_data = review.to_dict()

    summary = Table(title="Brain Review")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", review.target_name)
    summary.add_row("Focus endpoint", review.focus_endpoint or "none")
    summary.add_row("Sections", str(len(review.sections)))
    summary.add_row("Safety gates", str(len(review.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    section_table = Table(title="Brain Review Sections")
    section_table.add_column("#", justify="right")
    section_table.add_column("Section")

    for index, section in enumerate(review.sections, start=1):
        section_table.add_row(str(index), section.title)

    console.print(section_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain review JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only reasoning review. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("brain-prompt")
def brain_prompt_command(
    ai_brain_json: Path = typer.Argument(..., help="Path to AI brain plan JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the prompt package.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured prompt package.",
    ),
):
    """Build a planning-only LLM brain prompt package from AI brain JSON."""
    if not ai_brain_json.exists():
        console.print(f"[bold red]AI brain JSON not found:[/bold red] {ai_brain_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(ai_brain_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid AI brain JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]AI brain JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = build_brain_prompt_package(data)
    markdown = render_brain_prompt_package_markdown(package)
    package_data = package.to_dict()

    summary = Table(title="LLM Brain Prompt Package")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", package.target_name)
    summary.add_row("Focus endpoint", package.focus_endpoint or "none")
    summary.add_row("Messages", str(package.message_count))
    summary.add_row("Safety gates", str(len(package.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no LLM provider, curl, browser, network, Kali, or shell execution")
    console.print(summary)

    messages_table = Table(title="Prompt Messages")
    messages_table.add_column("#", justify="right")
    messages_table.add_column("Role")
    messages_table.add_column("Characters", justify="right")

    for index, message in enumerate(package.messages, start=1):
        messages_table.add_row(str(index), message.role, str(len(message.content)))

    console.print(messages_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved brain prompt Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(package_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved brain prompt JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a provider-ready prompt package. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("ai-brain")
def ai_brain_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the AI brain plan.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured AI brain plan.",
    ),
):
    """Build a planning-only AI brain plan from research-state JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_ai_brain_plan(data)
    markdown = render_ai_brain_plan_markdown(plan)
    plan_data = plan.to_dict()

    summary = Table(title="AI Brain Plan")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", plan.target_name)
    summary.add_row("Focus items", str(len(plan.focus_queue)))
    summary.add_row("Global actions", str(len(plan.global_actions)))
    summary.add_row("Safety gates", str(len(plan.safety_gates)))
    summary.add_row("Provider execution", "disabled")
    summary.add_row("Execution", "planning-only; no curl, browser, network, Kali, or LLM provider execution")
    console.print(summary)

    focus_table = Table(title="AI Brain Focus Queue")
    focus_table.add_column("#", justify="right")
    focus_table.add_column("Endpoint")
    focus_table.add_column("Priority")
    focus_table.add_column("Triage")
    focus_table.add_column("Actions", justify="right")
    focus_table.add_column("Reason")

    for index, item in enumerate(plan.focus_queue, start=1):
        focus_table.add_row(
            str(index),
            item.endpoint,
            f"{item.priority_band}/{item.priority_score}",
            item.triage_state,
            str(len(item.next_actions)),
            item.reason,
        )

    console.print(focus_table)

    gates_table = Table(title="AI Brain Safety Gates")
    gates_table.add_column("#", justify="right")
    gates_table.add_column("Gate")

    for index, gate in enumerate(plan.safety_gates, start=1):
        gates_table.add_row(str(index), gate)

    console.print(gates_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved AI brain plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved AI brain plan JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a planning-only AI brain plan. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )






@app.command("case-summary")
def case_summary_command(
    case_timeline_json: Path = typer.Argument(..., help="Path to case-timeline JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the case summary.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured case summary.",
    ),
):
    """Build a planning-only case summary from case-timeline JSON."""
    if not case_timeline_json.exists():
        console.print(f"[bold red]Case timeline JSON not found:[/bold red] {case_timeline_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_timeline_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case timeline JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case timeline JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    summary_obj = build_case_summary(data)
    markdown = render_case_summary_markdown(summary_obj)
    summary_data = summary_obj.to_dict()

    summary_table = Table(title="Case Summary")
    summary_table.add_column("Field", style="bold")
    summary_table.add_column("Value")
    summary_table.add_row("Target", summary_obj.target_name)
    summary_table.add_row("Events", str(summary_obj.event_count))
    summary_table.add_row("Current state", summary_obj.current_state)
    summary_table.add_row("Execution", "planning-only; local artifacts only")
    console.print(summary_table)

    points_table = Table(title="Key Points")
    points_table.add_column("#", justify="right")
    points_table.add_column("Point")

    for index, point in enumerate(summary_obj.key_points, start=1):
        points_table.add_row(str(index), point)

    console.print(points_table)

    steps_table = Table(title="Recommended Next Steps")
    steps_table.add_column("#", justify="right")
    steps_table.add_column("Step")

    for index, step in enumerate(summary_obj.recommended_next_steps, start=1):
        steps_table.add_row(str(index), step)

    console.print(steps_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case summary JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reads local case timeline artifacts. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("case-timeline")
def case_timeline_command(
    case_dir: Path = typer.Argument(..., help="Directory containing Blackhole case artifacts."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the case timeline.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured case timeline.",
    ),
):
    """Build a planning-only case timeline from local Blackhole artifacts."""
    if not case_dir.exists():
        console.print(f"[bold red]Case directory not found:[/bold red] {case_dir}")
        raise typer.Exit(code=1)

    timeline = build_case_timeline(case_dir)
    markdown = render_case_timeline_markdown(timeline)
    data = timeline.to_dict()

    summary = Table(title="Case Timeline")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", timeline.target_name)
    summary.add_row("Events", str(timeline.event_count))
    summary.add_row("Execution", "planning-only; local artifacts only")
    console.print(summary)

    events_table = Table(title="Timeline Events")
    events_table.add_column("#", justify="right")
    events_table.add_column("Type")
    events_table.add_column("Title")
    events_table.add_column("Summary")

    for event in timeline.events:
        events_table.add_row(
            str(event.order),
            event.event_type,
            event.title,
            event.summary,
        )

    console.print(events_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved case timeline Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case timeline JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reads local case artifacts. "
        "It does not call LLM providers, send requests, execute shell commands, launch browsers, or use Kali tools."
    )


@app.command("research-state-apply")
def research_state_apply_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    update_plan: Path = typer.Option(..., "--update-plan", help="Path to research-state-update JSON."),
    output_file: Path = typer.Option(..., "--output-file", "--output", help="Output path for updated research-state JSON."),
    result_json: Path | None = typer.Option(None, "--result-json", help="Optional path to write full apply result JSON."),
):
    """Apply a research-state update plan to a local copy of research-state JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    if not update_plan.exists():
        console.print(f"[bold red]Update plan JSON not found:[/bold red] {update_plan}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
        plan_data = json.loads(update_plan.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict) or not isinstance(plan_data, dict):
        console.print("[bold red]Research-state and update-plan JSON must both be objects.[/bold red]")
        raise typer.Exit(code=2)

    result = apply_research_state_update_plan(state_data, plan_data)
    result_data = result.to_dict()

    summary = Table(title="Research State Apply Result")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", result.target_name)
    summary.add_row("Endpoint", result.endpoint)
    summary.add_row("Validation result", result.validation_result)
    summary.add_row("Patches", str(len(result.applied_patches)))
    summary.add_row("Execution", "local-only; no network, browser, shell, Kali, tool, or LLM execution")
    console.print(summary)

    patches_table = Table(title="Applied Patches")
    patches_table.add_column("#", justify="right")
    patches_table.add_column("Path")
    patches_table.add_column("Applied")
    patches_table.add_column("New Value")

    for index, patch in enumerate(result.applied_patches, start=1):
        patches_table.add_row(
            str(index),
            escape(patch.path),
            str(patch.applied),
            escape(str(patch.new_value)),
        )

    console.print(patches_table)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result.updated_research_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    console.print(f"[bold green]Saved updated research-state JSON:[/bold green] {output_file}")

    if result_json:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(result_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved apply result JSON:[/bold green] {result_json}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only writes a local updated copy. "
        "It does not mutate the original file or execute tools."
    )





@app.command("result-flow")
def result_flow_command(
    research_state_json: Path = typer.Option(..., "--research-state", help="Path to research-state JSON."),
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint that was manually validated."),
    observed_status: int | None = typer.Option(None, "--observed-status", help="Observed HTTP status code."),
    expected_status: int | None = typer.Option(None, "--expected-status", help="Expected HTTP status code."),
    observed_body: str = typer.Option("", "--observed-body", help="Short observed response/body note."),
    expected_body: str = typer.Option("", "--expected-body", help="Short expected response/body note."),
    note: str = typer.Option("", "--note", help="Human validation note."),
    updated_state: Path = typer.Option(..., "--updated-state", help="Path to write updated research-state JSON."),
    result_json: Path | None = typer.Option(None, "--result-json", help="Optional path to write full result-flow JSON."),
):
    """Run local interpretation -> state update planning -> local state apply."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    flow = build_result_flow(
        research_state_data=state_data,
        endpoint=endpoint,
        observed_status=observed_status,
        expected_status=expected_status,
        observed_body=observed_body,
        expected_body=expected_body,
        note=note,
    )
    flow_data = flow.to_dict()

    summary = Table(title="Result Flow")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", endpoint)
    summary.add_row("Suggested result", flow.interpretation.suggested_result)
    summary.add_row("Confidence", flow.interpretation.confidence)
    summary.add_row("Update validation result", flow.update_plan.validation_result)
    summary.add_row("Applied patches", str(len(flow.apply_result.applied_patches)))
    summary.add_row("Execution", "local-only; no target interaction")
    console.print(summary)

    updated_state.parent.mkdir(parents=True, exist_ok=True)
    updated_state.write_text(
        json.dumps(flow.apply_result.updated_research_state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    console.print(f"[bold green]Saved updated research-state JSON:[/bold green] {updated_state}")

    if result_json:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(flow_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result-flow JSON:[/bold green] {result_json}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only interprets a human-provided result summary and writes a local updated state copy. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-to-state-update")
def result_to_state_update_command(
    research_state_json: Path = typer.Option(..., "--research-state", help="Path to research-state JSON."),
    interpretation_json: Path = typer.Option(..., "--interpretation", help="Path to interpret-result JSON."),
    note: str = typer.Option("", "--note", help="Optional human override note."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a research-state update plan from result interpretation JSON."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    if not interpretation_json.exists():
        console.print(f"[bold red]Interpretation JSON not found:[/bold red] {interpretation_json}")
        raise typer.Exit(code=1)

    try:
        state_data = json.loads(research_state_json.read_text(encoding="utf-8"))
        interpretation_data = json.loads(interpretation_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(state_data, dict) or not isinstance(interpretation_data, dict):
        console.print("[bold red]Research-state and interpretation JSON must both be objects.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_update_plan_from_interpretation(
        research_state_data=state_data,
        interpretation_data=interpretation_data,
        note=note,
    )
    markdown = render_research_state_update_plan_markdown(plan)
    plan_data = plan.to_dict()

    table = Table(title="Result to State Update")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", plan.target_name)
    table.add_row("Endpoint", plan.endpoint)
    table.add_row("Validation result", plan.validation_result)
    table.add_row("Actions", str(len(plan.actions)))
    table.add_row("Execution", "planning-only; no state mutation or tool execution")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved state update Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved state update JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only converts interpretation into a reviewable state-update plan. "
        "It does not mutate research-state files automatically."
    )



@app.command("import-result-evidence")
def import_result_evidence_command(
    evidence_file: Path = typer.Argument(..., help="Path to local result evidence JSON."),
    source: str = typer.Option("manual-json", "--source", help="Evidence source label."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for normalized result evidence.",
    ),
):
    """Normalize local result evidence JSON for interpret-result/result-flow."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence JSON not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(evidence_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid evidence JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Evidence JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        evidence = import_result_evidence(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence:[/bold red] {exc}")
        raise typer.Exit(code=2)

    evidence_data = evidence.to_dict()

    table = Table(title="Normalized Result Evidence")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Endpoint", escape(evidence.endpoint))
    table.add_row("Observed status", str(evidence.observed_status))
    table.add_row("Expected status", str(evidence.expected_status))
    table.add_row("Source", evidence.source)
    table.add_row("Execution", "planning-only; local evidence normalization only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(evidence_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved normalized result evidence JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(evidence_data, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only normalizes local evidence JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("import-result-evidence-batch")
def import_result_evidence_batch_command(
    evidence_dir: Path = typer.Argument(..., help="Directory containing local result evidence JSON files."),
    source: str = typer.Option("manual-json-batch", "--source", help="Evidence batch source label."),
    pattern: str = typer.Option("*.json", "--pattern", help="Glob pattern for evidence JSON files."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for normalized result evidence batch.",
    ),
):
    """Normalize a directory of local result evidence JSON files."""
    try:
        batch = import_result_evidence_batch(evidence_dir, source=source, pattern=pattern)
    except FileNotFoundError as exc:
        console.print(f"[bold red]Evidence directory not found:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except NotADirectoryError as exc:
        console.print(f"[bold red]Evidence path is not a directory:[/bold red] {exc}")
        raise typer.Exit(code=1)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch:[/bold red] {exc}")
        raise typer.Exit(code=2)

    batch_data = batch.to_dict()

    table = Table(title="Normalized Result Evidence Batch")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Directory", str(evidence_dir))
    table.add_row("Pattern", pattern)
    table.add_row("Count", str(batch_data["count"]))
    table.add_row("Source", batch.source)
    table.add_row("Execution", "planning-only; local evidence normalization only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(batch_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved normalized result evidence batch JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(batch_data, indent=2, sort_keys=True))


@app.command("review-result-evidence-batch")
def review_result_evidence_batch_command(
    batch_file: Path = typer.Argument(..., help="Path to normalized result evidence batch JSON."),
    source: str = typer.Option("result-evidence-batch-review", "--source", help="Batch review source label."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional JSON output path for result evidence batch review.",
    ),
):
    """Review a normalized result evidence batch using planning-only interpretation."""
    if not batch_file.exists():
        console.print(f"[bold red]Result evidence batch JSON not found:[/bold red] {batch_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(batch_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        review = review_result_evidence_batch(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    review_data = review.to_dict()

    table = Table(title="Result Evidence Batch Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Batch file", str(batch_file))
    table.add_row("Count", str(review_data["count"]))
    table.add_row("Supported", str(review_data["supported_count"]))
    table.add_row("Rejected", str(review_data["rejected_count"]))
    table.add_row("Needs more evidence", str(review_data["needs_more_evidence_count"]))
    table.add_row("Missing expected status", str(review_data["missing_expected_status_count"]))
    table.add_row("Execution", "planning-only; local batch review only")
    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence batch review JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(review_data, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews local batch evidence. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-review-report")
def result_evidence_review_report_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path containing the rendered Markdown.",
    ),
    title: str = typer.Option("Result Evidence Batch Review Report", "--title", help="Markdown report title."),
    source: str = typer.Option("result-evidence-review-report", "--source", help="Report source label."),
):
    """Render a local result evidence batch review JSON into a planning-only Markdown report."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        report = render_result_evidence_review_report(data, title=title, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence batch review report input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    report_data = report.to_dict()

    table = Table(title="Result Evidence Review Report")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Markdown lines", str(len(report.markdown.splitlines())))
    table.add_row("Execution", "planning-only; local Markdown rendering only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(report.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(report_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence review report JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(report.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders local review JSON into Markdown. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-finding-draft")
def result_evidence_finding_draft_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path containing the rendered Markdown.",
    ),
    title: str = typer.Option("Candidate Finding Draft", "--title", help="Markdown draft title."),
    include_all: bool = typer.Option(False, "--include-all", help="Include rejected and needs-more-evidence items."),
    source: str = typer.Option("result-evidence-finding-draft", "--source", help="Draft source label."),
):
    """Render a planning-only candidate finding draft from batch review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        draft = render_result_evidence_finding_draft(
            data,
            title=title,
            include_all=include_all,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence finding draft input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    draft_data = draft.to_dict()

    table = Table(title="Result Evidence Finding Draft")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Selected evidence items", str(draft.selected_count))
    table.add_row("Markdown lines", str(len(draft.markdown.splitlines())))
    table.add_row("Execution", "planning-only; local draft rendering only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(draft.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence finding draft Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence finding draft JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(draft.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders local review JSON into a candidate draft. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-finding-package")
def result_evidence_finding_package_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    output_dir: Path = typer.Option(..., "--output-dir", "--output", help="Directory to write the finding package."),
    finding_title: str = typer.Option("Candidate Finding Draft", "--title", help="Finding draft title."),
    include_all: bool = typer.Option(False, "--include-all", help="Include rejected and needs-more-evidence items."),
    source: str = typer.Option("result-evidence-finding-package", "--source", help="Package source label."),
):
    """Build a local finding package from result evidence batch review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        package = build_result_evidence_finding_package(
            data,
            finding_title=finding_title,
            include_all=include_all,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence finding package input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output_dir.mkdir(parents=True, exist_ok=True)

    for relative_name, content in package.files.items():
        output_path = output_dir / relative_name
        output_path.write_text(content, encoding="utf-8")

    package_data = package.to_dict()

    table = Table(title="Result Evidence Finding Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Output directory", str(output_dir))
    table.add_row("Files", str(package_data["file_count"]))
    table.add_row("Selected evidence items", str(package.metadata["selected_item_count"]))
    table.add_row("Execution", "planning-only; local package generation only")
    console.print(table)

    console.print(f"[bold green]Saved result evidence finding package:[/bold green] {output_dir}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only writes local package artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-hypothesis")
def result_evidence_hypothesis_command(
    review_file: Path = typer.Argument(..., help="Path to result evidence batch review JSON."),
    supported_only: bool = typer.Option(False, "--supported-only", help="Generate hypotheses only for supported review items."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-hypothesis", "--source", help="Hypothesis source label."),
):
    """Generate planning-only security hypotheses from local result evidence review JSON."""
    if not review_file.exists():
        console.print(f"[bold red]Result evidence batch review JSON not found:[/bold red] {review_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence batch review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence batch review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        hypotheses = generate_result_evidence_hypotheses(
            data,
            supported_only=supported_only,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence hypothesis input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    hypothesis_data = hypotheses.to_dict()
    markdown = hypotheses.to_markdown()

    table = Table(title="Result Evidence Hypotheses")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review file", str(review_file))
    table.add_row("Hypotheses", str(hypothesis_data["count"]))
    table.add_row("Supported only", str(supported_only))
    table.add_row("Execution", "planning-only; local hypothesis generation only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence hypotheses Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(hypothesis_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence hypotheses JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only generates planning-only local hypotheses. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-validation-plan")
def result_evidence_validation_plan_command(
    hypothesis_file: Path = typer.Argument(..., help="Path to result evidence hypothesis JSON."),
    high_priority_only: bool = typer.Option(False, "--high-priority-only", help="Include only high and medium-high priority plans."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-validation-plan", "--source", help="Validation plan source label."),
):
    """Build a planning-only manual validation plan from result evidence hypotheses."""
    if not hypothesis_file.exists():
        console.print(f"[bold red]Result evidence hypothesis JSON not found:[/bold red] {hypothesis_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(hypothesis_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence hypothesis JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence hypothesis JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_result_evidence_validation_plan(
            data,
            high_priority_only=high_priority_only,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence validation plan input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    plan_data = plan.to_dict()
    markdown = plan.to_markdown()

    table = Table(title="Result Evidence Validation Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Hypothesis file", str(hypothesis_file))
    table.add_row("Plans", str(plan_data["count"]))
    table.add_row("High priority only", str(high_priority_only))
    table.add_row("Execution", "planning-only; local validation planning only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence validation plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence validation plan JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only generates a local manual validation plan. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-case-summary")
def result_evidence_case_summary_command(
    validation_plan_file: Path = typer.Argument(..., help="Path to result evidence validation plan JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-case-summary", "--source", help="Case summary source label."),
):
    """Build a case-level intelligence summary from a local validation plan JSON."""
    if not validation_plan_file.exists():
        console.print(f"[bold red]Result evidence validation plan JSON not found:[/bold red] {validation_plan_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(validation_plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid result evidence validation plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Result evidence validation plan JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        summary = build_result_evidence_case_summary(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence case summary input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    summary_data = summary.to_dict()
    markdown = summary.to_markdown()

    table = Table(title="Result Evidence Case Summary")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Validation plan file", str(validation_plan_file))
    table.add_row("Findings", str(summary_data["count"]))
    table.add_row("Strongest candidates", str(len(summary_data["strongest_candidates"])))
    table.add_row("Weak/rejected candidates", str(len(summary_data["weak_or_rejected_candidates"])))
    table.add_row("Execution", "planning-only; local case summary only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence case summary Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(summary_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence case summary JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only summarizes local validation plan JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat")
def case_chat_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer from the case summary."),
    session_file: Path | None = typer.Option(
        None,
        "--session-file",
        help="Optional local JSON session file to append this case-chat turn.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Answer a local research question from a case summary JSON artifact."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        answer = answer_case_question(data, question)
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    answer_data = answer.to_dict()

    table = Table(title="Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", answer.intent)
    table.add_row("Cited endpoints", str(len(answer.cited_endpoints)))
    table.add_row("Next actions", str(len(answer.next_actions)))
    table.add_row("Execution", "planning-only; local artifact chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(answer.answer)

    if answer.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in answer.next_actions:
            console.print(f"- {item}")

    if session_file:
        try:
            session = append_case_chat_turn_to_file(session_file, answer)
        except ValueError as exc:
            console.print(f"[bold red]Invalid case chat session file:[/bold red] {exc}")
            raise typer.Exit(code=2)

        answer_data["session"] = session.to_dict()
        console.print(f"[bold green]Saved case chat session:[/bold green] {session_file}")
        console.print(f"[bold green]Session summary:[/bold green] {session.summary_text()}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(answer_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local case-summary JSON. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-priority-ranking")
def result_evidence_priority_ranking_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    include_weak: bool = typer.Option(True, "--include-weak/--exclude-weak", help="Include weak or likely false-positive candidates."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-priority-ranking", "--source", help="Priority ranking source label."),
):
    """Rank local case-summary candidates by priority, readiness, and evidence strength."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        ranking = build_result_evidence_priority_ranking(
            data,
            include_weak=include_weak,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence priority ranking input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    ranking_data = ranking.to_dict()
    markdown = ranking.to_markdown()

    table = Table(title="Result Evidence Priority Ranking")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Candidates", str(ranking_data["count"]))
    table.add_row("Include weak", str(include_weak))
    table.add_row("Execution", "planning-only; local ranking only")
    console.print(table)

    if ranking_data["top_candidate"]:
        top = ranking_data["top_candidate"]
        console.print(f"[bold green]Top candidate:[/bold green] {top['endpoint']} score={top['score']}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence priority ranking Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(ranking_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence priority ranking JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only ranks local case-summary candidates. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("result-evidence-multi-agent-review")
def result_evidence_multi_agent_review_command(
    ranking_file: Path = typer.Argument(..., help="Path to result evidence priority ranking JSON."),
    include_low_priority: bool = typer.Option(
        True,
        "--include-low-priority/--exclude-low-priority",
        help="Include low priority or likely false-positive candidates.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-multi-agent-review", "--source", help="Multi-agent review source label."),
):
    """Build specialist review plans from a local result evidence priority ranking."""
    if not ranking_file.exists():
        console.print(f"[bold red]Priority ranking JSON not found:[/bold red] {ranking_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(ranking_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid priority ranking JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Priority ranking JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_result_evidence_multi_agent_review_plan(
            data,
            include_low_priority=include_low_priority,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid result evidence multi-agent review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    plan_data = plan.to_dict()
    markdown = plan.to_markdown()

    table = Table(title="Result Evidence Multi-Agent Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Ranking file", str(ranking_file))
    table.add_row("Candidate plans", str(plan_data["count"]))
    table.add_row("Agent tasks", str(plan_data["total_agent_tasks"]))
    table.add_row("Include low priority", str(include_low_priority))
    table.add_row("Execution", "planning-only; local specialist review planning only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence multi-agent review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result evidence multi-agent review JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local specialist review plans. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-report-assistant")
def case_report_assistant_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    ranking_file: Path | None = typer.Option(
        None,
        "--ranking",
        help="Optional result evidence priority ranking JSON.",
    ),
    multi_agent_review_file: Path | None = typer.Option(
        None,
        "--multi-agent-review",
        help="Optional result evidence multi-agent review JSON.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-report-assistant", "--source", help="Report assistant source label."),
):
    """Build a planning-only report skeleton from local case intelligence artifacts."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    ranking = None
    if ranking_file:
        if not ranking_file.exists():
            console.print(f"[bold red]Priority ranking JSON not found:[/bold red] {ranking_file}")
            raise typer.Exit(code=1)

        try:
            ranking = json.loads(ranking_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid priority ranking JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(ranking, dict):
            console.print("[bold red]Priority ranking JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    multi_agent_review = None
    if multi_agent_review_file:
        if not multi_agent_review_file.exists():
            console.print(f"[bold red]Multi-agent review JSON not found:[/bold red] {multi_agent_review_file}")
            raise typer.Exit(code=1)

        try:
            multi_agent_review = json.loads(multi_agent_review_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid multi-agent review JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(multi_agent_review, dict):
            console.print("[bold red]Multi-agent review JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        draft = build_case_report_assistant_draft(
            case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case report assistant input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    draft_data = draft.to_dict()

    table = Table(title="Case-to-Report Assistant")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Affected endpoints", str(len(draft.affected_endpoints)))
    table.add_row("Title candidates", str(len(draft.title_candidates)))
    table.add_row("Readiness", draft.readiness)
    table.add_row("Execution", "planning-only; local report skeleton only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(draft.markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case report assistant Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case report assistant JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(draft.markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only renders a local report skeleton. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-context")
def case_chat_context_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer from multiple artifacts."),
    ranking_file: Path | None = typer.Option(
        None,
        "--ranking",
        help="Optional result evidence priority ranking JSON.",
    ),
    multi_agent_review_file: Path | None = typer.Option(
        None,
        "--multi-agent-review",
        help="Optional result evidence multi-agent review JSON.",
    ),
    report_assistant_file: Path | None = typer.Option(
        None,
        "--report-assistant",
        help="Optional case-report-assistant JSON.",
    ),
    session_file: Path | None = typer.Option(
        None,
        "--session-file",
        help="Optional local case-chat session JSON.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-case-chat-context", "--source", help="Context chat source label."),
):
    """Answer a stronger local research question from multiple case artifacts."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")
    session = load_optional_json(session_file, "Case chat session")

    try:
        answer = answer_case_context_question(
            case_summary,
            question,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
            session=session,
            source=source,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat context input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    answer_data = answer.to_dict()

    table = Table(title="Strong Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", answer.intent)
    table.add_row("Included artifacts", ", ".join(answer.included_artifacts))
    table.add_row("Cited endpoints", str(len(answer.cited_endpoints)))
    table.add_row("Next actions", str(len(answer.next_actions)))
    table.add_row("Execution", "planning-only; local multi-artifact chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(answer.answer)

    if answer.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in answer.next_actions:
            console.print(f"- {item}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(answer_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat context JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local case artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("chat-context-router")
def chat_context_router_command(
    artifact_file: Path = typer.Argument(..., help="Path to a local result evidence artifact JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
    source: str = typer.Option("result-evidence-chat-context-router", "--source", help="Router source label."),
):
    """Route a local artifact to supported chat/review commands and questions."""
    if not artifact_file.exists():
        console.print(f"[bold red]Artifact JSON not found:[/bold red] {artifact_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(artifact_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid artifact JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Artifact JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        route = route_chat_context(data, source=source)
    except ValueError as exc:
        console.print(f"[bold red]Invalid chat context router input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    route_data = route.to_dict()
    markdown = route.to_markdown()

    table = Table(title="Chat Context Router")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Artifact", str(artifact_file))
    table.add_row("Artifact kind", route.artifact_kind)
    table.add_row("Recommended command", route.recommended_command)
    table.add_row("Supported questions", str(len(route.supported_questions)))
    table.add_row("Execution", "planning-only; local artifact routing only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved chat context route Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(route_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved chat context route JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only routes local artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-grounded")
def case_chat_grounded_command(
    case_summary_file: Path = typer.Argument(..., help="Path to result evidence case summary JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Local research question to answer with grounding snippets."),
    ranking_file: Path | None = typer.Option(None, "--ranking", help="Optional result evidence priority ranking JSON."),
    multi_agent_review_file: Path | None = typer.Option(None, "--multi-agent-review", help="Optional multi-agent review JSON."),
    report_assistant_file: Path | None = typer.Option(None, "--report-assistant", help="Optional report assistant JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Answer from local case artifacts and include deterministic grounding snippets."""
    if not case_summary_file.exists():
        console.print(f"[bold red]Case summary JSON not found:[/bold red] {case_summary_file}")
        raise typer.Exit(code=1)

    try:
        case_summary = json.loads(case_summary_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case summary JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_summary, dict):
        console.print("[bold red]Case summary JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")

    try:
        answer = answer_case_context_question(
            case_summary,
            question,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
        )
        grounded = build_grounded_answer(
            answer=answer.answer,
            intent=answer.intent,
            cited_endpoints=answer.cited_endpoints,
            next_actions=answer.next_actions,
            case_summary=case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid grounded case chat input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    grounded_data = grounded.to_dict()

    table = Table(title="Grounded Local Research Chat")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case summary", str(case_summary_file))
    table.add_row("Intent", grounded.intent)
    table.add_row("Cited endpoints", str(len(grounded.cited_endpoints)))
    table.add_row("Grounding snippets", str(len(grounded.grounding)))
    table.add_row("Execution", "planning-only; local grounded chat only")
    console.print(table)

    console.print()
    console.print("[bold]Answer[/bold]")
    console.print(grounded.answer)

    if grounded.grounding:
        console.print()
        console.print("[bold]Grounding[/bold]")
        for snippet in grounded.grounding[:12]:
            console.print(f"- {snippet.artifact}:{snippet.path} = {snippet.value}")

    if grounded.next_actions:
        console.print()
        console.print("[bold]Next actions[/bold]")
        for item in grounded.next_actions:
            console.print(f"- {item}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(grounded_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved grounded case chat JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only answers from local artifacts and local snippets. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-memory-build")
def case_memory_build_command(
    case_summary_file: Path | None = typer.Option(None, "--case-summary", help="Optional result evidence case summary JSON."),
    ranking_file: Path | None = typer.Option(None, "--ranking", help="Optional result evidence priority ranking JSON."),
    multi_agent_review_file: Path | None = typer.Option(None, "--multi-agent-review", help="Optional multi-agent review JSON."),
    report_assistant_file: Path | None = typer.Option(None, "--report-assistant", help="Optional report assistant JSON."),
    grounded_answer_file: Path | None = typer.Option(None, "--grounded-answer", help="Optional grounded answer JSON."),
    session_file: Path | None = typer.Option(None, "--session-file", help="Optional case-chat session JSON."),
    output_file: Path = typer.Option(..., "--output-file", "--output", help="Path to write case memory JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional Markdown output path."),
):
    """Build a local multi-artifact case memory JSON file."""
    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    case_summary = load_optional_json(case_summary_file, "Case summary")
    ranking = load_optional_json(ranking_file, "Priority ranking")
    multi_agent_review = load_optional_json(multi_agent_review_file, "Multi-agent review")
    report_assistant = load_optional_json(report_assistant_file, "Report assistant")
    grounded_answer = load_optional_json(grounded_answer_file, "Grounded answer")
    session = load_optional_json(session_file, "Case chat session")

    try:
        memory = build_result_evidence_case_memory(
            case_summary=case_summary,
            ranking=ranking,
            multi_agent_review=multi_agent_review,
            report_assistant=report_assistant,
            grounded_answer=grounded_answer,
            session=session,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case memory input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    memory_data = memory.to_dict()
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(memory_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    table = Table(title="Multi-Artifact Case Memory")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Output file", str(output_file))
    table.add_row("Top endpoint", memory.top_endpoint)
    table.add_row("Cited endpoints", str(len(memory.cited_endpoints)))
    table.add_row("Open next actions", str(len(memory.open_next_actions)))
    table.add_row("Missing evidence", str(len(memory.missing_evidence)))
    table.add_row("Execution", "planning-only; local case memory build only")
    console.print(table)
    console.print(f"[bold green]Saved case memory JSON:[/bold green] {output_file}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(memory.to_markdown() + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case memory Markdown:[/bold green] {markdown_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local case memory from local artifacts. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-prompt-package")
def case_chat_prompt_package_command(
    case_memory_file: Path = typer.Option(..., "--case-memory", help="Path to result evidence case memory JSON."),
    question: str = typer.Option(..., "--question", "-q", help="Question to package for optional LLM review."),
    grounded_answer_file: Path | None = typer.Option(None, "--grounded-answer", help="Optional grounded answer JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a safe reviewable LLM prompt package from local case-chat artifacts without calling a provider."""
    if not case_memory_file.exists():
        console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
        raise typer.Exit(code=1)

    try:
        case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(case_memory, dict):
        console.print("[bold red]Case memory JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    grounded_answer = None
    if grounded_answer_file:
        if not grounded_answer_file.exists():
            console.print(f"[bold red]Grounded answer JSON not found:[/bold red] {grounded_answer_file}")
            raise typer.Exit(code=1)

        try:
            grounded_answer = json.loads(grounded_answer_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid grounded answer JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(grounded_answer, dict):
            console.print("[bold red]Grounded answer JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        package = build_case_chat_prompt_package(
            case_memory=case_memory,
            question=question,
            grounded_answer=grounded_answer,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat prompt package input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    package_data = package.to_dict()
    markdown = render_case_chat_prompt_package_markdown(package)

    table = Table(title="Case Chat Prompt Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Case memory", str(case_memory_file))
    table.add_row("Question", package.question)
    table.add_row("Artifact kinds", ", ".join(package.artifact_kinds))
    table.add_row("Redaction applied", str(package.prompt_package.redaction_applied))
    table.add_row("Provider execution", "false")
    table.add_row("Execution", "planning-only; local prompt packaging only")
    console.print(table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat prompt Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(package_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat prompt JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local reviewable prompt package. "
        "It does not call LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-gate")
def case_chat_provider_gate_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to case-chat prompt package JSON."),
    provider_name: str = typer.Option("disabled", "--provider", help="Future LLM provider name. Current default is disabled."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Check the local provider gate for a case-chat prompt package without calling any provider."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        gate = build_case_chat_provider_gate(
            data,
            provider_name=provider_name,
            allow_provider_execution=allow_provider_execution,
            require_prompt_audit_pass=require_prompt_audit_pass,
            model=model,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat provider gate input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    gate_data = gate.to_dict()
    markdown = gate.to_markdown()

    table = Table(title="Case Chat Provider Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", gate.provider_name)
    table.add_row("Allowed", str(gate.allowed))
    table.add_row("Audit status", gate.audit_status)
    table.add_row("Reason", gate.reason)
    table.add_row("Provider execution performed", "false")
    console.print(table)

    if gate.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in gate.required_actions:
            console.print(f"- {action}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only checks a local provider gate. "
        "It does not call LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-dry-run")
def case_chat_provider_dry_run_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to case-chat prompt package JSON."),
    provider_name: str = typer.Option("disabled", "--provider", help="Future LLM provider name. Current default is disabled."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a real provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Dry-run the local prompt audit, provider gate, and disabled provider stub."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        dry_run = build_case_chat_provider_dry_run(
            data,
            provider_name=provider_name,
            allow_provider_execution=allow_provider_execution,
            require_prompt_audit_pass=require_prompt_audit_pass,
            model=model,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid case chat provider dry-run input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    dry_run_data = dry_run.to_dict()
    markdown = dry_run.to_markdown()

    table = Table(title="Case Chat Provider Dry Run")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", dry_run.provider_name)
    table.add_row("Audit status", dry_run.audit_status)
    table.add_row("Gate allowed", str(dry_run.gate_allowed))
    table.add_row("Gate reason", dry_run.gate_reason)
    table.add_row("Disabled provider status", dry_run.disabled_provider_status)
    table.add_row("Provider execution performed", "false")
    console.print(table)

    if dry_run.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in dry_run.required_actions:
            console.print(f"- {action}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider dry-run Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(dry_run_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved case chat provider dry-run JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only performs a local dry-run. "
        "It does not call real LLM providers, send requests, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-result-import")
def case_chat_provider_result_import_command(
    provider_result_file: Path = typer.Option(..., "--provider-result", help="Path to manually saved provider output text."),
    prompt_package_file: Path = typer.Option(..., "--prompt-package", help="Path to case-chat prompt package JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Import manually saved provider output as an untrusted local suggestion."""
    if not provider_result_file.exists():
        console.print(f"[bold red]Provider result text not found:[/bold red] {provider_result_file}")
        raise typer.Exit(code=1)

    if not prompt_package_file.exists():
        console.print(f"[bold red]Case chat prompt package JSON not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    provider_output = provider_result_file.read_text(encoding="utf-8")

    try:
        prompt_package = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid case chat prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(prompt_package, dict):
        console.print("[bold red]Case chat prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        imported = import_case_chat_provider_result(provider_output, prompt_package)
    except ValueError as exc:
        console.print(f"[bold red]Invalid provider result import input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    imported_data = imported.to_dict()
    markdown = imported.to_markdown()

    table = Table(title="Imported Case Chat Provider Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider result", str(provider_result_file))
    table.add_row("Prompt package", str(prompt_package_file))
    table.add_row("Suggested actions", str(len(imported.suggested_actions)))
    table.add_row("Warning flags", str(len(imported.warning_flags)))
    table.add_row("Untrusted suggestion", "true")
    table.add_row("Provider execution by Blackhole", "false")
    console.print(table)

    if imported.warning_flags:
        console.print("[bold yellow]Warning flags:[/bold yellow]")
        for flag in imported.warning_flags:
            console.print(f"- {flag}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved imported provider result Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(imported_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved imported provider result JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only imports local provider output as an untrusted suggestion. "
        "It does not call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-provider-result-review")
def case_chat_provider_result_review_command(
    imported_result_file: Path = typer.Option(..., "--imported-result", help="Path to imported provider result JSON."),
    case_memory_file: Path | None = typer.Option(None, "--case-memory", help="Optional case memory JSON."),
    grounded_answer_file: Path | None = typer.Option(None, "--grounded-answer", help="Optional grounded answer JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review an imported provider result against local evidence artifacts."""
    if not imported_result_file.exists():
        console.print(f"[bold red]Imported provider result JSON not found:[/bold red] {imported_result_file}")
        raise typer.Exit(code=1)

    try:
        imported_result = json.loads(imported_result_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid imported provider result JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(imported_result, dict):
        console.print("[bold red]Imported provider result JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    def load_optional_json(path: Path | None, label: str) -> dict | None:
        if path is None:
            return None

        if not path.exists():
            console.print(f"[bold red]{label} JSON not found:[/bold red] {path}")
            raise typer.Exit(code=1)

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid {label} JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(data, dict):
            console.print(f"[bold red]{label} JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

        return data

    case_memory = load_optional_json(case_memory_file, "Case memory")
    grounded_answer = load_optional_json(grounded_answer_file, "Grounded answer")

    try:
        review = review_case_chat_provider_result(
            imported_result,
            case_memory=case_memory,
            grounded_answer=grounded_answer,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid provider result review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    review_data = review.to_dict()
    markdown = review.to_markdown()

    table = Table(title="Provider Suggestion Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Imported result", str(imported_result_file))
    table.add_row("Recommendation", review.recommendation)
    table.add_row("Reviewed actions", str(len(review.reviewed_actions)))
    table.add_row("Warning flags", str(len(review.warning_flags)))
    table.add_row("Unsupported claims", str(len(review.unsupported_claims)))
    table.add_row("Untrusted suggestion", "true")
    table.add_row("Provider execution by Blackhole", "false")
    console.print(table)

    if review.warning_flags:
        console.print("[bold yellow]Warning flags:[/bold yellow]")
        for flag in review.warning_flags:
            console.print(f"- {flag}")

    if review.unsupported_claims:
        console.print("[bold yellow]Unsupported claims:[/bold yellow]")
        for claim in review.unsupported_claims:
            console.print(f"- {claim}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved provider result review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved provider result review JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews imported provider output as untrusted text. "
        "It does not call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-suggestion-action-plan")
def case_chat_suggestion_action_plan_command(
    provider_review_file: Path = typer.Option(..., "--provider-review", help="Path to provider result review JSON."),
    case_memory_file: Path | None = typer.Option(None, "--case-memory", help="Optional case memory JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a safe manual action plan from a reviewed provider suggestion."""
    if not provider_review_file.exists():
        console.print(f"[bold red]Provider result review JSON not found:[/bold red] {provider_review_file}")
        raise typer.Exit(code=1)

    try:
        provider_review = json.loads(provider_review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid provider result review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(provider_review, dict):
        console.print("[bold red]Provider result review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    case_memory = None
    if case_memory_file:
        if not case_memory_file.exists():
            console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
            raise typer.Exit(code=1)

        try:
            case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(case_memory, dict):
            console.print("[bold red]Case memory JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        plan = build_provider_suggestion_action_plan(
            provider_review,
            case_memory=case_memory,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid suggestion action plan input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    plan_data = plan.to_dict()
    markdown = plan.to_markdown()

    table = Table(title="Provider Suggestion Action Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider review", str(provider_review_file))
    table.add_row("Recommendation", plan.recommendation)
    table.add_row("Approved actions", str(len(plan.approved_actions)))
    table.add_row("Needs evidence", str(len(plan.evidence_needed_actions)))
    table.add_row("Rejected actions", str(len(plan.rejected_actions)))
    table.add_row("Missing evidence", str(len(plan.missing_evidence)))
    table.add_row("Provider execution by Blackhole", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if plan.report_guardrails:
        console.print("[bold yellow]Report guardrails:[/bold yellow]")
        for guardrail in plan.report_guardrails:
            console.print(f"- {guardrail}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved suggestion action plan Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved suggestion action plan JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only turns reviewed provider suggestions into a local manual action plan. "
        "It does not call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-action-plan-apply-preview")
def case_chat_action_plan_apply_preview_command(
    action_plan_file: Path = typer.Option(..., "--action-plan", help="Path to suggestion action plan JSON."),
    case_memory_file: Path | None = typer.Option(None, "--case-memory", help="Optional case memory JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Preview safe local case memory / research state updates from an action plan."""
    if not action_plan_file.exists():
        console.print(f"[bold red]Suggestion action plan JSON not found:[/bold red] {action_plan_file}")
        raise typer.Exit(code=1)

    try:
        action_plan = json.loads(action_plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid suggestion action plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(action_plan, dict):
        console.print("[bold red]Suggestion action plan JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    case_memory = None
    if case_memory_file:
        if not case_memory_file.exists():
            console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
            raise typer.Exit(code=1)

        try:
            case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(case_memory, dict):
            console.print("[bold red]Case memory JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        preview = build_provider_suggestion_action_plan_apply_preview(
            action_plan,
            case_memory=case_memory,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid action plan apply preview input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    preview_data = preview.to_dict()
    markdown = preview.to_markdown()

    table = Table(title="Action Plan Apply Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Action plan", str(action_plan_file))
    table.add_row("Recommendation", preview.recommendation)
    table.add_row("Case memory update previews", str(len(preview.case_memory_updates)))
    table.add_row("Research state update previews", str(len(preview.research_state_updates)))
    table.add_row("Blocked updates", str(len(preview.blocked_updates)))
    table.add_row("Missing evidence", str(len(preview.missing_evidence)))
    table.add_row("State mutation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if preview.report_guardrails:
        console.print("[bold yellow]Report guardrails:[/bold yellow]")
        for guardrail in preview.report_guardrails:
            console.print(f"- {guardrail}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved action plan apply preview Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(preview_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved action plan apply preview JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only previews local case memory / research state updates. "
        "It does not write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-action-plan-apply-preview-review")
def case_chat_action_plan_apply_preview_review_command(
    apply_preview_file: Path = typer.Option(..., "--apply-preview", help="Path to action plan apply preview JSON."),
    case_memory_file: Path | None = typer.Option(None, "--case-memory", help="Optional case memory JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review an action plan apply preview before any future state write."""
    if not apply_preview_file.exists():
        console.print(f"[bold red]Action plan apply preview JSON not found:[/bold red] {apply_preview_file}")
        raise typer.Exit(code=1)

    try:
        apply_preview = json.loads(apply_preview_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid action plan apply preview JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(apply_preview, dict):
        console.print("[bold red]Action plan apply preview JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    case_memory = None
    if case_memory_file:
        if not case_memory_file.exists():
            console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
            raise typer.Exit(code=1)

        try:
            case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(case_memory, dict):
            console.print("[bold red]Case memory JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        review = build_action_plan_apply_preview_review(
            apply_preview,
            case_memory=case_memory,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid action plan apply preview review input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    review_data = review.to_dict()
    markdown = review.to_markdown()

    table = Table(title="Action Plan Apply Preview Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Apply preview", str(apply_preview_file))
    table.add_row("Recommendation", review.recommendation)
    table.add_row("Duplicate candidates", str(len(review.duplicate_update_candidates)))
    table.add_row("Blocked actions", str(len(review.blocked_action_findings)))
    table.add_row("Evidence gaps", str(len(review.evidence_gap_findings)))
    table.add_row("Unsafe update risks", str(len(review.unsafe_update_findings)))
    table.add_row("Overclaim risks", str(len(review.overclaim_risks)))
    table.add_row("Safe planning notes", str(len(review.safe_planning_notes)))
    table.add_row("State mutation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if review.report_guardrails:
        console.print("[bold yellow]Report guardrails:[/bold yellow]")
        for guardrail in review.report_guardrails:
            console.print(f"- {guardrail}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved action plan apply preview review Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(review_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved action plan apply preview review JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local apply preview. "
        "It does not write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-reviewed-apply-packet")
def case_chat_reviewed_apply_packet_command(
    apply_preview_review_file: Path = typer.Option(..., "--apply-preview-review", help="Path to apply preview review JSON."),
    case_memory_file: Path | None = typer.Option(None, "--case-memory", help="Optional case memory JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a final human approval packet from an apply-preview review."""
    if not apply_preview_review_file.exists():
        console.print(f"[bold red]Action plan apply preview review JSON not found:[/bold red] {apply_preview_review_file}")
        raise typer.Exit(code=1)

    try:
        apply_preview_review = json.loads(apply_preview_review_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid action plan apply preview review JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(apply_preview_review, dict):
        console.print("[bold red]Action plan apply preview review JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    case_memory = None
    if case_memory_file:
        if not case_memory_file.exists():
            console.print(f"[bold red]Case memory JSON not found:[/bold red] {case_memory_file}")
            raise typer.Exit(code=1)

        try:
            case_memory = json.loads(case_memory_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            console.print(f"[bold red]Invalid case memory JSON:[/bold red] {exc}")
            raise typer.Exit(code=2)

        if not isinstance(case_memory, dict):
            console.print("[bold red]Case memory JSON must be an object.[/bold red]")
            raise typer.Exit(code=2)

    try:
        packet = build_reviewed_apply_packet(
            apply_preview_review,
            case_memory=case_memory,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid reviewed apply packet input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    packet_data = packet.to_dict()
    markdown = packet.to_markdown()

    table = Table(title="Reviewed Apply Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Apply preview review", str(apply_preview_review_file))
    table.add_row("Recommendation", packet.recommendation)
    table.add_row("Approved planning updates", str(len(packet.approved_planning_updates)))
    table.add_row("Duplicate updates", str(len(packet.duplicate_updates)))
    table.add_row("Blocked updates", str(len(packet.blocked_updates)))
    table.add_row("Evidence gaps", str(len(packet.evidence_gaps)))
    table.add_row("Unsafe / rejected items", str(len(packet.unsafe_or_rejected_items)))
    table.add_row("Overclaim risks", str(len(packet.overclaim_risks)))
    table.add_row("Human approval required", "true")
    table.add_row("State mutation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if packet.human_approval_checklist:
        console.print("[bold yellow]Human approval checklist:[/bold yellow]")
        for item in packet.human_approval_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved reviewed apply packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(packet_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved reviewed apply packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a human approval packet. "
        "It does not write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-reviewed-apply-packet-export-bundle")
def case_chat_reviewed_apply_packet_export_bundle_command(
    reviewed_apply_packet_file: Path = typer.Option(..., "--reviewed-apply-packet", help="Path to reviewed apply packet JSON."),
    artifact_files: list[Path] = typer.Option([], "--artifact", help="Optional local artifact path to reference in the bundle."),
    artifact_role: str = typer.Option("supporting-artifact", "--artifact-role", help="Role to assign to included artifacts."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local export bundle manifest from a reviewed apply packet."""
    if not reviewed_apply_packet_file.exists():
        console.print(f"[bold red]Reviewed apply packet JSON not found:[/bold red] {reviewed_apply_packet_file}")
        raise typer.Exit(code=1)

    try:
        reviewed_apply_packet = json.loads(reviewed_apply_packet_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid reviewed apply packet JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(reviewed_apply_packet, dict):
        console.print("[bold red]Reviewed apply packet JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    artifact_refs = [
        build_bundle_artifact_from_path(path, role=artifact_role).to_dict()
        for path in artifact_files
    ]

    try:
        bundle = build_reviewed_apply_packet_export_bundle(
            reviewed_apply_packet,
            artifact_refs=artifact_refs,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid reviewed apply packet export bundle input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    bundle_data = bundle.to_dict()
    markdown = bundle.to_markdown()

    table = Table(title="Reviewed Apply Packet Export Bundle")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Reviewed apply packet", str(reviewed_apply_packet_file))
    table.add_row("Bundle ID", bundle.bundle_id)
    table.add_row("Recommendation", bundle.recommendation)
    table.add_row("Approved planning updates", str(bundle.packet_counts["approved_planning_updates"]))
    table.add_row("Duplicate updates", str(bundle.packet_counts["duplicate_updates"]))
    table.add_row("Blocked updates", str(bundle.packet_counts["blocked_updates"]))
    table.add_row("Evidence gaps", str(bundle.packet_counts["evidence_gaps"]))
    table.add_row("Unsafe / rejected items", str(bundle.packet_counts["unsafe_or_rejected_items"]))
    table.add_row("Overclaim risks", str(bundle.packet_counts["overclaim_risks"]))
    table.add_row("Included artifacts", str(len(bundle.included_artifacts)))
    table.add_row("Human approval required", "true")
    table.add_row("State mutation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if bundle.human_review_checklist:
        console.print("[bold yellow]Human review checklist:[/bold yellow]")
        for item in bundle.human_review_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved reviewed apply packet export bundle Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(bundle_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved reviewed apply packet export bundle JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local export bundle manifest. "
        "It does not write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-export-bundle-review-gate")
def case_chat_export_bundle_review_gate_command(
    export_bundle_file: Path = typer.Option(..., "--export-bundle", help="Path to reviewed apply packet export bundle JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review an export bundle before report or future workflow use."""
    if not export_bundle_file.exists():
        console.print(f"[bold red]Export bundle JSON not found:[/bold red] {export_bundle_file}")
        raise typer.Exit(code=1)

    try:
        export_bundle = json.loads(export_bundle_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid export bundle JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(export_bundle, dict):
        console.print("[bold red]Export bundle JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        review_gate = build_export_bundle_review_gate(export_bundle)
    except ValueError as exc:
        console.print(f"[bold red]Invalid export bundle review gate input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    gate_data = review_gate.to_dict()
    markdown = review_gate.to_markdown()

    table = Table(title="Export Bundle Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Export bundle", str(export_bundle_file))
    table.add_row("Recommendation", review_gate.recommendation)
    table.add_row("Missing artifacts", str(len(review_gate.missing_artifact_findings)))
    table.add_row("Artifact integrity findings", str(len(review_gate.artifact_integrity_findings)))
    table.add_row("Packet risk findings", str(len(review_gate.packet_risk_findings)))
    table.add_row("Evidence gap findings", str(len(review_gate.evidence_gap_findings)))
    table.add_row("Overclaim findings", str(len(review_gate.overclaim_findings)))
    table.add_row("Safety findings", str(len(review_gate.safety_findings)))
    table.add_row("Approved review notes", str(len(review_gate.approved_review_notes)))
    table.add_row("Human approval required", "true")
    table.add_row("State mutation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if review_gate.human_review_checklist:
        console.print("[bold yellow]Human review checklist:[/bold yellow]")
        for item in review_gate.human_review_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved export bundle review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved export bundle review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local export bundle. "
        "It does not write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-export-bundle-report-readiness-review")
def case_chat_export_bundle_report_readiness_review_command(
    review_gate_file: Path = typer.Option(..., "--review-gate", help="Path to export bundle review gate JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review whether a gated export bundle can support a human-written report."""
    if not review_gate_file.exists():
        console.print(f"[bold red]Export bundle review gate JSON not found:[/bold red] {review_gate_file}")
        raise typer.Exit(code=1)

    try:
        review_gate = json.loads(review_gate_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid export bundle review gate JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(review_gate, dict):
        console.print("[bold red]Export bundle review gate JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        readiness = build_export_bundle_report_readiness_review(review_gate)
    except ValueError as exc:
        console.print(f"[bold red]Invalid export bundle report readiness input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    readiness_data = readiness.to_dict()
    markdown = readiness.to_markdown()

    table = Table(title="Export Bundle Report Readiness Review")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Review gate", str(review_gate_file))
    table.add_row("Recommendation", readiness.recommendation)
    table.add_row("Report support notes", str(len(readiness.report_ready_support_notes)))
    table.add_row("Report blockers", str(len(readiness.report_blockers)))
    table.add_row("Missing evidence", str(len(readiness.missing_evidence)))
    table.add_row("Unsafe / rejected items", str(len(readiness.unsafe_or_rejected_items)))
    table.add_row("Artifact problems", str(len(readiness.artifact_problems)))
    table.add_row("Overclaim risks", str(len(readiness.overclaim_risks)))
    table.add_row("Safety blockers", str(len(readiness.safety_blockers)))
    table.add_row("Report generation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if readiness.final_report_readiness_checklist:
        console.print("[bold yellow]Final report-readiness checklist:[/bold yellow]")
        for item in readiness.final_report_readiness_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved export bundle report readiness Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(readiness_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved export bundle report readiness JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews report readiness. "
        "It does not generate reports, write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-report-readiness-finding-draft-packet")
def case_chat_report_readiness_finding_draft_packet_command(
    report_readiness_file: Path = typer.Option(..., "--report-readiness", help="Path to export bundle report readiness JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a safe human report-draft packet from report-readiness review JSON."""
    if not report_readiness_file.exists():
        console.print(f"[bold red]Export bundle report readiness JSON not found:[/bold red] {report_readiness_file}")
        raise typer.Exit(code=1)

    try:
        report_readiness = json.loads(report_readiness_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid export bundle report readiness JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(report_readiness, dict):
        console.print("[bold red]Export bundle report readiness JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        packet = build_report_readiness_finding_draft_packet(report_readiness)
    except ValueError as exc:
        console.print(f"[bold red]Invalid report readiness finding draft packet input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    packet_data = packet.to_dict()
    markdown = packet.to_markdown()

    table = Table(title="Report Readiness Finding Draft Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Report readiness", str(report_readiness_file))
    table.add_row("Recommendation", packet.recommendation)
    table.add_row("Title candidates", str(len(packet.title_candidates)))
    table.add_row("Evidence checklist", str(len(packet.evidence_checklist)))
    table.add_row("Reproduction placeholders", str(len(packet.reproduction_plan_placeholders)))
    table.add_row("Impact guardrails", str(len(packet.impact_wording_guardrails)))
    table.add_row("Severity guardrails", str(len(packet.severity_wording_guardrails)))
    table.add_row("Blocked claims", str(len(packet.blocked_claims)))
    table.add_row("Do-not-claim-yet items", str(len(packet.do_not_claim_yet)))
    table.add_row("Report generation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if packet.final_human_writing_checklist:
        console.print("[bold yellow]Final human writing checklist:[/bold yellow]")
        for item in packet.final_human_writing_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved report readiness finding draft packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(packet_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved report readiness finding draft packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a report-draft packet for human writing. "
        "It does not generate reports, submit reports, write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-finding-draft-packet-review-gate")
def case_chat_finding_draft_packet_review_gate_command(
    finding_draft_packet_file: Path = typer.Option(..., "--finding-draft-packet", help="Path to finding draft packet JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a finding draft packet before human report writing."""
    if not finding_draft_packet_file.exists():
        console.print(f"[bold red]Finding draft packet JSON not found:[/bold red] {finding_draft_packet_file}")
        raise typer.Exit(code=1)

    try:
        finding_draft_packet = json.loads(finding_draft_packet_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid finding draft packet JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(finding_draft_packet, dict):
        console.print("[bold red]Finding draft packet JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        review_gate = build_finding_draft_packet_review_gate(finding_draft_packet)
    except ValueError as exc:
        console.print(f"[bold red]Invalid finding draft packet review gate input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    gate_data = review_gate.to_dict()
    markdown = review_gate.to_markdown()

    table = Table(title="Finding Draft Packet Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Finding draft packet", str(finding_draft_packet_file))
    table.add_row("Recommendation", review_gate.recommendation)
    table.add_row("Title findings", str(len(review_gate.title_quality_findings)))
    table.add_row("Evidence findings", str(len(review_gate.evidence_checklist_findings)))
    table.add_row("Reproduction findings", str(len(review_gate.reproduction_gap_findings)))
    table.add_row("Wording findings", str(len(review_gate.wording_guardrail_findings)))
    table.add_row("Blocked claims", str(len(review_gate.blocked_claim_findings)))
    table.add_row("Do-not-claim findings", str(len(review_gate.do_not_claim_findings)))
    table.add_row("Safety findings", str(len(review_gate.safety_findings)))
    table.add_row("Approved writing support", str(len(review_gate.approved_writing_support)))
    table.add_row("Report generation", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if review_gate.final_review_checklist:
        console.print("[bold yellow]Final review checklist:[/bold yellow]")
        for item in review_gate.final_review_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved finding draft packet review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved finding draft packet review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a finding draft packet for human writing. "
        "It does not generate reports, submit reports, write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-human-report-skeleton-packet")
def case_chat_human_report_skeleton_packet_command(
    finding_draft_review_gate_file: Path = typer.Option(..., "--finding-draft-review-gate", help="Path to finding draft packet review gate JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a safe human report skeleton packet from a finding draft review gate."""
    if not finding_draft_review_gate_file.exists():
        console.print(f"[bold red]Finding draft packet review gate JSON not found:[/bold red] {finding_draft_review_gate_file}")
        raise typer.Exit(code=1)

    try:
        review_gate = json.loads(finding_draft_review_gate_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid finding draft packet review gate JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(review_gate, dict):
        console.print("[bold red]Finding draft packet review gate JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        packet = build_human_report_skeleton_packet(review_gate)
    except ValueError as exc:
        console.print(f"[bold red]Invalid human report skeleton packet input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    packet_data = packet.to_dict()
    markdown = packet.to_markdown()

    table = Table(title="Human Report Skeleton Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Finding draft review gate", str(finding_draft_review_gate_file))
    table.add_row("Recommendation", packet.recommendation)
    table.add_row("Summary status", packet.summary.status)
    table.add_row("Impact status", packet.impact.status)
    table.add_row("Steps status", packet.steps_to_reproduce.status)
    table.add_row("Evidence status", packet.evidence.status)
    table.add_row("Severity status", packet.severity_rationale.status)
    table.add_row("Blocked claims status", packet.blocked_claims_do_not_claim.status)
    table.add_row("Final report generated", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if packet.human_final_writing_checklist:
        console.print("[bold yellow]Human final-writing checklist:[/bold yellow]")
        for item in packet.human_final_writing_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human report skeleton packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(packet_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human report skeleton packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a report skeleton packet for human writing. "
        "It does not generate reports, submit reports, write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("case-chat-human-report-skeleton-review-gate")
def case_chat_human_report_skeleton_review_gate_command(
    human_report_skeleton_file: Path = typer.Option(..., "--human-report-skeleton", help="Path to human report skeleton packet JSON."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a human report skeleton packet before report writing."""
    if not human_report_skeleton_file.exists():
        console.print(f"[bold red]Human report skeleton packet JSON not found:[/bold red] {human_report_skeleton_file}")
        raise typer.Exit(code=1)

    try:
        human_report_skeleton = json.loads(human_report_skeleton_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid human report skeleton packet JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(human_report_skeleton, dict):
        console.print("[bold red]Human report skeleton packet JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        review_gate = build_human_report_skeleton_review_gate(human_report_skeleton)
    except ValueError as exc:
        console.print(f"[bold red]Invalid human report skeleton review gate input:[/bold red] {exc}")
        raise typer.Exit(code=2)

    gate_data = review_gate.to_dict()
    markdown = review_gate.to_markdown()

    table = Table(title="Human Report Skeleton Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Human report skeleton", str(human_report_skeleton_file))
    table.add_row("Recommendation", review_gate.recommendation)
    table.add_row("Section completeness findings", str(len(review_gate.section_completeness_findings)))
    table.add_row("Blocker leakage findings", str(len(review_gate.blocker_leakage_findings)))
    table.add_row("Evidence mapping findings", str(len(review_gate.evidence_mapping_findings)))
    table.add_row("Impact/severity findings", str(len(review_gate.impact_severity_findings)))
    table.add_row("Blocked/do-not-claim findings", str(len(review_gate.blocked_do_not_claim_findings)))
    table.add_row("Safety findings", str(len(review_gate.safety_findings)))
    table.add_row("Approved skeleton sections", str(len(review_gate.approved_skeleton_sections)))
    table.add_row("Final report generated", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if review_gate.final_review_checklist:
        console.print("[bold yellow]Final review checklist:[/bold yellow]")
        for item in review_gate.final_review_checklist:
            console.print(f"- [ ] {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human report skeleton review gate Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(gate_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved human report skeleton review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a report skeleton packet for human writing. "
        "It does not generate reports, submit reports, write state, call LLM providers, execute tools, or confirm vulnerabilities automatically."
    )


@app.command("interpret-result")
def interpret_result_command(
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint that was manually validated."),
    observed_status: int | None = typer.Option(None, "--observed-status", help="Observed HTTP status code."),
    expected_status: int | None = typer.Option(None, "--expected-status", help="Expected HTTP status code."),
    observed_body: str = typer.Option("", "--observed-body", help="Short observed response/body note."),
    expected_body: str = typer.Option("", "--expected-body", help="Short expected response/body note."),
    note: str = typer.Option("", "--note", help="Human validation note."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Interpret a manual validation result summary."""
    result = interpret_validation_result(
        endpoint=endpoint,
        observed_status=observed_status,
        expected_status=expected_status,
        observed_body=observed_body,
        expected_body=expected_body,
        note=note,
    )
    data = result.to_dict()

    table = Table(title="Result Interpretation")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Endpoint", endpoint)
    table.add_row("Suggested result", result.suggested_result)
    table.add_row("Confidence", result.confidence)
    table.add_row("Rationale", result.rationale)
    table.add_row("Signals", str(len(result.signals)))
    table.add_row("Execution", "planning-only; no request execution")
    console.print(table)

    signals_table = Table(title="Interpretation Signals")
    signals_table.add_column("#", justify="right")
    signals_table.add_column("Signal")
    signals_table.add_column("Weight", justify="right")
    signals_table.add_column("Reason")

    for index, signal in enumerate(result.signals, start=1):
        signals_table.add_row(
            str(index),
            signal.name,
            str(signal.weight),
            signal.reason,
        )

    console.print(signals_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved result interpretation JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only interprets a human-provided result summary. "
        "It does not send requests, execute tools, call LLM providers, or confirm vulnerabilities automatically."
    )


@app.command("research-state-update")
def research_state_update_command(
    research_state_json: Path = typer.Argument(..., help="Path to research-state JSON."),
    endpoint: str = typer.Option(..., "--endpoint", help="Endpoint to update in the research state."),
    validation_result: str = typer.Option(
        ...,
        "--validation-result",
        help="Manual validation result: supported, rejected, needs-more-evidence, or deprioritize.",
    ),
    note: str = typer.Option("", "--note", help="Optional human validation note."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the update plan.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured update plan.",
    ),
):
    """Build a planning-only research-state update plan."""
    if not research_state_json.exists():
        console.print(f"[bold red]Research-state JSON not found:[/bold red] {research_state_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_state_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research-state JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research-state JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    try:
        plan = build_research_state_update_plan(
            data,
            endpoint=endpoint,
            validation_result=validation_result,
            note=note,
        )
    except ValueError as exc:
        console.print(f"[bold red]Invalid validation result:[/bold red] {exc}")
        raise typer.Exit(code=2)

    markdown = render_research_state_update_plan_markdown(plan)
    plan_data = plan.to_dict()

    summary = Table(title="Research State Update Plan")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", plan.target_name)
    summary.add_row("Endpoint", plan.endpoint)
    summary.add_row("Validation result", plan.validation_result)
    summary.add_row("Actions", str(len(plan.actions)))
    summary.add_row("Human review required", str(plan.required_human_review))
    summary.add_row("Execution", "planning-only; no state mutation, tool execution, network, browser, Kali, shell, or LLM execution")
    console.print(summary)

    actions_table = Table(title="Proposed State Updates")
    actions_table.add_column("#", justify="right")
    actions_table.add_column("Path")
    actions_table.add_column("Old")
    actions_table.add_column("New")
    actions_table.add_column("Reason")

    for index, action in enumerate(plan.actions, start=1):
        actions_table.add_row(
            str(index),
            escape(action.path),
            escape(str(action.old_value)),
            escape(str(action.new_value)),
            escape(action.reason),
        )

    console.print(actions_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research-state update Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research-state update JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only proposes research-state updates. "
        "It does not mutate files automatically or execute tools."
    )


@app.command("research-state")
def research_state_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the research state summary.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured research state.",
    ),
):
    """Build planning-only research state / case memory from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    state = build_research_state_from_orchestration(data)
    markdown = render_research_state_markdown(state)
    state_data = state.to_dict()

    summary = Table(title="Research State / Case Memory")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", state.target_name)
    summary.add_row("Endpoints", str(state.endpoint_count))
    summary.add_row("Decisions", str(len(state.decisions)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    endpoint_table = Table(title="Research State Endpoints")
    endpoint_table.add_column("#", justify="right")
    endpoint_table.add_column("Endpoint")
    endpoint_table.add_column("Priority")
    endpoint_table.add_column("Triage")
    endpoint_table.add_column("Hypotheses", justify="right")
    endpoint_table.add_column("Artifacts", justify="right")

    for index, endpoint_state in enumerate(state.endpoints, start=1):
        endpoint_table.add_row(
            str(index),
            endpoint_state.endpoint,
            f"{endpoint_state.priority_band}/{endpoint_state.priority_score}",
            endpoint_state.triage_state,
            str(len(endpoint_state.hypotheses)),
            str(len(endpoint_state.artifacts)),
        )

    console.print(endpoint_table)

    decision_table = Table(title="Research State Decisions")
    decision_table.add_column("#", justify="right")
    decision_table.add_column("Decision")
    decision_table.add_column("Status")
    decision_table.add_column("Rationale")

    for index, decision in enumerate(state.decisions, start=1):
        decision_table.add_row(
            str(index),
            decision.name,
            decision.status,
            decision.rationale,
        )

    console.print(decision_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research state Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(state_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research state JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates planning-only case memory. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("validation-runbook")
def validation_runbook_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the validation runbook.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured validation runbook.",
    ),
):
    """Build a planning-only validation runbook from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    runbook = build_validation_runbook(data)
    markdown = render_validation_runbook_markdown(runbook)
    runbook_data = runbook.to_dict()

    summary = Table(title="Validation Runbook")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", runbook.target_name)
    summary.add_row("Endpoint runbooks", str(runbook.endpoint_count))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    endpoint_table = Table(title="Validation Runbook Endpoints")
    endpoint_table.add_column("#", justify="right")
    endpoint_table.add_column("Endpoint")
    endpoint_table.add_column("Priority")
    endpoint_table.add_column("Steps", justify="right")
    endpoint_table.add_column("Approval Steps", justify="right")

    for index, endpoint_runbook in enumerate(runbook.endpoint_runbooks, start=1):
        approval_count = sum(1 for step in endpoint_runbook.steps if step.human_approval_required)
        endpoint_table.add_row(
            str(index),
            endpoint_runbook.endpoint,
            f"{endpoint_runbook.priority_band}/{endpoint_runbook.priority_score}",
            str(len(endpoint_runbook.steps)),
            str(approval_count),
        )

    console.print(endpoint_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved validation runbook Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(runbook_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved validation runbook JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a manual validation runbook. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("report-draft")
def report_draft_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON."),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown file to write the report draft.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON file to write the structured report draft.",
    ),
):
    """Build a planning-only report draft from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    draft = build_report_draft(data)
    markdown = render_report_draft_markdown(draft)
    draft_data = draft.to_dict()

    summary = Table(title="Report Draft")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Title", draft.title)
    summary.add_row("Target", draft.target_name)
    summary.add_row("Endpoints", str(draft.endpoint_count))
    summary.add_row("Sections", str(len(draft.sections)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    section_table = Table(title="Report Draft Sections")
    section_table.add_column("#", justify="right")
    section_table.add_column("Section")

    for index, section in enumerate(draft.sections, start=1):
        section_table.add_row(str(index), section.title)

    console.print(section_table)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved report draft Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(draft_data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved report draft JSON:[/bold green] {json_output}")

    if not output_file and not json_output:
        console.print(markdown)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a report skeleton. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )


@app.command("evidence-workspace")
def evidence_workspace_command(
    orchestration_json: Path = typer.Argument(..., help="Path to orchestration JSON containing evidence requirements."),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        "--out",
        help="Directory where the local evidence workspace should be created.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the workspace manifest without creating files.",
    ),
):
    """Create a local evidence workspace from orchestration JSON."""
    if not orchestration_json.exists():
        console.print(f"[bold red]Orchestration JSON not found:[/bold red] {orchestration_json}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(orchestration_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid orchestration JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Orchestration JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    manifest = build_evidence_workspace_manifest(data, output_dir)
    manifest_data = manifest.to_dict()

    summary = Table(title="Evidence Workspace")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Target", manifest.target_name)
    summary.add_row("Output dir", manifest.workspace_root)
    summary.add_row("Endpoints", str(manifest.endpoint_count))
    summary.add_row("Mode", "dry-run" if dry_run else "write-files")
    summary.add_row("Execution", "local-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    files_table = Table(title="Workspace Files")
    files_table.add_column("#", justify="right")
    files_table.add_column("Path")
    files_table.add_column("Purpose")

    all_files = list(manifest.files)
    for endpoint in manifest.endpoints:
        all_files.extend(endpoint.files)

    for index, file in enumerate(all_files, start=1):
        files_table.add_row(str(index), file.path, file.purpose)

    console.print(files_table)

    if dry_run:
        console.print("[bold yellow]Dry run:[/bold yellow] no files were created.")
    else:
        materialize_evidence_workspace(manifest)
        console.print(f"[bold green]Evidence workspace created:[/bold green] {output_dir}")

    manifest_path = output_dir / "manifest.json"
    console.print(f"[bold]Manifest path:[/bold] {manifest_path}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates local planning files. "
        "It does not send requests, execute shell commands against targets, launch browsers, or call LLM providers."
    )


@app.command("evidence-requirements")
def evidence_requirements_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save evidence requirements JSON.",
    ),
):
    """Build planning-only evidence requirements for endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)
    plan = build_evidence_requirement_plan(endpoint_values)
    data = plan.to_dict()

    summary = Table(title="Evidence Requirements Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Input file", str(input_file))
    summary.add_row("Endpoints", str(plan.endpoint_count))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    requirement_names = sorted({
        requirement.name
        for endpoint_plan in plan.endpoint_plans
        for requirement in endpoint_plan.requirements
    })
    console.print("[bold]Requirement names:[/bold] " + ", ".join(requirement_names))

    for endpoint_plan in plan.endpoint_plans:
        endpoint_table = Table(title=f"Evidence Requirements: {endpoint_plan.endpoint}")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Requirement")
        endpoint_table.add_column("Artifact")
        endpoint_table.add_column("Sensitivity")
        endpoint_table.add_column("Redact")
        endpoint_table.add_column("Approval")

        for index, requirement in enumerate(endpoint_plan.requirements, start=1):
            endpoint_table.add_row(
                str(index),
                requirement.name,
                requirement.artifact_type,
                requirement.sensitivity,
                "YES" if requirement.redaction_required else "NO",
                "YES" if requirement.human_approval_required else "NO",
            )

        console.print(endpoint_table)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only plans evidence collection. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved evidence requirements JSON:[/bold green] {json_output}")


@app.command("attack-surface")
def attack_surface_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save attack surface grouping JSON.",
    ),
):
    """Group endpoints into planning-only attack-surface buckets."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)
    surface = build_attack_surface_map(endpoint_values)
    data = surface.to_dict()

    summary = Table(title="Attack Surface Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Input file", str(input_file))
    summary.add_row("Endpoints", str(surface.endpoint_count))
    summary.add_row("Groups", str(len(surface.groups)))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    group_table = Table(title="Attack Surface Groups")
    group_table.add_column("#", justify="right")
    group_table.add_column("Group")
    group_table.add_column("Count", justify="right")
    group_table.add_column("Max Score", justify="right")
    group_table.add_column("Avg Score", justify="right")
    group_table.add_column("Priority Hint")

    for index, group in enumerate(surface.groups, start=1):
        group_table.add_row(
            str(index),
            group.spec.name,
            str(group.count),
            str(group.max_score),
            str(group.average_score),
            group.spec.priority_hint,
        )

    console.print(group_table)

    for group in surface.groups:
        endpoint_table = Table(title=f"{group.spec.title} ({group.spec.name})")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Score", justify="right")
        endpoint_table.add_column("Band")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(group.endpoints, start=1):
            endpoint_table.add_row(
                str(index),
                str(endpoint.score),
                endpoint.band,
                endpoint.endpoint,
            )

        console.print(endpoint_table)

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only groups endpoint strings. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved attack surface JSON:[/bold green] {json_output}")


@app.command("endpoint-priority")
def endpoint_priority_command(
    endpoint: str = typer.Argument(..., help="Endpoint path or URL to score."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save endpoint priority JSON.",
    ),
):
    """Score one endpoint using planning-only priority heuristics."""
    result = score_endpoint(endpoint)
    data = result.to_dict()

    summary = Table(title="Endpoint Priority Score")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Endpoint", result.endpoint)
    summary.add_row("Normalized path", result.normalized_path)
    summary.add_row("Score", str(result.score))
    summary.add_row("Band", result.band)
    summary.add_row("Categories", ", ".join(result.categories))
    summary.add_row("Execution", "planning-only; no curl, browser, network, or LLM provider execution")
    console.print(summary)

    console.print("[bold]Signal names:[/bold] " + ", ".join(signal.name for signal in result.signals))

    signal_table = Table(title="Priority Signals")
    signal_table.add_column("#", justify="right")
    signal_table.add_column("Signal")
    signal_table.add_column("Points", justify="right")
    signal_table.add_column("Reason")

    for index, signal in enumerate(result.signals, start=1):
        signal_table.add_row(
            str(index),
            signal.name,
            str(signal.points),
            signal.reason,
        )

    console.print(signal_table)

    if result.recommended_next_steps:
        console.print("[bold]Recommended next steps:[/bold]")
        for step in result.recommended_next_steps:
            console.print(f"- {step}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only scores and explains priority. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved endpoint priority JSON:[/bold green] {json_output}")


@app.command("prioritize-endpoints")
def prioritize_endpoints_command(
    input_file: Path = typer.Argument(..., help="Text file containing endpoint paths, URLs, logs, JS, HTML, or HAR-like text."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save prioritized endpoint JSON.",
    ),
):
    """Score and sort endpoints from highest to lowest priority."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    mined = [endpoint.value for endpoint in mine_endpoints(text)]
    line_candidates = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    endpoint_values = sorted(set(mined + line_candidates))
    results = prioritize_endpoints(endpoint_values)
    data = {
        "input_file": str(input_file),
        "endpoint_count": len(results),
        "planning_only": True,
        "execution_state": "not_executed",
        "results": [result.to_dict() for result in results],
    }

    summary = Table(title="Prioritized Endpoints")
    summary.add_column("#", justify="right")
    summary.add_column("Score", justify="right")
    summary.add_column("Band")
    summary.add_column("Endpoint")

    for index, result in enumerate(results, start=1):
        summary.add_row(
            str(index),
            str(result.score),
            result.band,
            result.endpoint,
        )

    console.print(summary)

    console.print("[bold]Priority order:[/bold]")
    for index, result in enumerate(results, start=1):
        console.print(f"{index}. [{result.band}] {result.score} - {result.endpoint}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only ranks endpoint strings. "
        "It does not send requests, execute shell commands, launch browsers, or call LLM providers."
    )

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved prioritized endpoint JSON:[/bold green] {json_output}")


@app.command("plan-curl")
def plan_curl_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to build a safe curl plan for."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum curl execution time in seconds."),
):
    """Build a safe curl command plan after Scope Guard approval."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    plan = build_curl_plan(scope=scope, url=url, method=method, timeout=timeout)

    table = Table(title="Safe Curl Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Human approval required", "YES" if plan.requires_human_approval else "NO")
    table.add_row("Command", plan.command_text if plan.command_text else "not generated")

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)


@app.command("run-curl")
def run_curl_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to request with safe curl execution."),
    method: str = typer.Option("GET", "--method", "-X", help="HTTP method."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum curl execution time in seconds."),
    yes: bool = typer.Option(False, "--yes", "-y", help="Actually execute after Scope Guard approval."),
):
    """Execute a safe curl request only after Scope Guard approval and explicit --yes."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    plan = build_curl_plan(scope=scope, url=url, method=method, timeout=timeout)

    table = Table(title="Safe Curl Execution")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Method", method.upper())
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Command", plan.command_text if plan.command_text else "not generated")
    table.add_row("Execution requested", "YES" if yes else "NO")

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)

    if not yes:
        console.print()
        console.print("[yellow]Preview only.[/yellow] Re-run with [bold]--yes[/bold] to execute.")
        return

    result = execute_curl_plan(plan)
    parsed = parse_http_response(result.stdout)
    summary = summarize_response(parsed.status_code, parsed.headers, parsed.body)

    store = EvidenceStore()
    evidence_path = store.save_http_evidence(
        target_name=scope.target_name,
        task_name=f"curl {method.upper()} {url}",
        url=url,
        method=method,
        request={"command": result.command_text},
        response_headers=parsed.headers,
        response_body=parsed.body,
        status_code=parsed.status_code,
        notes="Captured by bugintel run-curl",
    )

    console.print()
    console.print(f"[bold]Exit code:[/bold] {result.exit_code}")
    console.print(f"[bold]Parsed status:[/bold] {parsed.status_code}")
    console.print(f"[bold]Body size:[/bold] {summary.body_size} bytes")
    console.print(f"[bold]Interesting keywords:[/bold] {', '.join(summary.interesting_keywords) if summary.interesting_keywords else 'none'}")
    console.print(f"[bold green]Evidence saved:[/bold green] {evidence_path}")

    if result.stdout:
        console.print()
        console.print("[bold green]STDOUT preview:[/bold green]")
        console.print(result.stdout[:4000])

    if result.stderr:
        console.print()
        console.print("[bold red]STDERR preview:[/bold red]")
        console.print(result.stderr[:2000])


@app.command("generate-report")
def generate_report_command(
    evidence_file: Path = typer.Argument(..., help="Evidence JSON file to convert into Markdown."),
    output_file: Path = typer.Option(..., "--output", "-o", help="Output Markdown report path."),
):
    """Generate a Markdown evidence report from saved evidence JSON."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence file not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    saved = save_evidence_report(evidence_file, output_file)

    console.print(f"[bold green]Report generated:[/bold green] {saved}")


@app.command("save-browser-capture")
def save_browser_capture_command(
    capture_file: Path = typer.Argument(..., help="Browser capture result JSON file to save as evidence."),
):
    """
    Save a browser capture result JSON as redacted browser evidence.

    This command does not execute a browser. It stores output from a future
    Playwright/DevTools/browser capture adapter using the browser evidence model.
    """
    if not capture_file.exists():
        console.print(f"[bold red]Browser capture file not found:[/bold red] {capture_file}")
        raise typer.Exit(code=1)

    data = json.loads(capture_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser"]
    missing_fields = [
        field
        for field in required_fields
        if not data.get(field)
    ]

    if missing_fields:
        console.print(
            "[bold red]Browser capture file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    result = BrowserCaptureResult(
        target_name=str(data["target_name"]),
        task_name=str(data["task_name"]),
        start_url=str(data["start_url"]),
        browser=str(data["browser"]),
        network_events=list(data.get("network_events") or []),
        screenshots=list(data.get("screenshots") or []),
        html_snapshots=list(data.get("html_snapshots") or []),
        execution_output=dict(data.get("execution_output") or {}),
        notes=str(data.get("notes") or "Captured by bugintel save-browser-capture"),
    )

    store = EvidenceStore()
    evidence_path = store.save_browser_evidence(**result.to_evidence_kwargs())

    console.print(f"[bold green]Browser evidence saved:[/bold green] {evidence_path}")




def _research_plan_from_dict(data: dict) -> ResearchPlan:
    hypotheses = []

    for item in data.get("hypotheses", []):
        evidence_refs = tuple(
            EvidenceReference(
                evidence_type=str(ref.get("evidence_type", "")),
                source=str(ref.get("source", "")),
                locator=str(ref.get("locator", "")),
                summary=str(ref.get("summary", "")),
                tags=tuple(ref.get("tags", [])),
            )
            for ref in item.get("evidence", [])
            if isinstance(ref, dict)
        )

        hypotheses.append(
            ResearchHypothesis(
                title=str(item.get("title", "")),
                category=str(item.get("category", "")),
                rationale=str(item.get("rationale", "")),
                confidence=str(item.get("confidence", "medium")),
                evidence=evidence_refs,
                suggested_tests=tuple(item.get("suggested_tests", [])),
                tags=tuple(item.get("tags", [])),
            )
        )

    recommendations = []

    for item in data.get("recommendations", []):
        recommendations.append(
            ResearchRecommendation(
                priority=int(item.get("priority", 1)),
                title=str(item.get("title", "")),
                reason=str(item.get("reason", "")),
                next_actions=tuple(item.get("next_actions", [])),
                related_hypotheses=tuple(item.get("related_hypotheses", [])),
                safety_notes=tuple(item.get("safety_notes", [])),
            )
        )

    return ResearchPlan(
        target_name=str(data.get("target_name", "unknown-target")),
        source_evidence_type=str(data.get("source_evidence_type", "browser")),
        generated_by=str(data.get("generated_by", "deterministic")),
        hypotheses=tuple(hypotheses),
        recommendations=tuple(recommendations),
        safety_notes=tuple(data.get("safety_notes", ())),
    )



def _llm_prompt_package_from_dict(data: dict) -> LLMPromptPackage:
    safety_notes = data.get("safety_notes", ())

    return LLMPromptPackage(
        system_prompt=str(data.get("system_prompt", "")),
        user_prompt=str(data.get("user_prompt", "")),
        redaction_applied=bool(data.get("redaction_applied", False)),
        source=str(data.get("source", "research_plan")),
        safety_notes=tuple(safety_notes),
    )



@app.command("audit-llm-prompt")
def audit_llm_prompt_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to LLM prompt package JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the prompt safety audit JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the prompt safety audit Markdown."),
):
    """Audit an LLM prompt package locally before provider use."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]LLM prompt package file not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid LLM prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]LLM prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = _llm_prompt_package_from_dict(data)
    report = audit_llm_prompt_package(package)
    report_data = report.to_dict()

    table = Table(title="LLM Prompt Safety Audit")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Status", report.status)
    table.add_row("Findings", str(report.finding_count))
    table.add_row("High", str(report.high_count))
    table.add_row("Medium", str(report.medium_count))
    table.add_row("Low", str(report.low_count))

    console.print(table)

    if report.findings:
        findings_table = Table(title="Prompt Safety Findings")
        findings_table.add_column("Severity", style="bold")
        findings_table.add_column("Category")
        findings_table.add_column("Label")
        findings_table.add_column("Evidence")

        for finding in report.findings:
            findings_table.add_row(
                finding.severity,
                finding.category,
                finding.label,
                finding.evidence,
            )

        console.print(findings_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(report_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt safety audit JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_llm_prompt_safety_markdown(report),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt safety audit Markdown saved:[/bold green] {markdown_output}")



@app.command("llm-provider-status")
def llm_provider_status_command(
    provider_name: str = typer.Option("disabled", "--provider", help="LLM provider name to validate."),
    allow_provider_execution: bool = typer.Option(
        False,
        "--allow-provider-execution",
        help="Explicit future-provider execution opt-in. This command still does not run a provider.",
    ),
    require_prompt_audit_pass: bool = typer.Option(
        True,
        "--require-prompt-audit-pass/--no-require-prompt-audit-pass",
        help="Require a passing prompt audit before any future provider execution.",
    ),
    model: str = typer.Option("", "--model", help="Future model label. Does not trigger provider execution."),
    timeout_seconds: int = typer.Option(30, "--timeout-seconds", help="Future provider timeout setting."),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        "--output",
        help="Optional path to save provider gate status JSON.",
    ),
):
    """Show the disabled-by-default LLM provider gate status."""
    config = LLMProviderConfig(
        provider_name=provider_name,
        allow_provider_execution=allow_provider_execution,
        require_prompt_audit_pass=require_prompt_audit_pass,
        model=model,
        timeout_seconds=timeout_seconds,
    )
    gate = validate_provider_config(config)
    payload = {
        "config": config.to_dict(),
        "gate": gate.to_dict(),
        "notes": (
            "This command only validates configuration. "
            "It does not read API keys, call providers, make network requests, or execute commands."
        ),
    }

    table = Table(title="LLM Provider Gate Status")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Provider", gate.provider_name)
    table.add_row("Allowed", str(gate.allowed))
    table.add_row("Reason", gate.reason)
    table.add_row("Require prompt audit pass", str(config.require_prompt_audit_pass))
    table.add_row("Model", config.model or "<unset>")
    table.add_row("Timeout seconds", str(config.timeout_seconds))
    console.print(table)

    if gate.required_actions:
        console.print("[bold yellow]Required actions:[/bold yellow]")
        for action in gate.required_actions:
            console.print(f"- {action}")

    if json_output is not None:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        console.print(f"[bold green]LLM provider gate status JSON saved:[/bold green] {json_output}")


@app.command("run-llm-provider")
def run_llm_provider_command(
    prompt_package_file: Path = typer.Argument(..., help="Path to LLM prompt package JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the disabled provider result JSON."),
):
    """Run the disabled-by-default LLM provider stub."""
    if not prompt_package_file.exists():
        console.print(f"[bold red]LLM prompt package file not found:[/bold red] {prompt_package_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(prompt_package_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid LLM prompt package JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]LLM prompt package JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    package = _llm_prompt_package_from_dict(data)
    result = run_disabled_llm_provider(package)
    result_data = result.to_dict()

    table = Table(title="LLM Provider Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Provider", result.provider_name)
    table.add_row("Status", result.status)
    table.add_row("Reason", result.reason)
    table.add_row("Model", result.model or "-")
    table.add_row("Output Bytes", str(len(result.output_text.encode("utf-8"))))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM provider result JSON saved:[/bold green] {json_output}")


@app.command("build-llm-prompt")
def build_llm_prompt_command(
    research_plan_file: Path = typer.Argument(..., help="Path to deterministic research plan JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the LLM prompt package JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the LLM prompt package Markdown."),
):
    """Build a safe reviewable LLM prompt package from a deterministic research plan."""
    if not research_plan_file.exists():
        console.print(f"[bold red]Research plan file not found:[/bold red] {research_plan_file}")
        raise typer.Exit(code=1)

    try:
        data = json.loads(research_plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(data, dict):
        console.print("[bold red]Research plan JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = _research_plan_from_dict(data)
    package = build_llm_prompt_package_from_research_plan(plan)
    package_data = package.to_dict()

    table = Table(title="LLM Prompt Package")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Source", package.source)
    table.add_row("Redaction Applied", "YES" if package.redaction_applied else "NO")
    table.add_row("Safety Notes", str(len(package.safety_notes)))
    table.add_row("System Prompt Bytes", str(len(package.system_prompt.encode("utf-8"))))
    table.add_row("User Prompt Bytes", str(len(package.user_prompt.encode("utf-8"))))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(package_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt package JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_llm_prompt_package_markdown(package),
            encoding="utf-8",
        )
        console.print(f"[bold green]LLM prompt package Markdown saved:[/bold green] {markdown_output}")


@app.command("plan-research")
def plan_research_command(
    evidence_file: Path = typer.Argument(..., help="Path to browser evidence or browser capture-result JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the research plan JSON."),
    markdown_output: Path | None = typer.Option(None, "--markdown-output", help="Optional path to save the research plan Markdown report."),
):
    """Build a deterministic research plan from existing browser evidence."""
    if not evidence_file.exists():
        console.print(f"[bold red]Evidence file not found:[/bold red] {evidence_file}")
        raise typer.Exit(code=1)

    try:
        evidence = json.loads(evidence_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON evidence file:[/bold red] {exc}")
        raise typer.Exit(code=2)

    if not isinstance(evidence, dict):
        console.print("[bold red]Evidence JSON must be an object.[/bold red]")
        raise typer.Exit(code=2)

    plan = build_research_plan_from_browser_evidence(evidence)
    plan_data = plan.to_dict()

    table = Table(title="Research Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", plan.target_name)
    table.add_row("Source Evidence Type", plan.source_evidence_type)
    table.add_row("Generated By", plan.generated_by)
    table.add_row("Hypotheses", str(len(plan.hypotheses)))
    table.add_row("Recommendations", str(len(plan.recommendations)))

    console.print(table)

    if plan.hypotheses:
        hypothesis_table = Table(title="Research Hypotheses")
        hypothesis_table.add_column("Category", style="bold")
        hypothesis_table.add_column("Confidence")
        hypothesis_table.add_column("Title")

        for hypothesis in plan.hypotheses:
            hypothesis_table.add_row(
                hypothesis.category,
                hypothesis.confidence,
                hypothesis.title,
            )

        console.print(hypothesis_table)

    if plan.recommendations:
        recommendation_table = Table(title="Research Recommendations")
        recommendation_table.add_column("Priority", style="bold")
        recommendation_table.add_column("Title")
        recommendation_table.add_column("Reason")

        for recommendation in plan.recommendations:
            recommendation_table.add_row(
                str(recommendation.priority),
                recommendation.title,
                recommendation.reason,
            )

        console.print(recommendation_table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(plan_data, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Research plan JSON saved:[/bold green] {json_output}")

    if markdown_output:
        markdown_output.parent.mkdir(parents=True, exist_ok=True)
        markdown_output.write_text(
            render_research_plan_markdown(plan),
            encoding="utf-8",
        )
        console.print(f"[bold green]Research plan Markdown saved:[/bold green] {markdown_output}")


@app.command("orchestrate")
def orchestrate_command(
    input_file: Path = typer.Argument(..., help="File containing JS/HTML/HAR/log text to mine endpoints from."),
    target_name: str = typer.Option("demo-lab", "--target", "-t", help="Target/workspace name."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for the orchestration plan."),
):
    """Create a multi-agent research plan from discovered endpoints."""
    if not input_file.exists():
        console.print(f"[bold red]Input file not found:[/bold red] {input_file}")
        raise typer.Exit(code=1)

    text = input_file.read_text(encoding="utf-8", errors="replace")
    endpoint_values = _endpoint_values_from_text(text)

    plan = create_orchestration_plan(
        target_name=target_name,
        endpoints=endpoint_values,
    )

    rendered = render_tree(plan.root)

    console.print(f"[bold green]Created orchestration plan for:[/bold green] {target_name}")
    console.print(f"[bold]Endpoints discovered:[/bold] {len(plan.endpoints)}")
    console.print(f"[bold]Agent assignments:[/bold] {len(plan.assignments)}")
    console.print()
    console.print(rendered)

    table = Table(title="Agent Assignments")
    table.add_column("#", justify="right")
    table.add_column("Endpoint")
    table.add_column("Agent")
    table.add_column("Mode")
    table.add_column("Human Approval")

    for index, assignment in enumerate(plan.assignments, start=1):
        table.add_row(
            str(index),
            assignment.endpoint,
            assignment.agent_name,
            assignment.mode,
            "YES" if assignment.requires_human_approval else "NO",
        )

    console.print()
    console.print(table)

    _print_endpoint_priority_table(plan.endpoint_priorities)
    _print_attack_surface_table(plan.attack_surface_map)
    _print_evidence_requirements_table(plan.evidence_requirement_plan)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
        console.print()
        console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("analyze-html")
def analyze_html_command(
    html_file: Path = typer.Argument(..., help="HTML file to analyze."),
    base_url: str = typer.Option(..., "--base-url", help="Base URL used to resolve relative links."),
):
    """Passively analyze HTML for links, scripts, forms, and endpoints."""
    if not html_file.exists():
        console.print(f"[bold red]HTML file not found:[/bold red] {html_file}")
        raise typer.Exit(code=1)

    html = html_file.read_text(encoding="utf-8", errors="replace")
    result = analyze_html(base_url=base_url, html=html)

    summary = Table(title="Website Recon Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("Links", str(len(result.links)))
    summary.add_row("Scripts", str(len(result.scripts)))
    summary.add_row("Forms", str(len(result.forms)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.links:
        table = Table(title="Links")
        table.add_column("#", justify="right")
        table.add_column("URL")
        for index, link in enumerate(result.links, start=1):
            table.add_row(str(index), link)
        console.print(table)

    if result.scripts:
        table = Table(title="JavaScript Sources")
        table.add_column("#", justify="right")
        table.add_column("Script URL")
        for index, script in enumerate(result.scripts, start=1):
            table.add_row(str(index), script)
        console.print(table)

    if result.forms:
        table = Table(title="Forms")
        table.add_column("#", justify="right")
        table.add_column("Method")
        table.add_column("Action")
        table.add_column("Inputs")
        for index, form in enumerate(result.forms, start=1):
            table.add_row(str(index), form.method, form.action, ", ".join(form.inputs))
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("fetch-page")
def fetch_page_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    url: str = typer.Argument(..., help="URL to fetch and analyze."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
):
    """Fetch one in-scope web page, analyze HTML, and save evidence."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)
    result = fetch_web_page(scope=scope, url=url, timeout=timeout)

    table = Table(title="Website Fetch Result")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", scope.target_name)
    table.add_row("URL", url)
    table.add_row("Allowed", "YES" if result.allowed else "NO")
    table.add_row("Reason", result.reason)
    table.add_row("Final URL", result.final_url or "none")
    table.add_row("Status", str(result.status_code) if result.status_code is not None else "none")
    table.add_row("Error", result.error or "none")

    console.print(table)

    if not result.allowed:
        raise typer.Exit(code=2)

    if result.error:
        raise typer.Exit(code=3)

    recon = analyze_html(base_url=result.final_url or url, html=result.text)

    summary = Table(title="Passive HTML Analysis")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("Links", str(len(recon.links)))
    summary.add_row("Scripts", str(len(recon.scripts)))
    summary.add_row("Forms", str(len(recon.forms)))
    summary.add_row("Endpoints", str(len(recon.endpoints)))

    console.print(summary)

    if recon.endpoints:
        endpoint_table = Table(title="Discovered Endpoints")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(recon.endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)

    store = EvidenceStore()
    evidence_path = store.save_http_evidence(
        target_name=scope.target_name,
        task_name=f"fetch page {url}",
        url=url,
        method="GET",
        request={"url": url, "type": "website_fetch"},
        response_headers=result.headers,
        response_body=result.text,
        status_code=result.status_code,
        notes="Captured by bugintel fetch-page",
    )

    console.print(f"[bold green]Evidence saved:[/bold green] {evidence_path}")


@app.command("collect-js")
def collect_js_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    page_url: str = typer.Argument(..., help="Page URL to fetch, analyze, and collect JS from."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
):
    """Fetch one in-scope page, collect JavaScript sources, and mine JS endpoints."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    page = fetch_web_page(scope=scope, url=page_url, timeout=timeout)

    table = Table(title="Page Fetch")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", scope.target_name)
    table.add_row("Page URL", page_url)
    table.add_row("Allowed", "YES" if page.allowed else "NO")
    table.add_row("Reason", page.reason)
    table.add_row("Status", str(page.status_code) if page.status_code is not None else "none")
    table.add_row("Error", page.error or "none")
    console.print(table)

    if not page.allowed:
        raise typer.Exit(code=2)

    if page.error:
        raise typer.Exit(code=3)

    result = collect_js_sources(
        scope=scope,
        page_url=page.final_url or page_url,
        html=page.text,
        timeout=timeout,
    )

    summary = Table(title="JavaScript Collection Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")
    summary.add_row("Scripts discovered", str(result.script_count))
    summary.add_row("Script fetch results", str(len(result.sources)))
    summary.add_row("Unique JS endpoints", str(len(result.all_endpoints)))
    console.print(summary)

    if result.sources:
        sources_table = Table(title="JavaScript Sources")
        sources_table.add_column("#", justify="right")
        sources_table.add_column("URL")
        sources_table.add_column("Allowed")
        sources_table.add_column("Status")
        sources_table.add_column("Endpoints")
        sources_table.add_column("Reason/Error")

        for index, source in enumerate(result.sources, start=1):
            reason_error = source.error or source.reason
            sources_table.add_row(
                str(index),
                source.url,
                "YES" if source.allowed else "NO",
                str(source.status_code) if source.status_code is not None else "none",
                str(len(source.endpoints)),
                reason_error,
            )

        console.print(sources_table)

    if result.all_endpoints:
        endpoint_table = Table(title="Endpoints Mined from JavaScript")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(result.all_endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)


@app.command("web-recon")
def web_recon_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    page_url: str = typer.Argument(..., help="Page URL to run website recon against."),
    timeout: int = typer.Option(15, "--timeout", help="Maximum request time in seconds."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for orchestration plan."),
):
    """Run Website Mode pipeline: fetch page, analyze HTML, collect JS, mine endpoints, orchestrate."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    result = run_website_recon(
        scope=scope,
        page_url=page_url,
        timeout=timeout,
    )

    fetch_table = Table(title="Website Recon Fetch")
    fetch_table.add_column("Field", style="bold")
    fetch_table.add_column("Value")
    fetch_table.add_row("Target", scope.target_name)
    fetch_table.add_row("Page URL", page_url)
    fetch_table.add_row("Allowed", "YES" if result.fetch.allowed else "NO")
    fetch_table.add_row("Reason", result.fetch.reason)
    fetch_table.add_row("Status", str(result.fetch.status_code) if result.fetch.status_code is not None else "none")
    fetch_table.add_row("Error", result.fetch.error or "none")
    console.print(fetch_table)

    if not result.fetch.allowed:
        raise typer.Exit(code=2)

    if result.fetch.error:
        raise typer.Exit(code=3)

    summary = Table(title="Website Recon Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Count")

    summary.add_row("HTML links", str(len(result.html_recon.links) if result.html_recon else 0))
    summary.add_row("HTML scripts", str(len(result.html_recon.scripts) if result.html_recon else 0))
    summary.add_row("HTML forms", str(len(result.html_recon.forms) if result.html_recon else 0))
    summary.add_row("JS sources", str(len(result.js_recon.sources) if result.js_recon else 0))
    summary.add_row("Merged endpoints", str(len(result.endpoints)))
    summary.add_row(
        "Agent assignments",
        str(len(result.orchestration_plan.assignments) if result.orchestration_plan else 0),
    )

    console.print(summary)

    if result.endpoints:
        endpoint_table = Table(title="Merged Endpoint Inventory")
        endpoint_table.add_column("#", justify="right")
        endpoint_table.add_column("Endpoint")

        for index, endpoint in enumerate(result.endpoints, start=1):
            endpoint_table.add_row(str(index), endpoint)

        console.print(endpoint_table)

    if result.orchestration_plan:
        assignment_table = Table(title="Agent Assignments")
        assignment_table.add_column("#", justify="right")
        assignment_table.add_column("Endpoint")
        assignment_table.add_column("Agent")
        assignment_table.add_column("Mode")
        assignment_table.add_column("Human Approval")

        for index, assignment in enumerate(result.orchestration_plan.assignments, start=1):
            assignment_table.add_row(
                str(index),
                assignment.endpoint,
                assignment.agent_name,
                assignment.mode,
                "YES" if assignment.requires_human_approval else "NO",
            )

        console.print(assignment_table)

        _print_endpoint_priority_table(result.orchestration_plan.endpoint_priorities)
        _print_attack_surface_table(result.orchestration_plan.attack_surface_map)
        _print_evidence_requirements_table(result.orchestration_plan.evidence_requirement_plan)

        if json_output:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(result.orchestration_plan.to_dict(), indent=2), encoding="utf-8")
            console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("import-har")
def import_har_command(
    har_file: Path = typer.Argument(..., help="HAR file exported from browser DevTools, proxy, or compatible traffic capture."),
    target_name: str = typer.Option("har-import", "--target", "-t", help="Target/workspace name."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path for orchestration plan."),
):
    """Import a HAR file, extract endpoints, and optionally save a multi-agent plan."""
    if not har_file.exists():
        console.print(f"[bold red]HAR file not found:[/bold red] {har_file}")
        raise typer.Exit(code=1)

    result = load_har(har_file)

    summary = Table(title="HAR Import Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("HAR file", str(har_file))
    summary.add_row("Entries", str(len(result.entries)))
    summary.add_row("Unique endpoints", str(len(result.endpoints)))
    summary.add_row("API-like entries", str(len(result.api_entries)))

    console.print(summary)

    if result.entries:
        table = Table(title="HAR Entries")
        table.add_column("#", justify="right")
        table.add_column("Method")
        table.add_column("Status")
        table.add_column("Category")
        table.add_column("Endpoint")

        for index, entry in enumerate(result.entries, start=1):
            table.add_row(
                str(index),
                entry.method,
                str(entry.status_code) if entry.status_code is not None else "none",
                entry.category,
                entry.endpoint,
            )

        console.print(table)

    if result.endpoints:
        plan = create_orchestration_plan(
            target_name=target_name,
            endpoints=result.endpoints,
        )

        console.print()
        console.print(f"[bold green]Created orchestration plan for:[/bold green] {target_name}")
        console.print(f"[bold]Agent assignments:[/bold] {len(plan.assignments)}")

        assignment_table = Table(title="Agent Assignments from HAR")
        assignment_table.add_column("#", justify="right")
        assignment_table.add_column("Endpoint")
        assignment_table.add_column("Agent")
        assignment_table.add_column("Mode")
        assignment_table.add_column("Human Approval")

        for index, assignment in enumerate(plan.assignments, start=1):
            assignment_table.add_row(
                str(index),
                assignment.endpoint,
                assignment.agent_name,
                assignment.mode,
                "YES" if assignment.requires_human_approval else "NO",
            )

        console.print(assignment_table)

        _print_endpoint_priority_table(plan.endpoint_priorities, title="Endpoint Priorities from HAR")
        _print_attack_surface_table(plan.attack_surface_map, title="Attack Surface Groups from HAR")
        _print_evidence_requirements_table(plan.evidence_requirement_plan, title="Evidence Requirements from HAR")

        if json_output:
            json_output.parent.mkdir(parents=True, exist_ok=True)
            json_output.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
            console.print(f"[bold green]Saved orchestration JSON:[/bold green] {json_output}")


@app.command("analyze-android")
def analyze_android_command(
    manifest_file: Path = typer.Argument(..., help="AndroidManifest.xml file to analyze."),
    extra_file: Path | None = typer.Option(None, "--extra", help="Optional extra config/source text file to mine endpoints from."),
):
    """Analyze Android manifest/config text for components, permissions, deep links, and endpoints."""
    if not manifest_file.exists():
        console.print(f"[bold red]Manifest file not found:[/bold red] {manifest_file}")
        raise typer.Exit(code=1)

    manifest_text = manifest_file.read_text(encoding="utf-8", errors="replace")
    extra_text = ""

    if extra_file:
        if not extra_file.exists():
            console.print(f"[bold red]Extra file not found:[/bold red] {extra_file}")
            raise typer.Exit(code=1)
        extra_text = extra_file.read_text(encoding="utf-8", errors="replace")

    result = analyze_android_manifest(
        manifest_text=manifest_text,
        extra_text=extra_text,
    )

    summary = Table(title="Android Analysis Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("Package", result.package_name or "unknown")
    summary.add_row("Permissions", str(len(result.permissions)))
    summary.add_row("Components", str(len(result.components)))
    summary.add_row("Exported components", str(len(result.exported_components)))
    summary.add_row("Deep links", str(len(result.deep_links)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.permissions:
        table = Table(title="Permissions")
        table.add_column("#", justify="right")
        table.add_column("Permission")
        for index, permission in enumerate(result.permissions, start=1):
            table.add_row(str(index), permission)
        console.print(table)

    if result.components:
        table = Table(title="Components")
        table.add_column("#", justify="right")
        table.add_column("Kind")
        table.add_column("Name")
        table.add_column("Exported")
        for index, component in enumerate(result.components, start=1):
            table.add_row(
                str(index),
                component.kind,
                component.name,
                "YES" if component.exported is True else "NO" if component.exported is False else "unknown",
            )
        console.print(table)

    if result.deep_links:
        table = Table(title="Deep Links")
        table.add_column("#", justify="right")
        table.add_column("Component")
        table.add_column("Scheme")
        table.add_column("Host")
        table.add_column("Path")
        for index, link in enumerate(result.deep_links, start=1):
            table.add_row(str(index), link.component, link.scheme, link.host, link.path)
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints Mined from Android Text")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("analyze-ios")
def analyze_ios_command(
    plist_file: Path = typer.Argument(..., help="iOS Info.plist XML file to analyze."),
    extra_file: Path | None = typer.Option(None, "--extra", help="Optional extra config/source text file to mine endpoints from."),
):
    """Analyze iOS plist/config text for bundle info, URL schemes, associated domains, ATS, hosts, and endpoints."""
    if not plist_file.exists():
        console.print(f"[bold red]Plist file not found:[/bold red] {plist_file}")
        raise typer.Exit(code=1)

    plist_text = plist_file.read_text(encoding="utf-8", errors="replace")
    extra_text = ""

    if extra_file:
        if not extra_file.exists():
            console.print(f"[bold red]Extra file not found:[/bold red] {extra_file}")
            raise typer.Exit(code=1)
        extra_text = extra_file.read_text(encoding="utf-8", errors="replace")

    result = analyze_ios_plist(
        plist_text=plist_text,
        extra_text=extra_text,
    )

    summary = Table(title="iOS Analysis Summary")
    summary.add_column("Field", style="bold")
    summary.add_column("Value")

    summary.add_row("Bundle ID", result.bundle_id or "unknown")
    summary.add_row("Display name", result.display_name or "unknown")
    summary.add_row("URL scheme groups", str(len(result.url_schemes)))
    summary.add_row("Associated domains", str(len(result.associated_domains)))
    summary.add_row(
        "ATS arbitrary loads",
        "YES" if result.ats_allows_arbitrary_loads is True else "NO" if result.ats_allows_arbitrary_loads is False else "unknown",
    )
    summary.add_row("Hosts", str(len(result.hosts)))
    summary.add_row("Endpoints", str(len(result.endpoints)))

    console.print(summary)

    if result.url_schemes:
        table = Table(title="URL Schemes")
        table.add_column("#", justify="right")
        table.add_column("Name")
        table.add_column("Schemes")
        for index, item in enumerate(result.url_schemes, start=1):
            table.add_row(str(index), item.name, ", ".join(item.schemes))
        console.print(table)

    if result.associated_domains:
        table = Table(title="Associated Domains")
        table.add_column("#", justify="right")
        table.add_column("Domain")
        for index, domain in enumerate(result.associated_domains, start=1):
            table.add_row(str(index), domain)
        console.print(table)

    if result.hosts:
        table = Table(title="Hosts")
        table.add_column("#", justify="right")
        table.add_column("Host")
        for index, host in enumerate(result.hosts, start=1):
            table.add_row(str(index), host)
        console.print(table)

    if result.endpoints:
        table = Table(title="Endpoints Mined from iOS Text")
        table.add_column("#", justify="right")
        table.add_column("Endpoint")
        for index, endpoint in enumerate(result.endpoints, start=1):
            table.add_row(str(index), endpoint)
        console.print(table)


@app.command("plan-browser")
def plan_browser_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to plan."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Plan browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Plan screenshot evidence capture."),
):
    """Create a safe browser automation plan after Scope Guard approval."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    table = Table(title="Browser Action Plan")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", plan.target_name)
    table.add_row("Start URL", plan.start_url)
    table.add_row("Browser", plan.browser)
    table.add_row("Allowed", "YES" if plan.allowed else "NO")
    table.add_row("Reason", plan.reason)
    table.add_row("Human approval required", "YES" if plan.requires_human_approval else "NO")
    table.add_row("Actions", str(len(plan.actions)))

    console.print(table)

    if not plan.allowed:
        raise typer.Exit(code=2)

    if plan.actions:
        action_table = Table(title="Planned Browser Actions")
        action_table.add_column("#", justify="right")
        action_table.add_column("Action")
        action_table.add_column("Value")
        action_table.add_column("Description")

        for index, action in enumerate(plan.actions, start=1):
            action_table.add_row(
                str(index),
                action.action_type,
                action.value,
                action.description,
            )

        console.print(action_table)


@app.command("preview-playwright")
def preview_playwright_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to preview."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Preview browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Preview screenshot evidence capture."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Preview HTML snapshot capture."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Preview headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Preview browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Preview page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Preview screenshot artifact path."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Mark preview as live-execution allowed. This command still does not launch a browser."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Preview routing through the real Playwright adapter."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the preview JSON."),
):
    """
    Build a safe Playwright execution preview.

    This command does not launch a browser. It validates the start URL through
    Scope Guard, builds a BrowserPlan, and emits a Playwright execution preview
    that can later feed browser execution/evidence workflows.
    """
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    if not plan.allowed:
        console.print(f"[bold red]Browser plan blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    preview = build_playwright_execution_preview(
        plan=plan,
        config=config,
    )

    table = Table(title="Playwright Execution Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Runner", str(preview["runner"]))
    table.add_row("Status", str(preview["status"]))
    table.add_row("Browser", str(preview["browser"]))
    table.add_row("Start URL", str(preview["start_url"]))
    table.add_row("Live execution allowed", "YES" if preview["live_execution_allowed"] else "NO")
    table.add_row("Use real adapter", "YES" if preview.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if preview["playwright_available"] else "NO")
    table.add_row("Reason", str(preview["reason"]))
    table.add_row("Headless", "YES" if preview["headless"] else "NO")
    table.add_row("Timeout ms", str(preview["timeout_ms"]))
    table.add_row("Wait until", str(preview["wait_until"]))
    table.add_row("Capture network", "YES" if preview["capture_network"] else "NO")
    table.add_row("Capture screenshot", "YES" if preview["capture_screenshot"] else "NO")
    table.add_row("Capture HTML", "YES" if preview["capture_html"] else "NO")
    table.add_row("Screenshot path", str(preview["screenshot_path"]))
    table.add_row("Planned actions", str(len(preview["planned_actions"])))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(preview, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Preview JSON saved:[/bold green] {json_output}")




@app.command("execute-playwright-plan")
def execute_playwright_plan_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL to execute."),
    task_name: str = typer.Option("playwright execution", "--task-name", help="Task name for the future browser capture result."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Request browser network capture."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Request screenshot evidence capture."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Request HTML snapshot capture."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Future headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Future browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Future page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Future screenshot artifact path."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Explicitly pass the live execution safety gate."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Route through the real Playwright adapter after safety gates pass."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the capture result JSON."),
):
    """
    Exercise the safety-gated Playwright execution skeleton.

    This command does not launch a browser yet. By default, it refuses execution.
    It exists to validate that future live browser execution stays behind the
    Scope Guard, explicit human approval, and Playwright availability gates.
    """
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    try:
        result = execute_playwright_plan(
            plan=plan,
            task_name=task_name,
            config=config,
            notes="Captured by bugintel execute-playwright-plan skeleton.",
        )
    except PlaywrightExecutionSafetyError as exc:
        console.print(f"[bold red]Playwright execution blocked:[/bold red] {exc}")
        raise typer.Exit(code=2)

    table = Table(title="Playwright Execution Skeleton")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    output = result.execution_output

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Runner", str(output.get("runner", "playwright")))
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Reason", str(output.get("reason", "")))
    table.add_row("Live execution allowed", "YES" if output.get("live_execution_allowed") else "NO")
    table.add_row("Use real adapter", "YES" if output.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if output.get("playwright_available") else "NO")

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")




@app.command("build-playwright-request")
def build_playwright_request_command(
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file."),
    start_url: str = typer.Argument(..., help="Browser start URL for the future request."),
    task_name: str = typer.Option("playwright request", "--task-name", help="Task name for the browser job ticket."),
    browser: str = typer.Option("chromium", "--browser", help="Browser label: chromium, chrome, or firefox."),
    capture_network: bool = typer.Option(True, "--capture-network/--no-capture-network", help="Include future network capture in the request."),
    capture_screenshot: bool = typer.Option(True, "--capture-screenshot/--no-capture-screenshot", help="Include future screenshot capture in the request."),
    capture_html: bool = typer.Option(True, "--capture-html/--no-capture-html", help="Include future HTML snapshot capture in the request."),
    headless: bool = typer.Option(True, "--headless/--headed", help="Future headless/headed browser setting."),
    timeout_ms: int = typer.Option(15000, "--timeout-ms", help="Future browser timeout in milliseconds."),
    wait_until: str = typer.Option("load", "--wait-until", help="Future page load wait condition."),
    screenshot_path: str = typer.Option("artifacts/browser-screenshot.png", "--screenshot-path", help="Future screenshot config path."),
    base_artifact_dir: Path = typer.Option(Path("artifacts/browser"), "--base-artifact-dir", help="Base directory for planned browser artifacts."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Record explicit live-execution approval in the request."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Record real Playwright adapter routing in the request."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the request JSON."),
):
    """Build a reviewable Playwright execution request JSON."""
    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    with scope_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scope = load_scope_from_dict(data)

    plan = build_browser_plan(
        scope=scope,
        start_url=start_url,
        browser=browser,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
    )

    if not plan.allowed:
        console.print(f"[bold red]Playwright request blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=headless,
        timeout_ms=timeout_ms,
        wait_until=wait_until,
        capture_network=capture_network,
        capture_screenshot=capture_screenshot,
        capture_html=capture_html,
        screenshot_path=screenshot_path,
        allow_live_execution=allow_live_execution,
        use_real_adapter=use_real_adapter,
    )

    request = build_playwright_execution_request(
        plan=plan,
        task_name=task_name,
        config=config,
        base_artifact_dir=base_artifact_dir,
    )

    request_data = request.to_dict()

    table = Table(title="Playwright Execution Request")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", request.target_name)
    table.add_row("Task", request.task_name)
    table.add_row("Browser", request.browser)
    table.add_row("Start URL", request.start_url)
    table.add_row("Live execution allowed", "YES" if request.config.allow_live_execution else "NO")
    table.add_row("Use real adapter", "YES" if request.config.use_real_adapter else "NO")
    table.add_row("Artifact directory", request.artifacts.artifact_dir)
    table.add_row("Screenshot path", request.artifacts.screenshot_path)
    table.add_row("HTML snapshot path", request.artifacts.html_snapshot_path)
    table.add_row("Network log path", request.artifacts.network_log_path)
    table.add_row("Trace path", request.artifacts.trace_path)
    table.add_row("Planned actions", str(len(request.planned_actions)))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(request_data, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Request JSON saved:[/bold green] {json_output}")




@app.command("preview-playwright-request")
def preview_playwright_request_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the preview JSON."),
):
    """Build a Playwright execution preview from a saved request JSON."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser", "config", "planned_actions"]
    missing_fields = [
        field
        for field in required_fields
        if field not in data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    config_data = data.get("config") or {}
    actions_data = data.get("planned_actions") or []

    actions = [
        BrowserAction(
            action_type=str(action.get("action_type", "")),
            value=str(action.get("value", "")),
            description=str(action.get("description", "")),
        )
        for action in actions_data
        if isinstance(action, dict)
    ]

    plan = BrowserPlan(
        allowed=True,
        reason="Loaded from Playwright execution request JSON.",
        target_name=str(data["target_name"]),
        start_url=str(data["start_url"]),
        browser=str(data["browser"]),
        actions=actions,
        requires_human_approval=True,
    )

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=bool(config_data.get("allow_live_execution", False)),
        use_real_adapter=bool(config_data.get("use_real_adapter", False)),
    )

    preview = build_playwright_execution_preview(
        plan=plan,
        config=config,
    )

    preview["target_name"] = str(data["target_name"])
    preview["task_name"] = str(data["task_name"])
    preview["request_file"] = str(request_file)
    if "artifacts" in data:
        preview["artifacts"] = data["artifacts"]

    table = Table(title="Playwright Request Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", str(preview["target_name"]))
    table.add_row("Task", str(preview["task_name"]))
    table.add_row("Runner", str(preview["runner"]))
    table.add_row("Status", str(preview["status"]))
    table.add_row("Browser", str(preview["browser"]))
    table.add_row("Start URL", str(preview["start_url"]))
    table.add_row("Live execution allowed", "YES" if preview["live_execution_allowed"] else "NO")
    table.add_row("Playwright available", "YES" if preview["playwright_available"] else "NO")
    table.add_row("Reason", str(preview["reason"]))
    table.add_row("Planned actions", str(len(preview["planned_actions"])))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(preview, indent=2, sort_keys=True), encoding="utf-8")
        console.print(f"[bold green]Preview JSON saved:[/bold green] {json_output}")




@app.command("execute-playwright-request")
def execute_playwright_request_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    scope_file: Path = typer.Argument(..., help="Path to target scope YAML file for re-validation."),
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Explicitly pass the live execution safety gate."),
    use_real_adapter: bool = typer.Option(False, "--use-real-adapter", help="Route through the real Playwright adapter after safety gates pass."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the capture result JSON."),
):
    """Run the safety-gated Playwright execution handoff from a saved request."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    if not scope_file.exists():
        console.print(f"[bold red]Scope file not found:[/bold red] {scope_file}")
        raise typer.Exit(code=1)

    request_data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = ["target_name", "task_name", "start_url", "browser", "config", "planned_actions"]
    missing_fields = [
        field
        for field in required_fields
        if field not in request_data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    with scope_file.open("r", encoding="utf-8") as f:
        scope_data = yaml.safe_load(f)

    scope = load_scope_from_dict(scope_data)
    config_data = request_data.get("config") or {}

    plan = build_browser_plan(
        scope=scope,
        start_url=str(request_data["start_url"]),
        browser=str(request_data["browser"]),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
    )

    if not plan.allowed:
        console.print(f"[bold red]Playwright request execution blocked:[/bold red] {plan.reason}")
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=allow_live_execution,
        use_real_adapter=bool(config_data.get("use_real_adapter", False)) or use_real_adapter,
    )

    try:
        result = execute_playwright_plan(
            plan=plan,
            task_name=str(request_data["task_name"]),
            config=config,
            notes="Captured by bugintel execute-playwright-request skeleton.",
        )
    except PlaywrightExecutionSafetyError as exc:
        console.print(f"[bold red]Playwright request execution blocked:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output = result.execution_output

    table = Table(title="Playwright Request Execution Skeleton")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Runner", str(output.get("runner", "playwright")))
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Reason", str(output.get("reason", "")))
    table.add_row("Live execution allowed", "YES" if output.get("live_execution_allowed") else "NO")
    table.add_row("Use real adapter", "YES" if output.get("use_real_adapter") else "NO")
    table.add_row("Playwright available", "YES" if output.get("playwright_available") else "NO")

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")



@app.command("load-browser-artifacts")
def load_browser_artifacts_command(
    request_file: Path = typer.Argument(..., help="Path to Playwright execution request JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional path to save the capture result JSON."),
):
    """Load planned browser artifacts into a capture result JSON."""
    if not request_file.exists():
        console.print(f"[bold red]Playwright request file not found:[/bold red] {request_file}")
        raise typer.Exit(code=1)

    request_data = json.loads(request_file.read_text(encoding="utf-8"))

    required_fields = [
        "target_name",
        "task_name",
        "start_url",
        "browser",
        "config",
        "planned_actions",
        "artifacts",
    ]
    missing_fields = [
        field
        for field in required_fields
        if field not in request_data
    ]

    if missing_fields:
        console.print(
            "[bold red]Playwright request file missing required fields:[/bold red] "
            + ", ".join(missing_fields)
        )
        raise typer.Exit(code=2)

    config_data = request_data.get("config") or {}
    artifacts_data = request_data.get("artifacts") or {}

    required_artifact_fields = [
        "artifact_dir",
        "screenshot_path",
        "html_snapshot_path",
        "network_log_path",
        "trace_path",
    ]
    missing_artifact_fields = [
        field
        for field in required_artifact_fields
        if field not in artifacts_data
    ]

    if missing_artifact_fields:
        console.print(
            "[bold red]Playwright request artifacts missing required fields:[/bold red] "
            + ", ".join(missing_artifact_fields)
        )
        raise typer.Exit(code=2)

    config = BrowserExecutionConfig(
        headless=bool(config_data.get("headless", True)),
        timeout_ms=int(config_data.get("timeout_ms", 15000)),
        wait_until=str(config_data.get("wait_until", "load")),
        capture_network=bool(config_data.get("capture_network", True)),
        capture_screenshot=bool(config_data.get("capture_screenshot", True)),
        capture_html=bool(config_data.get("capture_html", True)),
        screenshot_path=str(config_data.get("screenshot_path", "artifacts/browser-screenshot.png")),
        allow_live_execution=bool(config_data.get("allow_live_execution", False)),
        use_real_adapter=bool(config_data.get("use_real_adapter", False)),
    )

    artifacts = PlaywrightArtifactPlan(
        artifact_dir=str(artifacts_data["artifact_dir"]),
        screenshot_path=str(artifacts_data["screenshot_path"]),
        html_snapshot_path=str(artifacts_data["html_snapshot_path"]),
        network_log_path=str(artifacts_data["network_log_path"]),
        trace_path=str(artifacts_data["trace_path"]),
    )

    request = PlaywrightExecutionRequest(
        target_name=str(request_data["target_name"]),
        task_name=str(request_data["task_name"]),
        start_url=str(request_data["start_url"]),
        browser=str(request_data["browser"]),
        config=config,
        artifacts=artifacts,
        planned_actions=list(request_data.get("planned_actions") or []),
    )

    context = build_playwright_adapter_context(request)

    try:
        result = load_browser_capture_result_from_artifacts(
            context,
            notes="Loaded by bugintel load-browser-artifacts.",
        )
    except ValueError as exc:
        console.print(f"[bold red]Browser artifact loading failed:[/bold red] {exc}")
        raise typer.Exit(code=2)

    output = result.execution_output

    table = Table(title="Browser Artifacts Loaded")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Target", result.target_name)
    table.add_row("Task", result.task_name)
    table.add_row("Browser", result.browser)
    table.add_row("Start URL", result.start_url)
    table.add_row("Status", str(output.get("status", "unknown")))
    table.add_row("Network events", str(output.get("loaded_network_events", 0)))
    table.add_row("Screenshots", str(output.get("loaded_screenshots", 0)))
    table.add_row("HTML snapshots", str(output.get("loaded_html_snapshots", 0)))

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")






@app.command("brain-chat-research-investigation-plan-packet")
def brain_chat_research_investigation_plan_packet_command(
    selection_file: Path = typer.Option(..., "--selection-file", "--selection", help="Local JSON file containing a research hypothesis selection packet."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local-only research investigation plan packet."""
    if not selection_file.exists():
        console.print(f"[bold red]Research hypothesis selection JSON not found:[/bold red] {selection_file}")
        raise typer.Exit(code=1)

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)

    try:
        packet = build_research_investigation_plan_packet_from_file(
            selection_file,
            output_file=output_file,
            json_output=json_output,
        )
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[bold red]Invalid selection packet:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    table = Table(title="Brain Chat Research Investigation Plan Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target name", str(packet.get("target_name", "unknown-target")))
    table.add_row("Packet status", str(packet.get("packet_status", "unknown")))
    table.add_row("Selection status", str(packet.get("selection_status", "unknown")))
    table.add_row("Investigation plan status", str(packet.get("investigation_plan_status", "unknown")))
    table.add_row("Selected count", str(packet.get("selected_count", 0)))
    table.add_row("Plan count", str(packet.get("plan_count", 0)))
    table.add_row("Primary hypothesis", str(packet.get("primary_hypothesis_id", "") or "none"))
    table.add_row("Allowed local next steps", str(packet.get("allowed_local_next_steps_count", 0)))
    table.add_row("Rejected actions", str(packet.get("rejected_actions_count", 0)))

    safety_flags = packet.get("safety_flags", {})
    if isinstance(safety_flags, dict):
        table.add_row("Web browsing", str(bool(safety_flags.get("web_browsing", False))).lower())
        table.add_row("Network interaction", str(bool(safety_flags.get("network_interaction", False))).lower())
        table.add_row("Command generation", str(bool(safety_flags.get("command_generation", False))).lower())
        table.add_row("Tool execution", str(bool(safety_flags.get("tool_execution", False))).lower())
        table.add_row("Browser execution", str(bool(safety_flags.get("browser_execution", False))).lower())
        table.add_row("Curl execution", str(bool(safety_flags.get("curl_execution", False))).lower())
        table.add_row("Kali execution", str(bool(safety_flags.get("kali_execution", False))).lower())
        table.add_row("Burp execution", str(bool(safety_flags.get("burp_execution", False))).lower())
        table.add_row("Target interaction", str(bool(safety_flags.get("target_interaction", False))).lower())
        table.add_row("Evidence collection", str(bool(safety_flags.get("evidence_collection", False))).lower())
        table.add_row("Validation execution", str(bool(safety_flags.get("validation_execution", False))).lower())
        table.add_row("Report submission", str(bool(safety_flags.get("report_submission", False))).lower())
        table.add_row("Vulnerability confirmation", str(bool(safety_flags.get("vulnerability_confirmation", False))).lower())

    console.print(table)
    console.print(f"[bold yellow]Investigation plan status:[/bold yellow] {packet.get('investigation_plan_status', 'unknown')}")

    plans = packet.get("plans", [])
    if isinstance(plans, list) and plans:
        console.print("[bold yellow]Investigation plans:[/bold yellow]")
        for plan in plans:
            if isinstance(plan, dict):
                console.print(
                    f"- {plan.get('hypothesis_id', 'unknown')} "
                    f"[{plan.get('priority', 'unknown')}/{plan.get('confidence', 'unknown')}] "
                    f"{plan.get('hypothesis_type', 'unknown')} :: {plan.get('title', '')}"
                )

    rejected_actions = packet.get("rejected_actions", [])
    if isinstance(rejected_actions, list) and rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in rejected_actions:
            if isinstance(item, dict):
                console.print(f"- {item.get('action', '')}: {item.get('reason', '')}")
            else:
                console.print(f"- {item}")

    if output_file:
        console.print(f"[bold green]Investigation plan packet saved:[/bold green] {output_file}")

    if json_output:
        console.print(f"[bold green]Investigation plan JSON saved:[/bold green] {json_output}")

















@app.command("brain-chat-research-hypothesis-feedback-packet")
def brain_chat_research_hypothesis_feedback_packet_command(
    hypothesis_file: Path = typer.Option(
        ...,
        "--hypothesis-file",
        "--hypothesis-packet",
        help=(
            "Local JSON research hypothesis packet."
        ),
    ),
    observation_file: Path = typer.Option(
        ...,
        "--observation-file",
        "--observation-packet",
        help=(
            "Local JSON normalized research observation packet."
        ),
    ),
    review_file: Path = typer.Option(
        ...,
        "--review-file",
        "--observation-review",
        help=(
            "Local JSON observation review-gate artifact."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Build proposed hypothesis feedback."""
    required_files = (
        (
            "Research hypothesis packet",
            hypothesis_file,
        ),
        (
            "Research observation packet",
            observation_file,
        ),
        (
            "Research observation review",
            review_file,
        ),
    )

    for label, source_file in required_files:
        if source_file.exists():
            continue

        console.print(
            f"[bold red]{label} not found:"
            f"[/bold red] {source_file}"
        )
        raise typer.Exit(code=1)

    try:
        packet = (
            build_research_hypothesis_feedback_packet_from_files(
                hypothesis_file,
                observation_file,
                review_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback "
            f"JSON input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback "
            f"input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = packet.get("counts")

    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Hypothesis Feedback Packet"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = (
        (
            "Hypothesis file",
            str(hypothesis_file),
        ),
        (
            "Observation file",
            str(observation_file),
        ),
        (
            "Review file",
            str(review_file),
        ),
        (
            "Target",
            str(
                packet.get("target_name")
                or "unknown-target"
            ),
        ),
        (
            "Packet status",
            str(
                packet.get("packet_status")
                or "unknown"
            ),
        ),
        (
            "Summary",
            str(packet.get("summary") or ""),
        ),
        (
            "Packet ready",
            str(bool(packet.get("packet_ready"))),
        ),
        (
            "Feedback review ready",
            str(
                bool(
                    packet.get(
                        "hypothesis_feedback_review_ready"
                    )
                )
            ),
        ),
        (
            "Source hypotheses",
            str(
                counts.get("source_hypotheses")
                or 0
            ),
        ),
        (
            "Verified impacts",
            str(
                counts.get(
                    "verified_hypothesis_impacts"
                )
                or 0
            ),
        ),
        (
            "Feedback proposals",
            str(
                counts.get("feedback_proposals")
                or 0
            ),
        ),
        (
            "Categorical confidence changes",
            str(
                counts.get(
                    "categorical_confidence_changes"
                )
                or 0
            ),
        ),
        (
            "Strengthening proposals",
            str(
                counts.get(
                    "strengthening_proposals"
                )
                or 0
            ),
        ),
        (
            "Weakening proposals",
            str(
                counts.get("weakening_proposals")
                or 0
            ),
        ),
        (
            "Hold proposals",
            str(
                counts.get("hold_proposals")
                or 0
            ),
        ),
        (
            "High findings",
            str(
                counts.get("high_findings")
                or 0
            ),
        ),
        (
            "Medium findings",
            str(
                counts.get("medium_findings")
                or 0
            ),
        ),
        (
            "Confidence update ready",
            "false",
        ),
        (
            "Selection update ready",
            "false",
        ),
        (
            "Research-state transition ready",
            "false",
        ),
        (
            "Runtime execution allowed",
            "false",
        ),
    )

    for field, value in rows:
        table.add_row(field, value)

    console.print(table)

    proposals = packet.get(
        "feedback_proposals"
    )

    if isinstance(proposals, list) and proposals:
        proposal_table = Table(
            title="Hypothesis Feedback Proposals"
        )
        proposal_table.add_column("Feedback")
        proposal_table.add_column("Hypothesis")
        proposal_table.add_column("Current")
        proposal_table.add_column("Proposed")
        proposal_table.add_column("Delta")
        proposal_table.add_column("Direction")
        proposal_table.add_column("Disposition")
        proposal_table.add_column("Change")
        proposal_table.add_column("Observations")

        for proposal in proposals:
            if not isinstance(proposal, dict):
                continue

            proposal_table.add_row(
                str(
                    proposal.get("feedback_id")
                    or ""
                ),
                str(
                    proposal.get("hypothesis_id")
                    or ""
                ),
                str(
                    proposal.get(
                        "current_confidence"
                    )
                    or ""
                ),
                str(
                    proposal.get(
                        "proposed_confidence"
                    )
                    or ""
                ),
                str(
                    proposal.get(
                        "net_confidence_delta"
                    )
                    or 0
                ),
                str(
                    proposal.get(
                        "evidence_direction"
                    )
                    or ""
                ),
                str(
                    proposal.get(
                        "proposed_disposition"
                    )
                    or ""
                ),
                str(
                    bool(
                        proposal.get(
                            "categorical_confidence_change"
                        )
                    )
                ),
                str(
                    proposal.get(
                        "observation_count"
                    )
                    or 0
                ),
            )

        console.print(proposal_table)

    findings = packet.get("findings")

    if isinstance(findings, list) and findings:
        console.print(
            "[bold yellow]Feedback findings:"
            "[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = packet.get(
        "allowed_next_steps"
    )

    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:"
            "[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = packet.get(
        "rejected_next_steps"
    )

    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:"
            "[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    digest_rows = (
        (
            "Hypothesis packet digest",
            packet.get(
                "hypothesis_packet_digest"
            ),
        ),
        (
            "Observation packet digest",
            packet.get(
                "observation_packet_digest"
            ),
        ),
        (
            "Observation review digest",
            packet.get(
                "observation_review_digest"
            ),
        ),
        (
            "Feedback digest",
            packet.get("feedback_digest"),
        ),
    )

    for label, digest in digest_rows:
        if not digest:
            continue

        console.print(
            f"[bold yellow]{label}:[/bold yellow] "
            f"`{digest}`"
        )

    if output_file:
        console.print(
            "[bold green]Saved hypothesis feedback "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved hypothesis feedback "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command "
        "creates local proposed hypothesis-confidence feedback "
        "only. It does not change hypothesis confidence, alter "
        "hypothesis selection, modify investigation plans, "
        "mutate research state, generate commands or payloads, "
        "execute tools, launch browsers, replay Burp requests, "
        "run Kali tools, send network requests, interact with "
        "targets, collect evidence, validate findings, submit "
        "reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-observation-review-gate")
def brain_chat_research_observation_review_gate_command(
    packet_file: Path = typer.Option(
        ...,
        "--packet-file",
        "--observation-packet",
        help=(
            "Local JSON file containing a normalized "
            "research observation packet."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Review a normalized research observation packet."""
    if not packet_file.exists():
        console.print(
            "[bold red]Research observation packet not found:"
            f"[/bold red] {packet_file}"
        )
        raise typer.Exit(code=1)

    try:
        review = (
            build_research_observation_review_gate_from_file(
                packet_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research observation packet "
            f"JSON:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid research observation review "
            f"input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = review.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Observation Review Gate"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = (
        ("Packet file", str(packet_file)),
        (
            "Target",
            str(
                review.get("target_name")
                or "unknown-target"
            ),
        ),
        (
            "Focus endpoint",
            str(
                review.get("focus_endpoint")
                or "none"
            ),
        ),
        (
            "Source packet status",
            str(
                review.get("source_packet_status")
                or "unknown"
            ),
        ),
        (
            "Review status",
            str(
                review.get("review_status")
                or "unknown"
            ),
        ),
        (
            "Summary",
            str(review.get("summary") or ""),
        ),
        (
            "Review ready",
            str(bool(review.get("review_ready"))),
        ),
        (
            "Hypothesis feedback packet ready",
            str(
                bool(
                    review.get(
                        "hypothesis_feedback_packet_ready"
                    )
                )
            ),
        ),
        (
            "Research-state transition ready",
            str(
                bool(
                    review.get(
                        "research_state_transition_ready"
                    )
                )
            ),
        ),
        (
            "Observations",
            str(counts.get("observations") or 0),
        ),
        (
            "Ready observations",
            str(
                counts.get("ready_observations")
                or 0
            ),
        ),
        (
            "Blocked observations",
            str(
                counts.get("blocked_observations")
                or 0
            ),
        ),
        (
            "Review-needed observations",
            str(
                counts.get(
                    "review_needed_observations"
                )
                or 0
            ),
        ),
        (
            "Expected hypothesis impacts",
            str(
                counts.get(
                    "expected_hypothesis_impacts"
                )
                or 0
            ),
        ),
        (
            "Packet findings",
            str(
                counts.get("packet_findings")
                or 0
            ),
        ),
        (
            "Observation findings",
            str(
                counts.get("observation_findings")
                or 0
            ),
        ),
        (
            "Impact findings",
            str(
                counts.get("impact_findings")
                or 0
            ),
        ),
        (
            "High findings",
            str(counts.get("high_findings") or 0),
        ),
        (
            "Medium findings",
            str(
                counts.get("medium_findings")
                or 0
            ),
        ),
        (
            "Low findings",
            str(counts.get("low_findings") or 0),
        ),
        (
            "Hypothesis mutation allowed",
            "false",
        ),
        (
            "Research-state mutation allowed",
            "false",
        ),
        (
            "Runtime execution allowed",
            "false",
        ),
    )

    for field, value in rows:
        table.add_row(field, value)

    console.print(table)

    observation_reviews = review.get(
        "observation_reviews"
    )

    if (
        isinstance(observation_reviews, list)
        and observation_reviews
    ):
        observation_table = Table(
            title="Observation Reviews"
        )
        observation_table.add_column("ID")
        observation_table.add_column("Request")
        observation_table.add_column("Action")
        observation_table.add_column("Hypothesis")
        observation_table.add_column("Outcome")
        observation_table.add_column("Strength")
        observation_table.add_column("Delta")
        observation_table.add_column("Status")
        observation_table.add_column("Ready")
        observation_table.add_column("Findings")

        for item in observation_reviews:
            if not isinstance(item, dict):
                continue

            observation_table.add_row(
                str(
                    item.get("observation_id")
                    or ""
                ),
                str(item.get("request_id") or "none"),
                str(item.get("action_id") or "none"),
                str(
                    item.get("hypothesis_id")
                    or "none"
                ),
                str(item.get("outcome") or ""),
                str(
                    item.get("evidence_strength")
                    or ""
                ),
                str(
                    item.get(
                        "expected_confidence_delta"
                    )
                    or 0
                ),
                str(
                    item.get("review_status")
                    or "unknown"
                ),
                str(bool(item.get("review_ready"))),
                str(item.get("finding_count") or 0),
            )

        console.print(observation_table)

    impacts = review.get(
        "expected_preliminary_hypothesis_impacts"
    )

    if isinstance(impacts, list) and impacts:
        impact_table = Table(
            title="Verified Preliminary Hypothesis Impacts"
        )
        impact_table.add_column("Hypothesis")
        impact_table.add_column("Observations")
        impact_table.add_column("Net Delta")
        impact_table.add_column("Direction")
        impact_table.add_column("Automatic Update")

        for item in impacts:
            if not isinstance(item, dict):
                continue

            impact_table.add_row(
                str(item.get("hypothesis_id") or ""),
                str(
                    item.get("observation_count")
                    or 0
                ),
                str(
                    item.get("net_confidence_delta")
                    or 0
                ),
                str(
                    item.get(
                        "preliminary_direction"
                    )
                    or ""
                ),
                str(
                    bool(
                        item.get(
                            "automatic_update_allowed"
                        )
                    )
                ),
            )

        console.print(impact_table)

    finding_sections = (
        ("Packet findings", "packet_findings"),
        (
            "Observation findings",
            "observation_findings",
        ),
        ("Impact findings", "impact_findings"),
    )

    for heading, key in finding_sections:
        findings = review.get(key)

        if not isinstance(findings, list) or not findings:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = review.get(
        "allowed_next_steps"
    )

    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:"
            "[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = review.get(
        "rejected_next_steps"
    )

    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:"
            "[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    source_packet_digest = review.get(
        "source_packet_digest"
    )
    review_digest = review.get("review_digest")

    if source_packet_digest:
        console.print(
            "[bold yellow]Source packet digest:"
            "[/bold yellow] "
            f"`{source_packet_digest}`"
        )

    if review_digest:
        console.print(
            "[bold yellow]Review digest:"
            "[/bold yellow] "
            f"`{review_digest}`"
        )

    if output_file:
        console.print(
            "[bold green]Saved observation review "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved observation review "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command "
        "performs local integrity, linkage, authorization, "
        "redaction, safety, and hypothesis-impact consistency "
        "review only. It does not execute commands, launch "
        "browsers, replay Burp requests, run Kali tools, send "
        "network requests, interact with targets, collect "
        "evidence, validate findings, automatically change "
        "hypothesis confidence, mutate research state, submit "
        "reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-observation-packet")
def brain_chat_research_observation_packet_command(
    observation_file: Path = typer.Option(
        ...,
        "--observation-file",
        "--observations",
        help=(
            "Local JSON file containing imported research "
            "observation records."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Normalize imported research observations."""
    if not observation_file.exists():
        console.print(
            "[bold red]Research observation input not found:"
            f"[/bold red] {observation_file}"
        )
        raise typer.Exit(code=1)

    try:
        packet = (
            build_research_observation_packet_from_file(
                observation_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research observation JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid research observation input:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = packet.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(title="Research Observation Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = (
        ("Observation file", str(observation_file)),
        (
            "Target",
            str(
                packet.get("target_name")
                or "unknown-target"
            ),
        ),
        (
            "Focus endpoint",
            str(
                packet.get("focus_endpoint")
                or "none"
            ),
        ),
        (
            "Packet status",
            str(
                packet.get("packet_status")
                or "unknown"
            ),
        ),
        (
            "Summary",
            str(packet.get("summary") or ""),
        ),
        (
            "Packet ready",
            str(bool(packet.get("packet_ready"))),
        ),
        (
            "Observation review ready",
            str(
                bool(
                    packet.get(
                        "observation_review_ready"
                    )
                )
            ),
        ),
        (
            "Hypothesis feedback review ready",
            str(
                bool(
                    packet.get(
                        "hypothesis_feedback_review_ready"
                    )
                )
            ),
        ),
        (
            "Research-state transition ready",
            str(
                bool(
                    packet.get(
                        "research_state_transition_ready"
                    )
                )
            ),
        ),
        (
            "Observations",
            str(
                packet.get("observation_count")
                or 0
            ),
        ),
        (
            "Linked requests",
            str(counts.get("linked_requests") or 0),
        ),
        (
            "Linked actions",
            str(counts.get("linked_actions") or 0),
        ),
        (
            "Linked hypotheses",
            str(
                counts.get("linked_hypotheses")
                or 0
            ),
        ),
        (
            "Preliminary hypothesis impacts",
            str(
                counts.get(
                    "preliminary_hypothesis_impacts"
                )
                or 0
            ),
        ),
        (
            "High findings",
            str(counts.get("high_findings") or 0),
        ),
        (
            "Medium findings",
            str(
                counts.get("medium_findings")
                or 0
            ),
        ),
        (
            "Low findings",
            str(counts.get("low_findings") or 0),
        ),
        (
            "Hypothesis mutation allowed",
            "false",
        ),
        (
            "Research-state mutation allowed",
            "false",
        ),
        (
            "Runtime execution allowed",
            "false",
        ),
    )

    for field, value in rows:
        table.add_row(field, value)

    console.print(table)

    observations = packet.get("observations")

    if isinstance(observations, list) and observations:
        observation_table = Table(
            title="Normalized Observations"
        )
        observation_table.add_column("ID")
        observation_table.add_column("Request")
        observation_table.add_column("Action")
        observation_table.add_column("Hypothesis")
        observation_table.add_column("Source")
        observation_table.add_column("Outcome")
        observation_table.add_column("Strength")
        observation_table.add_column("Delta")
        observation_table.add_column("Reviewed")

        for item in observations:
            if not isinstance(item, dict):
                continue

            observation_table.add_row(
                str(
                    item.get("observation_id")
                    or ""
                ),
                str(item.get("request_id") or "none"),
                str(item.get("action_id") or "none"),
                str(
                    item.get("hypothesis_id")
                    or "none"
                ),
                str(item.get("source_type") or ""),
                str(item.get("outcome") or ""),
                str(
                    item.get("evidence_strength")
                    or ""
                ),
                str(
                    item.get(
                        "preliminary_confidence_delta"
                    )
                    or 0
                ),
                str(
                    bool(
                        item.get("human_reviewed")
                    )
                ),
            )

        console.print(observation_table)

    impacts = packet.get(
        "preliminary_hypothesis_impacts"
    )

    if isinstance(impacts, list) and impacts:
        impact_table = Table(
            title="Preliminary Hypothesis Impacts"
        )
        impact_table.add_column("Hypothesis")
        impact_table.add_column("Observations")
        impact_table.add_column("Net Delta")
        impact_table.add_column("Direction")
        impact_table.add_column("Automatic Update")

        for item in impacts:
            if not isinstance(item, dict):
                continue

            impact_table.add_row(
                str(item.get("hypothesis_id") or ""),
                str(
                    item.get("observation_count")
                    or 0
                ),
                str(
                    item.get("net_confidence_delta")
                    or 0
                ),
                str(
                    item.get(
                        "preliminary_direction"
                    )
                    or ""
                ),
                str(
                    bool(
                        item.get(
                            "automatic_update_allowed"
                        )
                    )
                ),
            )

        console.print(impact_table)

    findings = packet.get("findings")

    if isinstance(findings, list) and findings:
        console.print(
            "[bold yellow]Observation findings:"
            "[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = packet.get(
        "allowed_next_steps"
    )

    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:"
            "[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = packet.get(
        "rejected_next_steps"
    )

    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:"
            "[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    packet_digest = packet.get("packet_digest")

    if packet_digest:
        console.print(
            "[bold yellow]Packet digest:"
            "[/bold yellow] "
            f"`{packet_digest}`"
        )

    if output_file:
        console.print(
            "[bold green]Saved observation packet "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved observation packet "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command "
        "only imports and normalizes local, user-provided "
        "observation records. It does not execute commands, "
        "launch browsers, replay Burp requests, run Kali "
        "tools, send network requests, interact with targets, "
        "collect evidence, validate findings, automatically "
        "change hypothesis confidence, mutate research state, "
        "submit reports, or confirm vulnerabilities."
    )

@app.command(
    "brain-chat-research-typed-tool-request-review-gate"
)
def brain_chat_research_typed_tool_request_review_gate_command(
    manifest_file: Path = typer.Option(
        ...,
        "--manifest-file",
        "--typed-manifest",
        help=(
            "Local JSON file containing a research typed "
            "tool-request manifest."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Review a typed research tool-request manifest."""
    if not manifest_file.exists():
        console.print(
            "[bold red]Research typed tool-request manifest "
            f"not found:[/bold red] {manifest_file}"
        )
        raise typer.Exit(code=1)

    try:
        review = (
            build_research_typed_tool_request_review_gate_from_file(
                manifest_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid typed tool-request manifest "
            f"JSON:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid typed tool-request review-gate "
            f"input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = review.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Typed Tool Request Review Gate"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    rows = (
        ("Manifest file", str(manifest_file)),
        (
            "Target",
            str(
                review.get("target_name")
                or "unknown-target"
            ),
        ),
        (
            "Focus endpoint",
            str(
                review.get("focus_endpoint")
                or "none"
            ),
        ),
        (
            "Review status",
            str(
                review.get("review_status")
                or "unknown"
            ),
        ),
        (
            "Summary",
            str(review.get("summary") or ""),
        ),
        (
            "Review ready",
            str(bool(review.get("review_ready"))),
        ),
        (
            "Runtime approval template ready",
            str(
                bool(
                    review.get(
                        "runtime_approval_template_ready"
                    )
                )
            ),
        ),
        (
            "Typed requests",
            str(
                review.get("typed_request_count")
                or 0
            ),
        ),
        (
            "Ready requests",
            str(counts.get("ready_requests") or 0),
        ),
        (
            "Blocked requests",
            str(
                counts.get("blocked_requests")
                or 0
            ),
        ),
        (
            "Manifest findings",
            str(
                counts.get("manifest_findings")
                or 0
            ),
        ),
        (
            "Request findings",
            str(
                counts.get("request_findings")
                or 0
            ),
        ),
        (
            "Execution-gate findings",
            str(counts.get("gate_findings") or 0),
        ),
        (
            "High findings",
            str(counts.get("high_findings") or 0),
        ),
        (
            "Medium findings",
            str(counts.get("medium_findings") or 0),
        ),
        (
            "Command generation allowed",
            "false",
        ),
        (
            "Package installation allowed",
            "false",
        ),
        (
            "Runtime execution allowed",
            "false",
        ),
        (
            "Network interaction allowed",
            "false",
        ),
        (
            "Target interaction allowed",
            "false",
        ),
    )

    for field, value in rows:
        table.add_row(field, value)

    console.print(table)

    request_reviews = review.get("request_reviews")

    if (
        isinstance(request_reviews, list)
        and request_reviews
    ):
        request_table = Table(
            title="Typed Request Reviews"
        )
        request_table.add_column("Request ID")
        request_table.add_column("Action ID")
        request_table.add_column("Tool Family")
        request_table.add_column("Adapter")
        request_table.add_column("Risk")
        request_table.add_column("Status")
        request_table.add_column("Ready")
        request_table.add_column("Findings")

        for item in request_reviews:
            if not isinstance(item, dict):
                continue

            request_table.add_row(
                str(item.get("request_id") or ""),
                str(item.get("action_id") or ""),
                str(item.get("tool_family") or ""),
                str(item.get("adapter_family") or ""),
                str(item.get("risk_level") or ""),
                str(
                    item.get("review_status")
                    or "unknown"
                ),
                str(bool(item.get("review_ready"))),
                str(item.get("finding_count") or 0),
            )

        console.print(request_table)

    finding_sections = (
        ("Manifest findings", "manifest_findings"),
        ("Request findings", "request_findings"),
        (
            "Execution-gate findings",
            "gate_findings",
        ),
    )

    for heading, key in finding_sections:
        findings = review.get(key)

        if not isinstance(findings, list) or not findings:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = review.get(
        "allowed_next_steps"
    )

    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:"
            "[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = review.get(
        "rejected_next_steps"
    )

    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:"
            "[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        console.print(
            "[bold green]Saved typed request review "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved typed request review "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command "
        "performs local integrity, adapter-contract, digest, "
        "focus-endpoint, and execution-gate consistency "
        "review only. It does not generate commands or "
        "payloads, install software, execute tools, launch "
        "browsers, replay Burp requests, use Kali tools, "
        "send network requests, interact with targets, "
        "collect evidence, validate findings, mutate state, "
        "submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-typed-tool-request-manifest")
def brain_chat_research_typed_tool_request_manifest_command(
    approved_action_file: Path = typer.Option(
        ...,
        "--approved-action-file",
        "--approved-actions",
        help=(
            "Local JSON file containing a research "
            "approved-action packet."
        ),
    ),
    focus_endpoint: str | None = typer.Option(
        None,
        "--focus-endpoint",
        help=(
            "Optional approved focus endpoint to include in "
            "the fail-closed execution-gate compatibility "
            "preview."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Build typed planning-only tool requests."""
    if not approved_action_file.exists():
        console.print(
            "[bold red]Research approved-action JSON "
            f"not found:[/bold red] {approved_action_file}"
        )
        raise typer.Exit(code=1)

    try:
        manifest = (
            build_research_typed_tool_request_manifest_from_file(
                approved_action_file,
                output_file=output_file,
                json_output=json_output,
                focus_endpoint=focus_endpoint,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research approved-action "
            f"JSON:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid typed tool-request manifest "
            f"input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = manifest.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Typed Tool Request Manifest"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row(
        "Approved-action file",
        str(approved_action_file),
    )
    table.add_row(
        "Target",
        str(
            manifest.get("target_name")
            or "unknown-target"
        ),
    )
    table.add_row(
        "Focus endpoint",
        str(
            manifest.get("focus_endpoint")
            or "none"
        ),
    )
    table.add_row(
        "Manifest status",
        str(
            manifest.get("manifest_status")
            or "unknown"
        ),
    )
    table.add_row(
        "Summary",
        str(manifest.get("summary") or ""),
    )
    table.add_row(
        "Manifest ready",
        str(bool(manifest.get("manifest_ready"))),
    )
    table.add_row(
        "Execution-gate input ready",
        str(
            bool(
                manifest.get(
                    "execution_gate_input_ready"
                )
            )
        ),
    )
    table.add_row(
        "Execution-gate review ready",
        str(
            bool(
                manifest.get(
                    "execution_gate_review_ready"
                )
            )
        ),
    )
    table.add_row(
        "Existing gate compatible",
        str(
            bool(
                manifest.get(
                    "existing_tool_execution_gate_compatible"
                )
            )
        ),
    )
    table.add_row(
        "Typed requests",
        str(manifest.get("typed_request_count") or 0),
    )
    table.add_row(
        "Tool families",
        str(counts.get("tool_families") or 0),
    )
    table.add_row(
        "Adapter families",
        str(counts.get("adapter_families") or 0),
    )
    table.add_row(
        "Request kinds",
        str(counts.get("request_kinds") or 0),
    )
    table.add_row(
        "Risk levels",
        str(counts.get("risk_levels") or 0),
    )
    table.add_row(
        "Runtime-gated requests",
        str(
            counts.get("runtime_gated_requests")
            or 0
        ),
    )
    table.add_row(
        "Scope-required requests",
        str(
            counts.get("scope_required_requests")
            or 0
        ),
    )
    table.add_row(
        "Controlled-assets requests",
        str(
            counts.get(
                "controlled_assets_requests"
            )
            or 0
        ),
    )
    table.add_row(
        "Observation-capture requests",
        str(
            counts.get(
                "observation_capture_requests"
            )
            or 0
        ),
    )
    table.add_row(
        "Source findings",
        str(counts.get("source_findings") or 0),
    )
    table.add_row(
        "Request findings",
        str(counts.get("request_findings") or 0),
    )
    table.add_row(
        "High findings",
        str(counts.get("high_findings") or 0),
    )
    table.add_row(
        "Medium findings",
        str(counts.get("medium_findings") or 0),
    )
    table.add_row(
        "Focus endpoint required",
        str(
            bool(
                manifest.get(
                    "requires_focus_endpoint_before_runtime_review"
                )
            )
        ),
    )
    table.add_row(
        "Gate preview decision",
        str(
            manifest.get(
                "execution_gate_preview_decision"
            )
            or "unknown"
        ),
    )
    table.add_row(
        "Gate preview execution allowed",
        str(
            bool(
                manifest.get(
                    "execution_gate_preview_execution_allowed"
                )
            )
        ),
    )
    table.add_row(
        "Command generation allowed",
        "false",
    )
    table.add_row(
        "Payload generation allowed",
        "false",
    )
    table.add_row(
        "Package installation allowed",
        "false",
    )
    table.add_row(
        "Runtime execution allowed",
        "false",
    )
    table.add_row(
        "Network interaction allowed",
        "false",
    )
    table.add_row(
        "Target interaction allowed",
        "false",
    )
    table.add_row(
        "Evidence collection allowed",
        "false",
    )
    table.add_row(
        "Validation allowed",
        "false",
    )

    console.print(table)

    typed_requests = manifest.get("typed_requests")

    if (
        isinstance(typed_requests, list)
        and typed_requests
    ):
        request_table = Table(
            title="Typed Planning Requests"
        )
        request_table.add_column("Order")
        request_table.add_column("Request ID")
        request_table.add_column("Action ID")
        request_table.add_column("Request Kind")
        request_table.add_column("Tool Family")
        request_table.add_column("Adapter")
        request_table.add_column("Risk")
        request_table.add_column("Scope")
        request_table.add_column("Assets")
        request_table.add_column("Runtime Gate")
        request_table.add_column("Eligible")

        for item in typed_requests:
            if not isinstance(item, dict):
                continue

            request_table.add_row(
                str(item.get("manual_order") or 0),
                str(item.get("request_id") or ""),
                str(item.get("action_id") or ""),
                str(item.get("request_kind") or ""),
                str(item.get("tool_family") or ""),
                str(item.get("adapter_family") or ""),
                str(item.get("risk_level") or ""),
                str(
                    bool(
                        item.get(
                            "requires_scope_confirmation"
                        )
                    )
                ),
                str(
                    bool(
                        item.get(
                            "requires_controlled_assets"
                        )
                    )
                ),
                str(
                    bool(
                        item.get(
                            "requires_runtime_gate"
                        )
                    )
                ),
                str(
                    bool(
                        item.get("manifest_eligible")
                    )
                ),
            )

        console.print(request_table)

    count_sections = (
        ("Tool family counts", "tool_family_counts"),
        (
            "Adapter family counts",
            "adapter_family_counts",
        ),
        ("Request kind counts", "request_kind_counts"),
        ("Risk level counts", "risk_level_counts"),
    )

    for heading, key in count_sections:
        values = manifest.get(key)

        if not isinstance(values, dict) or not values:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for name, count in values.items():
            console.print(f"- {name}: {count}")

    finding_sections = (
        ("Source findings", "source_findings"),
        ("Request findings", "request_findings"),
    )

    for heading, key in finding_sections:
        findings = manifest.get(key)

        if not isinstance(findings, list) or not findings:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    gate_preview = manifest.get(
        "execution_gate_preview"
    )

    if isinstance(gate_preview, dict):
        console.print(
            "[bold yellow]Execution-gate "
            "compatibility preview:[/bold yellow]"
        )
        console.print(
            "- decision: "
            f"{gate_preview.get('gate_decision', 'unknown')}"
        )
        console.print(
            "- execution_allowed: "
            f"{bool(gate_preview.get('execution_allowed'))}"
        )
        console.print(
            "- planning_only: "
            f"{bool(gate_preview.get('planning_only'))}"
        )
        console.print(
            "- execution_state: "
            f"{gate_preview.get('execution_state', 'unknown')}"
        )

        blockers = gate_preview.get("blockers")
        if isinstance(blockers, list):
            for blocker in blockers:
                console.print(f"- blocker: {blocker}")

    allowed_next_steps = manifest.get(
        "allowed_next_steps"
    )

    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = manifest.get(
        "rejected_next_steps"
    )

    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    console.print(
        "[bold yellow]Digests:[/bold yellow]"
    )
    console.print(
        "- approved-action packet: "
        f"{manifest.get('approved_action_packet_digest', '')}"
    )
    console.print(
        "- typed manifest: "
        f"{manifest.get('manifest_digest', '')}"
    )

    if output_file:
        console.print(
            "[bold green]Saved research typed tool-request "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved research typed tool-request "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only "
        "converts approved planning actions into typed, "
        "non-executable request records and builds a fail-closed "
        "execution-gate compatibility preview. It does not "
        "generate commands or payloads, install software, "
        "execute tools, launch browsers, replay Burp requests, "
        "use Kali tools, send network requests, collect "
        "evidence, validate findings, mutate state, submit "
        "reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-approved-action-packet")
def brain_chat_research_approved_action_packet_command(
    decision_file: Path = typer.Option(
        ...,
        "--decision-file",
        "--decision",
        help=(
            "Local JSON file containing a research action "
            "decision packet."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Normalize effectively approved research actions."""
    if not decision_file.exists():
        console.print(
            "[bold red]Research action decision JSON not found:"
            f"[/bold red] {decision_file}"
        )
        raise typer.Exit(code=1)

    try:
        packet = (
            build_research_approved_action_packet_from_file(
                decision_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research action decision JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid approved-action packet "
            f"input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = packet.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Approved Action Packet"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row(
        "Decision file",
        str(decision_file),
    )
    table.add_row(
        "Target",
        str(packet.get("target_name") or "unknown-target"),
    )
    table.add_row(
        "Packet status",
        str(packet.get("packet_status") or "unknown"),
    )
    table.add_row(
        "Summary",
        str(packet.get("summary") or ""),
    )
    table.add_row(
        "Reviewer",
        str(packet.get("reviewer") or "unspecified"),
    )
    table.add_row(
        "Source decision status",
        str(
            packet.get("source_decision_status")
            or "unknown"
        ),
    )
    table.add_row(
        "Source decision ready",
        str(bool(packet.get("source_decision_ready"))),
    )
    table.add_row(
        "Effective approval granted",
        str(
            bool(
                packet.get(
                    "source_effective_approval_granted"
                )
            )
        ),
    )
    table.add_row(
        "Packet ready",
        str(bool(packet.get("packet_ready"))),
    )
    table.add_row(
        "Typed manifest ready",
        str(
            bool(
                packet.get(
                    "typed_tool_request_manifest_ready"
                )
            )
        ),
    )
    table.add_row(
        "Approved actions",
        str(packet.get("approved_action_count") or 0),
    )
    table.add_row(
        "Tool families",
        str(counts.get("tool_families") or 0),
    )
    table.add_row(
        "Adapter families",
        str(counts.get("adapter_families") or 0),
    )
    table.add_row(
        "Risk levels",
        str(counts.get("risk_levels") or 0),
    )
    table.add_row(
        "Scope-confirmation actions",
        str(
            counts.get(
                "scope_confirmation_actions"
            )
            or 0
        ),
    )
    table.add_row(
        "Controlled-assets actions",
        str(
            counts.get(
                "controlled_assets_actions"
            )
            or 0
        ),
    )
    table.add_row(
        "Runtime-gated actions",
        str(
            counts.get("runtime_gated_actions")
            or 0
        ),
    )
    table.add_row(
        "Source findings",
        str(counts.get("source_findings") or 0),
    )
    table.add_row(
        "Action findings",
        str(counts.get("action_findings") or 0),
    )
    table.add_row(
        "High findings",
        str(counts.get("high_findings") or 0),
    )
    table.add_row(
        "Medium findings",
        str(counts.get("medium_findings") or 0),
    )
    table.add_row(
        "Command generation allowed",
        "false",
    )
    table.add_row(
        "Package installation allowed",
        "false",
    )
    table.add_row(
        "Runtime execution allowed",
        "false",
    )
    table.add_row(
        "Target interaction allowed",
        "false",
    )
    table.add_row(
        "Evidence collection allowed",
        "false",
    )
    table.add_row(
        "Validation allowed",
        "false",
    )

    console.print(table)

    approved_actions = packet.get("approved_actions")
    if (
        isinstance(approved_actions, list)
        and approved_actions
    ):
        actions_table = Table(
            title="Normalized Approved Actions"
        )
        actions_table.add_column("Order")
        actions_table.add_column("Action ID")
        actions_table.add_column("Action Type")
        actions_table.add_column("Tool Family")
        actions_table.add_column("Adapter")
        actions_table.add_column("Risk")
        actions_table.add_column("Runtime Gate")
        actions_table.add_column("Manifest Eligible")

        for item in approved_actions:
            if not isinstance(item, dict):
                continue

            actions_table.add_row(
                str(item.get("manual_order") or 0),
                str(item.get("action_id") or ""),
                str(item.get("action_type") or ""),
                str(item.get("tool_family") or ""),
                str(item.get("adapter_family") or ""),
                str(item.get("risk_level") or ""),
                str(
                    bool(
                        item.get(
                            "requires_runtime_gate"
                        )
                    )
                ),
                str(
                    bool(
                        item.get("manifest_eligible")
                    )
                ),
            )

        console.print(actions_table)

    count_sections = (
        ("Tool family counts", "tool_family_counts"),
        (
            "Adapter family counts",
            "adapter_family_counts",
        ),
        ("Risk level counts", "risk_level_counts"),
    )

    for heading, key in count_sections:
        values = packet.get(key)

        if not isinstance(values, dict) or not values:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for name, count in values.items():
            console.print(f"- {name}: {count}")

    finding_sections = (
        ("Source findings", "source_findings"),
        ("Action findings", "action_findings"),
    )

    for heading, key in finding_sections:
        findings = packet.get(key)

        if not isinstance(findings, list) or not findings:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = packet.get("allowed_next_steps")
    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:[/bold yellow]"
        )

        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = packet.get(
        "rejected_next_steps"
    )
    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:[/bold yellow]"
        )

        for item in rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        console.print(
            "[bold green]Saved research approved-action "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved research approved-action "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only "
        "normalizes effectively approved actions into typed "
        "planning records. It does not generate commands, "
        "install software, execute tools, launch browsers, "
        "interact with Burp Suite, use Kali tools, send "
        "requests, collect evidence, validate findings, mutate "
        "state, submit reports, or confirm vulnerabilities. "
        "A typed tool-request manifest and separate execution "
        "gate are still required."
    )

@app.command("brain-chat-research-hypothesis-feedback-decision-template")
def brain_chat_research_hypothesis_feedback_decision_template_command(
    feedback_file: Path = typer.Option(
        ...,
        "--feedback-file",
        "--feedback-packet",
        help="Local JSON file containing a hypothesis feedback packet.",
    ),
    output_file: Path = typer.Option(
        ...,
        "--output-file",
        "--output",
        help="Required output path for the local human feedback-decision template JSON.",
    ),
):
    """Build a local human decision template for hypothesis feedback."""
    if not feedback_file.exists():
        console.print(
            "[bold red]Hypothesis feedback packet JSON not found:"
            f"[/bold red] {feedback_file}"
        )
        raise typer.Exit(code=1)

    try:
        feedback_packet = load_research_hypothesis_feedback_decision_template_json(
            feedback_file
        )
        decision_template = build_research_hypothesis_feedback_decision_template(
            feedback_packet
        )
        write_research_hypothesis_feedback_decision_template_json(
            output_file,
            decision_template,
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback packet JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback decision-template input:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    decisions = decision_template.get("decisions")
    decision_count = len(decisions) if isinstance(decisions, list) else 0

    table = Table(title="Hypothesis Feedback Decision Template")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Feedback file", str(feedback_file))
    table.add_row("Output file", str(output_file))
    table.add_row("Target", str(decision_template.get("target_name") or "unknown-target"))
    table.add_row("Decision input kind", str(decision_template.get("kind") or "unknown"))
    table.add_row("Feedback decisions", str(decision_count))
    table.add_row("Default decision", "deferred")
    table.add_row("Planning only", str(bool(decision_template.get("planning_only"))))
    table.add_row("Execution state", str(decision_template.get("execution_state") or "unknown"))

    console.print(table)
    console.print(
        "[bold green]Saved hypothesis feedback decision template JSON:"
        f"[/bold green] {output_file}"
    )
    console.print(
        "[bold yellow]Next step:[/bold yellow] Set a reviewer and record exactly one accepted, rejected, changes-requested, or deferred decision for every feedback proposal before building the feedback decision packet."
    )
    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only creates a local feedback decision template. It does not accept feedback, update hypothesis confidence, mutate selection, alter investigation plans, mutate research state, execute tools, collect evidence, validate findings, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-research-hypothesis-feedback-decision-packet")
def brain_chat_research_hypothesis_feedback_decision_packet_command(
    feedback_file: Path = typer.Option(
        ...,
        "--feedback-file",
        "--feedback-packet",
        help="Local JSON file containing a hypothesis feedback packet.",
    ),
    decision_file: Path = typer.Option(
        ...,
        "--decision-file",
        "--decisions",
        help="Local JSON file containing completed human feedback decisions.",
    ),
    json_output: Path = typer.Option(
        ...,
        "--json-output",
        "--output",
        help="Required output path for the feedback decision-packet JSON.",
    ),
):
    """Build a human decision packet for hypothesis feedback."""
    if not feedback_file.exists():
        console.print(
            "[bold red]Hypothesis feedback packet JSON not found:"
            f"[/bold red] {feedback_file}"
        )
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(
            "[bold red]Hypothesis feedback decision JSON not found:"
            f"[/bold red] {decision_file}"
        )
        raise typer.Exit(code=1)

    try:
        packet = build_research_hypothesis_feedback_decision_packet_from_files(
            feedback_file,
            decision_file,
            json_output,
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback decision input JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid hypothesis feedback decision packet input:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    table = Table(title="Hypothesis Feedback Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Feedback file", str(feedback_file))
    table.add_row("Decision file", str(decision_file))
    table.add_row("JSON output", str(json_output))
    table.add_row("Target", str(packet.get("target_name") or "unknown-target"))
    table.add_row("Decision status", str(packet.get("decision_status") or "unknown"))
    table.add_row("Decision ready", str(bool(packet.get("decision_ready"))))
    table.add_row(
        "Confidence update packet ready",
        str(bool(packet.get("hypothesis_confidence_update_packet_ready"))),
    )
    table.add_row("Accepted feedback", str(packet.get("accepted_feedback_count", 0)))
    table.add_row("Rejected feedback", str(packet.get("rejected_feedback_count", 0)))
    table.add_row(
        "Changes requested",
        str(packet.get("changes_requested_feedback_count", 0)),
    )
    table.add_row("Deferred feedback", str(packet.get("deferred_feedback_count", 0)))
    table.add_row("Missing decisions", str(packet.get("missing_decision_count", 0)))
    table.add_row("Decision digest", str(packet.get("decision_digest") or ""))

    console.print(table)

    console.print(
        "[bold green]Saved hypothesis feedback decision packet JSON:"
        f"[/bold green] {json_output}"
    )

    console.print(
        "[bold yellow]Next step:[/bold yellow] If the packet is ready, build a "
        "separate confidence-update packet from accepted feedback decisions. "
        "Do not mutate hypothesis confidence directly from this packet."
    )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only records local "
        "human feedback decisions. It does not update confidence, mutate "
        "selection, alter investigation plans, mutate research state, execute "
        "tools, collect evidence, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-research-action-decision-template")
def brain_chat_research_action_decision_template_command(
    proposal_file: Path = typer.Option(
        ...,
        "--proposal-file",
        "--proposal",
        help=(
            "Local JSON file containing a research action "
            "proposal packet."
        ),
    ),
    output_file: Path = typer.Option(
        ...,
        "--output-file",
        "--output",
        help=(
            "Required output path for the local human "
            "decision-template JSON."
        ),
    ),
):
    """Build a local human decision template for action proposals."""
    if not proposal_file.exists():
        console.print(
            "[bold red]Research action proposal JSON not found:"
            f"[/bold red] {proposal_file}"
        )
        raise typer.Exit(code=1)

    try:
        proposal_packet = (
            load_research_action_decision_json(
                proposal_file
            )
        )
        decision_template = (
            build_research_action_decision_template(
                proposal_packet
            )
        )
        write_research_action_decision_json(
            output_file,
            decision_template,
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research action proposal JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid research action proposal "
            f"template input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    decisions = decision_template.get("decisions")
    decision_count = (
        len(decisions)
        if isinstance(decisions, list)
        else 0
    )

    table = Table(
        title="Research Action Decision Template"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Proposal file", str(proposal_file))
    table.add_row("Output file", str(output_file))
    table.add_row(
        "Target",
        str(
            decision_template.get("target_name")
            or "unknown-target"
        ),
    )
    table.add_row(
        "Decision input kind",
        str(decision_template.get("kind") or "unknown"),
    )
    table.add_row(
        "Action decisions",
        str(decision_count),
    )
    table.add_row(
        "Default decision",
        "deferred",
    )
    table.add_row(
        "Planning only",
        str(
            bool(
                decision_template.get("planning_only")
            )
        ),
    )
    table.add_row(
        "Execution state",
        str(
            decision_template.get("execution_state")
            or "unknown"
        ),
    )

    console.print(table)

    console.print(
        "[bold green]Saved research action decision "
        f"template JSON:[/bold green] {output_file}"
    )

    console.print(
        "[bold yellow]Next step:[/bold yellow] Set a reviewer "
        "and record exactly one approved, rejected, "
        "changes-requested, or deferred decision for every "
        "action before building the decision packet."
    )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only "
        "creates a local decision template. It does not approve "
        "actions, generate commands, install software, execute "
        "tools, send requests, collect evidence, validate "
        "findings, mutate state, submit reports, or confirm "
        "vulnerabilities."
    )


@app.command("brain-chat-research-action-decision-packet")
def brain_chat_research_action_decision_packet_command(
    proposal_file: Path = typer.Option(
        ...,
        "--proposal-file",
        "--proposal",
        help=(
            "Local JSON file containing the research action "
            "proposal packet."
        ),
    ),
    review_file: Path = typer.Option(
        ...,
        "--review-file",
        "--review",
        help=(
            "Local JSON file containing the matching action "
            "proposal review gate."
        ),
    ),
    decision_file: Path = typer.Option(
        ...,
        "--decision-file",
        "--decision",
        help=(
            "Local JSON file containing explicit human "
            "decisions for every action."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Import human decisions for reviewed research actions."""
    missing_inputs = (
        (
            proposal_file,
            "Research action proposal JSON not found",
        ),
        (
            review_file,
            "Research action proposal review JSON not found",
        ),
        (
            decision_file,
            "Research action decision JSON not found",
        ),
    )

    for input_path, message in missing_inputs:
        if not input_path.exists():
            console.print(
                f"[bold red]{message}:[/bold red] "
                f"{input_path}"
            )
            raise typer.Exit(code=1)

    try:
        packet = (
            build_research_action_decision_packet_from_files(
                proposal_file,
                review_file,
                decision_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research action decision "
            f"pipeline JSON:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid research action decision "
            f"pipeline input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = packet.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    table = Table(
        title="Research Action Decision Packet"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row(
        "Target",
        str(packet.get("target_name") or "unknown-target"),
    )
    table.add_row(
        "Decision status",
        str(packet.get("decision_status") or "unknown"),
    )
    table.add_row(
        "Summary",
        str(packet.get("summary") or ""),
    )
    table.add_row(
        "Reviewer",
        str(packet.get("reviewer") or "unspecified"),
    )
    table.add_row(
        "Proposal status",
        str(packet.get("proposal_status") or "unknown"),
    )
    table.add_row(
        "Review status",
        str(packet.get("review_status") or "unknown"),
    )
    table.add_row(
        "Decision ready",
        str(bool(packet.get("decision_ready"))),
    )
    table.add_row(
        "Effective approval granted",
        str(
            bool(
                packet.get(
                    "effective_approval_granted"
                )
            )
        ),
    )
    table.add_row(
        "Approved-action packet ready",
        str(
            bool(
                packet.get(
                    "approved_action_packet_ready"
                )
            )
        ),
    )
    table.add_row(
        "Proposal count",
        str(packet.get("proposal_count") or 0),
    )
    table.add_row(
        "Decision count",
        str(packet.get("decision_count") or 0),
    )
    table.add_row(
        "Approved",
        str(packet.get("approved_action_count") or 0),
    )
    table.add_row(
        "Rejected",
        str(packet.get("rejected_action_count") or 0),
    )
    table.add_row(
        "Changes requested",
        str(packet.get("changes_requested_count") or 0),
    )
    table.add_row(
        "Deferred",
        str(packet.get("deferred_action_count") or 0),
    )
    table.add_row(
        "Missing decisions",
        str(packet.get("missing_decision_count") or 0),
    )
    table.add_row(
        "Source findings",
        str(counts.get("source_findings") or 0),
    )
    table.add_row(
        "Decision findings",
        str(counts.get("decision_findings") or 0),
    )
    table.add_row(
        "High findings",
        str(counts.get("high_findings") or 0),
    )
    table.add_row(
        "Medium findings",
        str(counts.get("medium_findings") or 0),
    )
    table.add_row(
        "Command generation allowed",
        "false",
    )
    table.add_row(
        "Package installation allowed",
        "false",
    )
    table.add_row(
        "Runtime execution allowed",
        "false",
    )
    table.add_row(
        "Target interaction allowed",
        "false",
    )
    table.add_row(
        "Evidence collection allowed",
        "false",
    )
    table.add_row(
        "Validation allowed",
        "false",
    )

    console.print(table)

    action_decisions = packet.get("action_decisions")
    if (
        isinstance(action_decisions, list)
        and action_decisions
    ):
        decisions_table = Table(
            title="Per-Action Human Decisions"
        )
        decisions_table.add_column("Order")
        decisions_table.add_column("Action ID")
        decisions_table.add_column("Tool Family")
        decisions_table.add_column("Decision")
        decisions_table.add_column("Effective")

        for item in action_decisions:
            if not isinstance(item, dict):
                continue

            decisions_table.add_row(
                str(item.get("manual_order") or 0),
                str(item.get("action_id") or ""),
                str(
                    item.get("proposed_tool_family")
                    or ""
                ),
                str(item.get("decision") or ""),
                str(
                    bool(
                        item.get(
                            "effective_approval_granted"
                        )
                    )
                ),
            )

        console.print(decisions_table)

    finding_sections = (
        ("Source findings", "source_findings"),
        ("Decision findings", "decision_findings"),
    )

    for heading, key in finding_sections:
        findings = packet.get(key)

        if not isinstance(findings, list) or not findings:
            continue

        console.print(
            f"[bold yellow]{heading}:[/bold yellow]"
        )

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            console.print(
                "- "
                f"[{finding.get('severity', 'unknown')}] "
                f"{finding.get('category', 'finding')} / "
                f"{finding.get('subject', 'unknown')}: "
                f"{finding.get('message', '')} "
                "Required action: "
                f"{finding.get('required_action', '')}"
            )

    allowed_next_steps = packet.get("allowed_next_steps")
    if (
        isinstance(allowed_next_steps, list)
        and allowed_next_steps
    ):
        console.print(
            "[bold yellow]Allowed next steps:[/bold yellow]"
        )
        for item in allowed_next_steps:
            console.print(f"- {item}")

    rejected_next_steps = packet.get(
        "rejected_next_steps"
    )
    if (
        isinstance(rejected_next_steps, list)
        and rejected_next_steps
    ):
        console.print(
            "[bold yellow]Rejected next steps:[/bold yellow]"
        )
        for item in rejected_next_steps:
            console.print(f"- {item}")

    if output_file:
        console.print(
            "[bold green]Saved research action decision "
            f"Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved research action decision "
            f"JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only "
        "records and validates local human decisions. Effective "
        "approval permits only the next planning packet stage. "
        "It does not generate commands, install software, "
        "execute tools, launch browsers, interact with Burp "
        "Suite, use Kali tools, send requests, collect evidence, "
        "validate findings, mutate state, submit reports, or "
        "confirm vulnerabilities."
    )

@app.command("brain-chat-research-action-proposal-review-gate")
def brain_chat_research_action_proposal_review_gate_command(
    proposal_file: Path = typer.Option(
        ...,
        "--proposal-file",
        "--proposal",
        help=(
            "Local JSON file containing a research action "
            "proposal packet."
        ),
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Review a local research action proposal packet."""
    if not proposal_file.exists():
        console.print(
            "[bold red]Research action proposal JSON not found:"
            f"[/bold red] {proposal_file}"
        )
        raise typer.Exit(code=1)

    try:
        review_gate = (
            build_research_action_proposal_review_gate_from_file(
                proposal_file,
                output_file=output_file,
                json_output=json_output,
            )
        )
    except json.JSONDecodeError as exc:
        console.print(
            "[bold red]Invalid research action proposal JSON:"
            f"[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(
            "[bold red]Invalid research action proposal "
            f"review-gate input:[/bold red] {exc}"
        )
        raise typer.Exit(code=2) from exc

    counts = review_gate.get("counts") or {}

    table = Table(
        title="Brain Chat Research Action Proposal Review Gate"
    )
    table.add_column("Field", style="bold")
    table.add_column("Value")

    table.add_row("Proposal file", str(proposal_file))
    table.add_row(
        "Target",
        str(review_gate.get("target_name") or "unknown-target"),
    )
    table.add_row(
        "Review status",
        str(review_gate.get("review_status") or "unknown"),
    )
    table.add_row(
        "Recommendation",
        str(review_gate.get("recommendation") or ""),
    )
    table.add_row(
        "Proposal status",
        str(review_gate.get("proposal_status") or "unknown"),
    )
    table.add_row(
        "Source review status",
        str(review_gate.get("source_review_status") or "unknown"),
    )
    table.add_row(
        "Source review ready",
        str(bool(review_gate.get("source_review_ready"))),
    )
    table.add_row(
        "Source action proposal ready",
        str(bool(review_gate.get("source_action_proposal_ready"))),
    )
    table.add_row(
        "Plan count",
        str(review_gate.get("plan_count") or 0),
    )
    table.add_row(
        "Declared proposal count",
        str(review_gate.get("declared_proposal_count") or 0),
    )
    table.add_row(
        "Proposal count",
        str(review_gate.get("proposal_count") or 0),
    )
    table.add_row(
        "Review ready",
        str(bool(review_gate.get("review_ready"))),
    )
    table.add_row(
        "Schema findings",
        str(counts.get("schema_findings") or 0),
    )
    table.add_row(
        "Safety findings",
        str(counts.get("safety_findings") or 0),
    )
    table.add_row(
        "Proposal findings",
        str(counts.get("proposal_findings") or 0),
    )
    table.add_row(
        "High findings",
        str(counts.get("high_findings") or 0),
    )
    table.add_row(
        "Medium findings",
        str(counts.get("medium_findings") or 0),
    )
    table.add_row(
        "Human review items",
        str(counts.get("human_review_items") or 0),
    )
    table.add_row("Command generation allowed", "false")
    table.add_row("Package installation allowed", "false")
    table.add_row("Execution allowed", "false")
    table.add_row("Runtime execution allowed", "false")
    table.add_row("Target interaction allowed", "false")
    table.add_row("Evidence collection allowed", "false")
    table.add_row("Validation allowed", "false")
    table.add_row("Report submission allowed", "false")
    table.add_row("Vulnerability confirmation allowed", "false")

    console.print(table)

    finding_sections = (
        ("Schema findings", "schema_findings"),
        ("Safety findings", "safety_findings"),
        ("Proposal findings", "proposal_findings"),
    )

    for heading, key in finding_sections:
        findings = review_gate.get(key)
        if not isinstance(findings, list) or not findings:
            continue

        console.print(f"[bold yellow]{heading}:[/bold yellow]")

        for finding in findings:
            if not isinstance(finding, dict):
                continue

            severity = str(finding.get("severity") or "unknown")
            category = str(finding.get("category") or "finding")
            subject = str(finding.get("subject") or "unknown")
            message = str(finding.get("message") or "")
            required_action = str(
                finding.get("required_action") or ""
            )

            console.print(
                f"- [{severity}] {category} / {subject}: "
                f"{message} Required action: {required_action}"
            )

    human_review_items = review_gate.get("human_review_items")
    if isinstance(human_review_items, list) and human_review_items:
        console.print(
            "[bold yellow]Human review items:[/bold yellow]"
        )
        for item in human_review_items:
            console.print(f"- [ ] {item}")

    rejected_actions = review_gate.get("rejected_actions")
    if isinstance(rejected_actions, list) and rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in rejected_actions:
            console.print(f"- {item}")

    if output_file:
        console.print(
            "[bold green]Saved research action proposal "
            f"review-gate Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            "[bold green]Saved research action proposal "
            f"review-gate JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only "
        "reviews a local research action proposal packet. It does "
        "not generate commands, install software, execute tools, "
        "launch browsers, interact with Burp Suite, use Kali tools, "
        "send requests, collect evidence, validate findings, mutate "
        "state, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-action-proposal-packet")
def brain_chat_research_action_proposal_packet_command(
    plan_file: Path = typer.Option(
        ...,
        "--plan-file",
        "--plan",
        help="Local JSON file containing a research investigation plan packet.",
    ),
    review_file: Path = typer.Option(
        ...,
        "--review-file",
        "--review",
        help="Local JSON file containing the matching investigation plan review gate.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional Markdown output path.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional JSON output path.",
    ),
):
    """Build local-only research action proposals from a reviewed investigation plan."""
    if not plan_file.exists():
        console.print(
            f"[bold red]Research investigation plan JSON not found:[/bold red] {plan_file}"
        )
        raise typer.Exit(code=1)

    if not review_file.exists():
        console.print(
            f"[bold red]Research investigation plan review JSON not found:[/bold red] {review_file}"
        )
        raise typer.Exit(code=1)

    try:
        packet = build_research_action_proposal_packet_from_files(
            plan_file,
            review_file,
            output_file=output_file,
            json_output=json_output,
        )
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research action proposal input JSON:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(f"[bold red]Invalid research action proposal input:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    table = Table(title="Brain Chat Research Action Proposal Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Plan file", str(plan_file))
    table.add_row("Review file", str(review_file))
    table.add_row("Target", packet.target_name)
    table.add_row("Proposal status", packet.proposal_status)
    table.add_row("Review status", packet.review_status)
    table.add_row("Review ready", str(packet.review_ready))
    table.add_row("Action proposal ready", str(packet.action_proposal_ready))
    table.add_row("Plan count", str(packet.plan_count))
    table.add_row("Proposal count", str(packet.proposal_count))
    table.add_row("Blockers", str(len(packet.blockers)))
    table.add_row("Human review items", str(len(packet.human_review_items)))
    table.add_row("Execution allowed", "false")
    table.add_row("Runtime execution allowed", "false")
    table.add_row("Command generation allowed", "false")
    table.add_row("Package installation", "false")
    table.add_row("Target interaction", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    if packet.proposals:
        console.print("[bold yellow]Proposed actions:[/bold yellow]")
        for item in packet.proposals:
            console.print(
                f"- {item.action_id} [{item.action_type}] "
                f"{item.hypothesis_id}: {item.title} "
                f"(tool-family={item.proposed_tool_family}, execution=false)"
            )

    if packet.blockers:
        console.print("[bold yellow]Blockers:[/bold yellow]")
        for item in packet.blockers:
            console.print(f"- {item}")

    if packet.human_review_items:
        console.print("[bold yellow]Human review items:[/bold yellow]")
        for item in packet.human_review_items:
            console.print(f"- [ ] {item}")

    if packet.rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in packet.rejected_actions:
            console.print(f"- {item}")

    if output_file:
        console.print(
            f"[bold green]Saved research action proposal Markdown:[/bold green] {output_file}"
        )

    if json_output:
        console.print(
            f"[bold green]Saved research action proposal JSON:[/bold green] {json_output}"
        )

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds local research action proposals. "
        "It does not generate executable commands, install software, execute tools, launch browsers, "
        "interact with Burp Suite, send requests, collect evidence, validate findings, mutate state, "
        "submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-investigation-plan-review-gate")
def brain_chat_research_investigation_plan_review_gate_command(
    plan_file: Path = typer.Option(..., "--plan-file", "--plan", help="Local JSON file containing a research investigation plan packet."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Review a local research investigation plan packet before human review."""
    if not plan_file.exists():
        console.print(f"[bold red]Research investigation plan JSON not found:[/bold red] {plan_file}")
        raise typer.Exit(code=1)

    try:
        if output_file:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        if json_output:
            json_output.parent.mkdir(parents=True, exist_ok=True)

        review_gate = build_research_investigation_plan_review_gate_from_file(
            plan_file,
            output_file=output_file,
            json_output=json_output,
        )
    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid research investigation plan JSON:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    except ValueError as exc:
        console.print(f"[bold red]Invalid investigation plan review gate input:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    table = Table(title="Brain Chat Research Investigation Plan Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Plan file", str(plan_file))
    table.add_row("Target", str(review_gate.get("target_name", "unknown-target")))
    table.add_row("Review status", str(review_gate.get("review_status", "unknown")))
    table.add_row("Recommendation", str(review_gate.get("recommendation", "")))
    table.add_row("Packet status", str(review_gate.get("packet_status", "unknown")))
    table.add_row("Investigation plan status", str(review_gate.get("investigation_plan_status", "unknown")))
    table.add_row("Selected count", str(review_gate.get("selected_count", 0)))
    table.add_row("Plan count", str(review_gate.get("plan_count", 0)))
    table.add_row("Review ready", str(review_gate.get("review_ready", False)))
    table.add_row("Schema findings", str(len(review_gate.get("schema_findings", []))))
    table.add_row("Safety findings", str(len(review_gate.get("safety_findings", []))))
    table.add_row("Plan findings", str(len(review_gate.get("plan_findings", []))))
    table.add_row("Human review items", str(len(review_gate.get("human_review_items", []))))
    table.add_row("Rejected actions", str(len(review_gate.get("rejected_actions", []))))
    table.add_row("Runtime execution allowed", "false")
    table.add_row("Validation allowed", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)

    schema_findings = review_gate.get("schema_findings", [])
    if schema_findings:
        console.print("[bold yellow]Schema findings:[/bold yellow]")
        for item in schema_findings:
            console.print(f"- [{item.get('severity', 'unknown')}] {item.get('subject', 'unknown')}: {item.get('message', '')}")

    safety_findings = review_gate.get("safety_findings", [])
    if safety_findings:
        console.print("[bold yellow]Safety findings:[/bold yellow]")
        for item in safety_findings:
            console.print(f"- [{item.get('severity', 'unknown')}] {item.get('subject', 'unknown')}: {item.get('message', '')}")

    plan_findings = review_gate.get("plan_findings", [])
    if plan_findings:
        console.print("[bold yellow]Plan findings:[/bold yellow]")
        for item in plan_findings:
            console.print(f"- [{item.get('severity', 'unknown')}] {item.get('subject', 'unknown')}: {item.get('message', '')}")

    human_review_items = review_gate.get("human_review_items", [])
    if human_review_items:
        console.print("[bold yellow]Human review items:[/bold yellow]")
        for item in human_review_items:
            console.print(f"- [ ] {item}")

    rejected_actions = review_gate.get("rejected_actions", [])
    if rejected_actions:
        console.print("[bold yellow]Rejected actions:[/bold yellow]")
        for item in rejected_actions:
            console.print(f"- {item}")

    if output_file:
        console.print(f"[bold green]Saved research investigation plan review gate Markdown:[/bold green] {output_file}")

    if json_output:
        console.print(f"[bold green]Saved research investigation plan review gate JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only reviews a local research investigation plan packet. "
        "It does not browse, generate commands, execute tools, launch browsers, use Kali tools, send requests, "
        "collect evidence, validate findings, submit reports, write state, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-hypothesis-selection-packet")
def brain_chat_research_hypothesis_selection_packet_command(
    sources_file: Path = typer.Option(..., "--sources-file", "--sources", help="Local JSON file containing research sources."),
    target_name: str = typer.Option("unknown-target", "--target-name", "--target", help="Target name for the selection packet."),
    max_selected: int = typer.Option(3, "--max-selected", help="Maximum number of hypotheses to select."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic research hypothesis selection packet."""
    if not sources_file.exists():
        console.print(f"[bold red]Research sources JSON not found:[/bold red] {sources_file}")
        raise typer.Exit(code=1)

    resolved_target_name = target_name

    try:
        raw = json.loads(sources_file.read_text(encoding="utf-8"))

        if isinstance(raw, dict):
            if raw.get("target_name"):
                resolved_target_name = str(raw.get("target_name"))
            raw_sources = raw.get("sources", [])
        else:
            raw_sources = raw

        if not isinstance(raw_sources, list):
            console.print("[bold red]Research sources JSON must be a list or an object with a sources list.[/bold red]")
            raise typer.Exit(code=1)

        if not all(isinstance(item, dict) for item in raw_sources):
            console.print("[bold red]Each research source must be a JSON object.[/bold red]")
            raise typer.Exit(code=1)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    source_packet = build_research_source_packet(raw_sources, target_name=resolved_target_name)
    hypothesis_packet = build_research_hypothesis_packet(source_packet)
    packet = build_research_hypothesis_selection_packet(hypothesis_packet, max_selected=max_selected)

    markdown = packet.to_markdown()
    data = packet.to_dict()

    table = Table(title="Brain Chat Research Hypothesis Selection Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target name", packet.target_name)
    table.add_row("Packet status", packet.packet_status)
    table.add_row("Hypothesis packet status", packet.hypothesis_packet_status)
    table.add_row("Selection status", packet.selection_status)
    table.add_row("Selected count", str(packet.selected_count))
    table.add_row("Primary hypothesis", packet.primary_hypothesis_id or "none")
    table.add_row("Selection gaps", str(len(packet.selection_gaps)))
    table.add_row("Allowed local next steps", str(len(packet.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(packet.rejected_actions)))
    table.add_row("Web browsing", "false")
    table.add_row("Network interaction", "false")
    table.add_row("Command generation", "false")
    table.add_row("Tool execution", "false")
    table.add_row("Browser execution", "false")
    table.add_row("Curl execution", "false")
    table.add_row("Kali execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Selection status:[/bold yellow] {packet.selection_status}")

    if packet.selected_hypotheses:
        console.print("[bold yellow]Selected hypotheses:[/bold yellow]")
        for item in packet.selected_hypotheses:
            console.print(
                f"- rank={item.selection_rank} score={item.selection_score} "
                f"{item.hypothesis_id} [{item.priority}/{item.confidence}] "
                f"{item.hypothesis_type} :: {item.attack_surface}"
            )

    if packet.selection_gaps:
        console.print("[bold yellow]Selection gaps:[/bold yellow]")
        for item in packet.selection_gaps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in packet.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research hypothesis selection packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research hypothesis selection packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic research hypothesis selection packet. "
        "It does not browse, generate commands, execute tools, send requests, collect evidence, validate, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-research-hypothesis-packet")
def brain_chat_research_hypothesis_packet_command(
    sources_file: Path = typer.Option(..., "--sources-file", "--sources", help="Local JSON file containing research sources."),
    target_name: str = typer.Option("unknown-target", "--target-name", "--target", help="Target name for the hypothesis packet."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic research hypothesis packet."""
    if not sources_file.exists():
        console.print(f"[bold red]Research sources JSON not found:[/bold red] {sources_file}")
        raise typer.Exit(code=1)

    resolved_target_name = target_name

    try:
        raw = json.loads(sources_file.read_text(encoding="utf-8"))

        if isinstance(raw, dict):
            if raw.get("target_name"):
                resolved_target_name = str(raw.get("target_name"))
            raw_sources = raw.get("sources", [])
        else:
            raw_sources = raw

        if not isinstance(raw_sources, list):
            console.print("[bold red]Research sources JSON must be a list or an object with a sources list.[/bold red]")
            raise typer.Exit(code=1)

        if not all(isinstance(item, dict) for item in raw_sources):
            console.print("[bold red]Each research source must be a JSON object.[/bold red]")
            raise typer.Exit(code=1)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    source_packet = build_research_source_packet(raw_sources, target_name=resolved_target_name)
    packet = build_research_hypothesis_packet(source_packet)
    markdown = packet.to_markdown()
    data = packet.to_dict()

    table = Table(title="Brain Chat Research Hypothesis Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target name", packet.target_name)
    table.add_row("Packet status", packet.packet_status)
    table.add_row("Source packet status", packet.source_packet_status)
    table.add_row("Hypothesis count", str(packet.hypothesis_count))
    table.add_row("Source gaps", str(len(packet.source_gaps)))
    table.add_row("Hypothesis gaps", str(len(packet.hypothesis_gaps)))
    table.add_row("Allowed local next steps", str(len(packet.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(packet.rejected_actions)))
    table.add_row("Web browsing", "false")
    table.add_row("Network interaction", "false")
    table.add_row("Command generation", "false")
    table.add_row("Tool execution", "false")
    table.add_row("Browser execution", "false")
    table.add_row("Curl execution", "false")
    table.add_row("Kali execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Packet status:[/bold yellow] {packet.packet_status}")

    if packet.hypotheses:
        console.print("[bold yellow]Hypotheses:[/bold yellow]")
        for item in packet.hypotheses:
            console.print(f"- {item.hypothesis_id} [{item.priority}/{item.confidence}] {item.title}")

    if packet.source_gaps:
        console.print("[bold yellow]Source gaps:[/bold yellow]")
        for item in packet.source_gaps:
            console.print(f"- {item}")

    if packet.hypothesis_gaps:
        console.print("[bold yellow]Hypothesis gaps:[/bold yellow]")
        for item in packet.hypothesis_gaps:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in packet.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research hypothesis packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research hypothesis packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic research hypothesis packet. "
        "It does not browse, generate commands, execute tools, send requests, collect evidence, validate, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-research-source-packet")
def brain_chat_research_source_packet_command(
    sources_file: Path | None = typer.Option(None, "--sources-file", "--sources", help="Optional local JSON file containing research sources."),
    target_name: str = typer.Option("unknown-target", "--target-name", "--target", help="Target name for the research packet."),
    output_file: Path | None = typer.Option(None, "--output-file", "--output", help="Optional Markdown output path."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional JSON output path."),
):
    """Build a local deterministic research source packet."""
    raw_sources = []
    resolved_target_name = target_name

    try:
        if sources_file is not None:
            if not sources_file.exists():
                console.print(f"[bold red]Research sources JSON not found:[/bold red] {sources_file}")
                raise typer.Exit(code=1)

            raw = json.loads(sources_file.read_text(encoding="utf-8"))

            if isinstance(raw, dict):
                if raw.get("target_name"):
                    resolved_target_name = str(raw.get("target_name"))
                raw_sources = raw.get("sources", [])
            else:
                raw_sources = raw

            if not isinstance(raw_sources, list):
                console.print("[bold red]Research sources JSON must be a list or an object with a sources list.[/bold red]")
                raise typer.Exit(code=1)

            if not all(isinstance(item, dict) for item in raw_sources):
                console.print("[bold red]Each research source must be a JSON object.[/bold red]")
                raise typer.Exit(code=1)

    except json.JSONDecodeError as exc:
        console.print(f"[bold red]Invalid JSON:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    packet = build_research_source_packet(raw_sources, target_name=resolved_target_name)
    markdown = packet.to_markdown()
    data = packet.to_dict()

    table = Table(title="Brain Chat Research Source Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target name", packet.target_name)
    table.add_row("Packet status", packet.packet_status)
    table.add_row("Source count", str(packet.source_count))
    table.add_row("Source types", ", ".join(packet.source_types) if packet.source_types else "none")
    table.add_row("Research questions", str(len(packet.research_questions)))
    table.add_row("Likely attack surfaces", str(len(packet.likely_attack_surfaces)))
    table.add_row("Source gaps", str(len(packet.source_gaps)))
    table.add_row("Allowed local next steps", str(len(packet.allowed_local_next_steps)))
    table.add_row("Rejected actions", str(len(packet.rejected_actions)))
    table.add_row("Web browsing", "false")
    table.add_row("Network interaction", "false")
    table.add_row("Tool execution", "false")
    table.add_row("Browser execution", "false")
    table.add_row("Curl execution", "false")
    table.add_row("Kali execution", "false")
    table.add_row("Evidence collection", "false")
    table.add_row("Validation execution", "false")
    table.add_row("Report submission", "false")
    table.add_row("Vulnerability confirmation", "false")
    console.print(table)
    console.print(f"[bold yellow]Packet status:[/bold yellow] {packet.packet_status}")

    if packet.likely_attack_surfaces:
        console.print("[bold yellow]Likely attack surfaces:[/bold yellow]")
        for item in packet.likely_attack_surfaces:
            console.print(f"- {item}")

    if packet.source_gaps:
        console.print("[bold yellow]Source gaps:[/bold yellow]")
        for item in packet.source_gaps:
            console.print(f"- {item}")

    if packet.research_questions:
        console.print("[bold yellow]Research questions:[/bold yellow]")
        for item in packet.research_questions:
            console.print(f"- {item}")

    console.print("[bold yellow]Rejected actions:[/bold yellow]")
    for item in packet.rejected_actions:
        console.print(f"- {item}")

    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(markdown, encoding="utf-8")
        console.print(f"[bold green]Saved research source packet Markdown:[/bold green] {output_file}")

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        console.print(f"[bold green]Saved research source packet JSON:[/bold green] {json_output}")

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local deterministic research source packet. "
        "It does not browse the web, call providers, execute tools, send requests, collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-hypothesis-confidence-update-packet")
def brain_chat_research_hypothesis_confidence_update_packet_command(
    hypothesis_file: Path = typer.Option(..., "--hypothesis-file", "--hypothesis-packet", help="Path to source research hypothesis packet JSON."),
    decision_file: Path = typer.Option(..., "--decision-file", "--decision-packet", help="Path to accepted hypothesis feedback decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for confidence update packet."),
):
    """Build a local-only proposed hypothesis confidence update packet."""
    if not hypothesis_file.exists():
        console.print(f"[bold red]Hypothesis packet JSON not found:[/bold red] {hypothesis_file}")
        raise typer.Exit(code=1)

    if not decision_file.exists():
        console.print(f"[bold red]Feedback decision packet JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_hypothesis_confidence_update_packet_from_files(
            hypothesis_file,
            decision_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Hypothesis Confidence Update Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["update_status"])
    table.add_row("Hypotheses", str(packet["hypothesis_count"]))
    table.add_row("Accepted feedback", str(packet["accepted_feedback_count"]))
    table.add_row("Confidence updates", str(packet["confidence_update_count"]))
    table.add_row("Transition review required", str(packet["research_state_transition_review_required"]))
    table.add_row("State transition ready", str(packet["research_state_transition_ready"]))
    table.add_row("Execution", "planning-only; no confidence mutation, state mutation, target interaction, or tool execution")
    console.print(table)

    if packet["confidence_updates"]:
        updates = Table(title="Proposed Confidence Updates")
        updates.add_column("Update")
        updates.add_column("Hypothesis")
        updates.add_column("Current")
        updates.add_column("Proposed")
        updates.add_column("Ready")
        for item in packet["confidence_updates"]:
            updates.add_row(
                item["update_id"],
                item["hypothesis_id"],
                item["current_confidence"],
                item["proposed_confidence"],
                str(item["effective_confidence_update_ready"]),
            )
        console.print(updates)

    if json_output:
        console.print(f"[bold green]Saved hypothesis confidence update packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local proposed confidence update packet. "
        "It does not mutate hypothesis confidence, persistent research state, selected hypotheses, investigation plans, "
        "targets, evidence, reports, or vulnerability status."
    )

@app.command("brain-chat-research-state-transition-review-gate")
def brain_chat_research_state_transition_review_gate_command(
    update_file: Path = typer.Option(..., "--update-file", "--confidence-update-packet", help="Path to hypothesis confidence update packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for research-state transition review gate."),
):
    """Build a local-only research-state transition review gate."""
    if not update_file.exists():
        console.print(f"[bold red]Confidence update packet JSON not found:[/bold red] {update_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_transition_review_gate_from_file(
            update_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["gate_status"])
    table.add_row("Confidence updates", str(gate["confidence_update_count"]))
    table.add_row("Transition candidates", str(gate["transition_candidate_count"]))
    table.add_row("Transition review ready", str(gate["transition_review_ready"]))
    table.add_row("Human decision required", str(gate["human_transition_decision_required"]))
    table.add_row("State transition packet ready", str(gate["research_state_transition_packet_ready"]))
    table.add_row("Execution", "planning-only; no confidence mutation, state mutation, target interaction, or tool execution")
    console.print(table)

    if gate["transition_candidates"]:
        candidates = Table(title="Transition Candidates")
        candidates.add_column("Transition")
        candidates.add_column("Hypothesis")
        candidates.add_column("Current")
        candidates.add_column("Proposed")
        candidates.add_column("Decision")
        for item in gate["transition_candidates"]:
            candidates.add_row(
                item["transition_id"],
                item["hypothesis_id"],
                item["current_confidence"],
                item["proposed_confidence"],
                item["review_decision"],
            )
        console.print(candidates)

    if json_output:
        console.print(f"[bold green]Saved research-state transition review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local transition review gate. "
        "It does not mutate hypothesis confidence, persistent research state, selected hypotheses, investigation plans, "
        "targets, evidence, reports, or vulnerability status."
    )

@app.command("brain-chat-research-state-transition-decision-template")
def brain_chat_research_state_transition_decision_template_command(
    gate_file: Path = typer.Option(..., "--gate-file", "--transition-review-gate", help="Path to research-state transition review gate JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for transition decision template."),
):
    """Build a local-only human transition decision template."""
    if not gate_file.exists():
        console.print(f"[bold red]Research-state transition review gate JSON not found:[/bold red] {gate_file}")
        raise typer.Exit(code=1)

    try:
        template = build_research_state_transition_decision_template_from_file(
            gate_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Decision Template")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", template["target_name"])
    table.add_row("Status", template["template_status"])
    table.add_row("Transition decisions", str(template["transition_decision_count"]))
    table.add_row("Human decision required", str(template["human_transition_decision_required"]))
    table.add_row("Human decision complete", str(template["human_transition_decision_complete"]))
    table.add_row("State transition packet ready", str(template["research_state_transition_packet_ready"]))
    table.add_row("Execution", "planning-only; no confidence mutation, state mutation, target interaction, or tool execution")
    console.print(table)

    if template["transition_decisions"]:
        decisions = Table(title="Pending Transition Decisions")
        decisions.add_column("Decision")
        decisions.add_column("Transition")
        decisions.add_column("Hypothesis")
        decisions.add_column("Current")
        decisions.add_column("Proposed")
        decisions.add_column("Status")
        for item in template["transition_decisions"]:
            decisions.add_row(
                item["decision_id"],
                item["transition_id"],
                item["hypothesis_id"],
                item["current_confidence"],
                item["proposed_confidence"],
                item["decision"],
            )
        console.print(decisions)

    if json_output:
        console.print(f"[bold green]Saved research-state transition decision template JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(template, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local human decision template. "
        "It does not approve transitions, mutate hypothesis confidence, mutate persistent research state, "
        "execute tools, interact with targets, collect evidence, submit reports, or confirm vulnerabilities."
    )


@app.command("brain-chat-research-state-transition-decision-packet")
def brain_chat_research_state_transition_decision_packet_command(
    gate_file: Path = typer.Option(..., "--gate-file", "--transition-review-gate", help="Path to research-state transition review gate JSON."),
    template_file: Path = typer.Option(..., "--template-file", "--decision-template", help="Path to completed transition decision template JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for transition decision packet."),
):
    """Build a local-only human transition decision packet."""
    if not gate_file.exists():
        console.print(f"[bold red]Research-state transition review gate JSON not found:[/bold red] {gate_file}")
        raise typer.Exit(code=1)
    if not template_file.exists():
        console.print(f"[bold red]Research-state transition decision template JSON not found:[/bold red] {template_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_transition_decision_packet_from_files(
            gate_file,
            template_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Transition decisions", str(packet["transition_decision_count"]))
    table.add_row("Approved transitions", str(packet["approved_transition_count"]))
    table.add_row("Decision complete", str(packet["human_transition_decision_complete"]))
    table.add_row("Transition packet ready", str(packet["research_state_transition_packet_ready"]))
    table.add_row("Execution", "planning-only; no confidence mutation, state mutation, target interaction, or tool execution")
    console.print(table)

    if packet["transition_decisions"]:
        decisions = Table(title="Human Transition Decisions")
        decisions.add_column("Decision")
        decisions.add_column("Transition")
        decisions.add_column("Hypothesis")
        decisions.add_column("Choice")
        decisions.add_column("Approved")
        for item in packet["transition_decisions"]:
            decisions.add_row(
                item["decision_id"],
                item["transition_id"],
                item["hypothesis_id"],
                item["decision"],
                str(item["approved_for_state_transition_packet"]),
            )
        console.print(decisions)

    if json_output:
        console.print(f"[bold green]Saved research-state transition decision packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local human decision packet. "
        "It does not apply confidence updates, mutate persistent research state, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-transition-packet")
def brain_chat_research_state_transition_packet_command(
    decision_file: Path = typer.Option(..., "--decision-file", "--transition-decision-packet", help="Path to completed research-state transition decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for local research-state transition packet."),
):
    """Build a local-only research-state transition packet."""
    if not decision_file.exists():
        console.print(f"[bold red]Research-state transition decision packet JSON not found:[/bold red] {decision_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_transition_packet_from_file(
            decision_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Local Research-State Transition Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["packet_status"])
    table.add_row("Approved transitions", str(packet["approved_transition_count"]))
    table.add_row("Transition operations", str(packet["transition_operation_count"]))
    table.add_row("Apply review required", str(packet["research_state_transition_apply_review_required"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["transition_operations"]:
        operations = Table(title="Local Transition Operations")
        operations.add_column("Operation")
        operations.add_column("Hypothesis")
        operations.add_column("Field")
        operations.add_column("Current")
        operations.add_column("Proposed")
        operations.add_column("Apply Review")
        for item in packet["transition_operations"]:
            operations.add_row(
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
                str(item["apply_review_required"]),
            )
        console.print(operations)

    if json_output:
        console.print(f"[bold green]Saved local research-state transition packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local transition packet. "
        "It does not write persistent research state, mutate hypothesis confidence, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-transition-apply-review-gate")
def brain_chat_research_state_transition_apply_review_gate_command(
    transition_packet_file: Path = typer.Option(..., "--transition-packet-file", "--transition-packet", help="Path to local research-state transition packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for apply review gate."),
):
    """Build a local-only research-state transition apply review gate."""
    if not transition_packet_file.exists():
        console.print(f"[bold red]Research-state transition packet JSON not found:[/bold red] {transition_packet_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_transition_apply_review_gate_from_file(
            transition_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Apply Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["gate_status"])
    table.add_row("Transition operations", str(gate["transition_operation_count"]))
    table.add_row("Apply review items", str(gate["apply_review_item_count"]))
    table.add_row("Apply review ready", str(gate["apply_review_ready"]))
    table.add_row("Human apply decision required", str(gate["human_apply_decision_required"]))
    table.add_row("Persistent write ready", str(gate["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(gate["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if gate["apply_review_items"]:
        items = Table(title="Apply Review Items")
        items.add_column("Review Item")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        items.add_column("Decision Required")
        for item in gate["apply_review_items"]:
            items.add_row(
                item["review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
                str(item["human_apply_decision_required"]),
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved research-state transition apply review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local apply review gate. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-transition-apply-decision-packet")
def brain_chat_research_state_transition_apply_decision_packet_command(
    apply_review_gate_file: Path = typer.Option(..., "--apply-review-gate-file", "--apply-review-gate", help="Path to research-state transition apply review gate JSON."),
    human_apply_decisions_file: Path = typer.Option(..., "--human-apply-decisions-file", "--apply-decisions", help="Path to human apply decisions JSON array."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for apply decision packet."),
):
    """Build a local-only human apply decision packet."""
    if not apply_review_gate_file.exists():
        console.print(f"[bold red]Research-state transition apply review gate JSON not found:[/bold red] {apply_review_gate_file}")
        raise typer.Exit(code=1)

    if not human_apply_decisions_file.exists():
        console.print(f"[bold red]Human apply decisions JSON not found:[/bold red] {human_apply_decisions_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_transition_apply_decision_packet_from_files(
            apply_review_gate_file,
            human_apply_decisions_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Apply Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Apply review items", str(packet["apply_review_item_count"]))
    table.add_row("Apply decisions", str(packet["apply_decision_count"]))
    table.add_row("Approved apply decisions", str(packet["approved_apply_decision_count"]))
    table.add_row("Human apply decision complete", str(packet["human_apply_decision_complete"]))
    table.add_row("Apply preview ready", str(packet["research_state_transition_apply_preview_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["apply_decisions"]:
        decisions = Table(title="Human Apply Decisions")
        decisions.add_column("Decision")
        decisions.add_column("Review Item")
        decisions.add_column("Operation")
        decisions.add_column("Hypothesis")
        decisions.add_column("Field")
        decisions.add_column("Value")
        decisions.add_column("Preview")
        for item in packet["apply_decisions"]:
            decisions.add_row(
                item["apply_decision_id"],
                item["review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["decision"],
                str(item["apply_preview_required"]),
            )
        console.print(decisions)

    if json_output:
        console.print(f"[bold green]Saved research-state transition apply decision packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local human apply decision packet. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-transition-apply-preview")
def brain_chat_research_state_transition_apply_preview_command(
    apply_decision_packet_file: Path = typer.Option(..., "--apply-decision-packet-file", "--apply-decision-packet", help="Path to research-state transition apply decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for local apply preview."),
):
    """Build a local-only research-state transition apply preview."""
    if not apply_decision_packet_file.exists():
        console.print(f"[bold red]Research-state transition apply decision packet JSON not found:[/bold red] {apply_decision_packet_file}")
        raise typer.Exit(code=1)

    try:
        preview = build_research_state_transition_apply_preview_from_file(
            apply_decision_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Transition Apply Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", preview["target_name"])
    table.add_row("Status", preview["preview_status"])
    table.add_row("Approved apply decisions", str(preview["approved_apply_decision_count"]))
    table.add_row("Preview items", str(preview["preview_item_count"]))
    table.add_row("Apply preview ready", str(preview["apply_preview_ready"]))
    table.add_row("Persistence review required", str(preview["persistence_write_review_gate_required"]))
    table.add_row("Persistence review ready", str(preview["persistence_write_review_gate_ready"]))
    table.add_row("Persistent write ready", str(preview["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(preview["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if preview["preview_items"]:
        items = Table(title="Apply Preview Items")
        items.add_column("Preview")
        items.add_column("Apply Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in preview["preview_items"]:
            items.add_row(
                item["preview_item_id"],
                item["apply_decision_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved research-state transition apply preview JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(preview, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local apply preview. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-persistence-write-review-gate")
def brain_chat_research_state_persistence_write_review_gate_command(
    apply_preview_file: Path = typer.Option(..., "--apply-preview-file", "--apply-preview", help="Path to research-state transition apply preview JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for persistence write review gate."),
):
    """Build a local-only persistence write review gate."""
    if not apply_preview_file.exists():
        console.print(f"[bold red]Research-state transition apply preview JSON not found:[/bold red] {apply_preview_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_persistence_write_review_gate_from_file(
            apply_preview_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Research-State Persistence Write Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["gate_status"])
    table.add_row("Apply preview items", str(gate["apply_preview_item_count"]))
    table.add_row("Review items", str(gate["persistence_write_review_item_count"]))
    table.add_row("Persistence review ready", str(gate["persistence_write_review_ready"]))
    table.add_row("Human decision required", str(gate["human_persistence_write_decision_required"]))
    table.add_row("Human decision complete", str(gate["human_persistence_write_decision_complete"]))
    table.add_row("Decision packet ready", str(gate["persistence_write_decision_packet_ready"]))
    table.add_row("Persistent write ready", str(gate["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(gate["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if gate["review_items"]:
        items = Table(title="Persistence Write Review Items")
        items.add_column("Review")
        items.add_column("Preview")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in gate["review_items"]:
            items.add_row(
                item["persistence_write_review_item_id"],
                item["preview_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved persistence write review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local review gate. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-persistence-write-decision-packet")
def brain_chat_research_state_persistence_write_decision_packet_command(
    persistence_write_review_gate_file: Path = typer.Option(..., "--persistence-write-review-gate-file", "--write-review-gate", help="Path to persistence write review gate JSON."),
    human_persistence_write_decisions_file: Path = typer.Option(..., "--human-persistence-write-decisions-file", "--write-decisions", help="Path to human persistence write decisions JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for human persistence write decision packet."),
):
    """Build a human persistence write decision packet."""
    if not persistence_write_review_gate_file.exists():
        console.print(f"[bold red]Persistence write review gate JSON not found:[/bold red] {persistence_write_review_gate_file}")
        raise typer.Exit(code=1)

    if not human_persistence_write_decisions_file.exists():
        console.print(f"[bold red]Human persistence write decisions JSON not found:[/bold red] {human_persistence_write_decisions_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_persistence_write_decision_packet_from_files(
            persistence_write_review_gate_file,
            human_persistence_write_decisions_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Human Persistence Write Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Review items", str(packet["persistence_write_review_item_count"]))
    table.add_row("Decisions", str(packet["persistence_write_decision_count"]))
    table.add_row("Approved decisions", str(packet["approved_persistence_write_decision_count"]))
    table.add_row("Human decision required", str(packet["human_persistence_write_decision_required"]))
    table.add_row("Human decision complete", str(packet["human_persistence_write_decision_complete"]))
    table.add_row("Local write packet preview required", str(packet["local_write_packet_preview_required"]))
    table.add_row("Local write packet preview ready", str(packet["local_write_packet_preview_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["persistence_write_decisions"]:
        items = Table(title="Persistence Write Decisions")
        items.add_column("Decision")
        items.add_column("Review")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Decision value")
        items.add_column("Approved")
        for item in packet["persistence_write_decisions"]:
            items.add_row(
                item["persistence_write_decision_id"],
                item["persistence_write_review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["decision"],
                str(item["local_write_packet_preview_required"]),
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved human persistence write decision packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only records human persistence write decisions. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-local-write-packet-preview")
def brain_chat_research_state_local_write_packet_preview_command(
    persistence_write_decision_packet_file: Path = typer.Option(..., "--persistence-write-decision-packet-file", "--write-decision-packet", help="Path to persistence write decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for local write packet preview."),
):
    """Build a local-only write packet preview."""
    if not persistence_write_decision_packet_file.exists():
        console.print(f"[bold red]Persistence write decision packet JSON not found:[/bold red] {persistence_write_decision_packet_file}")
        raise typer.Exit(code=1)

    try:
        preview = build_research_state_local_write_packet_preview_from_file(
            persistence_write_decision_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Local Write Packet Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", preview["target_name"])
    table.add_row("Status", preview["preview_status"])
    table.add_row("Approved decisions", str(preview["approved_persistence_write_decision_count"]))
    table.add_row("Preview items", str(preview["local_write_packet_preview_item_count"]))
    table.add_row("Local write packet preview ready", str(preview["local_write_packet_preview_ready"]))
    table.add_row("Write execution review required", str(preview["write_execution_review_gate_required"]))
    table.add_row("Write execution review ready", str(preview["write_execution_review_gate_ready"]))
    table.add_row("Persistent write ready", str(preview["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(preview["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if preview["preview_items"]:
        items = Table(title="Local Write Packet Preview Items")
        items.add_column("Preview")
        items.add_column("Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in preview["preview_items"]:
            items.add_row(
                item["local_write_packet_preview_item_id"],
                item["persistence_write_decision_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved local write packet preview JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(preview, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local write packet preview. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-write-execution-review-gate")
def brain_chat_research_state_write_execution_review_gate_command(
    local_write_packet_preview_file: Path = typer.Option(..., "--local-write-packet-preview-file", "--write-preview", help="Path to local write packet preview JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for write execution review gate."),
):
    """Build a write execution review gate."""
    if not local_write_packet_preview_file.exists():
        console.print(f"[bold red]Local write packet preview JSON not found:[/bold red] {local_write_packet_preview_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_write_execution_review_gate_from_file(
            local_write_packet_preview_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Write Execution Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["gate_status"])
    table.add_row("Preview items", str(gate["local_write_packet_preview_item_count"]))
    table.add_row("Review items", str(gate["write_execution_review_item_count"]))
    table.add_row("Write execution review ready", str(gate["write_execution_review_ready"]))
    table.add_row("Human review required", str(gate["human_write_execution_review_required"]))
    table.add_row("Human review complete", str(gate["human_write_execution_review_complete"]))
    table.add_row("Decision packet ready", str(gate["write_execution_decision_packet_ready"]))
    table.add_row("Persistent write ready", str(gate["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(gate["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if gate["review_items"]:
        items = Table(title="Write Execution Review Items")
        items.add_column("Review")
        items.add_column("Preview")
        items.add_column("Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in gate["review_items"]:
            items.add_row(
                item["write_execution_review_item_id"],
                item["local_write_packet_preview_item_id"],
                item["persistence_write_decision_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved write execution review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a write execution review gate. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-write-execution-decision-packet")
def brain_chat_research_state_write_execution_decision_packet_command(
    write_execution_review_gate_file: Path = typer.Option(..., "--write-execution-review-gate-file", "--execution-review-gate", help="Path to write execution review gate JSON."),
    human_write_execution_decisions_file: Path = typer.Option(..., "--human-write-execution-decisions-file", "--write-decisions", help="Path to human write execution decisions JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for write execution decision packet."),
):
    """Build a human write execution decision packet."""
    if not write_execution_review_gate_file.exists():
        console.print(f"[bold red]Write execution review gate JSON not found:[/bold red] {write_execution_review_gate_file}")
        raise typer.Exit(code=1)

    if not human_write_execution_decisions_file.exists():
        console.print(f"[bold red]Human write execution decisions JSON not found:[/bold red] {human_write_execution_decisions_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_write_execution_decision_packet_from_files(
            write_execution_review_gate_file,
            human_write_execution_decisions_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Write Execution Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Review items", str(packet["write_execution_review_item_count"]))
    table.add_row("Decisions", str(packet["write_execution_decision_count"]))
    table.add_row("Approved decisions", str(packet["approved_write_execution_decision_count"]))
    table.add_row("Human decision required", str(packet["human_write_execution_decision_required"]))
    table.add_row("Human decision complete", str(packet["human_write_execution_decision_complete"]))
    table.add_row("Local packet required", str(packet["local_write_execution_packet_required"]))
    table.add_row("Local packet ready", str(packet["local_write_execution_packet_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["write_execution_decisions"]:
        items = Table(title="Write Execution Decisions")
        items.add_column("Decision ID")
        items.add_column("Review")
        items.add_column("Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in packet["write_execution_decisions"]:
            items.add_row(
                item["write_execution_decision_id"],
                item["write_execution_review_item_id"],
                item["decision"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved write execution decision packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a human write execution decision packet. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-local-write-execution-packet")
def brain_chat_research_state_local_write_execution_packet_command(
    write_execution_decision_packet_file: Path = typer.Option(..., "--write-execution-decision-packet-file", "--execution-decision-packet", help="Path to write execution decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for local write execution packet."),
):
    """Build a local write execution packet."""
    if not write_execution_decision_packet_file.exists():
        console.print(f"[bold red]Write execution decision packet JSON not found:[/bold red] {write_execution_decision_packet_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_local_write_execution_packet_from_file(
            write_execution_decision_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Local Write Execution Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["packet_status"])
    table.add_row("Approved decisions", str(packet["approved_write_execution_decision_count"]))
    table.add_row("Local items", str(packet["local_write_execution_packet_item_count"]))
    table.add_row("Local packet ready", str(packet["local_write_execution_packet_ready"]))
    table.add_row("Final apply review required", str(packet["final_persistence_apply_review_gate_required"]))
    table.add_row("Final apply review ready", str(packet["final_persistence_apply_review_gate_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["local_write_execution_items"]:
        items = Table(title="Local Write Execution Items")
        items.add_column("Local")
        items.add_column("Decision")
        items.add_column("Review")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in packet["local_write_execution_items"]:
            items.add_row(
                item["local_write_execution_packet_item_id"],
                item["write_execution_decision_id"],
                item["write_execution_review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved local write execution packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a local write execution packet. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-final-persistence-apply-review-gate")
def brain_chat_research_state_final_persistence_apply_review_gate_command(
    local_write_execution_packet_file: Path = typer.Option(..., "--local-write-execution-packet-file", "--local-write-packet", help="Path to local write execution packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for final persistence apply review gate."),
):
    """Build a final persistence apply review gate."""
    if not local_write_execution_packet_file.exists():
        console.print(f"[bold red]Local write execution packet JSON not found:[/bold red] {local_write_execution_packet_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_final_persistence_apply_review_gate_from_file(
            local_write_execution_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Final Persistence Apply Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["gate_status"])
    table.add_row("Local write items", str(gate["local_write_execution_packet_item_count"]))
    table.add_row("Review items", str(gate["final_persistence_apply_review_item_count"]))
    table.add_row("Human decision required", str(gate["human_final_persistence_apply_decision_required"]))
    table.add_row("Human decision complete", str(gate["human_final_persistence_apply_decision_complete"]))
    table.add_row("Decision packet required", str(gate["final_persistence_apply_decision_packet_required"]))
    table.add_row("Decision packet ready", str(gate["final_persistence_apply_decision_packet_ready"]))
    table.add_row("Persistent write ready", str(gate["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(gate["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if gate["final_persistence_apply_review_items"]:
        items = Table(title="Final Persistence Apply Review Items")
        items.add_column("Review")
        items.add_column("Local")
        items.add_column("Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in gate["final_persistence_apply_review_items"]:
            items.add_row(
                item["final_persistence_apply_review_item_id"],
                item["local_write_execution_packet_item_id"],
                item["write_execution_decision_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved final persistence apply review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a final persistence apply review gate. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-human-final-apply-decision-packet")
def brain_chat_research_state_human_final_apply_decision_packet_command(
    final_persistence_apply_review_gate_file: Path = typer.Option(..., "--final-persistence-apply-review-gate-file", "--final-apply-review-gate", help="Path to final persistence apply review gate JSON."),
    human_final_apply_decisions_file: Path = typer.Option(..., "--human-final-apply-decisions-file", "--final-apply-decisions", help="Path to explicit human final apply decisions JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for human final apply decision packet."),
):
    """Build a human final apply decision packet."""
    if not final_persistence_apply_review_gate_file.exists():
        console.print(f"[bold red]Final persistence apply review gate JSON not found:[/bold red] {final_persistence_apply_review_gate_file}")
        raise typer.Exit(code=1)

    if not human_final_apply_decisions_file.exists():
        console.print(f"[bold red]Human final apply decisions JSON not found:[/bold red] {human_final_apply_decisions_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_human_final_apply_decision_packet_from_files(
            final_persistence_apply_review_gate_file,
            human_final_apply_decisions_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Human Final Apply Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Review items", str(packet["final_persistence_apply_review_item_count"]))
    table.add_row("Human decisions", str(packet["human_final_apply_decision_count"]))
    table.add_row("Approved decisions", str(packet["approved_final_apply_decision_count"]))
    table.add_row("Human decision required", str(packet["human_final_apply_decision_required"]))
    table.add_row("Human decision complete", str(packet["human_final_apply_decision_complete"]))
    table.add_row("Final local apply preview required", str(packet["final_local_apply_preview_required"]))
    table.add_row("Final local apply preview ready", str(packet["final_local_apply_preview_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["final_apply_decisions"]:
        items = Table(title="Human Final Apply Decisions")
        items.add_column("Decision")
        items.add_column("Review")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Choice")
        items.add_column("Approved")
        for item in packet["final_apply_decisions"]:
            items.add_row(
                item["human_final_apply_decision_id"],
                item["final_persistence_apply_review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["decision"],
                str(item["final_local_apply_preview_required"]),
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved human final apply decision packet JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a human final apply decision packet. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-final-local-apply-preview")
def brain_chat_research_state_final_local_apply_preview_command(
    human_final_apply_decision_packet_file: Path = typer.Option(..., "--human-final-apply-decision-packet-file", "--final-apply-decision-packet", help="Path to human final apply decision packet JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for final local apply preview."),
):
    """Build a final local apply preview."""
    if not human_final_apply_decision_packet_file.exists():
        console.print(f"[bold red]Human final apply decision packet JSON not found:[/bold red] {human_final_apply_decision_packet_file}")
        raise typer.Exit(code=1)

    try:
        preview = build_research_state_final_local_apply_preview_from_file(
            human_final_apply_decision_packet_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Final Local Apply Preview")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", preview["target_name"])
    table.add_row("Status", preview["preview_status"])
    table.add_row("Approved decisions", str(preview["approved_final_apply_decision_count"]))
    table.add_row("Preview items", str(preview["final_local_apply_preview_item_count"]))
    table.add_row("Final local apply preview ready", str(preview["final_local_apply_preview_ready"]))
    table.add_row("Final apply execution review required", str(preview["final_apply_execution_review_gate_required"]))
    table.add_row("Final apply execution review ready", str(preview["final_apply_execution_review_gate_ready"]))
    table.add_row("Persistent write ready", str(preview["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(preview["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if preview["final_local_apply_preview_items"]:
        items = Table(title="Final Local Apply Preview Items")
        items.add_column("Preview")
        items.add_column("Decision")
        items.add_column("Review")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in preview["final_local_apply_preview_items"]:
            items.add_row(
                item["final_local_apply_preview_item_id"],
                item["human_final_apply_decision_id"],
                item["final_persistence_apply_review_item_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved final local apply preview JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(preview, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a final local apply preview. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-final-apply-execution-review-gate")
def brain_chat_research_state_final_apply_execution_review_gate_command(
    final_local_apply_preview_file: Path = typer.Option(..., "--final-local-apply-preview-file", "--final-local-apply-preview", help="Path to final local apply preview JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for final apply execution review gate."),
):
    """Build a final apply execution review gate."""
    if not final_local_apply_preview_file.exists():
        console.print(f"[bold red]Final local apply preview JSON not found:[/bold red] {final_local_apply_preview_file}")
        raise typer.Exit(code=1)

    try:
        gate = build_research_state_final_apply_execution_review_gate_from_file(
            final_local_apply_preview_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Final Apply Execution Review Gate")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", gate["target_name"])
    table.add_row("Status", gate["review_status"])
    table.add_row("Preview items", str(gate["final_local_apply_preview_item_count"]))
    table.add_row("Review items", str(gate["final_apply_execution_review_item_count"]))
    table.add_row("Final apply execution review ready", str(gate["final_apply_execution_review_ready"]))
    table.add_row("Human final apply execution decision required", str(gate["human_final_apply_execution_decision_required"]))
    table.add_row("Human final apply execution decision complete", str(gate["human_final_apply_execution_decision_complete"]))
    table.add_row("Persistent write ready", str(gate["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(gate["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if gate["final_apply_execution_review_items"]:
        items = Table(title="Final Apply Execution Review Items")
        items.add_column("Review")
        items.add_column("Preview")
        items.add_column("Decision")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        items.add_column("Current")
        items.add_column("Proposed")
        for item in gate["final_apply_execution_review_items"]:
            items.add_row(
                item["final_apply_execution_review_item_id"],
                item["final_local_apply_preview_item_id"],
                item["human_final_apply_decision_id"],
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
                item["current_value"],
                item["proposed_value"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved final apply execution review gate JSON:[/bold green] {json_output}")
    else:
        console.print(json.dumps(gate, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a final apply execution review gate. "
        "It does not write persistent research state, apply confidence changes, execute tools, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )

@app.command("brain-chat-research-state-human-final-apply-execution-decision-packet")
def brain_chat_research_state_human_final_apply_execution_decision_packet_command(
    final_apply_execution_review_gate_file: Path = typer.Option(..., "--final-apply-execution-review-gate-file", "--final-execution-review-gate", help="Path to final apply execution review gate JSON."),
    human_final_apply_execution_decisions_file: Path = typer.Option(..., "--human-final-apply-execution-decisions-file", "--final-execution-decisions", help="Path to human final apply execution decisions JSON."),
    json_output: Path | None = typer.Option(None, "--json-output", "--output", help="Optional JSON output path for human final apply execution decision packet."),
):
    """Build a human final apply execution decision packet."""
    if not final_apply_execution_review_gate_file.exists():
        console.print(f"[bold red]Final apply execution review gate JSON not found:[/bold red] {final_apply_execution_review_gate_file}")
        raise typer.Exit(code=1)

    if not human_final_apply_execution_decisions_file.exists():
        console.print(f"[bold red]Human final apply execution decisions JSON not found:[/bold red] {human_final_apply_execution_decisions_file}")
        raise typer.Exit(code=1)

    try:
        packet = build_research_state_human_final_apply_execution_decision_packet_from_files(
            final_apply_execution_review_gate_file,
            human_final_apply_execution_decisions_file,
            json_output,
        )
    except ValueError as exc:
        console.print(f"[bold red]{exc}[/bold red]")
        raise typer.Exit(code=2) from exc

    table = Table(title="Human Final Apply Execution Decision Packet")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("Target", packet["target_name"])
    table.add_row("Status", packet["decision_status"])
    table.add_row("Review items", str(packet["final_apply_execution_review_item_count"]))
    table.add_row("Human decisions", str(packet["human_final_apply_execution_decision_count"]))
    table.add_row("Approved decisions", str(packet["approved_final_apply_execution_decision_count"]))
    table.add_row("Human decision complete", str(packet["human_final_apply_execution_decision_complete"]))
    table.add_row("Final apply execution packet required", str(packet["final_apply_execution_packet_required"]))
    table.add_row("Final apply execution packet ready", str(packet["final_apply_execution_packet_ready"]))
    table.add_row("Persistent write ready", str(packet["persistent_research_state_write_ready"]))
    table.add_row("Persistent write allowed", str(packet["persistent_research_state_write_allowed"]))
    table.add_row("Execution", "planning-only; no persistence, confidence mutation, target interaction, or tool execution")
    console.print(table)

    if packet["human_final_apply_execution_decisions"]:
        items = Table(title="Human Final Apply Execution Decisions")
        items.add_column("Decision")
        items.add_column("Review")
        items.add_column("Action")
        items.add_column("Valid")
        items.add_column("Approved")
        items.add_column("Operation")
        items.add_column("Hypothesis")
        items.add_column("Field")
        for item in packet["human_final_apply_execution_decisions"]:
            items.add_row(
                item["human_final_apply_execution_decision_id"],
                item["final_apply_execution_review_item_id"],
                item["decision"],
                str(item["decision_valid"]),
                str(item["final_apply_execution_approved"]),
                item["operation_id"],
                item["hypothesis_id"],
                item["field_path"],
            )
        console.print(items)

    if json_output:
        console.print(f"[bold green]Saved human final apply execution decision packet JSON:[/bold green] {json_output}")
    else:
        print(json.dumps(packet, indent=2, sort_keys=True))

    console.print(
        "[bold yellow]Safety:[/bold yellow] This command only builds a human final apply execution decision packet. "
        "It does not execute a final apply path, write persistent research state, apply confidence changes, interact with targets, "
        "collect evidence, submit reports, or confirm vulnerabilities."
    )




@app.command("case-intake-brain-question-set")
def case_intake_brain_question_set_command(
    handoff_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-handoff JSON output.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown question-set output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON question-set output.",
    ),
) -> None:
    """Run all standard deterministic brain questions over a case intake handoff."""
    from bugintel.core.case_intake_brain_handoff_question_set_runner import (
        run_case_intake_brain_handoff_question_set,
    )

    if not handoff_file.exists():
        raise typer.BadParameter(f"handoff file does not exist: {handoff_file}")

    handoff = json.loads(handoff_file.read_text())
    question_set = run_case_intake_brain_handoff_question_set(handoff)

    data = question_set.to_dict()

    table = Table(title="Case Intake Brain Handoff Question Set")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Target", question_set.target_name)
    table.add_row("Handoff status", question_set.handoff_status)
    table.add_row("Questions answered", str(len(question_set.answers)))
    table.add_row("Blocked", str(question_set.blocked))
    table.add_row("Focus endpoints", str(question_set.focus_endpoint_count))
    table.add_row("Deferred endpoints", str(question_set.deferred_endpoint_count))
    table.add_row("Evidence gaps", str(question_set.evidence_gap_count))
    table.add_row("Validation allowed", str(question_set.validation_allowed))
    table.add_row("Runtime execution allowed", str(question_set.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(question_set.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(question_set.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    for index, answer in enumerate(question_set.answers, start=1):
        console.print(f"\n[bold]Question {index}:[/bold] {answer.question}")
        console.print(f"[bold]Route:[/bold] {answer.route}")
        console.print(f"[bold]Focus endpoint:[/bold] {answer.focus_endpoint or 'none'}")
        console.print(f"[bold]Answer:[/bold]\n{answer.answer}")
        console.print("[bold]Recommended next action:[/bold]")
        console.print(answer.recommended_next_action)

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain question-set JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(question_set.to_markdown())
        console.print(f"Saved case intake brain question-set Markdown: {output_file}")

    console.print(
        "Safety: This command only answers local deterministic handoff questions. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-evidence-checklist")
def case_intake_brain_evidence_checklist_command(
    handoff_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-handoff JSON output.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown evidence checklist output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON evidence checklist output.",
    ),
) -> None:
    """Export evidence gaps from a case intake brain handoff as a manual checklist."""
    from bugintel.core.case_intake_brain_handoff_evidence_checklist_exporter import (
        export_case_intake_brain_handoff_evidence_checklist,
    )

    if not handoff_file.exists():
        raise typer.BadParameter(f"handoff file does not exist: {handoff_file}")

    handoff = json.loads(handoff_file.read_text())
    checklist = export_case_intake_brain_handoff_evidence_checklist(handoff)
    data = checklist.to_dict()

    table = Table(title="Case Intake Brain Evidence Checklist")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Target", checklist.target_name)
    table.add_row("Handoff status", checklist.handoff_status)
    table.add_row("Checklist items", str(len(checklist.checklist_items)))
    table.add_row("Endpoints with gaps", str(checklist.endpoint_count))
    table.add_row("Evidence gaps", str(checklist.evidence_gap_count))
    table.add_row("Required before report", str(checklist.required_before_report_count))
    table.add_row("Blocked", str(checklist.blocked))
    table.add_row("Validation allowed", str(checklist.validation_allowed))
    table.add_row("Runtime execution allowed", str(checklist.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(checklist.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(checklist.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if checklist.checklist_items:
        console.print("\n[bold]Checklist preview:[/bold]")
        for item in checklist.checklist_items[:12]:
            console.print(
                f"- [ ] {item.checklist_id} `{item.endpoint}` / `{item.gap_type}`: {item.description}"
            )
        if len(checklist.checklist_items) > 12:
            console.print(f"... {len(checklist.checklist_items) - 12} more item(s)")
    else:
        console.print("\nNo evidence gaps are recorded in this handoff.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain evidence checklist JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(checklist.to_markdown())
        console.print(f"Saved case intake brain evidence checklist Markdown: {output_file}")

    console.print(
        "Safety: This command only exports local deterministic checklist text. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-manual-validation-plan")
def case_intake_brain_manual_validation_plan_command(
    handoff_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-handoff JSON output.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown manual validation plan output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON manual validation plan output.",
    ),
) -> None:
    """Export a manual validation plan from a case intake brain handoff."""
    from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
        export_case_intake_brain_handoff_manual_validation_plan,
    )

    if not handoff_file.exists():
        raise typer.BadParameter(f"handoff file does not exist: {handoff_file}")

    handoff = json.loads(handoff_file.read_text())
    plan = export_case_intake_brain_handoff_manual_validation_plan(handoff)
    data = plan.to_dict()

    table = Table(title="Case Intake Brain Manual Validation Plan")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Target", plan.target_name)
    table.add_row("Handoff status", plan.handoff_status)
    table.add_row("Plan endpoints", str(plan.plan_endpoint_count))
    table.add_row("Deferred endpoints", str(plan.deferred_endpoint_count))
    table.add_row("Evidence gaps", str(plan.evidence_gap_count))
    table.add_row("Approval required", str(plan.approval_required))
    table.add_row("Read-only required", str(plan.read_only_required))
    table.add_row("Blocked", str(plan.blocked))
    table.add_row("Validation allowed", str(plan.validation_allowed))
    table.add_row("Runtime execution allowed", str(plan.runtime_execution_allowed))
    table.add_row("Report submission allowed", str(plan.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(plan.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if plan.plan_endpoints:
        console.print("\n[bold]Plan preview:[/bold]")
        for endpoint in plan.plan_endpoints[:5]:
            console.print(
                f"- `{endpoint.endpoint}` / `{endpoint.lane}` / score `{endpoint.priority_score}`"
            )
            for step in endpoint.validation_steps[:4]:
                console.print(f"  - {step}")
    else:
        console.print("\nNo focus endpoints are available for manual validation planning.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain manual validation plan JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(plan.to_markdown())
        console.print(f"Saved case intake brain manual validation plan Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic manual validation plan. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-approval-packet")
def case_intake_brain_approval_packet_command(
    manual_validation_plan_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-manual-validation-plan JSON output.",
    ),
    endpoint: str | None = typer.Option(
        None,
        "--endpoint",
        help="Endpoint to export an approval packet for. Defaults to the first plan endpoint.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown approval packet output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON approval packet output.",
    ),
) -> None:
    """Export a human approval packet from a manual validation plan."""
    from bugintel.core.case_intake_brain_handoff_approval_packet_exporter import (
        export_case_intake_brain_handoff_approval_packet,
    )

    if not manual_validation_plan_file.exists():
        raise typer.BadParameter(f"manual validation plan file does not exist: {manual_validation_plan_file}")

    manual_validation_plan = json.loads(manual_validation_plan_file.read_text())
    packet = export_case_intake_brain_handoff_approval_packet(
        manual_validation_plan,
        endpoint=endpoint,
    )
    data = packet.to_dict()

    table = Table(title="Case Intake Brain Approval Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Approval ID", packet.approval_id)
    table.add_row("Target", packet.target_name)
    table.add_row("Endpoint", packet.endpoint)
    table.add_row("Lane", packet.lane)
    table.add_row("Score", str(packet.priority_score))
    table.add_row("Proposed action", packet.proposed_action)
    table.add_row("Human approval required", str(packet.human_approval_required))
    table.add_row("Approved", str(packet.approved))
    table.add_row("Approval status", packet.approval_status)
    table.add_row("Read-only required", str(packet.read_only_required))
    table.add_row("Blocked", str(packet.blocked))
    table.add_row("Validation allowed", str(packet.validation_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(packet.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(packet.browser_execution_allowed))
    table.add_row("Evidence collection allowed", str(packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(packet.target_mutation_allowed))
    table.add_row("Report submission allowed", str(packet.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(packet.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if packet.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {packet.block_reason}")
    else:
        console.print("\n[bold]Approval question:[/bold]")
        console.print(packet.approval_question)
        console.print("\n[bold]Proposed read-only steps preview:[/bold]")
        for step in packet.validation_steps[:5]:
            console.print(f"- {step}")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain approval packet JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(packet.to_markdown())
        console.print(f"Saved case intake brain approval packet Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic approval packet. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-approval-decision")
def case_intake_brain_approval_decision_command(
    approval_packet_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-approval-packet JSON output.",
    ),
    decision: str = typer.Option(
        ...,
        "--decision",
        help="Human decision to record: approved, denied, or blocked.",
    ),
    decided_by: str = typer.Option(
        ...,
        "--decided-by",
        help="Name or handle of the human who made the decision.",
    ),
    reason: str = typer.Option(
        "",
        "--reason",
        help="Reason or note explaining the decision.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown approval decision output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON approval decision output.",
    ),
) -> None:
    """Record a human decision over a case intake brain approval packet."""
    from bugintel.core.case_intake_brain_handoff_approval_decision_recorder import (
        record_case_intake_brain_handoff_approval_decision,
    )

    if not approval_packet_file.exists():
        raise typer.BadParameter(f"approval packet file does not exist: {approval_packet_file}")

    approval_packet = json.loads(approval_packet_file.read_text())
    recorded = record_case_intake_brain_handoff_approval_decision(
        approval_packet,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
    )
    data = recorded.to_dict()

    table = Table(title="Case Intake Brain Approval Decision")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Decision ID", recorded.decision_id)
    table.add_row("Approval ID", recorded.approval_id)
    table.add_row("Target", recorded.target_name)
    table.add_row("Endpoint", recorded.endpoint)
    table.add_row("Decision", recorded.decision)
    table.add_row("Decision status", recorded.decision_status)
    table.add_row("Decided by", recorded.decided_by)
    table.add_row("Approved", str(recorded.approved))
    table.add_row("Denied", str(recorded.denied))
    table.add_row("Blocked", str(recorded.blocked))
    table.add_row("Can proceed to execution", str(recorded.can_proceed_to_execution))
    table.add_row("Human approval recorded", str(recorded.human_approval_recorded))
    table.add_row("Validation allowed", str(recorded.validation_allowed))
    table.add_row("Runtime execution allowed", str(recorded.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(recorded.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(recorded.browser_execution_allowed))
    table.add_row("Evidence collection allowed", str(recorded.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(recorded.target_mutation_allowed))
    table.add_row("Report submission allowed", str(recorded.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(recorded.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if recorded.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {recorded.packet_block_reason}")
    else:
        console.print("\n[bold]Recorded reason:[/bold]")
        console.print(recorded.reason or "No reason supplied.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain approval decision JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(recorded.to_markdown())
        console.print(f"Saved case intake brain approval decision Markdown: {output_file}")

    console.print(
        "Safety: This command only records a local deterministic approval decision. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-read-only-command-proposal")
def case_intake_brain_read_only_command_proposal_command(
    approval_decision_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-approval-decision JSON output.",
    ),
    command_family: str = typer.Option(
        "curl",
        "--command-family",
        help="Command family to propose. Currently supported: curl.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown command proposal output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON command proposal output.",
    ),
) -> None:
    """Export a read-only command proposal from an approval decision."""
    from bugintel.core.case_intake_brain_handoff_read_only_command_proposal_exporter import (
        export_case_intake_brain_handoff_read_only_command_proposal,
    )

    if not approval_decision_file.exists():
        raise typer.BadParameter(f"approval decision file does not exist: {approval_decision_file}")

    approval_decision = json.loads(approval_decision_file.read_text())
    proposal = export_case_intake_brain_handoff_read_only_command_proposal(
        approval_decision,
        command_family=command_family,
    )
    data = proposal.to_dict()

    table = Table(title="Case Intake Brain Read-Only Command Proposal")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Proposal ID", proposal.proposal_id)
    table.add_row("Decision ID", proposal.decision_id)
    table.add_row("Approval ID", proposal.approval_id)
    table.add_row("Target", proposal.target_name)
    table.add_row("Endpoint", proposal.endpoint)
    table.add_row("Command family", proposal.command_family)
    table.add_row("Command purpose", proposal.command_purpose)
    table.add_row("Blocked", str(proposal.blocked))
    table.add_row("Human review required", str(proposal.human_review_required))
    table.add_row("Separate execution approval required", str(proposal.requires_separate_execution_approval))
    table.add_row("Execution allowed", str(proposal.execution_allowed))
    table.add_row("Validation allowed", str(proposal.validation_allowed))
    table.add_row("Runtime execution allowed", str(proposal.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(proposal.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(proposal.browser_execution_allowed))
    table.add_row("Network requests allowed", str(proposal.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(proposal.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(proposal.target_mutation_allowed))
    table.add_row("Report submission allowed", str(proposal.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(proposal.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if proposal.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {proposal.block_reason}")
    else:
        console.print("\n[bold]Proposed command preview:[/bold]")
        console.print(proposal.proposed_command)
        console.print("\n[bold]Important:[/bold] This command is not executed and still requires separate execution approval.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain read-only command proposal JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(proposal.to_markdown())
        console.print(f"Saved case intake brain read-only command proposal Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic command proposal. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-execution-approval-gate")
def case_intake_brain_execution_approval_gate_command(
    command_proposal_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-read-only-command-proposal JSON output.",
    ),
    decision: str = typer.Option(
        ...,
        "--decision",
        help="Execution approval decision to record: approved, denied, or blocked.",
    ),
    decided_by: str = typer.Option(
        ...,
        "--decided-by",
        help="Name or handle of the human who made the execution approval decision.",
    ),
    reason: str = typer.Option(
        "",
        "--reason",
        help="Reason or note explaining the execution approval decision.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown execution approval gate output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON execution approval gate output.",
    ),
) -> None:
    """Record a separate execution approval decision over a command proposal."""
    from bugintel.core.case_intake_brain_handoff_execution_approval_gate import (
        record_case_intake_brain_handoff_execution_approval_gate,
    )

    if not command_proposal_file.exists():
        raise typer.BadParameter(f"command proposal file does not exist: {command_proposal_file}")

    command_proposal = json.loads(command_proposal_file.read_text())
    gate = record_case_intake_brain_handoff_execution_approval_gate(
        command_proposal,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
    )
    data = gate.to_dict()

    table = Table(title="Case Intake Brain Execution Approval Gate")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Gate ID", gate.gate_id)
    table.add_row("Proposal ID", gate.proposal_id)
    table.add_row("Decision ID", gate.decision_id)
    table.add_row("Approval ID", gate.approval_id)
    table.add_row("Target", gate.target_name)
    table.add_row("Endpoint", gate.endpoint)
    table.add_row("Command family", gate.command_family)
    table.add_row("Execution decision", gate.execution_decision)
    table.add_row("Execution gate status", gate.execution_gate_status)
    table.add_row("Decided by", gate.decided_by)
    table.add_row("Approved", str(gate.approved))
    table.add_row("Denied", str(gate.denied))
    table.add_row("Blocked", str(gate.blocked))
    table.add_row("Human execution approval recorded", str(gate.human_execution_approval_recorded))
    table.add_row("Can execute now", str(gate.can_execute_now))
    table.add_row("Requires runtime scope check", str(gate.requires_runtime_scope_check))
    table.add_row("Requires final human confirmation", str(gate.requires_final_human_confirmation))
    table.add_row("Requires adapter safety check", str(gate.requires_adapter_safety_check))
    table.add_row("Execution allowed", str(gate.execution_allowed))
    table.add_row("Validation allowed", str(gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(gate.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(gate.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(gate.browser_execution_allowed))
    table.add_row("Network requests allowed", str(gate.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(gate.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(gate.target_mutation_allowed))
    table.add_row("Report submission allowed", str(gate.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(gate.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if gate.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {gate.original_proposal_block_reason}")
    else:
        console.print("\n[bold]Recorded execution approval reason:[/bold]")
        console.print(gate.reason or "No reason supplied.")
        console.print("\n[bold]Important:[/bold] No command was executed. A future adapter must still perform runtime scope and safety checks.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain execution approval gate JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(gate.to_markdown())
        console.print(f"Saved case intake brain execution approval gate Markdown: {output_file}")

    console.print(
        "Safety: This command only records a local deterministic execution approval gate. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-runtime-safety-manifest")
def case_intake_brain_runtime_safety_manifest_command(
    execution_approval_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-execution-approval-gate JSON output.",
    ),
    adapter_family: str = typer.Option(
        "curl",
        "--adapter-family",
        help="Adapter family to create a runtime safety manifest for. Currently supported: curl.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown runtime safety manifest output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON runtime safety manifest output.",
    ),
) -> None:
    """Export a runtime safety manifest from an execution approval gate."""
    from bugintel.core.case_intake_brain_handoff_runtime_safety_manifest import (
        export_case_intake_brain_handoff_runtime_safety_manifest,
    )

    if not execution_approval_file.exists():
        raise typer.BadParameter(f"execution approval gate file does not exist: {execution_approval_file}")

    execution_approval_gate = json.loads(execution_approval_file.read_text())
    manifest = export_case_intake_brain_handoff_runtime_safety_manifest(
        execution_approval_gate,
        adapter_family=adapter_family,
    )
    data = manifest.to_dict()

    table = Table(title="Case Intake Brain Runtime Safety Manifest")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Manifest ID", manifest.manifest_id)
    table.add_row("Gate ID", manifest.gate_id)
    table.add_row("Proposal ID", manifest.proposal_id)
    table.add_row("Decision ID", manifest.decision_id)
    table.add_row("Approval ID", manifest.approval_id)
    table.add_row("Target", manifest.target_name)
    table.add_row("Endpoint", manifest.endpoint)
    table.add_row("Adapter family", manifest.adapter_family)
    table.add_row("Command family", manifest.command_family)
    table.add_row("Runtime manifest status", manifest.runtime_manifest_status)
    table.add_row("Execution decision", manifest.execution_decision)
    table.add_row("Human execution approval recorded", str(manifest.human_execution_approval_recorded))
    table.add_row("Blocked", str(manifest.blocked))
    table.add_row("Can execute now", str(manifest.can_execute_now))
    table.add_row("Manifest allows execution", str(manifest.manifest_allows_execution))
    table.add_row("Requires runtime scope check", str(manifest.requires_runtime_scope_check))
    table.add_row("Requires final human confirmation", str(manifest.requires_final_human_confirmation))
    table.add_row("Requires adapter safety check", str(manifest.requires_adapter_safety_check))
    table.add_row("Execution allowed", str(manifest.execution_allowed))
    table.add_row("Validation allowed", str(manifest.validation_allowed))
    table.add_row("Runtime execution allowed", str(manifest.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(manifest.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(manifest.browser_execution_allowed))
    table.add_row("Network requests allowed", str(manifest.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(manifest.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(manifest.target_mutation_allowed))
    table.add_row("Report submission allowed", str(manifest.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(manifest.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if manifest.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {manifest.block_reason}")
    else:
        console.print("\n[bold]Runtime safety manifest created.[/bold]")
        console.print("No command was executed. This manifest only defines checks a future adapter must satisfy.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain runtime safety manifest JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(manifest.to_markdown())
        console.print(f"Saved case intake brain runtime safety manifest Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic runtime safety manifest. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-adapter-dry-run-preview")
def case_intake_brain_adapter_dry_run_preview_command(
    runtime_safety_manifest_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-runtime-safety-manifest JSON output.",
    ),
    target_base_url: str = typer.Option(
        ...,
        "--target-base-url",
        help="Confirmed in-scope HTTPS target base URL to use in the dry-run preview.",
    ),
    controlled_account_token_placeholder: str = typer.Option(
        ...,
        "--controlled-account-token-placeholder",
        help="Non-secret placeholder label for the controlled account token.",
    ),
    path_parameter: list[str] = typer.Option(
        [],
        "--path-parameter",
        help="Path parameter replacement in key=value form. Can be repeated.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown adapter dry-run preview output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON adapter dry-run preview output.",
    ),
) -> None:
    """Export a resolved adapter dry-run preview from a runtime safety manifest."""
    from bugintel.core.case_intake_brain_handoff_adapter_dry_run_preview import (
        export_case_intake_brain_handoff_adapter_dry_run_preview,
    )

    if not runtime_safety_manifest_file.exists():
        raise typer.BadParameter(f"runtime safety manifest file does not exist: {runtime_safety_manifest_file}")

    runtime_safety_manifest = json.loads(runtime_safety_manifest_file.read_text())
    preview = export_case_intake_brain_handoff_adapter_dry_run_preview(
        runtime_safety_manifest,
        target_base_url=target_base_url,
        controlled_account_token_placeholder=controlled_account_token_placeholder,
        path_parameters=path_parameter,
    )
    data = preview.to_dict()

    table = Table(title="Case Intake Brain Adapter Dry-Run Preview")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Preview ID", preview.preview_id)
    table.add_row("Manifest ID", preview.manifest_id)
    table.add_row("Gate ID", preview.gate_id)
    table.add_row("Proposal ID", preview.proposal_id)
    table.add_row("Decision ID", preview.decision_id)
    table.add_row("Approval ID", preview.approval_id)
    table.add_row("Target", preview.target_name)
    table.add_row("Endpoint", preview.endpoint)
    table.add_row("Adapter family", preview.adapter_family)
    table.add_row("Command family", preview.command_family)
    table.add_row("Target base URL", preview.target_base_url)
    table.add_row("Resolved endpoint", preview.resolved_endpoint)
    table.add_row("Resolved target URL", preview.resolved_target_url)
    table.add_row("Dry-run preview status", preview.dry_run_preview_status)
    table.add_row("Blocked", str(preview.blocked))
    table.add_row("Dry-run only", str(preview.dry_run_only))
    table.add_row("Preview ready", str(preview.preview_ready))
    table.add_row("Can execute now", str(preview.can_execute_now))
    table.add_row("Preview allows execution", str(preview.preview_allows_execution))
    table.add_row("Execution allowed", str(preview.execution_allowed))
    table.add_row("Validation allowed", str(preview.validation_allowed))
    table.add_row("Runtime execution allowed", str(preview.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(preview.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(preview.browser_execution_allowed))
    table.add_row("Network requests allowed", str(preview.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(preview.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(preview.target_mutation_allowed))
    table.add_row("Report submission allowed", str(preview.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(preview.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if preview.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {preview.block_reason}")
    else:
        console.print("\n[bold]Resolved dry-run command preview:[/bold]")
        console.print(preview.resolved_command_preview)
        console.print("\n[bold]Important:[/bold] No command was executed. This is a dry-run preview only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain adapter dry-run preview JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(preview.to_markdown())
        console.print(f"Saved case intake brain adapter dry-run preview Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic adapter dry-run preview. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-adapter-final-confirmation")
def case_intake_brain_adapter_final_confirmation_command(
    adapter_dry_run_preview_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-adapter-dry-run-preview JSON output.",
    ),
    decision: str = typer.Option(
        ...,
        "--decision",
        help="Final confirmation decision to record: confirmed, denied, or blocked.",
    ),
    confirmed_by: str = typer.Option(
        "human-reviewer",
        "--confirmed-by",
        help="Neutral reviewer label for the human who made the final confirmation decision.",
    ),
    reason: str = typer.Option(
        "",
        "--reason",
        help="Reason or note explaining the final confirmation decision.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown adapter final confirmation output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON adapter final confirmation output.",
    ),
) -> None:
    """Record final human confirmation over an adapter dry-run preview."""
    from bugintel.core.case_intake_brain_handoff_adapter_final_confirmation_packet import (
        record_case_intake_brain_handoff_adapter_final_confirmation,
    )

    if not adapter_dry_run_preview_file.exists():
        raise typer.BadParameter(f"adapter dry-run preview file does not exist: {adapter_dry_run_preview_file}")

    adapter_dry_run_preview = json.loads(adapter_dry_run_preview_file.read_text())
    packet = record_case_intake_brain_handoff_adapter_final_confirmation(
        adapter_dry_run_preview,
        decision=decision,
        confirmed_by=confirmed_by,
        reason=reason,
    )
    data = packet.to_dict()

    table = Table(title="Case Intake Brain Adapter Final Confirmation Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Confirmation ID", packet.confirmation_id)
    table.add_row("Preview ID", packet.preview_id)
    table.add_row("Manifest ID", packet.manifest_id)
    table.add_row("Gate ID", packet.gate_id)
    table.add_row("Proposal ID", packet.proposal_id)
    table.add_row("Decision ID", packet.decision_id)
    table.add_row("Approval ID", packet.approval_id)
    table.add_row("Target", packet.target_name)
    table.add_row("Endpoint", packet.endpoint)
    table.add_row("Adapter family", packet.adapter_family)
    table.add_row("Command family", packet.command_family)
    table.add_row("Resolved target URL", packet.resolved_target_url)
    table.add_row("Final confirmation decision", packet.final_confirmation_decision)
    table.add_row("Final confirmation status", packet.final_confirmation_status)
    table.add_row("Confirmed by", packet.confirmed_by)
    table.add_row("Confirmed", str(packet.confirmed))
    table.add_row("Denied", str(packet.denied))
    table.add_row("Blocked", str(packet.blocked))
    table.add_row("Human final confirmation recorded", str(packet.human_final_confirmation_recorded))
    table.add_row("Dry-run only", str(packet.dry_run_only))
    table.add_row("Source preview ready", str(packet.source_preview_ready))
    table.add_row("Can execute now", str(packet.can_execute_now))
    table.add_row("Final confirmation allows execution", str(packet.final_confirmation_allows_execution))
    table.add_row("Execution allowed", str(packet.execution_allowed))
    table.add_row("Validation allowed", str(packet.validation_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(packet.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(packet.browser_execution_allowed))
    table.add_row("Network requests allowed", str(packet.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(packet.target_mutation_allowed))
    table.add_row("Report submission allowed", str(packet.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(packet.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if packet.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {packet.source_preview_block_reason}")
    else:
        console.print("\n[bold]Recorded final confirmation reason:[/bold]")
        console.print(packet.reason or "No reason supplied.")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a final confirmation packet only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain adapter final confirmation JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(packet.to_markdown())
        console.print(f"Saved case intake brain adapter final confirmation Markdown: {output_file}")

    console.print(
        "Safety: This command only records a local deterministic adapter final confirmation packet. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-execution-request")
def case_intake_brain_scoped_adapter_execution_request_command(
    adapter_final_confirmation_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-adapter-final-confirmation JSON output.",
    ),
    request_purpose: str = typer.Option(
        "future-scoped-adapter-review",
        "--request-purpose",
        help="Purpose label for the scoped adapter execution request.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown scoped adapter execution request output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON scoped adapter execution request output.",
    ),
) -> None:
    """Export a scoped adapter execution request from final confirmation."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_request import (
        export_case_intake_brain_handoff_scoped_adapter_execution_request,
    )

    if not adapter_final_confirmation_file.exists():
        raise typer.BadParameter(f"adapter final confirmation file does not exist: {adapter_final_confirmation_file}")

    adapter_final_confirmation = json.loads(adapter_final_confirmation_file.read_text())
    request = export_case_intake_brain_handoff_scoped_adapter_execution_request(
        adapter_final_confirmation,
        request_purpose=request_purpose,
    )
    data = request.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Execution Request")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Request ID", request.request_id)
    table.add_row("Confirmation ID", request.confirmation_id)
    table.add_row("Preview ID", request.preview_id)
    table.add_row("Manifest ID", request.manifest_id)
    table.add_row("Gate ID", request.gate_id)
    table.add_row("Proposal ID", request.proposal_id)
    table.add_row("Decision ID", request.decision_id)
    table.add_row("Approval ID", request.approval_id)
    table.add_row("Target", request.target_name)
    table.add_row("Endpoint", request.endpoint)
    table.add_row("Adapter family", request.adapter_family)
    table.add_row("Command family", request.command_family)
    table.add_row("Request purpose", request.request_purpose)
    table.add_row("Requested action", request.requested_action)
    table.add_row("Resolved target URL", request.resolved_target_url)
    table.add_row("Final confirmation decision", request.final_confirmation_decision)
    table.add_row("Final confirmation status", request.final_confirmation_status)
    table.add_row("Human final confirmation recorded", str(request.human_final_confirmation_recorded))
    table.add_row("Confirmed by", request.confirmed_by)
    table.add_row("Request status", request.request_status)
    table.add_row("Scope validation state", request.scope_validation_state)
    table.add_row("Adapter execution state", request.adapter_execution_state)
    table.add_row("Blocked", str(request.blocked))
    table.add_row("Dry-run only", str(request.dry_run_only))
    table.add_row("Can execute now", str(request.can_execute_now))
    table.add_row("Execution request allows execution", str(request.execution_request_allows_execution))
    table.add_row("Execution allowed", str(request.execution_allowed))
    table.add_row("Validation allowed", str(request.validation_allowed))
    table.add_row("Runtime execution allowed", str(request.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(request.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(request.browser_execution_allowed))
    table.add_row("Network requests allowed", str(request.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(request.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(request.target_mutation_allowed))
    table.add_row("Report submission allowed", str(request.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(request.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if request.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {request.block_reason}")
    else:
        console.print("\n[bold]Reviewed command packaged for future adapter:[/bold]")
        console.print(request.reviewed_command)
        console.print("\n[bold]Important:[/bold] No command was executed. This is a scoped execution request artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter execution request JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(request.to_markdown())
        console.print(f"Saved case intake brain scoped adapter execution request Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic scoped adapter execution request. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-runtime-scope-review")
def case_intake_brain_scoped_adapter_runtime_scope_review_command(
    scoped_adapter_execution_request_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-execution-request JSON output.",
    ),
    allowed_host: str = typer.Option(
        ...,
        "--allowed-host",
        help="Explicitly allowed hostname for the local runtime scope review.",
    ),
    allowed_scheme: str = typer.Option(
        "https",
        "--allowed-scheme",
        help="Explicitly allowed scheme. Only https is accepted.",
    ),
    allowed_method: str = typer.Option(
        "GET",
        "--allowed-method",
        help="Explicitly allowed read-only method.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown runtime scope review output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON runtime scope review output.",
    ),
) -> None:
    """Export a local runtime scope review for a scoped adapter request."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_scope_review import (
        export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review,
    )

    if not scoped_adapter_execution_request_file.exists():
        raise typer.BadParameter(
            f"scoped adapter execution request file does not exist: {scoped_adapter_execution_request_file}"
        )

    scoped_adapter_execution_request = json.loads(scoped_adapter_execution_request_file.read_text())
    review = export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(
        scoped_adapter_execution_request,
        allowed_host=allowed_host,
        allowed_scheme=allowed_scheme,
        allowed_method=allowed_method,
    )
    data = review.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Runtime Scope Review")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Review ID", review.review_id)
    table.add_row("Request ID", review.request_id)
    table.add_row("Confirmation ID", review.confirmation_id)
    table.add_row("Preview ID", review.preview_id)
    table.add_row("Target", review.target_name)
    table.add_row("Endpoint", review.endpoint)
    table.add_row("Adapter family", review.adapter_family)
    table.add_row("Command family", review.command_family)
    table.add_row("Resolved target URL", review.resolved_target_url)
    table.add_row("Reviewed scheme", review.reviewed_scheme)
    table.add_row("Reviewed host", review.reviewed_host)
    table.add_row("Reviewed path", review.reviewed_path)
    table.add_row("Reviewed method", review.reviewed_method)
    table.add_row("Allowed scheme", review.allowed_scheme)
    table.add_row("Allowed host", review.allowed_host)
    table.add_row("Allowed method", review.allowed_method)
    table.add_row("Runtime scope review status", review.runtime_scope_review_status)
    table.add_row("Scope validation state", review.scope_validation_state)
    table.add_row("Adapter execution state", review.adapter_execution_state)
    table.add_row("Blocked", str(review.blocked))
    table.add_row("Dry-run only", str(review.dry_run_only))
    table.add_row("Can execute now", str(review.can_execute_now))
    table.add_row("Runtime scope review allows execution", str(review.runtime_scope_review_allows_execution))
    table.add_row("Execution allowed", str(review.execution_allowed))
    table.add_row("Validation allowed", str(review.validation_allowed))
    table.add_row("Runtime execution allowed", str(review.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(review.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(review.browser_execution_allowed))
    table.add_row("Network requests allowed", str(review.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(review.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(review.target_mutation_allowed))
    table.add_row("Report submission allowed", str(review.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(review.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if review.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {review.block_reason}")
    else:
        console.print("\n[bold]Runtime scope review findings:[/bold]")
        for finding in review.review_findings:
            console.print(f"- {finding}")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local runtime scope review artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter runtime scope review JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(review.to_markdown())
        console.print(f"Saved case intake brain scoped adapter runtime scope review Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic runtime scope review. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-safety-review")
def case_intake_brain_scoped_adapter_safety_review_command(
    scoped_adapter_runtime_scope_review_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-runtime-scope-review JSON output.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown adapter safety review output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON adapter safety review output.",
    ),
) -> None:
    """Export a local adapter safety review for a scoped adapter request."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_safety_review import (
        export_case_intake_brain_handoff_scoped_adapter_safety_review,
    )

    if not scoped_adapter_runtime_scope_review_file.exists():
        raise typer.BadParameter(
            f"scoped adapter runtime scope review file does not exist: {scoped_adapter_runtime_scope_review_file}"
        )

    scoped_adapter_runtime_scope_review = json.loads(scoped_adapter_runtime_scope_review_file.read_text())
    review = export_case_intake_brain_handoff_scoped_adapter_safety_review(
        scoped_adapter_runtime_scope_review,
    )
    data = review.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Safety Review")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Safety review ID", review.safety_review_id)
    table.add_row("Runtime scope review ID", review.runtime_scope_review_id)
    table.add_row("Request ID", review.request_id)
    table.add_row("Confirmation ID", review.confirmation_id)
    table.add_row("Preview ID", review.preview_id)
    table.add_row("Target", review.target_name)
    table.add_row("Endpoint", review.endpoint)
    table.add_row("Adapter family", review.adapter_family)
    table.add_row("Command family", review.command_family)
    table.add_row("Resolved target URL", review.resolved_target_url)
    table.add_row("Reviewed method", review.reviewed_method)
    table.add_row("Reviewed host", review.reviewed_host)
    table.add_row("Adapter safety review status", review.adapter_safety_review_status)
    table.add_row("Adapter safety state", review.adapter_safety_state)
    table.add_row("Adapter execution state", review.adapter_execution_state)
    table.add_row("Present safe flags", ", ".join(review.present_safe_flags) or "none")
    table.add_row("Missing safe flags", ", ".join(review.missing_safe_flags) or "none")
    table.add_row("Blocked flags seen", ", ".join(review.blocked_flags_seen) or "none")
    table.add_row("Shell control patterns seen", ", ".join(review.shell_control_patterns_seen) or "none")
    table.add_row("Blocked", str(review.blocked))
    table.add_row("Dry-run only", str(review.dry_run_only))
    table.add_row("Can execute now", str(review.can_execute_now))
    table.add_row("Adapter safety review allows execution", str(review.adapter_safety_review_allows_execution))
    table.add_row("Execution allowed", str(review.execution_allowed))
    table.add_row("Validation allowed", str(review.validation_allowed))
    table.add_row("Runtime execution allowed", str(review.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(review.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(review.browser_execution_allowed))
    table.add_row("Network requests allowed", str(review.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(review.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(review.target_mutation_allowed))
    table.add_row("Report submission allowed", str(review.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(review.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if review.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {review.block_reason}")
    else:
        console.print("\n[bold]Adapter safety review findings:[/bold]")
        for finding in review.safe_command_findings:
            console.print(f"- {finding}")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local adapter safety review artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter safety review JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(review.to_markdown())
        console.print(f"Saved case intake brain scoped adapter safety review Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic adapter safety review. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-final-execution-gate")
def case_intake_brain_scoped_adapter_final_execution_gate_command(
    scoped_adapter_safety_review_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-safety-review JSON output.",
    ),
    decision: str = typer.Option(
        ...,
        "--decision",
        help="Final human gate decision: approved, denied, or blocked.",
    ),
    decided_by: str = typer.Option(
        "human-reviewer",
        "--decided-by",
        help="Neutral reviewer label for the human who made the final gate decision.",
    ),
    reason: str = typer.Option(
        ...,
        "--reason",
        help="Reason for the final human gate decision.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown final execution gate output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON final execution gate output.",
    ),
) -> None:
    """Record a final local execution gate decision for a scoped adapter request."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_final_execution_gate import (
        record_case_intake_brain_handoff_scoped_adapter_final_execution_gate,
    )

    if not scoped_adapter_safety_review_file.exists():
        raise typer.BadParameter(
            f"scoped adapter safety review file does not exist: {scoped_adapter_safety_review_file}"
        )

    scoped_adapter_safety_review = json.loads(scoped_adapter_safety_review_file.read_text())
    gate = record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
        scoped_adapter_safety_review,
        decision=decision,
        decided_by=decided_by,
        reason=reason,
    )
    data = gate.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Final Execution Gate")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Final gate ID", gate.final_gate_id)
    table.add_row("Safety review ID", gate.safety_review_id)
    table.add_row("Runtime scope review ID", gate.runtime_scope_review_id)
    table.add_row("Request ID", gate.request_id)
    table.add_row("Confirmation ID", gate.confirmation_id)
    table.add_row("Preview ID", gate.preview_id)
    table.add_row("Target", gate.target_name)
    table.add_row("Endpoint", gate.endpoint)
    table.add_row("Adapter family", gate.adapter_family)
    table.add_row("Command family", gate.command_family)
    table.add_row("Resolved target URL", gate.resolved_target_url)
    table.add_row("Reviewed method", gate.reviewed_method)
    table.add_row("Reviewed host", gate.reviewed_host)
    table.add_row("Adapter safety review status", gate.adapter_safety_review_status)
    table.add_row("Adapter safety state", gate.adapter_safety_state)
    table.add_row("Source adapter execution state", gate.source_adapter_execution_state)
    table.add_row("Final execution gate decision", gate.final_execution_gate_decision)
    table.add_row("Final execution gate status", gate.final_execution_gate_status)
    table.add_row("Decided by", gate.decided_by)
    table.add_row("Human final execution gate recorded", str(gate.human_final_execution_gate_recorded))
    table.add_row("Final go/no-go", gate.final_go_no_go)
    table.add_row("Adapter execution state", gate.adapter_execution_state)
    table.add_row("Blocked", str(gate.blocked))
    table.add_row("Dry-run only", str(gate.dry_run_only))
    table.add_row("Can execute now", str(gate.can_execute_now))
    table.add_row("Final execution gate allows execution", str(gate.final_execution_gate_allows_execution))
    table.add_row("Execution allowed", str(gate.execution_allowed))
    table.add_row("Validation allowed", str(gate.validation_allowed))
    table.add_row("Runtime execution allowed", str(gate.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(gate.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(gate.browser_execution_allowed))
    table.add_row("Network requests allowed", str(gate.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(gate.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(gate.target_mutation_allowed))
    table.add_row("Report submission allowed", str(gate.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(gate.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if gate.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {gate.block_reason}")
    else:
        console.print("\n[bold]Recorded final execution gate reason:[/bold]")
        console.print(gate.decision_reason or "No reason supplied.")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local final execution gate artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter final execution gate JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(gate.to_markdown())
        console.print(f"Saved case intake brain scoped adapter final execution gate Markdown: {output_file}")

    console.print(
        "Safety: This command only records a local deterministic final execution gate artifact. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-runtime-confirmation")
def case_intake_brain_scoped_adapter_runtime_confirmation_command(
    scoped_adapter_final_execution_gate_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-final-execution-gate JSON output.",
    ),
    confirmed_by: str = typer.Option(
        "human-reviewer",
        "--confirmed-by",
        help="Neutral reviewer label for the human who confirmed the exact runtime context.",
    ),
    confirmation_text: str = typer.Option(
        ...,
        "--confirmation-text",
        help="Human confirmation text for the exact scoped adapter runtime context.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown runtime confirmation output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON runtime confirmation output.",
    ),
) -> None:
    """Record a runtime confirmation packet for a scoped adapter request."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet import (
        record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet,
    )

    if not scoped_adapter_final_execution_gate_file.exists():
        raise typer.BadParameter(
            f"scoped adapter final execution gate file does not exist: {scoped_adapter_final_execution_gate_file}"
        )

    scoped_adapter_final_execution_gate = json.loads(scoped_adapter_final_execution_gate_file.read_text())
    packet = record_case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet(
        scoped_adapter_final_execution_gate,
        confirmed_by=confirmed_by,
        confirmation_text=confirmation_text,
    )
    data = packet.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Runtime Confirmation Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Runtime confirmation ID", packet.runtime_confirmation_id)
    table.add_row("Final gate ID", packet.final_gate_id)
    table.add_row("Safety review ID", packet.safety_review_id)
    table.add_row("Runtime scope review ID", packet.runtime_scope_review_id)
    table.add_row("Request ID", packet.request_id)
    table.add_row("Confirmation ID", packet.confirmation_id)
    table.add_row("Preview ID", packet.preview_id)
    table.add_row("Target", packet.target_name)
    table.add_row("Endpoint", packet.endpoint)
    table.add_row("Adapter family", packet.adapter_family)
    table.add_row("Command family", packet.command_family)
    table.add_row("Resolved target URL", packet.resolved_target_url)
    table.add_row("Reviewed method", packet.reviewed_method)
    table.add_row("Reviewed host", packet.reviewed_host)
    table.add_row("Final execution gate decision", packet.final_execution_gate_decision)
    table.add_row("Final execution gate status", packet.final_execution_gate_status)
    table.add_row("Final go/no-go", packet.final_go_no_go)
    table.add_row("Runtime confirmation status", packet.runtime_confirmation_status)
    table.add_row("Runtime confirmation state", packet.runtime_confirmation_state)
    table.add_row("Confirmed by", packet.confirmed_by)
    table.add_row("Human runtime confirmation recorded", str(packet.human_runtime_confirmation_recorded))
    table.add_row("Exact context confirmed", str(packet.exact_context_confirmed))
    table.add_row("Adapter execution state", packet.adapter_execution_state)
    table.add_row("Blocked", str(packet.blocked))
    table.add_row("Dry-run only", str(packet.dry_run_only))
    table.add_row("Can execute now", str(packet.can_execute_now))
    table.add_row("Runtime confirmation allows execution", str(packet.runtime_confirmation_allows_execution))
    table.add_row("Execution allowed", str(packet.execution_allowed))
    table.add_row("Validation allowed", str(packet.validation_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(packet.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(packet.browser_execution_allowed))
    table.add_row("Network requests allowed", str(packet.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(packet.target_mutation_allowed))
    table.add_row("Report submission allowed", str(packet.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(packet.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if packet.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {packet.block_reason}")
    else:
        console.print("\n[bold]Recorded runtime confirmation text:[/bold]")
        console.print(packet.confirmation_text or "No confirmation text supplied.")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local runtime confirmation artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter runtime confirmation JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(packet.to_markdown())
        console.print(f"Saved case intake brain scoped adapter runtime confirmation Markdown: {output_file}")

    console.print(
        "Safety: This command only records a local deterministic runtime confirmation packet. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-execution-plan")
def case_intake_brain_scoped_adapter_execution_plan_command(
    scoped_adapter_runtime_confirmation_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-runtime-confirmation JSON output.",
    ),
    planned_by: str = typer.Option(
        "human-reviewer",
        "--planned-by",
        help="Neutral reviewer label for the human who prepared the execution plan packet.",
    ),
    plan_purpose: str = typer.Option(
        ...,
        "--plan-purpose",
        help="Purpose for the future scoped adapter execution plan.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown execution plan output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON execution plan output.",
    ),
) -> None:
    """Export a local execution plan packet for a scoped adapter request."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_plan_packet import (
        export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet,
    )

    if not scoped_adapter_runtime_confirmation_file.exists():
        raise typer.BadParameter(
            f"scoped adapter runtime confirmation file does not exist: {scoped_adapter_runtime_confirmation_file}"
        )

    scoped_adapter_runtime_confirmation = json.loads(scoped_adapter_runtime_confirmation_file.read_text())
    plan = export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
        scoped_adapter_runtime_confirmation,
        planned_by=planned_by,
        plan_purpose=plan_purpose,
    )
    data = plan.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Execution Plan Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Execution plan ID", plan.execution_plan_id)
    table.add_row("Runtime confirmation ID", plan.runtime_confirmation_id)
    table.add_row("Final gate ID", plan.final_gate_id)
    table.add_row("Safety review ID", plan.safety_review_id)
    table.add_row("Runtime scope review ID", plan.runtime_scope_review_id)
    table.add_row("Request ID", plan.request_id)
    table.add_row("Confirmation ID", plan.confirmation_id)
    table.add_row("Preview ID", plan.preview_id)
    table.add_row("Target", plan.target_name)
    table.add_row("Endpoint", plan.endpoint)
    table.add_row("Adapter family", plan.adapter_family)
    table.add_row("Command family", plan.command_family)
    table.add_row("Planned by", plan.planned_by)
    table.add_row("Resolved target URL", plan.resolved_target_url)
    table.add_row("Reviewed method", plan.reviewed_method)
    table.add_row("Reviewed host", plan.reviewed_host)
    table.add_row("Runtime confirmation status", plan.runtime_confirmation_status)
    table.add_row("Runtime confirmation state", plan.runtime_confirmation_state)
    table.add_row("Human runtime confirmation recorded", str(plan.human_runtime_confirmation_recorded))
    table.add_row("Exact context confirmed", str(plan.exact_context_confirmed))
    table.add_row("Execution plan status", plan.execution_plan_status)
    table.add_row("Execution plan state", plan.execution_plan_state)
    table.add_row("Adapter execution state", plan.adapter_execution_state)
    table.add_row("Execution plan steps", str(len(plan.execution_plan_steps)))
    table.add_row("Execution preflight checks", str(len(plan.execution_preflight_checks)))
    table.add_row("Execution stop conditions", str(len(plan.execution_stop_conditions)))
    table.add_row("Blocked", str(plan.blocked))
    table.add_row("Dry-run only", str(plan.dry_run_only))
    table.add_row("Can execute now", str(plan.can_execute_now))
    table.add_row("Execution plan allows execution", str(plan.execution_plan_allows_execution))
    table.add_row("Execution allowed", str(plan.execution_allowed))
    table.add_row("Validation allowed", str(plan.validation_allowed))
    table.add_row("Runtime execution allowed", str(plan.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(plan.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(plan.browser_execution_allowed))
    table.add_row("Network requests allowed", str(plan.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(plan.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(plan.target_mutation_allowed))
    table.add_row("Report submission allowed", str(plan.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(plan.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if plan.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {plan.block_reason}")
    else:
        console.print("\n[bold]Execution plan steps:[/bold]")
        for index, step in enumerate(plan.execution_plan_steps, start=1):
            console.print(f"{index}. {step}")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local execution plan artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter execution plan JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(plan.to_markdown())
        console.print(f"Saved case intake brain scoped adapter execution plan Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic execution plan packet. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-execution-readiness")
def case_intake_brain_scoped_adapter_execution_readiness_command(
    scoped_adapter_execution_plan_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-execution-plan JSON output.",
    ),
    reviewed_by: str = typer.Option(
        "human-reviewer",
        "--reviewed-by",
        help="Neutral reviewer label for the human who reviewed execution readiness.",
    ),
    readiness_note: str = typer.Option(
        ...,
        "--readiness-note",
        help="Readiness note for future scoped adapter implementation only.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown execution readiness review output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON execution readiness review output.",
    ),
) -> None:
    """Review a scoped adapter execution plan for future implementation readiness."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_execution_readiness_review import (
        review_case_intake_brain_handoff_scoped_adapter_execution_readiness,
    )

    if not scoped_adapter_execution_plan_file.exists():
        raise typer.BadParameter(
            f"scoped adapter execution plan file does not exist: {scoped_adapter_execution_plan_file}"
        )

    scoped_adapter_execution_plan = json.loads(scoped_adapter_execution_plan_file.read_text())
    review = review_case_intake_brain_handoff_scoped_adapter_execution_readiness(
        scoped_adapter_execution_plan,
        reviewed_by=reviewed_by,
        readiness_note=readiness_note,
    )
    data = review.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Execution Readiness Review")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Readiness review ID", review.readiness_review_id)
    table.add_row("Execution plan ID", review.execution_plan_id)
    table.add_row("Runtime confirmation ID", review.runtime_confirmation_id)
    table.add_row("Final gate ID", review.final_gate_id)
    table.add_row("Safety review ID", review.safety_review_id)
    table.add_row("Runtime scope review ID", review.runtime_scope_review_id)
    table.add_row("Request ID", review.request_id)
    table.add_row("Confirmation ID", review.confirmation_id)
    table.add_row("Preview ID", review.preview_id)
    table.add_row("Target", review.target_name)
    table.add_row("Endpoint", review.endpoint)
    table.add_row("Adapter family", review.adapter_family)
    table.add_row("Command family", review.command_family)
    table.add_row("Planned by", review.planned_by)
    table.add_row("Reviewed by", review.reviewed_by)
    table.add_row("Resolved target URL", review.resolved_target_url)
    table.add_row("Reviewed method", review.reviewed_method)
    table.add_row("Reviewed host", review.reviewed_host)
    table.add_row("Execution plan status", review.execution_plan_status)
    table.add_row("Execution plan state", review.execution_plan_state)
    table.add_row("Readiness review status", review.readiness_review_status)
    table.add_row("Readiness review state", review.readiness_review_state)
    table.add_row("Implementation readiness", review.implementation_readiness)
    table.add_row("Adapter execution state", review.adapter_execution_state)
    table.add_row("Readiness findings", str(len(review.readiness_findings)))
    table.add_row("Blocking findings", str(len(review.blocking_findings)))
    table.add_row("Execution plan steps", str(len(review.execution_plan_steps)))
    table.add_row("Execution preflight checks", str(len(review.execution_preflight_checks)))
    table.add_row("Execution stop conditions", str(len(review.execution_stop_conditions)))
    table.add_row("Blocked", str(review.blocked))
    table.add_row("Dry-run only", str(review.dry_run_only))
    table.add_row("Can execute now", str(review.can_execute_now))
    table.add_row("Readiness review allows execution", str(review.readiness_review_allows_execution))
    table.add_row("Execution allowed", str(review.execution_allowed))
    table.add_row("Validation allowed", str(review.validation_allowed))
    table.add_row("Runtime execution allowed", str(review.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(review.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(review.browser_execution_allowed))
    table.add_row("Network requests allowed", str(review.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(review.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(review.target_mutation_allowed))
    table.add_row("Report submission allowed", str(review.report_submission_allowed))
    table.add_row(
        "Vulnerability confirmation allowed",
        str(review.vulnerability_confirmation_allowed),
    )

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row(
        "Vulnerability confirmation",
        str(safety["vulnerability_confirmation"]).lower(),
    )
    console.print(table)

    if review.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {review.block_reason}")
    else:
        console.print("\n[bold]Readiness findings:[/bold]")
        for finding in review.readiness_findings:
            console.print(f"- {finding}")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local readiness review artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter execution readiness JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(review.to_markdown())
        console.print(f"Saved case intake brain scoped adapter execution readiness Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic execution readiness review. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )



@app.command("case-intake-brain-scoped-adapter-implementation-blueprint")
def case_intake_brain_scoped_adapter_implementation_blueprint_command(
    scoped_adapter_execution_readiness_file: Path = typer.Argument(
        ...,
        help="Path to case-intake-brain-scoped-adapter-execution-readiness JSON output.",
    ),
    blueprinted_by: str = typer.Option(
        "human-reviewer",
        "--blueprinted-by",
        help="Neutral reviewer label for the human who prepared the implementation blueprint.",
    ),
    blueprint_note: str = typer.Option(
        ...,
        "--blueprint-note",
        help="Blueprint note for future scoped adapter implementation only.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Markdown implementation blueprint output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write JSON implementation blueprint output.",
    ),
) -> None:
    """Export a scoped adapter implementation blueprint for future implementation only."""
    from bugintel.core.case_intake_brain_handoff_scoped_adapter_implementation_blueprint import (
        export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint,
    )

    if not scoped_adapter_execution_readiness_file.exists():
        raise typer.BadParameter(
            f"scoped adapter execution readiness file does not exist: {scoped_adapter_execution_readiness_file}"
        )

    scoped_adapter_execution_readiness = json.loads(scoped_adapter_execution_readiness_file.read_text())
    blueprint = export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
        scoped_adapter_execution_readiness,
        blueprinted_by=blueprinted_by,
        blueprint_note=blueprint_note,
    )
    data = blueprint.to_dict()

    table = Table(title="Case Intake Brain Scoped Adapter Implementation Blueprint")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Implementation blueprint ID", blueprint.implementation_blueprint_id)
    table.add_row("Readiness review ID", blueprint.readiness_review_id)
    table.add_row("Execution plan ID", blueprint.execution_plan_id)
    table.add_row("Runtime confirmation ID", blueprint.runtime_confirmation_id)
    table.add_row("Final gate ID", blueprint.final_gate_id)
    table.add_row("Safety review ID", blueprint.safety_review_id)
    table.add_row("Runtime scope review ID", blueprint.runtime_scope_review_id)
    table.add_row("Request ID", blueprint.request_id)
    table.add_row("Target", blueprint.target_name)
    table.add_row("Endpoint", blueprint.endpoint)
    table.add_row("Adapter family", blueprint.adapter_family)
    table.add_row("Command family", blueprint.command_family)
    table.add_row("Planned by", blueprint.planned_by)
    table.add_row("Reviewed by", blueprint.reviewed_by)
    table.add_row("Blueprinted by", blueprint.blueprinted_by)
    table.add_row("Readiness review status", blueprint.readiness_review_status)
    table.add_row("Readiness review state", blueprint.readiness_review_state)
    table.add_row("Implementation readiness", blueprint.implementation_readiness)
    table.add_row("Implementation blueprint status", blueprint.implementation_blueprint_status)
    table.add_row("Implementation blueprint state", blueprint.implementation_blueprint_state)
    table.add_row("Adapter execution state", blueprint.adapter_execution_state)
    table.add_row("Proposed module files", str(len(blueprint.proposed_module_files)))
    table.add_row("Proposed interfaces", str(len(blueprint.proposed_interfaces)))
    table.add_row("Proposed dataclasses", str(len(blueprint.proposed_dataclasses)))
    table.add_row("Proposed validation guards", str(len(blueprint.proposed_validation_guards)))
    table.add_row("Proposed test files", str(len(blueprint.proposed_test_files)))
    table.add_row("Blueprint findings", str(len(blueprint.blueprint_findings)))
    table.add_row("Blocking findings", str(len(blueprint.blocking_findings)))
    table.add_row("Blocked", str(blueprint.blocked))
    table.add_row("Dry-run only", str(blueprint.dry_run_only))
    table.add_row("Can execute now", str(blueprint.can_execute_now))
    table.add_row("Implementation blueprint allows execution", str(blueprint.implementation_blueprint_allows_execution))
    table.add_row("Execution allowed", str(blueprint.execution_allowed))
    table.add_row("Validation allowed", str(blueprint.validation_allowed))
    table.add_row("Runtime execution allowed", str(blueprint.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(blueprint.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(blueprint.browser_execution_allowed))
    table.add_row("Network requests allowed", str(blueprint.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(blueprint.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(blueprint.target_mutation_allowed))
    table.add_row("Report submission allowed", str(blueprint.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(blueprint.vulnerability_confirmation_allowed))

    safety = data["safety"]
    table.add_row("Tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Report submission", str(safety["report_submission"]).lower())
    table.add_row("Vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if blueprint.blocked:
        console.print(f"\n[bold]Blocked:[/bold] {blueprint.block_reason}")
    else:
        console.print("\n[bold]Proposed module files:[/bold]")
        for item in blueprint.proposed_module_files:
            console.print(f"- {item}")
        console.print("\n[bold]Important:[/bold] No command was executed. This is a local implementation blueprint artifact only.")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved case intake brain scoped adapter implementation blueprint JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(blueprint.to_markdown())
        console.print(f"Saved case intake brain scoped adapter implementation blueprint Markdown: {output_file}")

    console.print(
        "Safety: This command only exports a local deterministic implementation blueprint. "
        "It does not send requests, execute tools, launch browsers, call providers, "
        "collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate")
def scoped_runtime_execution_gate_command(
    request_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime adapter request or implementation blueprint JSON.",
    ),
    future_authorization_requested: bool = typer.Option(
        False,
        "--future-authorization-requested",
        help="Record that future runtime authorization was requested. This still does not execute anything.",
    ),
    human_authorization_recorded: bool = typer.Option(
        False,
        "--human-authorization-recorded",
        help="Record human authorization metadata for future runtime authorization.",
    ),
    controlled_account_recorded: bool = typer.Option(
        False,
        "--controlled-account-recorded",
        help="Record controlled-account precondition metadata for future runtime authorization.",
    ),
    scope_review_recorded: bool = typer.Option(
        False,
        "--scope-review-recorded",
        help="Record scope review confirmation metadata for future runtime authorization.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate JSON output.",
    ),
    bundle_output_dir: Path | None = typer.Option(
        None,
        "--bundle-output-dir",
        help="Optional directory to write gate.json, gate.md, and manifest.json bundle files.",
    ),
) -> None:
    """Evaluate the scoped runtime execution gate without execution."""
    from bugintel.adapters.scoped_runtime.contracts import ScopedAdapterRequest
    from bugintel.adapters.scoped_runtime.execution_gate import (
        evaluate_scoped_runtime_execution_gate,
    )

    if not request_file.exists():
        raise typer.BadParameter(f"request file does not exist: {request_file}")

    request_data = json.loads(request_file.read_text())
    request = ScopedAdapterRequest.from_blueprint_artifact(request_data)
    artifact = evaluate_scoped_runtime_execution_gate(
        request,
        future_authorization_requested=future_authorization_requested,
        human_authorization_recorded=human_authorization_recorded,
        controlled_account_recorded=controlled_account_recorded,
        scope_review_recorded=scope_review_recorded,
    )
    data = artifact.to_dict()

    table = Table(title="Scoped Runtime Execution Gate")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Gate ID", artifact.gate_id)
    table.add_row("Request ID", artifact.request_id)
    table.add_row("Implementation blueprint ID", artifact.implementation_blueprint_id)
    table.add_row("Target", artifact.target_name)
    table.add_row("Endpoint", artifact.endpoint)
    table.add_row("Gate status", artifact.gate_status)
    table.add_row("Gate mode", artifact.gate_mode)
    table.add_row("Future authorization requested", str(artifact.future_authorization_requested))
    table.add_row("Human authorization recorded", str(artifact.human_authorization_recorded))
    table.add_row("Controlled account recorded", str(artifact.controlled_account_recorded))
    table.add_row("Scope review recorded", str(artifact.scope_review_recorded))
    table.add_row("Adapter execution state", artifact.adapter_execution_state)
    table.add_row("Can execute now", str(artifact.can_execute_now))
    table.add_row("Execution allowed", str(artifact.execution_allowed))
    table.add_row("Runtime execution allowed", str(artifact.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(artifact.tool_execution_allowed))
    table.add_row("Browser execution allowed", str(artifact.browser_execution_allowed))
    table.add_row("Network requests allowed", str(artifact.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(artifact.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(artifact.target_mutation_allowed))
    table.add_row("Report submission allowed", str(artifact.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(artifact.vulnerability_confirmation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if artifact.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in artifact.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Future runtime authorization recorded without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(artifact.to_markdown())
        console.print(f"Saved scoped runtime execution gate Markdown: {output_file}")

    if bundle_output_dir is not None:
        bundle_output_dir.mkdir(parents=True, exist_ok=True)
        bundle_json = bundle_output_dir / "gate.json"
        bundle_markdown = bundle_output_dir / "gate.md"
        bundle_manifest = bundle_output_dir / "manifest.json"
        bundle_json.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        bundle_markdown.write_text(artifact.to_markdown())
        bundle_manifest.write_text(json.dumps(artifact.to_bundle_manifest(), indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle: {bundle_output_dir}")

    console.print(
        "Safety: This command only evaluates a local deterministic scoped runtime execution gate. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-verify")
def scoped_runtime_execution_gate_bundle_verify_command(
    bundle_dir: Path = typer.Argument(
        ...,
        help="Path to a scoped runtime execution gate bundle directory.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle verification Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle verification JSON output.",
    ),
) -> None:
    """Verify a scoped runtime execution gate bundle without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        verify_scoped_runtime_execution_gate_bundle,
    )

    verification = verify_scoped_runtime_execution_gate_bundle(bundle_dir)
    data = verification.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Verification")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Bundle directory", verification.bundle_dir)
    table.add_row("Verification status", verification.verification_status)
    table.add_row("Bundle mode", verification.bundle_mode or "unknown")
    table.add_row("Gate ID", verification.gate_id or "unknown")
    table.add_row("Request ID", verification.request_id or "unknown")
    table.add_row("Gate status", verification.gate_status or "unknown")
    table.add_row("Present files", ", ".join(verification.present_files) or "none")
    table.add_row("Missing files", ", ".join(verification.missing_files) or "none")
    table.add_row("Unexpected files", ", ".join(verification.unexpected_files) or "none")
    table.add_row("Markdown has title", str(verification.markdown_has_title))
    table.add_row("Markdown has unredacted secret", str(verification.markdown_has_unredacted_secret))
    table.add_row("Markdown has redacted placeholder", str(verification.markdown_has_redacted_placeholder))
    table.add_row("Adapter execution state", verification.adapter_execution_state)
    table.add_row("Can execute now", str(verification.can_execute_now))
    table.add_row("Execution allowed", str(verification.execution_allowed))
    table.add_row("Runtime execution allowed", str(verification.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(verification.tool_execution_allowed))
    table.add_row("Network requests allowed", str(verification.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(verification.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(verification.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if verification.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in verification.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle verified without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle verification JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(verification.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle verification Markdown: {output_file}")

    console.print(
        "Safety: This command only verifies local scoped runtime execution gate bundle files. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-review-packet")
def scoped_runtime_execution_gate_bundle_review_packet_command(
    verification_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle verification JSON output.",
    ),
    reviewed_by: str = typer.Option(
        "human-reviewer",
        "--reviewed-by",
        help="Neutral reviewer label for the human who reviewed the bundle verification artifact.",
    ),
    review_note: str = typer.Option(
        ...,
        "--review-note",
        help="Human review note for the local bundle verification artifact.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle review packet Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle review packet JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle review packet without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        review_scoped_runtime_execution_gate_bundle_verification,
    )

    if not verification_file.exists():
        raise typer.BadParameter(f"verification file does not exist: {verification_file}")

    verification_data = json.loads(verification_file.read_text())
    packet = review_scoped_runtime_execution_gate_bundle_verification(
        verification_data,
        reviewed_by=reviewed_by,
        review_note=review_note,
    )
    data = packet.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Review Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Review packet ID", packet.review_packet_id)
    table.add_row("Verification status", packet.verification_status)
    table.add_row("Review status", packet.review_status)
    table.add_row("Review state", packet.review_state)
    table.add_row("Reviewed by", packet.reviewed_by)
    table.add_row("Bundle directory", packet.bundle_dir)
    table.add_row("Bundle mode", packet.bundle_mode)
    table.add_row("Gate ID", packet.gate_id)
    table.add_row("Request ID", packet.request_id)
    table.add_row("Gate status", packet.gate_status)
    table.add_row("Present files", ", ".join(packet.present_files) or "none")
    table.add_row("Missing files", ", ".join(packet.missing_files) or "none")
    table.add_row("Unexpected files", ", ".join(packet.unexpected_files) or "none")
    table.add_row("Adapter execution state", packet.adapter_execution_state)
    table.add_row("Can execute now", str(packet.can_execute_now))
    table.add_row("Execution allowed", str(packet.execution_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(packet.tool_execution_allowed))
    table.add_row("Network requests allowed", str(packet.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(packet.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if packet.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in packet.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle verification review packet accepted without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle review packet JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(packet.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle review packet Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle review packet. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-packet")
def scoped_runtime_execution_gate_bundle_handoff_packet_command(
    review_packet_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle review packet JSON output.",
    ),
    handoff_to: str = typer.Option(
        "future-reviewer",
        "--handoff-to",
        help="Neutral recipient label for the future reviewer or operator.",
    ),
    handoff_note: str = typer.Option(
        ...,
        "--handoff-note",
        help="Human handoff note for the local bundle review packet.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff packet Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff packet JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff packet without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        build_scoped_runtime_execution_gate_bundle_handoff_packet,
    )

    if not review_packet_file.exists():
        raise typer.BadParameter(f"review packet file does not exist: {review_packet_file}")

    review_packet_data = json.loads(review_packet_file.read_text())
    packet = build_scoped_runtime_execution_gate_bundle_handoff_packet(
        review_packet_data,
        handoff_to=handoff_to,
        handoff_note=handoff_note,
    )
    data = packet.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Handoff packet ID", packet.handoff_packet_id)
    table.add_row("Review packet ID", packet.review_packet_id)
    table.add_row("Verification status", packet.verification_status)
    table.add_row("Review status", packet.review_status)
    table.add_row("Handoff status", packet.handoff_status)
    table.add_row("Handoff state", packet.handoff_state)
    table.add_row("Reviewed by", packet.reviewed_by)
    table.add_row("Handoff to", packet.handoff_to)
    table.add_row("Bundle directory", packet.bundle_dir)
    table.add_row("Bundle mode", packet.bundle_mode)
    table.add_row("Gate ID", packet.gate_id)
    table.add_row("Request ID", packet.request_id)
    table.add_row("Gate status", packet.gate_status)
    table.add_row("Present files", ", ".join(packet.present_files) or "none")
    table.add_row("Missing files", ", ".join(packet.missing_files) or "none")
    table.add_row("Unexpected files", ", ".join(packet.unexpected_files) or "none")
    table.add_row("Adapter execution state", packet.adapter_execution_state)
    table.add_row("Can execute now", str(packet.can_execute_now))
    table.add_row("Execution allowed", str(packet.execution_allowed))
    table.add_row("Runtime execution allowed", str(packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(packet.tool_execution_allowed))
    table.add_row("Network requests allowed", str(packet.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(packet.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if packet.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in packet.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff packet ready without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff packet JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(packet.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff packet Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff packet. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-checklist")
def scoped_runtime_execution_gate_bundle_handoff_checklist_command(
    handoff_packet_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff packet JSON output.",
    ),
    checked_by: str = typer.Option(
        "human-reviewer",
        "--checked-by",
        help="Neutral checker label for the human who reviewed the handoff checklist.",
    ),
    checklist_note: str = typer.Option(
        ...,
        "--checklist-note",
        help="Human checklist note for the local bundle handoff packet.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff checklist without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        build_scoped_runtime_execution_gate_bundle_handoff_checklist,
    )

    if not handoff_packet_file.exists():
        raise typer.BadParameter(f"handoff packet file does not exist: {handoff_packet_file}")

    handoff_packet_data = json.loads(handoff_packet_file.read_text())
    checklist = build_scoped_runtime_execution_gate_bundle_handoff_checklist(
        handoff_packet_data,
        checked_by=checked_by,
        checklist_note=checklist_note,
    )
    data = checklist.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Checklist")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Checklist ID", checklist.checklist_id)
    table.add_row("Handoff packet ID", checklist.handoff_packet_id)
    table.add_row("Handoff status", checklist.handoff_status)
    table.add_row("Checklist status", checklist.checklist_status)
    table.add_row("Checklist state", checklist.checklist_state)
    table.add_row("Checked by", checklist.checked_by)
    table.add_row("Handoff to", checklist.handoff_to)
    table.add_row("Verification status", checklist.verification_status)
    table.add_row("Review status", checklist.review_status)
    table.add_row("Bundle directory", checklist.bundle_dir)
    table.add_row("Bundle mode", checklist.bundle_mode)
    table.add_row("Gate ID", checklist.gate_id)
    table.add_row("Request ID", checklist.request_id)
    table.add_row("Gate status", checklist.gate_status)
    table.add_row("Passed checks", str(len(checklist.passed_checks)))
    table.add_row("Failed checks", str(len(checklist.failed_checks)))
    table.add_row("Adapter execution state", checklist.adapter_execution_state)
    table.add_row("Can execute now", str(checklist.can_execute_now))
    table.add_row("Execution allowed", str(checklist.execution_allowed))
    table.add_row("Runtime execution allowed", str(checklist.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(checklist.tool_execution_allowed))
    table.add_row("Network requests allowed", str(checklist.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(checklist.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(checklist.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if checklist.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in checklist.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff checklist passed without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(checklist.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff checklist. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-checklist-summary")
def scoped_runtime_execution_gate_bundle_handoff_checklist_summary_command(
    checklist_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff checklist JSON output.",
    ),
    summarized_by: str = typer.Option(
        "human-reviewer",
        "--summarized-by",
        help="Neutral summarizer label for the human who reviewed the checklist summary.",
    ),
    summary_note: str = typer.Option(
        ...,
        "--summary-note",
        help="Human summary note for the local bundle handoff checklist.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist summary Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist summary JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff checklist summary without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        summarize_scoped_runtime_execution_gate_bundle_handoff_checklist,
    )

    if not checklist_file.exists():
        raise typer.BadParameter(f"checklist file does not exist: {checklist_file}")

    checklist_data = json.loads(checklist_file.read_text())
    summary = summarize_scoped_runtime_execution_gate_bundle_handoff_checklist(
        checklist_data,
        summarized_by=summarized_by,
        summary_note=summary_note,
    )
    data = summary.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Checklist Summary")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Summary ID", summary.summary_id)
    table.add_row("Checklist ID", summary.checklist_id)
    table.add_row("Handoff packet ID", summary.handoff_packet_id)
    table.add_row("Checklist status", summary.checklist_status)
    table.add_row("Summary status", summary.summary_status)
    table.add_row("Summary state", summary.summary_state)
    table.add_row("Summarized by", summary.summarized_by)
    table.add_row("Checked by", summary.checked_by)
    table.add_row("Handoff status", summary.handoff_status)
    table.add_row("Handoff to", summary.handoff_to)
    table.add_row("Verification status", summary.verification_status)
    table.add_row("Review status", summary.review_status)
    table.add_row("Bundle directory", summary.bundle_dir)
    table.add_row("Bundle mode", summary.bundle_mode)
    table.add_row("Gate ID", summary.gate_id)
    table.add_row("Request ID", summary.request_id)
    table.add_row("Gate status", summary.gate_status)
    table.add_row("Required checks", str(summary.required_check_count))
    table.add_row("Passed checks", str(summary.passed_check_count))
    table.add_row("Failed checks", str(summary.failed_check_count))
    table.add_row("Adapter execution state", summary.adapter_execution_state)
    table.add_row("Can execute now", str(summary.can_execute_now))
    table.add_row("Execution allowed", str(summary.execution_allowed))
    table.add_row("Runtime execution allowed", str(summary.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(summary.tool_execution_allowed))
    table.add_row("Network requests allowed", str(summary.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(summary.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(summary.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if summary.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in summary.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff checklist summary completed without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist summary JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(summary.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist summary Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff checklist summary. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-checklist-summary-receipt")
def scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt_command(
    summary_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff checklist summary JSON output.",
    ),
    received_by: str = typer.Option(
        "human-reviewer",
        "--received-by",
        help="Neutral receiver label for the human who recorded the summary receipt.",
    ),
    receipt_note: str = typer.Option(
        ...,
        "--receipt-note",
        help="Human receipt note for the local bundle handoff checklist summary.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist summary receipt Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff checklist summary receipt JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff checklist summary receipt without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        build_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt,
    )

    if not summary_file.exists():
        raise typer.BadParameter(f"summary file does not exist: {summary_file}")

    summary_data = json.loads(summary_file.read_text())
    receipt = build_scoped_runtime_execution_gate_bundle_handoff_checklist_summary_receipt(
        summary_data,
        received_by=received_by,
        receipt_note=receipt_note,
    )
    data = receipt.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Checklist Summary Receipt")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Receipt ID", receipt.receipt_id)
    table.add_row("Summary ID", receipt.summary_id)
    table.add_row("Checklist ID", receipt.checklist_id)
    table.add_row("Handoff packet ID", receipt.handoff_packet_id)
    table.add_row("Summary status", receipt.summary_status)
    table.add_row("Receipt status", receipt.receipt_status)
    table.add_row("Receipt state", receipt.receipt_state)
    table.add_row("Received by", receipt.received_by)
    table.add_row("Summarized by", receipt.summarized_by)
    table.add_row("Checked by", receipt.checked_by)
    table.add_row("Checklist status", receipt.checklist_status)
    table.add_row("Handoff status", receipt.handoff_status)
    table.add_row("Handoff to", receipt.handoff_to)
    table.add_row("Verification status", receipt.verification_status)
    table.add_row("Review status", receipt.review_status)
    table.add_row("Bundle directory", receipt.bundle_dir)
    table.add_row("Bundle mode", receipt.bundle_mode)
    table.add_row("Gate ID", receipt.gate_id)
    table.add_row("Request ID", receipt.request_id)
    table.add_row("Gate status", receipt.gate_status)
    table.add_row("Required checks", str(receipt.required_check_count))
    table.add_row("Passed checks", str(receipt.passed_check_count))
    table.add_row("Failed checks", str(receipt.failed_check_count))
    table.add_row("Final handoff outcome", receipt.final_handoff_outcome)
    table.add_row("Adapter execution state", receipt.adapter_execution_state)
    table.add_row("Can execute now", str(receipt.can_execute_now))
    table.add_row("Execution allowed", str(receipt.execution_allowed))
    table.add_row("Runtime execution allowed", str(receipt.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(receipt.tool_execution_allowed))
    table.add_row("Network requests allowed", str(receipt.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(receipt.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(receipt.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if receipt.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in receipt.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff checklist summary receipt accepted without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist summary receipt JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(receipt.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff checklist summary receipt Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff checklist summary receipt. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-receipt-archive-manifest")
def scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_command(
    receipt_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff checklist summary receipt JSON output.",
    ),
    archived_by: str = typer.Option(
        "human-reviewer",
        "--archived-by",
        help="Neutral archiver label for the human who recorded the archive manifest.",
    ),
    archive_note: str = typer.Option(
        ...,
        "--archive-note",
        help="Human archive note for the local bundle handoff receipt.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff receipt archive manifest without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        build_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest,
    )

    if not receipt_file.exists():
        raise typer.BadParameter(f"receipt file does not exist: {receipt_file}")

    receipt_data = json.loads(receipt_file.read_text())
    archive = build_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest(
        receipt_data,
        archived_by=archived_by,
        archive_note=archive_note,
    )
    data = archive.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Receipt Archive Manifest")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Archive manifest ID", archive.archive_manifest_id)
    table.add_row("Receipt ID", archive.receipt_id)
    table.add_row("Summary ID", archive.summary_id)
    table.add_row("Checklist ID", archive.checklist_id)
    table.add_row("Handoff packet ID", archive.handoff_packet_id)
    table.add_row("Archive status", archive.archive_status)
    table.add_row("Archive state", archive.archive_state)
    table.add_row("Archived by", archive.archived_by)
    table.add_row("Receipt status", archive.receipt_status)
    table.add_row("Receipt state", archive.receipt_state)
    table.add_row("Final handoff outcome", archive.final_handoff_outcome)
    table.add_row("Summary status", archive.summary_status)
    table.add_row("Checklist status", archive.checklist_status)
    table.add_row("Handoff status", archive.handoff_status)
    table.add_row("Verification status", archive.verification_status)
    table.add_row("Review status", archive.review_status)
    table.add_row("Bundle directory", archive.bundle_dir)
    table.add_row("Bundle mode", archive.bundle_mode)
    table.add_row("Gate ID", archive.gate_id)
    table.add_row("Request ID", archive.request_id)
    table.add_row("Gate status", archive.gate_status)
    table.add_row("Upstream artifact count", str(len(archive.upstream_artifact_chain)))
    table.add_row("Required checks", str(archive.required_check_count))
    table.add_row("Passed checks", str(archive.passed_check_count))
    table.add_row("Failed checks", str(archive.failed_check_count))
    table.add_row("Adapter execution state", archive.adapter_execution_state)
    table.add_row("Can execute now", str(archive.can_execute_now))
    table.add_row("Execution allowed", str(archive.execution_allowed))
    table.add_row("Runtime execution allowed", str(archive.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(archive.tool_execution_allowed))
    table.add_row("Network requests allowed", str(archive.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(archive.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(archive.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if archive.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in archive.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff receipt archive manifest created without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(archive.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff receipt archive manifest. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-receipt-archive-manifest-verify")
def scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verify_command(
    archive_manifest_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff receipt archive manifest JSON output.",
    ),
    verified_by: str = typer.Option(
        "human-reviewer",
        "--verified-by",
        help="Neutral verifier label for the human who verified the archive manifest.",
    ),
    verification_note: str = typer.Option(
        ...,
        "--verification-note",
        help="Human verification note for the local archive manifest.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest verification Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest verification JSON output.",
    ),
) -> None:
    """Verify a scoped runtime execution gate bundle handoff receipt archive manifest without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        verify_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest,
    )

    if not archive_manifest_file.exists():
        raise typer.BadParameter(f"archive manifest file does not exist: {archive_manifest_file}")

    archive_manifest_data = json.loads(archive_manifest_file.read_text())
    verification = verify_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest(
        archive_manifest_data,
        verified_by=verified_by,
        verification_note=verification_note,
    )
    data = verification.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Receipt Archive Manifest Verification")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Verification ID", verification.verification_id)
    table.add_row("Archive manifest ID", verification.archive_manifest_id)
    table.add_row("Receipt ID", verification.receipt_id)
    table.add_row("Verification status", verification.verification_status)
    table.add_row("Verification state", verification.verification_state)
    table.add_row("Verified by", verification.verified_by)
    table.add_row("Archive status", verification.archive_status)
    table.add_row("Archive state", verification.archive_state)
    table.add_row("Archived by", verification.archived_by)
    table.add_row("Receipt status", verification.receipt_status)
    table.add_row("Final handoff outcome", verification.final_handoff_outcome)
    table.add_row("Bundle mode", verification.bundle_mode)
    table.add_row("Gate ID", verification.gate_id)
    table.add_row("Request ID", verification.request_id)
    table.add_row("Gate status", verification.gate_status)
    table.add_row("Upstream artifact count", str(verification.upstream_artifact_count))
    table.add_row("Required checks", str(verification.required_check_count))
    table.add_row("Passed checks", str(verification.passed_check_count))
    table.add_row("Failed checks", str(verification.failed_check_count))
    table.add_row("Adapter execution state", verification.adapter_execution_state)
    table.add_row("Can execute now", str(verification.can_execute_now))
    table.add_row("Execution allowed", str(verification.execution_allowed))
    table.add_row("Runtime execution allowed", str(verification.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(verification.tool_execution_allowed))
    table.add_row("Network requests allowed", str(verification.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(verification.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(verification.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if verification.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in verification.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff receipt archive manifest verified without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest verification JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(verification.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest verification Markdown: {output_file}")

    console.print(
        "Safety: This command only verifies a local scoped runtime execution gate bundle handoff receipt archive manifest. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-execution-gate-bundle-handoff-receipt-archive-manifest-verification-review-packet")
def scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification_review_packet_command(
    verification_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime execution gate bundle handoff receipt archive manifest verification JSON output.",
    ),
    reviewed_by: str = typer.Option(
        "human-reviewer",
        "--reviewed-by",
        help="Neutral reviewer label for the human who reviewed the archive manifest verification.",
    ),
    review_note: str = typer.Option(
        ...,
        "--review-note",
        help="Human review note for the local archive manifest verification.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest verification review packet Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write scoped runtime execution gate bundle handoff receipt archive manifest verification review packet JSON output.",
    ),
) -> None:
    """Create a scoped runtime execution gate bundle handoff receipt archive manifest verification review packet without execution."""
    from bugintel.adapters.scoped_runtime.execution_gate import (
        review_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification,
    )

    if not verification_file.exists():
        raise typer.BadParameter(f"verification file does not exist: {verification_file}")

    verification_data = json.loads(verification_file.read_text())
    review_packet = review_scoped_runtime_execution_gate_bundle_handoff_receipt_archive_manifest_verification(
        verification_data,
        reviewed_by=reviewed_by,
        review_note=review_note,
    )
    data = review_packet.to_dict()

    table = Table(title="Scoped Runtime Execution Gate Bundle Handoff Receipt Archive Manifest Verification Review Packet")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Review packet ID", review_packet.review_packet_id)
    table.add_row("Verification ID", review_packet.verification_id)
    table.add_row("Archive manifest ID", review_packet.archive_manifest_id)
    table.add_row("Receipt ID", review_packet.receipt_id)
    table.add_row("Review status", review_packet.review_status)
    table.add_row("Review state", review_packet.review_state)
    table.add_row("Reviewed by", review_packet.reviewed_by)
    table.add_row("Verification status", review_packet.verification_status)
    table.add_row("Verification state", review_packet.verification_state)
    table.add_row("Verified by", review_packet.verified_by)
    table.add_row("Archived by", review_packet.archived_by)
    table.add_row("Archive status", review_packet.archive_status)
    table.add_row("Archive state", review_packet.archive_state)
    table.add_row("Receipt status", review_packet.receipt_status)
    table.add_row("Final handoff outcome", review_packet.final_handoff_outcome)
    table.add_row("Bundle mode", review_packet.bundle_mode)
    table.add_row("Gate ID", review_packet.gate_id)
    table.add_row("Request ID", review_packet.request_id)
    table.add_row("Gate status", review_packet.gate_status)
    table.add_row("Upstream artifact count", str(review_packet.upstream_artifact_count))
    table.add_row("Required checks", str(review_packet.required_check_count))
    table.add_row("Passed checks", str(review_packet.passed_check_count))
    table.add_row("Failed checks", str(review_packet.failed_check_count))
    table.add_row("Adapter execution state", review_packet.adapter_execution_state)
    table.add_row("Can execute now", str(review_packet.can_execute_now))
    table.add_row("Execution allowed", str(review_packet.execution_allowed))
    table.add_row("Runtime execution allowed", str(review_packet.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(review_packet.tool_execution_allowed))
    table.add_row("Network requests allowed", str(review_packet.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(review_packet.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(review_packet.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if review_packet.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in review_packet.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Bundle handoff receipt archive manifest verification review packet accepted without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest verification review packet JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(review_packet.to_markdown())
        console.print(f"Saved scoped runtime execution gate bundle handoff receipt archive manifest verification review packet Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime execution gate bundle handoff receipt archive manifest verification review packet. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-archive-chain-validate")
def scoped_runtime_archive_chain_validate_command(
    artifact_file: Path = typer.Argument(
        ...,
        help="Path to a scoped runtime archive-chain artifact JSON file.",
    ),
    expected_kind: str = typer.Option(
        "",
        "--expected-kind",
        help="Optional expected artifact kind.",
    ),
    required_field: list[str] | None = typer.Option(
        None,
        "--required-field",
        help="Required field name. May be provided multiple times.",
    ),
    expect_status: list[str] | None = typer.Option(
        None,
        "--expect-status",
        help="Expected status as field=value. May be provided multiple times.",
    ),
    expect_default_archive_chain: bool = typer.Option(
        False,
        "--expect-default-archive-chain",
        help="Require the default seven-artifact archive chain.",
    ),
    validated_by: str = typer.Option(
        "human-reviewer",
        "--validated-by",
        help="Neutral validator label.",
    ),
    validation_note: str = typer.Option(
        "",
        "--validation-note",
        help="Human validation note for this local archive-chain validation.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write archive-chain validation Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write archive-chain validation JSON output.",
    ),
) -> None:
    """Validate a scoped runtime archive-chain artifact without execution."""
    from bugintel.adapters.scoped_runtime.archive_chain import (
        EXPECTED_ARCHIVE_CHAIN,
        validate_scoped_runtime_archive_chain_artifact,
    )

    if not artifact_file.exists():
        raise typer.BadParameter(f"artifact file does not exist: {artifact_file}")

    expected_statuses: dict[str, str] = {}
    for item in expect_status or []:
        if "=" not in item:
            raise typer.BadParameter(f"expected status must use field=value format: {item}")
        key, value = item.split("=", 1)
        if not key.strip():
            raise typer.BadParameter(f"expected status field is empty: {item}")
        expected_statuses[key.strip()] = value.strip()

    artifact_data = json.loads(artifact_file.read_text())
    result = validate_scoped_runtime_archive_chain_artifact(
        artifact_data,
        expected_kind=expected_kind,
        required_fields=tuple(required_field or ()),
        expected_statuses=expected_statuses,
        expected_upstream_chain=EXPECTED_ARCHIVE_CHAIN if expect_default_archive_chain else None,
        validated_by=validated_by,
        validation_note=validation_note,
    )
    data = result.to_dict()

    table = Table(title="Scoped Runtime Archive Chain Validation")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Artifact kind", result.artifact_kind)
    table.add_row("Validation status", result.validation_status)
    table.add_row("Validation state", result.validation_state)
    table.add_row("Validated by", result.validated_by)
    table.add_row("Expected kind", result.expected_kind or "none")
    table.add_row("Required fields", ", ".join(result.required_fields) or "none")
    table.add_row("Expected statuses", ", ".join(f"{k}={v}" for k, v in result.expected_statuses.items()) or "none")
    table.add_row("Upstream artifact count", str(result.upstream_artifact_count))
    table.add_row("Expected upstream artifact count", str(result.expected_upstream_artifact_count))
    table.add_row("Adapter execution state", result.adapter_execution_state)
    table.add_row("Can execute now", str(result.can_execute_now))
    table.add_row("Execution allowed", str(result.execution_allowed))
    table.add_row("Runtime execution allowed", str(result.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(result.tool_execution_allowed))
    table.add_row("Network requests allowed", str(result.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(result.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(result.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if result.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in result.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Archive-chain artifact validated without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime archive-chain validation JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(result.to_markdown())
        console.print(f"Saved scoped runtime archive-chain validation Markdown: {output_file}")

    console.print(
        "Safety: This command only validates a local scoped runtime archive-chain artifact. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-archive-chain-batch-validate")
def scoped_runtime_archive_chain_batch_validate_command(
    artifact_dir: Path = typer.Argument(
        ...,
        help="Directory containing scoped runtime archive-chain JSON artifacts.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        help="Recursively include JSON files from subdirectories.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write archive-chain batch validation Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write archive-chain batch validation JSON output.",
    ),
) -> None:
    """Batch-validate scoped runtime archive-chain artifacts without execution."""
    from bugintel.adapters.scoped_runtime.archive_chain_batch import (
        validate_scoped_runtime_archive_chain_directory,
    )

    report = validate_scoped_runtime_archive_chain_directory(
        artifact_dir,
        recursive=recursive,
    )
    data = report.to_dict()

    table = Table(title="Scoped Runtime Archive Chain Batch Validation")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Batch ID", report.batch_id)
    table.add_row("Batch status", report.batch_status)
    table.add_row("Batch state", report.batch_state)
    table.add_row("Input directory", report.input_dir)
    table.add_row("Artifact count", str(report.artifact_count))
    table.add_row("Accepted count", str(report.accepted_count))
    table.add_row("Blocked count", str(report.blocked_count))
    table.add_row("Known kinds", str(len(report.kind_counts)))
    table.add_row("Adapter execution state", report.adapter_execution_state)
    table.add_row("Can execute now", str(report.can_execute_now))
    table.add_row("Execution allowed", str(report.execution_allowed))
    table.add_row("Runtime execution allowed", str(report.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(report.tool_execution_allowed))
    table.add_row("Network requests allowed", str(report.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(report.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(report.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if report.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in report.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Archive-chain batch validated without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime archive-chain batch validation JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(report.to_markdown())
        console.print(f"Saved scoped runtime archive-chain batch validation Markdown: {output_file}")

    console.print(
        "Safety: This command only batch-validates local scoped runtime archive-chain artifacts. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-archive-chain-integrity-manifest")
def scoped_runtime_archive_chain_integrity_manifest_command(
    artifact_dir: Path = typer.Argument(
        ...,
        help="Directory containing scoped runtime archive-chain JSON artifacts.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        help="Recursively include JSON files from subdirectories.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write archive-chain integrity manifest Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write archive-chain integrity manifest JSON output.",
    ),
) -> None:
    """Create a scoped runtime archive-chain integrity manifest without execution."""
    from bugintel.adapters.scoped_runtime.archive_chain_integrity import (
        build_scoped_runtime_archive_chain_integrity_manifest,
    )

    manifest = build_scoped_runtime_archive_chain_integrity_manifest(
        artifact_dir,
        recursive=recursive,
    )
    data = manifest.to_dict()

    table = Table(title="Scoped Runtime Archive Chain Integrity Manifest")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Manifest ID", manifest.manifest_id)
    table.add_row("Manifest status", manifest.manifest_status)
    table.add_row("Manifest state", manifest.manifest_state)
    table.add_row("Input directory", manifest.input_dir)
    table.add_row("Recursive", str(manifest.recursive))
    table.add_row("Artifact count", str(manifest.artifact_count))
    table.add_row("Accepted count", str(manifest.accepted_count))
    table.add_row("Blocked count", str(manifest.blocked_count))
    table.add_row("Batch validation status", manifest.batch_validation_status)
    table.add_row("Adapter execution state", manifest.adapter_execution_state)
    table.add_row("Can execute now", str(manifest.can_execute_now))
    table.add_row("Execution allowed", str(manifest.execution_allowed))
    table.add_row("Runtime execution allowed", str(manifest.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(manifest.tool_execution_allowed))
    table.add_row("Network requests allowed", str(manifest.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(manifest.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(manifest.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if manifest.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in manifest.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Archive-chain integrity manifest created without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime archive-chain integrity manifest JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(manifest.to_markdown())
        console.print(f"Saved scoped runtime archive-chain integrity manifest Markdown: {output_file}")

    console.print(
        "Safety: This command only creates a local scoped runtime archive-chain integrity manifest. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-archive-chain-integrity-verify")
def scoped_runtime_archive_chain_integrity_verify_command(
    manifest_file: Path = typer.Argument(
        ...,
        help="Path to scoped runtime archive-chain integrity manifest JSON.",
    ),
    artifact_dir: Path | None = typer.Option(
        None,
        "--artifact-dir",
        help="Optional artifact directory to recompute SHA-256 hashes.",
    ),
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write archive-chain integrity verification Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write archive-chain integrity verification JSON output.",
    ),
) -> None:
    """Verify a scoped runtime archive-chain integrity manifest without execution."""
    from bugintel.adapters.scoped_runtime.archive_chain_integrity import (
        verify_scoped_runtime_archive_chain_integrity_manifest,
    )

    if not manifest_file.exists():
        raise typer.BadParameter(f"manifest file does not exist: {manifest_file}")

    manifest_data = json.loads(manifest_file.read_text())
    verification = verify_scoped_runtime_archive_chain_integrity_manifest(
        manifest_data,
        artifact_dir=artifact_dir,
    )
    data = verification.to_dict()

    table = Table(title="Scoped Runtime Archive Chain Integrity Verification")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Verification ID", verification.verification_id)
    table.add_row("Manifest ID", verification.manifest_id)
    table.add_row("Verification status", verification.verification_status)
    table.add_row("Verification state", verification.verification_state)
    table.add_row("Manifest status", verification.manifest_status)
    table.add_row("Manifest state", verification.manifest_state)
    table.add_row("Artifact count", str(verification.artifact_count))
    table.add_row("Verified count", str(verification.verified_count))
    table.add_row("Missing count", str(verification.missing_count))
    table.add_row("Mismatch count", str(verification.mismatch_count))
    table.add_row("Recomputed from files", str(verification.recomputed_from_files))
    table.add_row("Adapter execution state", verification.adapter_execution_state)
    table.add_row("Can execute now", str(verification.can_execute_now))
    table.add_row("Execution allowed", str(verification.execution_allowed))
    table.add_row("Runtime execution allowed", str(verification.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(verification.tool_execution_allowed))
    table.add_row("Network requests allowed", str(verification.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(verification.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(verification.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if verification.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in verification.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Archive-chain integrity manifest verified without execution.[/bold]")

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved scoped runtime archive-chain integrity verification JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(verification.to_markdown())
        console.print(f"Saved scoped runtime archive-chain integrity verification Markdown: {output_file}")

    console.print(
        "Safety: This command only verifies a local scoped runtime archive-chain integrity manifest. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("scoped-runtime-archive-chain-audit-pack")
def scoped_runtime_archive_chain_audit_pack_command(
    artifact_dir: Path = typer.Argument(
        ...,
        help="Directory containing scoped runtime archive-chain JSON artifacts.",
    ),
    output_dir: Path = typer.Option(
        ...,
        "--output-dir",
        help="Directory to write the archive-chain audit pack.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        help="Recursively include JSON files from subdirectories.",
    ),
) -> None:
    """Create a scoped runtime archive-chain audit pack without execution."""
    from bugintel.adapters.scoped_runtime.archive_chain_audit_pack import (
        build_scoped_runtime_archive_chain_audit_pack,
    )

    audit_pack = build_scoped_runtime_archive_chain_audit_pack(
        artifact_dir,
        output_dir,
        recursive=recursive,
    )
    data = audit_pack.to_dict()

    table = Table(title="Scoped Runtime Archive Chain Audit Pack")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Audit pack ID", audit_pack.audit_pack_id)
    table.add_row("Audit pack status", audit_pack.audit_pack_status)
    table.add_row("Audit pack state", audit_pack.audit_pack_state)
    table.add_row("Artifact directory", audit_pack.artifact_dir)
    table.add_row("Output directory", audit_pack.output_dir)
    table.add_row("Recursive", str(audit_pack.recursive))
    table.add_row("Generated files", str(len(audit_pack.generated_files)))
    table.add_row("Batch validation status", audit_pack.batch_validation_status)
    table.add_row("Integrity manifest status", audit_pack.integrity_manifest_status)
    table.add_row("Integrity verification status", audit_pack.integrity_verification_status)
    table.add_row("Artifact count", str(audit_pack.artifact_count))
    table.add_row("Accepted count", str(audit_pack.accepted_count))
    table.add_row("Blocked count", str(audit_pack.blocked_count))
    table.add_row("Integrity record count", str(audit_pack.integrity_record_count))
    table.add_row("Integrity verified count", str(audit_pack.integrity_verified_count))
    table.add_row("Integrity missing count", str(audit_pack.integrity_missing_count))
    table.add_row("Integrity mismatch count", str(audit_pack.integrity_mismatch_count))
    table.add_row("Adapter execution state", audit_pack.adapter_execution_state)
    table.add_row("Can execute now", str(audit_pack.can_execute_now))
    table.add_row("Execution allowed", str(audit_pack.execution_allowed))
    table.add_row("Runtime execution allowed", str(audit_pack.runtime_execution_allowed))
    table.add_row("Tool execution allowed", str(audit_pack.tool_execution_allowed))
    table.add_row("Network requests allowed", str(audit_pack.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(audit_pack.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(audit_pack.target_mutation_allowed))

    safety = data["safety"]
    table.add_row("Safety network requests", str(safety["network_requests"]).lower())
    table.add_row("Safety tool execution", str(safety["tool_execution"]).lower())
    table.add_row("Safety evidence collection", str(safety["evidence_collection"]).lower())
    table.add_row("Safety validation execution", str(safety["validation_execution"]).lower())
    table.add_row("Safety report submission", str(safety["report_submission"]).lower())
    table.add_row("Safety vulnerability confirmation", str(safety["vulnerability_confirmation"]).lower())
    console.print(table)

    if audit_pack.blocking_findings:
        console.print("\n[bold]Blocking findings:[/bold]")
        for finding in audit_pack.blocking_findings:
            console.print(f"- {finding}")
    else:
        console.print("\n[bold]Archive-chain audit pack created without execution.[/bold]")

    console.print(f"Saved scoped runtime archive-chain audit pack: {output_dir}")
    console.print(
        "Safety: This command only creates a local scoped runtime archive-chain audit pack. "
        "It does not execute curl, call subprocess, send requests, execute tools, launch browsers, "
        "call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities."
    )


@app.command("blackhole-brain-architecture")
def blackhole_brain_architecture_command(
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Blackhole Brain architecture Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write Blackhole Brain architecture JSON output.",
    ),
) -> None:
    """Export the Blackhole Brain architecture specification."""
    from bugintel.brain.architecture import build_blackhole_brain_architecture_spec

    spec = build_blackhole_brain_architecture_spec()
    data = spec.to_dict()

    table = Table(title="Blackhole Brain Architecture")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Architecture ID", spec.architecture_id)
    table.add_row("Version", spec.version)
    table.add_row("Status", spec.status)
    table.add_row("Entities", str(len(spec.entities)))
    table.add_row("Relationships", str(len(spec.relationships)))
    table.add_row("Pipeline stages", str(len(spec.pipeline)))
    table.add_row("Memory layers", str(len(spec.memory_layers)))
    table.add_row("Service contracts", str(len(spec.service_contracts)))
    table.add_row("Extension points", str(len(spec.extension_points)))
    table.add_row("Adapter execution state", spec.safety.adapter_execution_state)
    table.add_row("Can execute now", str(spec.safety.can_execute_now))
    table.add_row("Execution allowed", str(spec.safety.execution_allowed))
    table.add_row("Network requests allowed", str(spec.safety.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(spec.safety.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(spec.safety.target_mutation_allowed))
    table.add_row("Report submission allowed", str(spec.safety.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(spec.safety.vulnerability_confirmation_allowed))
    console.print(table)

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved Blackhole Brain architecture JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(spec.to_markdown())
        console.print(f"Saved Blackhole Brain architecture Markdown: {output_file}")

    console.print(
        "Safety: architecture export only; no execution, no requests, no evidence collection, "
        "no target mutation, no report submission, and no vulnerability confirmation."
    )


@app.command("brain-knowledge-store")
def brain_knowledge_store_command(
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Brain Knowledge Store Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write Brain Knowledge Store JSON output.",
    ),
) -> None:
    """Export a local Brain Knowledge Store snapshot."""
    from bugintel.brain.knowledge_store import (
        BrainKnowledgeRecord,
        build_brain_knowledge_store_snapshot,
    )

    snapshot = build_brain_knowledge_store_snapshot(
        records=(
            BrainKnowledgeRecord(
                record_id="knowledge-store-foundation",
                record_type="architecture",
                title="Brain Knowledge Store foundation",
                summary="Local deterministic cross-case knowledge snapshot foundation.",
                source="brain-knowledge-store-cli",
                tags=("brain", "knowledge-store", "cross-case"),
                confidence=1.0,
            ),
        )
    )
    data = snapshot.to_dict()

    table = Table(title="Brain Knowledge Store")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Store ID", snapshot.store_id)
    table.add_row("Version", snapshot.version)
    table.add_row("Status", snapshot.status)
    table.add_row("Records", str(len(snapshot.records)))
    table.add_row("Entities", str(len(snapshot.entities)))
    table.add_row("Relationships", str(len(snapshot.relationships)))
    table.add_row("Hypotheses", str(len(snapshot.hypotheses)))
    table.add_row("Adapter execution state", snapshot.safety.adapter_execution_state)
    table.add_row("Can execute now", str(snapshot.safety.can_execute_now))
    table.add_row("Execution allowed", str(snapshot.safety.execution_allowed))
    table.add_row("Network requests allowed", str(snapshot.safety.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(snapshot.safety.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(snapshot.safety.target_mutation_allowed))
    table.add_row("Report submission allowed", str(snapshot.safety.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(snapshot.safety.vulnerability_confirmation_allowed))
    console.print(table)

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved Brain Knowledge Store JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(snapshot.to_markdown())
        console.print(f"Saved Brain Knowledge Store Markdown: {output_file}")

    console.print(
        "Safety: knowledge-store export only; no execution, no requests, no evidence collection, "
        "no target mutation, no report submission, and no vulnerability confirmation."
    )


@app.command("brain-pattern-library")
def brain_pattern_library_command(
    output_file: Path | None = typer.Option(
        None,
        "--output-file",
        "--output",
        help="Optional path to write Brain Pattern Library Markdown output.",
    ),
    json_output: Path | None = typer.Option(
        None,
        "--json-output",
        help="Optional path to write Brain Pattern Library JSON output.",
    ),
) -> None:
    """Export the local Brain Pattern Library."""
    from bugintel.brain.pattern_library import build_brain_pattern_library_snapshot

    snapshot = build_brain_pattern_library_snapshot()
    data = snapshot.to_dict()

    table = Table(title="Brain Pattern Library")
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    table.add_row("Library ID", snapshot.library_id)
    table.add_row("Version", snapshot.version)
    table.add_row("Status", snapshot.status)
    table.add_row("Patterns", str(len(snapshot.patterns)))
    table.add_row("Vulnerability classes", ", ".join(data["vulnerability_classes"]))
    table.add_row("Severity hints", ", ".join(data["severity_hints"]))
    table.add_row("Adapter execution state", snapshot.safety.adapter_execution_state)
    table.add_row("Can execute now", str(snapshot.safety.can_execute_now))
    table.add_row("Execution allowed", str(snapshot.safety.execution_allowed))
    table.add_row("Network requests allowed", str(snapshot.safety.network_requests_allowed))
    table.add_row("Evidence collection allowed", str(snapshot.safety.evidence_collection_allowed))
    table.add_row("Target mutation allowed", str(snapshot.safety.target_mutation_allowed))
    table.add_row("Report submission allowed", str(snapshot.safety.report_submission_allowed))
    table.add_row("Vulnerability confirmation allowed", str(snapshot.safety.vulnerability_confirmation_allowed))
    console.print(table)

    if json_output is not None:
        json_output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        console.print(f"Saved Brain Pattern Library JSON: {json_output}")

    if output_file is not None:
        output_file.write_text(snapshot.to_markdown())
        console.print(f"Saved Brain Pattern Library Markdown: {output_file}")

    console.print(
        "Safety: pattern-library export only; no execution, no requests, no evidence collection, "
        "no target mutation, no report submission, and no vulnerability confirmation."
    )


if __name__ == "__main__":
    app()
