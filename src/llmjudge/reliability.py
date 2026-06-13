"""Reliability wrapper: retries with backoff and an optional call timeout.

``RetryProvider`` wraps any provider and is itself a provider, so it composes:

    Judge(provider=RetryProvider(OpenAIProvider(...), retries=3, timeout=30))

Retries are deterministic (the sleep function is injectable for tests). The
timeout is enforced with a worker thread; on timeout the call is abandoned (the
result is discarded) and retried like any other failure.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout
from typing import Any

from llmjudge.errors import ProviderError
from llmjudge.providers.base import BaseProvider, Provider
from llmjudge.types import ProviderResponse


class RetryProvider(BaseProvider):
    """Adds retry-with-backoff and an optional timeout around a provider.

    Args:
        inner: The provider to wrap.
        retries: Number of *additional* attempts after the first (so total
            attempts = ``retries + 1``).
        backoff: Base seconds for exponential backoff (delay = ``backoff * 2**n``).
        timeout: Per-attempt wall-clock timeout in seconds (None disables).
        retry_on: Exception types that trigger a retry.
        sleep: Sleep function (injectable for deterministic tests).
    """

    def __init__(
        self,
        inner: Provider,
        *,
        retries: int = 2,
        backoff: float = 0.5,
        timeout: float | None = None,
        retry_on: tuple[type[BaseException], ...] = (ProviderError,),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.inner = inner
        self.name = getattr(inner, "name", "retry")
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout
        self.retry_on = retry_on
        self._sleep = sleep

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        """Call the inner provider, retrying on failure up to ``retries`` times."""
        last_exc: BaseException | None = None
        for attempt in range(self.retries + 1):
            try:
                return self._call(prompt, **kwargs)
            except self.retry_on as exc:
                last_exc = exc
                if attempt >= self.retries:
                    break
                self._sleep(self.backoff * (2**attempt))
        raise ProviderError(
            f"provider {self.name!r} failed after {self.retries + 1} attempt(s): {last_exc}"
        ) from last_exc

    def _call(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        if self.timeout is None:
            return self.inner.complete(prompt, **kwargs)
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(self.inner.complete, prompt, **kwargs)
        try:
            result = future.result(timeout=self.timeout)
        except FuturesTimeout as exc:
            # Don't wait for the abandoned worker; just stop blocking on it.
            executor.shutdown(wait=False)
            raise ProviderError(f"provider {self.name!r} call exceeded {self.timeout}s") from exc
        executor.shutdown(wait=False)
        return result
