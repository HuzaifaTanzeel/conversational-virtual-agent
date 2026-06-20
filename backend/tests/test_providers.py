"""Provider stub tests."""

import pytest

from app.providers.llm.anthropic import AnthropicProvider


@pytest.mark.asyncio
async def test_anthropic_stub_raises():
    provider = AnthropicProvider()
    with pytest.raises(NotImplementedError, match="AnthropicProvider"):
        await provider.complete([])
