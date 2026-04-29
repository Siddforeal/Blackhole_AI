"""
Disabled-by-default LLM provider abstraction for Blackhole AI Workbench.

This module does not call OpenAI, Anthropic, local models, or any network API.
It only defines a provider result shape and a disabled provider stub so future
LLM integration can be added behind explicit opt-in gates.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.llm_prompt import LLMPromptPackage


@dataclass(frozen=True)
class LLMProviderResult:
    """Result returned by an LLM provider adapter."""

    provider_name: str
    status: str
    reason: str
    output_text: str = ""
    model: str = ""
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    safety_notes: tuple[str, ...] = (
        "LLM provider execution is disabled by default.",
        "Provider output must be treated as suggestions, not confirmed findings.",
        "All testing must remain authorized and in scope.",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DisabledLLMProvider:
    """Provider stub that never sends prompts anywhere."""

    provider_name: str = "disabled"

    def run(self, prompt_package: LLMPromptPackage) -> LLMProviderResult:
        return LLMProviderResult(
            provider_name=self.provider_name,
            status="disabled",
            reason="LLM provider execution is disabled by default.",
            output_text="",
            model="",
        )


def run_disabled_llm_provider(
    prompt_package: LLMPromptPackage,
) -> LLMProviderResult:
    """Run the disabled provider stub."""
    return DisabledLLMProvider().run(prompt_package)
