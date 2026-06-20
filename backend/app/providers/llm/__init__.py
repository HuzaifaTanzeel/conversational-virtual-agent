from app.config import get_settings
from app.providers.llm.base import LLMProvider, Message


def get_llm_provider() -> LLMProvider:
    """
    Factory — returns the configured LLM implementation.
    SWAP: change LLM_PROVIDER env var to switch providers.
    Supported: openai | anthropic
    """
    settings = get_settings()

    if settings.llm_provider == "openai":
        from app.providers.llm.openai import OpenAIProvider
        return OpenAIProvider(settings)

    if settings.llm_provider == "anthropic":
        from app.providers.llm.anthropic import AnthropicProvider
        return AnthropicProvider(settings)

    raise ValueError(
        f"Unknown LLM provider: '{settings.llm_provider}'. "
        f"Supported values: openai, anthropic"
    )


__all__ = ["LLMProvider", "Message", "get_llm_provider"]
