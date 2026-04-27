"""
BugIntel AI Workbench CLI.

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
from bugintel.core.task_tree import build_endpoint_task_tree, render_tree
from bugintel.integrations.kali_runner import build_curl_plan, execute_curl_plan
from bugintel.integrations.playwright_runner import (
    BrowserCaptureResult,
    BrowserExecutionConfig,
    PlaywrightExecutionSafetyError,
    build_browser_plan,
    build_playwright_execution_preview,
    execute_playwright_plan,
)
from bugintel.integrations.web_fetcher import fetch_web_page
from bugintel.integrations.har_importer import load_har

app = typer.Typer(
    name="bugintel",
    help="BugIntel AI Workbench: human-in-the-loop vulnerability discovery and bug intelligence.",
)

console = Console()


@app.command()
def version():
    """Show BugIntel version."""
    console.print("[bold green]BugIntel AI Workbench[/bold green] version 0.3.0")


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
    endpoints = mine_endpoints(text)
    endpoint_values = [endpoint.value for endpoint in endpoints]

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
    endpoints = mine_endpoints(text)
    endpoint_values = [endpoint.value for endpoint in endpoints]

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
    allow_live_execution: bool = typer.Option(False, "--allow-live-execution", help="Explicitly pass the live execution safety gate. Browser launch is still not implemented yet."),
    json_output: Path | None = typer.Option(None, "--json-output", help="Optional path to save the capture result JSON if the skeleton reaches the handoff stage."),
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
    table.add_row("Playwright available", "YES" if output.get("playwright_available") else "NO")

    console.print(table)

    if json_output:
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(
            json.dumps(result.to_evidence_kwargs(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
        console.print(f"[bold green]Capture result JSON saved:[/bold green] {json_output}")




if __name__ == "__main__":
    app()
