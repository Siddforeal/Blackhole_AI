"""
Agent Registry for BugIntel AI Workbench.

Defines specialist agents used by the future AI orchestrator.

The registry does not execute attacks. It describes which agent is responsible
for which research task so the orchestrator can build a safe, auditable task tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    name: str
    mode: str
    purpose: str
    capabilities: list[str] = field(default_factory=list)
    requires_scope_guard: bool = True
    requires_human_approval: bool = True


def default_agent_registry() -> dict[str, AgentSpec]:
    agents = [
        AgentSpec(
            name="recon_agent",
            mode="website",
            purpose="Collect passive target intelligence and identify attack-surface areas.",
            capabilities=[
                "collect_urls",
                "collect_js_sources",
                "identify_login_flows",
                "identify_interesting_paths",
            ],
        ),
        AgentSpec(
            name="endpoint_agent",
            mode="api",
            purpose="Analyze discovered endpoints and create endpoint-specific testing tasks.",
            capabilities=[
                "categorize_endpoints",
                "prioritize_sensitive_routes",
                "create_endpoint_task_tree",
            ],
        ),
        AgentSpec(
            name="curl_agent",
            mode="kali",
            purpose="Plan and execute safe curl requests through Scope Guard and explicit approval.",
            capabilities=[
                "plan_curl",
                "run_approved_curl",
                "parse_http_response",
                "save_evidence",
            ],
        ),
        AgentSpec(
            name="authz_agent",
            mode="api",
            purpose="Plan authorization and access-control validation workflows.",
            capabilities=[
                "baseline_vs_candidate_plan",
                "random_id_check_plan",
                "role_comparison_plan",
                "response_diff_review",
            ],
        ),
        AgentSpec(
            name="browser_agent",
            mode="browser",
            purpose="Capture browser-observed behavior, network traffic, forms, and frontend sources.",
            capabilities=[
                "playwright_navigation",
                "network_capture",
                "har_capture",
                "screenshot_evidence",
                "js_collection",
            ],
        ),
        AgentSpec(
            name="source_agent",
            mode="source",
            purpose="Analyze source code or frontend code for routes, endpoints, secrets, and authz-sensitive paths.",
            capabilities=[
                "route_extraction",
                "secret_pattern_review",
                "authz_code_path_mapping",
                "source_endpoint_mining",
            ],
        ),
        AgentSpec(
            name="android_agent",
            mode="android",
            purpose="Analyze Android application packages and mobile API surfaces.",
            capabilities=[
                "manifest_analysis",
                "hardcoded_endpoint_extraction",
                "firebase_config_review",
                "deeplink_mapping",
            ],
        ),
        AgentSpec(
            name="ios_agent",
            mode="ios",
            purpose="Analyze iOS application packages, plist files, URL schemes, and API hosts.",
            capabilities=[
                "plist_analysis",
                "url_scheme_extraction",
                "mobile_config_review",
                "api_host_discovery",
            ],
        ),
        AgentSpec(
            name="report_agent",
            mode="reporting",
            purpose="Convert evidence and analysis into human-reviewable reports.",
            capabilities=[
                "evidence_to_markdown",
                "analyst_checklist",
                "report_quality_review",
            ],
            requires_scope_guard=False,
            requires_human_approval=False,
        ),
    ]

    return {agent.name: agent for agent in agents}


def list_agents() -> list[AgentSpec]:
    return list(default_agent_registry().values())


def get_agent(name: str) -> AgentSpec:
    registry = default_agent_registry()

    if name not in registry:
        raise KeyError(f"Unknown agent: {name}")

    return registry[name]


def agents_for_mode(mode: str) -> list[AgentSpec]:
    mode = mode.lower().strip()
    return [agent for agent in list_agents() if agent.mode == mode]


def suggest_agents_for_endpoint(endpoint: str) -> list[AgentSpec]:
    value = endpoint.lower()
    selected: list[str] = ["endpoint_agent", "curl_agent"]

    sensitive_keywords = [
        "admin",
        "account",
        "accounts",
        "user",
        "users",
        "project",
        "projects",
        "role",
        "permission",
        "billing",
        "invoice",
        "export",
        "integration",
        "webhook",
    ]

    if any(keyword in value for keyword in sensitive_keywords):
        selected.append("authz_agent")

    if any(keyword in value for keyword in ["upload", "file", "files", "attachment"]):
        selected.append("source_agent")

    registry = default_agent_registry()
    return [registry[name] for name in selected]
