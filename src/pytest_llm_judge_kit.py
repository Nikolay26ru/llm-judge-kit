"""pytest plugin: run LLM evals as ordinary pytest tests.

Shipped inside the ``llm_judge_kit`` distribution as a top-level module and wired up
via a ``pytest11`` entry point, so installing ``llm_judge_kit`` makes the
``llm_judge_kit`` fixture available in any pytest suite — no conftest wiring.

    def test_answer_is_grounded(llm_judge_kit):
        llm_judge_kit.assert_passes(
            prompt="How tall is the Eiffel Tower?",
            response=my_model_output,
            rubric="groundedness",
            context=source_docs,
            threshold=0.7,
        )

Select the judge model with ``--llm-judge-kit-provider`` or ``$LLM_JUDGE_KIT_PROVIDER``
(default ``"mock"`` so a suite runs offline until you point it at a real model).
``JudgeHelper`` is also usable directly in non-pytest eval scripts.

This is a separate top-level module (not ``llm_judge_kit.pytest_plugin``) on purpose:
pytest auto-loads plugins during bootstrap, and importing the ``llm_judge_kit``
package there would run all its imports before coverage starts. Here the
``llm_judge_kit`` imports are deferred into the methods, so loading the plugin pulls
in only pytest + stdlib.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from llm_judge_kit.providers.base import Provider
    from llm_judge_kit.types import JudgeResult

_DEFAULT_THRESHOLD = 0.7


class JudgeHelper:
    """A configured judge entry point for tests and eval scripts.

    The provider is resolved once and reused across calls (one client per test
    session); only the rubric varies per assertion.
    """

    def __init__(self, provider: str | Provider) -> None:
        from llm_judge_kit.providers.registry import make_provider

        self.provider: Provider = make_provider(provider) if isinstance(provider, str) else provider

    def score(
        self, prompt: str, response: str, *, rubric: str = "factuality", **kwargs: Any
    ) -> JudgeResult:
        """Score ``response`` against ``rubric`` and return the verdict."""
        from llm_judge_kit.judge import Judge

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
    option = config.getoption("--llm-judge-kit-provider")
    if isinstance(option, str) and option:
        return option
    return os.environ.get("LLM_JUDGE_KIT_PROVIDER") or "mock"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--llm-judge-kit-provider`` option."""
    group = parser.getgroup("llm_judge_kit")
    group.addoption(
        "--llm-judge-kit-provider",
        action="store",
        default=None,
        help=(
            "Provider spec for the llm_judge_kit fixture "
            "(default: $LLM_JUDGE_KIT_PROVIDER or 'mock')."
        ),
    )


@pytest.fixture(scope="session")
def llm_judge_kit(request: pytest.FixtureRequest) -> JudgeHelper:
    """A :class:`JudgeHelper` bound to the configured provider.

    Session-scoped so the provider (and any underlying client) is built once for
    the whole suite, not rebuilt per test.
    """
    return JudgeHelper(_resolve_provider(request.config))
