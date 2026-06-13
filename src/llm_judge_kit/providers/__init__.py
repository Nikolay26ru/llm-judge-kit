"""Provider backends and the provider registry.

The deterministic :class:`MockProvider` is registered eagerly (it has no
dependencies). Real providers are registered lazily so importing ``llm_judge_kit``
never imports a heavy SDK or requires an optional extra to be installed; the
SDK import happens only when that scheme is actually resolved and a client is
built.
"""

from __future__ import annotations

from llm_judge_kit.providers.anthropic import AnthropicProvider
from llm_judge_kit.providers.base import BaseProvider, Provider
from llm_judge_kit.providers.mock import MockProvider
from llm_judge_kit.providers.ollama import OllamaProvider
from llm_judge_kit.providers.openai import OpenAIProvider
from llm_judge_kit.providers.registry import (
    ProviderFactory,
    available_providers,
    make_provider,
    register_provider,
)

register_provider("mock", lambda model: MockProvider())
register_provider("openai", lambda model: OpenAIProvider(model))
register_provider("anthropic", lambda model: AnthropicProvider(model))
register_provider("ollama", lambda model: OllamaProvider(model))

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "Provider",
    "ProviderFactory",
    "available_providers",
    "make_provider",
    "register_provider",
]
