"""Wrap any provider with retries/timeout and a call cache — they compose.

Both wrappers are themselves providers, so they nest around any backend.
"""

from llmjudge import CachingProvider, Judge, MockProvider, RetryProvider

# RetryProvider adds retry-with-backoff + an optional timeout; CachingProvider
# memoizes identical calls. Order: cache around retry around the real provider.
provider = CachingProvider(RetryProvider(MockProvider(fixed_score=0.9), retries=3, timeout=30.0))
judge = Judge(provider=provider, rubric="factuality")

print(judge.score("Q", "A").score)  # first call hits the (mock) provider
print(judge.score("Q", "A").score)  # identical call served from the cache
