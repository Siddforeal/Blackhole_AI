from bugintel.core.llm_prompt import LLMPromptPackage
from bugintel.core.llm_provider_config import (
    LLMProviderConfig,
    check_prompt_audit_gate,
    validate_provider_config,
)
from bugintel.core.llm_safety import audit_llm_prompt_package


def test_default_provider_config_is_disabled():
    config = LLMProviderConfig()
    data = config.to_dict()

    assert data["provider_name"] == "disabled"
    assert data["allow_provider_execution"] is False
    assert data["require_prompt_audit_pass"] is True
    assert data["timeout_seconds"] == 30


def test_validate_provider_config_blocks_disabled_provider():
    result = validate_provider_config(LLMProviderConfig())

    assert result.allowed is False
    assert result.provider_name == "disabled"
    assert result.reason == "LLM provider execution is disabled by default."
    assert result.required_actions


def test_validate_provider_config_blocks_unknown_provider():
    result = validate_provider_config(
        LLMProviderConfig(
            provider_name="openai",
            allow_provider_execution=True,
            model="gpt-example",
        )
    )

    data = result.to_dict()

    assert data["allowed"] is False
    assert data["provider_name"] == "openai"
    assert "Unsupported LLM provider" in data["reason"]
    assert data["required_actions"]


def test_prompt_audit_gate_returns_disabled_before_audit_status():
    clean_package = LLMPromptPackage(
        system_prompt="You are a safe assistant.",
        user_prompt="Suggest read-only checks.",
        redaction_applied=False,
    )
    audit_report = audit_llm_prompt_package(clean_package)

    result = check_prompt_audit_gate(LLMProviderConfig(), audit_report)

    assert result.allowed is False
    assert result.provider_name == "disabled"
    assert "disabled by default" in result.reason


def test_prompt_audit_gate_blocks_nonpassing_audit_for_future_provider(monkeypatch):
    import bugintel.core.llm_provider_config as provider_config

    monkeypatch.setattr(
        provider_config,
        "SUPPORTED_PROVIDER_NAMES",
        ("disabled", "future-provider"),
    )

    risky_package = LLMPromptPackage(
        system_prompt="You are a safe assistant.",
        user_prompt="token=secret-value",
        redaction_applied=False,
    )
    audit_report = audit_llm_prompt_package(risky_package)

    result = check_prompt_audit_gate(
        LLMProviderConfig(
            provider_name="future-provider",
            allow_provider_execution=True,
            require_prompt_audit_pass=True,
            model="future-model",
        ),
        audit_report,
    )

    assert result.allowed is False
    assert result.provider_name == "future-provider"
    assert "Prompt audit did not pass" in result.reason
    assert result.required_actions


def test_prompt_audit_gate_allows_future_provider_only_when_opted_in_and_audit_passes(monkeypatch):
    import bugintel.core.llm_provider_config as provider_config

    monkeypatch.setattr(
        provider_config,
        "SUPPORTED_PROVIDER_NAMES",
        ("disabled", "future-provider"),
    )

    clean_package = LLMPromptPackage(
        system_prompt="You are a safe assistant.",
        user_prompt="Suggest read-only checks.",
        redaction_applied=False,
    )
    audit_report = audit_llm_prompt_package(clean_package)

    result = check_prompt_audit_gate(
        LLMProviderConfig(
            provider_name="future-provider",
            allow_provider_execution=True,
            require_prompt_audit_pass=True,
            model="future-model",
        ),
        audit_report,
    )

    assert result.allowed is True
    assert result.provider_name == "future-provider"
    assert "prompt audit gate" in result.reason
    assert result.required_actions == ()
