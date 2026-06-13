# Public API surface

Everything exported from the top-level `llm_judge_kit` package (its `__all__`)
is the **stable public API**. It follows [Semantic Versioning](https://semver.org):
within a `0.x` line we avoid breaking changes; any removal or rename ships with a
`CHANGELOG.md` entry and a version bump. A test (`tests/test_public_api.py`)
freezes this surface so it cannot drift by accident.

Two surfaces ship *alongside* the importable API and are equally stable:

- **CLI** — `llm-judge-kit eval | compare | report` (and `--version`).
- **pytest plugin** — the session-scoped `llm_judge_kit` fixture and
  `JudgeHelper.assert_passes(...)`, auto-registered via a `pytest11` entry point.

```python
from llm_judge_kit import Judge        # everything below imports from the top level
```

## Core

| Name | What it is |
| --- | --- |
| `Judge(provider, rubric, threshold=0.5)` | The headline primitive. `score(prompt, response, *, context=None, reference=None)` → `JudgeResult`. `__call__` is an alias for `score`. `Judge.consensus([...], rubric=...)` builds a `ConsensusJudge`. |
| `JudgeResult` | Frozen, typed verdict: `score` (float in `[0,1]`), `confidence`, `reason`, `evidence`, `violations`, `rubric`, `raw`, `metadata`. Casts via `float(r)` and compares (`<, <=, >, >=`) like its score; `passed(threshold=0.5)`. |
| `ProviderResponse` | Frozen container for a raw model call: `text`, `model`, token counts, `latency_ms`, `cost_usd`, `finish_reason`, `metadata`. |
| `Rubric(name, description, criteria=(), guidance="", requires_context=False)` | Declarative description of *what* to evaluate; `render(...)` produces the strict-JSON judging prompt. |

## Providers

| Name | What it is |
| --- | --- |
| `Provider` | Runtime-checkable `Protocol`: one method, `complete(prompt, **kwargs) -> ProviderResponse`. |
| `BaseProvider` | Convenience base with a `name` attribute. |
| `MockProvider` | Deterministic offline provider (fixed or prompt-hashed score); the default everywhere, so tests need no network. |
| `OpenAIProvider` | OpenAI Chat Completions; works with any OpenAI-compatible `base_url`. Extra: `llm-judge-kit[openai]`. |
| `AnthropicProvider` | Anthropic Messages API (default model `claude-opus-4-8`). Extra: `llm-judge-kit[anthropic]`. |
| `OllamaProvider` | Local Ollama over HTTP. Extra: `llm-judge-kit[ollama]`. |
| `register_provider(scheme, factory)` / `make_provider(spec)` / `available_providers()` | Register and resolve `"scheme:model"` specs. |

Provider SDKs are imported lazily, so the core stays dependency-free.

## Rubrics

| Name | What it is |
| --- | --- |
| `register_rubric(rubric, *, overwrite=False)` / `get_rubric(name)` / `available_rubrics()` | Manage the rubric registry. |

Built-ins (selectable by name): `factuality`, `groundedness` (requires
`context=`), `relevance`, `instruction_following`, `safety`, `coherence`,
`completeness`.

## Consensus & reliability (composable providers/judges)

| Name | What it is |
| --- | --- |
| `ConsensusJudge([judges...])` | Aggregates several judges; `confidence` is derived from inter-judge agreement; member votes land in `metadata`. |
| `RetryProvider(inner, retries=..., timeout=...)` | Retry-with-backoff wrapper; timeout is terminal (not retried). |
| `CachingProvider(inner, store=...)` | Memoizes calls; key = hash of `version + provider + model + prompt + kwargs`. |

## Benchmark & dataset

| Name | What it is |
| --- | --- |
| `run_benchmark(judge, cases, *, provider, rubric, threshold=0.5)` → `Report` | Score a dataset. |
| `Report` | Aggregate: `count`, `passed`, `pass_rate`, `mean_score`, `results`. |
| `CaseResult` | One `(Case, JudgeResult)` pair. |
| `Case` / `load_dataset(path)` | Dataset record and loader for `.jsonl` / `.ndjson` / `.json`. |

## Reporting

| Name | What it is |
| --- | --- |
| `render_json` / `render_markdown` / `render_html` | Render a `Report`. `render_json` round-trips via `load_report`. |
| `load_report(path)` | Load a JSON report back into a `Report` (validates/clamps scores). |

## Utilities, logging, errors, version

| Name | What it is |
| --- | --- |
| `extract_json(text)` | Robustly recover a JSON object from model output (fences, prose, trailing commas). |
| `get_logger()` / `enable_debug_logging()` | The `llm_judge_kit` logger (ships a `NullHandler`). |
| `LLMJudgeError` | Base exception. Subclasses: `ConfigurationError`, `ProviderError`, `ParseError`, `RubricError`, `DatasetError`. |
| `__version__` | Package version string. |
