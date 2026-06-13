"""Call cache wrapper.

``CachingProvider`` memoizes provider completions so repeated judgements (same
rendered prompt, same model, same library version) don't re-hit the API. The
cache key is a SHA-256 of ``version + provider + model + prompt + kwargs`` — the
rendered judging prompt already encodes the rubric and the (prompt, response)
inputs, so this is the ``prompt + rubric + provider + version`` key in practice.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import MutableMapping
from typing import Any

from llm_judge_kit._version import __version__
from llm_judge_kit.providers.base import BaseProvider, Provider
from llm_judge_kit.types import ProviderResponse


class CachingProvider(BaseProvider):
    """Memoizes an inner provider's completions.

    Args:
        inner: The provider to wrap.
        store: Backing store mapping cache key -> response. Defaults to a new
            in-memory dict (per instance, so cross-provider collisions cannot
            happen). If you SHARE one store across providers, they must be
            equivalent: the key captures provider class + name + model + version
            but not arbitrary per-instance config (e.g. a different ``base_url``
            or a mock's ``fixed_score``), so distinct configs with the same
            class/name/model would collide.
    """

    def __init__(
        self,
        inner: Provider,
        *,
        store: MutableMapping[str, ProviderResponse] | None = None,
    ) -> None:
        self.inner = inner
        self.name = getattr(inner, "name", "cache")
        self.store: MutableMapping[str, ProviderResponse] = {} if store is None else store

    def complete(self, prompt: str, **kwargs: Any) -> ProviderResponse:
        """Return a cached response if present, otherwise call and store it."""
        key = self._key(prompt, kwargs)
        cached = self.store.get(key)
        if cached is not None:
            return cached
        response = self.inner.complete(prompt, **kwargs)
        self.store[key] = response
        return response

    def _key(self, prompt: str, kwargs: dict[str, Any]) -> str:
        provider_cls = type(self.inner).__name__
        model = getattr(self.inner, "model", "")
        kwargs_repr = json.dumps(kwargs, sort_keys=True, default=repr)
        payload = "\x00".join(
            [__version__, provider_cls, self.name, str(model), prompt, kwargs_repr]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
