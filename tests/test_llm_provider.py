from bugintel.core.llm_prompt import build_llm_prompt_package_from_research_plan
from bugintel.core.llm_provider import (
    DisabledLLMProvider,
    LLMProviderResult,
    run_disabled_llm_provider,
)
from bugintel.core.research_planner import build_research_plan_from_browser_evidence


def make_prompt_package():
    evidence = {
        "target_name": "demo-lab",
        "task_name": "capture dashboard",
        "evidence_type": "browser",
        "network_events": [
            {
                "method": "GET",
                "url": "https://demo.example.com/api/accounts/123/users",
                "status_code": 200,
            }
        ],
    }

    plan = build_research_plan_from_browser_evidence(evidence)
    return build_llm_prompt_package_from_research_plan(plan)


def test_llm_provider_result_serializes_to_dict():
    result = LLMProviderResult(
        provider_name="disabled",
        status="disabled",
        reason="LLM provider execution is disabled by default.",
    )

    data = result.to_dict()

    assert data["provider_name"] == "disabled"
    assert data["status"] == "disabled"
    assert data["output_text"] == ""
    assert data["prompt_tokens"] is None
    assert data["completion_tokens"] is None
    assert data["safety_notes"]


def test_disabled_llm_provider_never_returns_model_output():
    package = make_prompt_package()
    provider = DisabledLLMProvider()

    result = provider.run(package)
    data = result.to_dict()

    assert data["provider_name"] == "disabled"
    assert data["status"] == "disabled"
    assert data["reason"] == "LLM provider execution is disabled by default."
    assert data["output_text"] == ""
    assert data["model"] == ""


def test_run_disabled_llm_provider_returns_disabled_result():
    package = make_prompt_package()

    result = run_disabled_llm_provider(package)

    assert result.provider_name == "disabled"
    assert result.status == "disabled"
    assert "disabled by default" in result.reason
    assert result.output_text == ""
