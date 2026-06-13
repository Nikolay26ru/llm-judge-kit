"""Minimal benchmark engine: run a judge over a dataset, collect a report.

Intentionally decoupled from the judge implementation — anything with a
``score(prompt, response, ...)`` method (a :class:`~llmjudge.Judge` or a
:class:`~llmjudge.ConsensusJudge`) can be benchmarked.
"""

from __future__ import annotations

import statistics
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Protocol

from llmjudge.dataset import Case
from llmjudge.types import JudgeResult


class Scorer(Protocol):
    """Structural type for anything that can score a (prompt, response) pair."""

    def score(self, prompt: str, response: str, **kwargs: Any) -> JudgeResult:  # noqa: D102
        ...


@dataclass(frozen=True)
class CaseResult:
    """A single case paired with its verdict."""

    case: Case
    result: JudgeResult


@dataclass(frozen=True)
class Report:
    """The outcome of benchmarking a judge over a dataset."""

    provider: str
    rubric: str
    threshold: float
    results: tuple[CaseResult, ...]

    @property
    def count(self) -> int:
        """Number of cases evaluated."""
        return len(self.results)

    @property
    def passed(self) -> int:
        """How many cases met the threshold."""
        return sum(1 for cr in self.results if cr.result.passed(self.threshold))

    @property
    def mean_score(self) -> float:
        """Mean score across cases (0.0 for an empty report)."""
        if not self.results:
            return 0.0
        return statistics.fmean(cr.result.score for cr in self.results)

    @property
    def pass_rate(self) -> float:
        """Fraction of cases that passed (0.0 for an empty report)."""
        return self.passed / self.count if self.count else 0.0


def run_benchmark(
    judge: Scorer,
    cases: Iterable[Case],
    *,
    provider: str,
    rubric: str,
    threshold: float = 0.5,
) -> Report:
    """Score every case with ``judge`` and return a :class:`Report`.

    ``provider`` and ``rubric`` are labels recorded on the report (the engine
    stays agnostic to which judge produced the scores).
    """
    results = tuple(
        CaseResult(
            case=case,
            result=judge.score(
                case.prompt,
                case.response,
                context=case.context,
                reference=case.reference,
            ),
        )
        for case in cases
    )
    return Report(provider=provider, rubric=rubric, threshold=threshold, results=results)
