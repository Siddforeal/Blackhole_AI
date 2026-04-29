"""
LLM provider configuration and hard opt-in gate.

This module does not call any provider, does not read API keys, does not make
network requests, and does not execute commands. It only validates whether a
future provider run is allowed by explicit configuration and safety audit state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.llm_safety import LLMPromptSafetyReport


SUPPORTED_PROVIDER_NAMES: tuple[str, ...] = (
    "disabled",
)


@dataclass(frozen=True)
class LLMProviderConfig:
    """Configuration for future provider execution."""

    provider_name: str = "disabled"
    allow_provider_execution: bool = False
    require_prompt_audit_pass: bool = True
    model: str = ""
    timeout_seconds: int = 30

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LLMProviderGateResult:
    """Result of checking whether provider execution is allowed."""

    allowed: bool
    provider_name: str
    reason: str
    required_actions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_provider_config(config: LLMProviderConfig) -> LLMProviderGateResult:
    """Validate provider configuration without running any provider."""
    if config.provider_name not in SUPPORTED_PROVIDER_NAMES:
        return LLMProviderGateResult(
            allowed=False,
            provider_name=config.provider_name,
            reason=f"Unsupported LLM provider: {config.provider_name}",
            required_actions=(
                "Use a supported provider name.",
                "Current supported provider names: disabled.",
            ),
        )

    if config.provider_name == "disabled":
        return LLMProviderGateResult(
            allowed=False,
            provider_name=config.provider_name,
            reason="LLM provider execution is disabled by default.",
            required_actions=(
                "Choose a future supported provider only after explicit opt-in support is implemented.",
            ),
        )

    if not config.allow_provider_execution:
        return LLMProviderGateResult(
            allowed=False,
            provider_name=config.provider_name,
            reason="Provider execution requires explicit opt-in.",
            required_actions=(
                "Set allow_provider_execution=True only after human approval.",
            ),
        )

    return LLMProviderGateResult(
        allowed=True,
        provider_name=config.provider_name,
        reason="Provider execution allowed by configuration.",
        required_actions=(),
    )


def check_prompt_audit_gate(
    config: LLMProviderConfig,
    audit_report: LLMPromptSafetyReport,
) -> LLMProviderGateResult:
    """Check prompt-audit requirements before any future provider run."""
    config_result = validate_provider_config(config)

    if not config_result.allowed:
        return config_result

    if config.require_prompt_audit_pass and audit_report.status != "pass":
        return LLMProviderGateResult(
            allowed=False,
            provider_name=config.provider_name,
            reason=f"Prompt audit did not pass: {audit_report.status}",
            required_actions=(
                "Review and fix prompt safety findings.",
                "Re-run audit-llm-prompt until the audit status is pass.",
            ),
        )

    return LLMProviderGateResult(
        allowed=True,
        provider_name=config.provider_name,
        reason="Provider execution allowed by configuration and prompt audit gate.",
        required_actions=(),
    )
