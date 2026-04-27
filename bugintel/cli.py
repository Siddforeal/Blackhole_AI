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
from bugintel.analyzers.endpoint_miner import mine_endpoints
from bugintel.analyzers.http_parser import parse_http_response
from bugintel.analyzers.response_diff import compare_responses, summarize_response
from bugintel.core.evidence_store import EvidenceStore
from bugintel.core.scope_guard import load_scope_from_dict
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.task_tree import build_endpoint_task_tree, render_tree
from bugintel.integrations.kali_runner import build_curl_plan, execute_curl_plan
from bugintel.integrations.web_fetcher import fetch_web_page

app = typer.Typer(
    name="bugintel",
    help="BugIntel AI Workbench: human-in-the-loop vulnerability discovery and bug intelligence.",
)

console = Console()


@app.command()
def version():
    """Show BugIntel version."""
    console.print("[bold green]BugIntel AI Workbench[/bold green] version 0.1.0")


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


if __name__ == "__main__":
    app()
