"""The public surface must stay importable and the docstring example must run."""

from __future__ import annotations

import subprocess
import sys

import llm_judge_kit


def test_all_names_are_importable() -> None:
    for name in llm_judge_kit.__all__:
        assert hasattr(llm_judge_kit, name), f"{name} missing from llm_judge_kit"


# Frozen public API surface. Changing this set is a deliberate, documented act:
# update the set AND CHANGELOG.md, and bump the version for any removal/rename
# (those break downstream code). This test catches accidental surface drift.
_PUBLIC_API = frozenset(
    {
        "AnthropicProvider",
        "BaseProvider",
        "CachingProvider",
        "Case",
        "CaseResult",
        "ConfigurationError",
        "ConsensusJudge",
        "DatasetError",
        "Judge",
        "JudgeResult",
        "LLMJudgeError",
        "MockProvider",
        "OllamaProvider",
        "OpenAIProvider",
        "ParseError",
        "Provider",
        "ProviderError",
        "ProviderResponse",
        "Report",
        "RetryProvider",
        "Rubric",
        "RubricError",
        "__version__",
        "available_providers",
        "available_rubrics",
        "enable_debug_logging",
        "extract_json",
        "get_logger",
        "get_rubric",
        "load_dataset",
        "load_report",
        "make_provider",
        "register_provider",
        "register_rubric",
        "render_html",
        "render_json",
        "render_markdown",
        "run_benchmark",
    }
)


def test_public_api_surface_is_frozen() -> None:
    current = set(llm_judge_kit.__all__)
    added = current - _PUBLIC_API
    removed = _PUBLIC_API - current
    assert not added, f"public API grew: {sorted(added)} (update _PUBLIC_API + CHANGELOG)"
    assert not removed, f"public API shrank: {sorted(removed)} (needs version bump + CHANGELOG)"


def test_version_is_sane() -> None:
    assert isinstance(llm_judge_kit.__version__, str)
    assert llm_judge_kit.__version__.count(".") >= 2


def test_headline_snippet_runs() -> None:
    # Mirrors the README / package docstring above-the-fold example.
    from llm_judge_kit import Judge, MockProvider

    judge = Judge(provider=MockProvider(fixed_score=0.9), rubric="factuality")
    result = judge.score("What is the capital of France?", "Paris.")
    assert result > 0.8
    assert result.passed()


def test_importing_core_pulls_in_no_provider_sdks() -> None:
    # The wedge promise: `import llm_judge_kit` must not drag in any provider SDK.
    # Checked in a fresh interpreter because other tests import them eagerly.
    probe = (
        "import sys; import llm_judge_kit; "
        "leaked = sorted(m for m in ('openai', 'anthropic', 'httpx') if m in sys.modules); "
        "assert not leaked, leaked"
    )
    proc = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"core import leaked provider SDKs: {proc.stderr.strip()}"
