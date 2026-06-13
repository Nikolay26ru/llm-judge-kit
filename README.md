# LLMJudge

> Provider-agnostic, reproducible, typed **LLM-as-a-judge** — a small primitive you can depend on.

[![CI](https://github.com/Nikolay26ru/llmjudge/actions/workflows/ci.yml/badge.svg)](https://github.com/Nikolay26ru/llmjudge/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

LLMJudge is the **wedge**: one tiny, well-tested module for scoring model
outputs with an LLM judge — the part most projects re-implement badly. The core
has **zero required runtime dependencies**, a stable typed API, and runs fully
offline in tests via a deterministic mock.

> 🚧 Under active construction. The core API below is the target shape.

## Why

- **Easy to depend on** — zero transitive deps in the core; providers are opt-in extras.
- **Reproducible** — deterministic offline mock; cache keyed by prompt+rubric+provider+version.
- **Typed** — `mypy --strict` clean; `JudgeResult` is a frozen dataclass with `__float__`.
- **Extensible** — add a provider / rubric / judge strategy without touching the core.

## License

MIT — see [LICENSE](LICENSE).
