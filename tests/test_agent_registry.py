from bugintel.core.agent_registry import (
    agents_for_mode,
    default_agent_registry,
    get_agent,
    list_agents,
    suggest_agents_for_endpoint,
)


def test_default_registry_contains_core_agents():
    registry = default_agent_registry()

    assert "recon_agent" in registry
    assert "endpoint_agent" in registry
    assert "curl_agent" in registry
    assert "authz_agent" in registry
    assert "browser_agent" in registry
    assert "android_agent" in registry
    assert "ios_agent" in registry
    assert "report_agent" in registry


def test_list_agents_returns_agent_specs():
    agents = list_agents()

    assert len(agents) >= 8
    assert all(agent.name for agent in agents)
    assert all(agent.purpose for agent in agents)


def test_get_agent_returns_specific_agent():
    agent = get_agent("curl_agent")

    assert agent.name == "curl_agent"
    assert agent.mode == "kali"
    assert "plan_curl" in agent.capabilities


def test_agents_for_mode_filters_by_mode():
    api_agents = agents_for_mode("api")

    names = [agent.name for agent in api_agents]

    assert "endpoint_agent" in names
    assert "authz_agent" in names


def test_suggest_agents_for_sensitive_endpoint_includes_authz():
    agents = suggest_agents_for_endpoint("/api/accounts/123/users")

    names = [agent.name for agent in agents]

    assert "endpoint_agent" in names
    assert "curl_agent" in names
    assert "authz_agent" in names


def test_suggest_agents_for_file_endpoint_includes_source_agent():
    agents = suggest_agents_for_endpoint("/api/files/upload")

    names = [agent.name for agent in agents]

    assert "source_agent" in names
