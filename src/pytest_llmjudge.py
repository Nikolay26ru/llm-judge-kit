"""pytest plugin: run LLM evals as ordinary pytest tests.

Shipped inside the ``llmjudge`` distribution as a top-level module and wired up
via a ``pytest11`` entry point, so installing ``llmjudge`` makes the
``llm_judge`` fixture available in any pytest suite — no conftest wiring.

    def test_answer_is_grounded(llm_judge):
        llm_judge.assert_passes(
            prompt="How tall is the Eiffel Tower?",
            response=my_model_output,
            rubric="groundedness",
            context=source_docs,
            threshold=0.7,
        )

Select the judge model with ``--llmjudge-provider`` or ``$LLMJUDGE_PROVIDER``
(default ``"mock"`` so a suite runs offline until you point it at a real model).
``JudgeHelper`` is also usable directly in non-pytest eval scripts.

This is a separate top-level module (not ``llmjudge.pytest_plugin``) on purpose:
pytest auto-loads plugins during bootstrap, and importing the ``llmjudge``
package there would run all its imports before coverage starts. Here the
``llmjudge`` imports are deferred into the methods, so loading the plugin pulls
in only pytest + stdlib.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from llmjudge.providers.base import Provider
    from llmjudge.types import JudgeResult

_DEFAULT_THRESHOLD = 0.7


class JudgeHelper:
    """A configured judge entry point for tests and eval scripts.

    The provider is resolved once and reused across calls (one client per test
    session); only the rubric varies per assertion.
    """

    def __init__(self, provider: str | Provider) -> None:
        from llmjudge.providers.registry import make_provider

        self.provider: Provider = make_provider(provider) if isinstance(provider, str) else provider

    def score(
        self, prompt: str, response: str, *, rubric: str = "factuality", **kwargs: Any
    ) -> JudgeResult:
        """Score ``response`` against ``rubric`` and return the verdict."""
        from llmjudge.judge import Judge

        return Judge(provider=self.provider, rubric=rubric).score(prompt, response, **kwargs)

    def assert_passes(
        self,
        prompt: str,
        response: str,
        *,
        rubric: str = "factuality",
        threshold: float = _DEFAULT_THRESHOLD,
        **kwargs: Any,
    ) -> JudgeResult:
        """Score and assert the result meets ``threshold``.

        On failure raises ``AssertionError`` with the score, reason, and any
        violations — so a failing eval reads like any other failing test.
        """
        result = self.score(prompt, response, rubric=rubric, **kwargs)
        if not result.passed(threshold):
            raise AssertionError(_format_failure(rubric, threshold, result))
        return result


def _format_failure(rubric: str, threshold: float, result: JudgeResult) -> str:
    lines = [f"{rubric} judge scored {result.score:.3f} < {threshold:.3f}"]
    if result.reason:
        lines.append(f"reason: {result.reason}")
    if result.violations:
        lines.append(f"violations: {list(result.violations)}")
    return "\n".join(lines)


def _resolve_provider(config: pytest.Config) -> str:
    option = config.getoption("--llmjudge-provider")
    if isinstance(option, str) and option:
        return option
    return os.environ.get("LLMJUDGE_PROVIDER") or "mock"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--llmjudge-provider`` option."""
    group = parser.getgroup("llmjudge")
    group.addoption(
        "--llmjudge-provider",
        action="store",
        default=None,
        help="Provider spec for the llm_judge fixture (default: $LLMJUDGE_PROVIDER or 'mock').",
    )


@pytest.fixture
def llm_judge(request: pytest.FixtureRequest) -> JudgeHelper:
    """A :class:`JudgeHelper` bound to the configured provider."""
    return JudgeHelper(_resolve_provider(request.config))
