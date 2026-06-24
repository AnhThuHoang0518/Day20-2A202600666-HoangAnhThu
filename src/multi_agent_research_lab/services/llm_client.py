"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import ConfigurationError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class CompletionClient(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion."""


class LLMClient:
    """OpenAI-backed LLM client.

    This lab uses OpenAI for generation. Search data can be mocked, but LLM output
    should come from the configured OpenAI model when the CLI runs.
    """

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion from OpenAI."""

        settings = get_settings()
        if not settings.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY is required for LLM generation.")

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        usage = response.usage
        return LLMResponse(
            content=(response.choices[0].message.content or "").strip(),
            input_tokens=None if usage is None else usage.prompt_tokens,
            output_tokens=None if usage is None else usage.completion_tokens,
            cost_usd=None,
        )
