"""Tests for the benchmark engine."""

from __future__ import annotations

import pytest

from llmjudge import Case, Judge, MockProvider, run_benchmark
from llmjudge.errors import ConfigurationError


def _judge(score: float, rubric: str = "relevance") -> Judge:
    return Judge(provider=MockProvider(fixed_score=score), rubric=rubric)


def test_report_stats_all_pass() -> None:
    cases = [Case(prompt="p1", response="r1"), Case(prompt="p2", response="r2")]
    report = run_benchmark(_judge(0.8), cases, provider="mock", rubric="relevance", threshold=0.5)
    assert report.count == 2
    assert report.passed == 2
    assert report.pass_rate == pytest.approx(1.0)
    assert report.mean_score == pytest.approx(0.8)
    assert report.provider == "mock"
    assert report.results[0].case.prompt == "p1"


def test_threshold_changes_pass_count() -> None:
    cases = [Case(prompt="p", response="r")]
    report = run_benchmark(_judge(0.6), cases, provider="mock", rubric="relevance", threshold=0.9)
    assert report.passed == 0
    assert report.pass_rate == pytest.approx(0.0)


def test_empty_dataset() -> None:
    report = run_benchmark(_judge(0.5), [], provider="mock", rubric="relevance", threshold=0.5)
    assert report.count == 0
    assert report.mean_score == pytest.approx(0.0)
    assert report.pass_rate == pytest.approx(0.0)


def test_context_is_passed_through() -> None:
    judge = _judge(0.9, rubric="groundedness")
    cases = [Case(prompt="p", response="r", context="the source")]
    report = run_benchmark(judge, cases, provider="mock", rubric="groundedness", threshold=0.5)
    assert report.passed == 1


def test_missing_context_propagates_error() -> None:
    judge = _judge(0.9, rubric="groundedness")
    cases = [Case(prompt="p", response="r")]  # no context
    with pytest.raises(ConfigurationError, match="requires context"):
        run_benchmark(judge, cases, provider="mock", rubric="groundedness", threshold=0.5)
