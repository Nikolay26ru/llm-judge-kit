"""Tests for the bundled pytest plugin (the adoption surface)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from pytest_llmjudge import JudgeHelper, _format_failure, _resolve_provider

from llmjudge import JudgeResult, MockProvider


def test_judge_helper_resolves_string_provider() -> None:
    assert JudgeHelper("mock").provider.name == "mock"


def test_judge_helper_accepts_provider_instance() -> None:
    provider = MockProvider(fixed_score=0.9)
    assert JudgeHelper(provider).provider is provider


def test_assert_passes_returns_result_on_success() -> None:
    helper = JudgeHelper(MockProvider(fixed_score=0.9))
    result = helper.assert_passes("p", "r", rubric="relevance", threshold=0.7)
    assert isinstance(result, JudgeResult)
    assert result.score == 0.9


def test_assert_passes_raises_with_diagnostics_on_failure() -> None:
    helper = JudgeHelper(MockProvider(fixed_score=0.2))
    with pytest.raises(AssertionError) as info:
        helper.assert_passes("p", "r", rubric="relevance", threshold=0.7)
    message = str(info.value)
    assert "scored 0.200 < 0.700" in message
    assert "reason:" in message
    assert "violations: ['mock_violation']" in message


def test_score_passes_through_kwargs() -> None:
    helper = JudgeHelper(MockProvider(fixed_score=0.95))
    result = helper.score("p", "r", rubric="groundedness", context="source")
    assert result.rubric == "groundedness"
    assert result.score == 0.95


def test_format_failure_omits_empty_sections() -> None:
    result = JudgeResult(score=0.1, reason="", violations=())
    message = _format_failure("factuality", 0.5, result)
    assert message == "factuality judge scored 0.100 < 0.500"


def test_resolve_provider_option_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMJUDGE_PROVIDER", "anthropic:x")
    config = SimpleNamespace(getoption=lambda _name: "openai:gpt-5")
    assert _resolve_provider(config) == "openai:gpt-5"  # type: ignore[arg-type]


def test_resolve_provider_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLMJUDGE_PROVIDER", "ollama:llama3")
    config = SimpleNamespace(getoption=lambda _name: None)
    assert _resolve_provider(config) == "ollama:llama3"  # type: ignore[arg-type]


def test_resolve_provider_defaults_to_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLMJUDGE_PROVIDER", raising=False)
    config = SimpleNamespace(getoption=lambda _name: None)
    assert _resolve_provider(config) == "mock"  # type: ignore[arg-type]


def test_llm_judge_fixture_is_available(llm_judge: JudgeHelper) -> None:
    # The fixture comes from the auto-loaded pytest11 entry point — its mere
    # availability proves the plugin is registered. Default provider is mock.
    assert isinstance(llm_judge, JudgeHelper)
    assert llm_judge.provider.name == "mock"
    result = llm_judge.assert_passes("2+2?", "4", rubric="relevance", threshold=0.0)
    assert isinstance(result, JudgeResult)
