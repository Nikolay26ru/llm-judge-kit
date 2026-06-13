# ROADMAP

Durable plan of record. Survives context compaction — re-read this after any
`/clear` or auto-compact to recover where work stopped. Keep checkboxes current.

Strategy: ship the **wedge** first — a small, flawless, easy-to-import
`llm_judge_kit` LLM-as-a-judge primitive — then build the platform around the
adopted core. Narrow and deep beats wide and shallow.

## M0 — Scaffold
- [x] `pyproject.toml` (Python 3.11+, src-layout, hatchling build backend)
- [x] ruff + mypy(strict) + pytest + coverage gate config
- [x] MIT `LICENSE`, `.gitignore` (with `.env`)
- [x] doc stubs: README / ROADMAP / CHANGELOG / CLAUDE.md / CONTRIBUTING.md
- [x] empty package imports
- [x] `.github/workflows/ci.yml` runs the same gate
- [x] gate green locally

## M1 — Wedge core (TOP priority)
- [x] `types.py` — `JudgeResult`, `ProviderResponse` (frozen, `__float__`, ordering, `passed()`)
- [x] `providers/base.py` — `Provider` Protocol + `BaseProvider`
- [x] `providers/mock.py` — deterministic `MockProvider` (offline)
- [x] `parsing.py` — robust JSON extraction from model output
- [x] `rubrics/` — built-in rubrics (factuality, groundedness, relevance, instruction_following, safety)
- [x] `errors.py` — typed exception hierarchy
- [x] provider registry / `Judge(provider="mock:...")` string spec parsing
- [x] `judge.py` — `Judge` class + target public API
- [x] README with a working 10-line example above the fold
- [x] full coverage on mock (100%); README example runs

## M2 — Real providers
- [x] openai-compatible provider (any OpenAI-compatible base_url)
- [x] anthropic provider
- [x] ollama provider (httpx)
- [x] live tests gated behind `LLM_JUDGE_KIT_LIVE_TESTS=1` (skip by default)
- [x] offline tests via injected fake clients (no network); lazy SDK import

## M3 — Consensus + reliability
- [x] `ConsensusJudge` (voting across judge models, confidence from agreement)
- [x] `Judge.consensus(...)` classmethod (target API)
- [x] `RetryProvider` — retry + backoff + timeout wrapper (composable)
- [x] `CachingProvider` — call cache (key = hash of version+provider+model+prompt+kwargs)
- [x] structured logging (`llm_judge_kit` logger, NullHandler, `enable_debug_logging`)
- [x] single-source version via `_version.py` + hatchling dynamic version

## M4 — Adoption surface
- [x] `pytest11` plugin (`llm_judge_kit` fixture, `assert_passes`, `--llm-judge-kit-provider`)
- [x] shipped as a top-level `pytest_llm_judge_kit` module (lazy imports) so the
      bootstrap auto-load doesn't break coverage or pull in the whole library
- [x] thin framework-agnostic integration note (LangChain/LlamaIndex/any) + examples
- [x] README "Integrations" section

## M5 — Platform layer
- [x] CLI (`llm-judge-kit eval` / `compare` / `report`) — argparse, zero deps, `--fail-under` for CI
- [x] reporting (JSON / Markdown / HTML), round-trips via `load_report`
- [x] minimal benchmark engine (`run_benchmark` + `Report` stats) + dataset loader (`.jsonl`/`.json`)
- [x] reporting kept separate from the engine (benchmark ⟂ reporting)

## Done / handoff
- [x] wheel builds (`uv build`; verified importable + CLI works from a clean env)
- [x] pushed to public GitHub repo, CI green on 3.11/3.12/3.13
- [x] published to PyPI as `llm-judge-kit` (v0.1.0)
- [ ] (human) submit to "Claude for Open Source"

All milestones M0–M5 complete. Gate green (ruff + ruff-format + mypy strict +
pytest, 99.9% coverage, 215 tests + 3 skipped live). New provider/judge/rubric
adds with no core changes (registries + protocols). Architecture is modular:
benchmark ⟂ provider ⟂ judge ⟂ reporting.

## Decisions log (ambiguity resolutions)
- Repo root at `~/llmjudge` (durable) rather than the session outputs path.
- Dev env pinned to CPython 3.12 (mypy/tooling stability); `requires-python>=3.11`.
- Core has zero runtime deps; providers behind extras `[openai]/[anthropic]/[ollama]`.
- pytest plugin ships inside the `llm_judge_kit` dist via a `pytest11` entry point
  (no second distribution to publish) — easier to depend on.
