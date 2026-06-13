"""LLMJudge — provider-agnostic, reproducible, typed LLM-as-a-judge.

The public API is intentionally tiny so downstream projects can depend on it
without surprises. The headline primitive is :class:`Judge`::

    from llmjudge import Judge

    judge = Judge(provider="mock", rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.0          # JudgeResult compares like its score

See ``README.md`` for a runnable example.
"""

from __future__ import annotations

from llmjudge._logging import enable_debug_logging, get_logger
from llmjudge._version import __version__
from llmjudge.benchmark import CaseResult, Report, run_benchmark
from llmjudge.caching import CachingProvider
from llmjudge.consensus import ConsensusJudge
from llmjudge.dataset import Case, load_dataset
from llmjudge.errors import (
    ConfigurationError,
    DatasetError,
    LLMJudgeError,
    ParseError,
    ProviderError,
    RubricError,
)
from llmjudge.judge import Judge
from llmjudge.parsing import extract_json
from llmjudge.providers import (
    AnthropicProvider,
    BaseProvider,
    MockProvider,
    OllamaProvider,
    OpenAIProvider,
    Provider,
    available_providers,
    make_provider,
    register_provider,
)
from llmjudge.reliability import RetryProvider
from llmjudge.reporting import (
    load_report,
    render_html,
    render_json,
    render_markdown,
)
from llmjudge.rubrics import (
    Rubric,
    available_rubrics,
    get_rubric,
    register_rubric,
)
from llmjudge.types import JudgeResult, ProviderResponse

__all__ = [
    "AnthropicProvider",
    "BaseProvider",
    "CachingProvider",
    "Case",
    "CaseResult",
    "ConfigurationError",
    "ConsensusJudge",
    "DatasetError",
    "Judge",
    "JudgeResult",
    "LLMJudgeError",
    "MockProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "ParseError",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "Report",
    "RetryProvider",
    "Rubric",
    "RubricError",
    "__version__",
    "available_providers",
    "available_rubrics",
    "enable_debug_logging",
    "extract_json",
    "get_logger",
    "get_rubric",
    "load_dataset",
    "load_report",
    "make_provider",
    "register_provider",
    "register_rubric",
    "render_html",
    "render_json",
    "render_markdown",
    "run_benchmark",
]
