"""Tests for CachingProvider."""

from __future__ import annotations

from typing import Any

from llmjudge import CachingProvider
from llmjudge.providers.base import BaseProvider
from llmjudge.types import ProviderResponse


class _Counter(BaseProvider):
    name = "counter"
    model = "m"

    def __init__(self) -> None:
        self.calls = 0

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        self.calls += 1
        return ProviderResponse(text='{"score": 0.5}', model="m")


def test_repeated_prompt_is_cached() -> None:
    inner = _Counter()
    provider = CachingProvider(inner)
    first = provider.complete("hello")
    second = provider.complete("hello")
    assert inner.calls == 1
    assert first is second


def test_different_prompt_misses_cache() -> None:
    inner = _Counter()
    provider = CachingProvider(inner)
    provider.complete("a")
    provider.complete("b")
    assert inner.calls == 2


def test_kwargs_are_part_of_key() -> None:
    inner = _Counter()
    provider = CachingProvider(inner)
    provider.complete("a", temperature=0)
    provider.complete("a", temperature=1)
    assert inner.calls == 2


def test_custom_store_is_populated() -> None:
    store: dict[str, ProviderResponse] = {}
    provider = CachingProvider(_Counter(), store=store)
    provider.complete("a")
    assert len(store) == 1


def test_prebuilt_store_serves_without_calling_inner() -> None:
    inner = _Counter()
    provider = CachingProvider(inner)
    key = provider._key("a", {})
    provider.store[key] = ProviderResponse(text='{"score": 0.99}', model="cached")
    result = provider.complete("a")
    assert result.model == "cached"
    assert inner.calls == 0


def test_name_propagates_from_inner() -> None:
    assert CachingProvider(_Counter()).name == "counter"


class _A(BaseProvider):
    name = "x"
    model = "m"

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        return ProviderResponse(text="A", model="m")


class _B(BaseProvider):
    name = "x"
    model = "m"

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        return ProviderResponse(text="B", model="m")


def test_distinct_provider_classes_do_not_collide_in_shared_store() -> None:
    # Same name+model, different classes, one shared store: the provider class
    # is part of the key, so B is not served A's cached response.
    store: dict[str, ProviderResponse] = {}
    a = CachingProvider(_A(), store=store)
    b = CachingProvider(_B(), store=store)
    assert a.complete("p").text == "A"
    assert b.complete("p").text == "B"
