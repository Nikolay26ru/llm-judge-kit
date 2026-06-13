"""Tests for RetryProvider (retry + backoff + timeout)."""

from __future__ import annotations

import time
from typing import Any

import pytest

from llmjudge import MockProvider, RetryProvider
from llmjudge.errors import ProviderError
from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse


class _Flaky(BaseProvider):
    name = "flaky"

    def __init__(self, fail_times: int, exc: type[BaseException] = ProviderError) -> None:
        self.fail_times = fail_times
        self.exc = exc
        self.calls = 0

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.exc("boom")
        return ProviderResponse(text='{"score": 0.5}', model="flaky")


class _Slow(BaseProvider):
    name = "slow"

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        time.sleep(0.05)
        return ProviderResponse(text="{}", model="slow")


def test_succeeds_after_retries_with_backoff() -> None:
    delays: list[float] = []
    inner = _Flaky(fail_times=2)
    provider = RetryProvider(inner, retries=3, backoff=0.5, sleep=delays.append)
    result = provider.complete("p")
    assert result.text == '{"score": 0.5}'
    assert inner.calls == 3
    assert delays == [0.5, 1.0]  # exponential: 0.5*2^0, 0.5*2^1


def test_exhaustion_raises_provider_error() -> None:
    inner = _Flaky(fail_times=99)
    provider = RetryProvider(inner, retries=2, sleep=lambda _d: None)
    with pytest.raises(ProviderError, match="failed after 3 attempt"):
        provider.complete("p")
    assert inner.calls == 3


def test_non_retryable_exception_propagates_immediately() -> None:
    inner = _Flaky(fail_times=1, exc=ValueError)
    provider = RetryProvider(inner, retries=3, sleep=lambda _d: None)
    with pytest.raises(ValueError, match="boom"):
        provider.complete("p")
    assert inner.calls == 1  # not retried


def test_name_propagates_from_inner() -> None:
    assert RetryProvider(MockProvider()).name == "mock"


def test_no_timeout_passthrough() -> None:
    provider = RetryProvider(MockProvider(fixed_score=0.5), timeout=5.0)
    assert provider.complete("p").model == "mock-1"


def test_timeout_raises_provider_error() -> None:
    provider = RetryProvider(_Slow(), retries=0, timeout=0.01)
    with pytest.raises(ProviderError):
        provider.complete("p")
