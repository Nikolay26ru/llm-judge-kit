"""Run an LLM eval as an ordinary pytest test — no conftest, no wiring.

Installing ``llm-judge-kit`` registers a ``pytest11`` plugin, so the
``llm_judge_kit`` fixture is available in any test file automatically. By
default it uses the offline, deterministic ``mock`` provider, so the suite is
green without an API key. Point it at a real judge to make thresholds bite:

    pytest examples/test_with_pytest.py                                   # offline (mock)
    pytest examples/test_with_pytest.py --llm-judge-kit-provider openai:gpt-5
    # or: export LLM_JUDGE_KIT_PROVIDER=anthropic:claude-opus-4-8

Run it from a clone, or after ``pip install llm-judge-kit pytest``.
"""


def test_answer_is_relevant(llm_judge_kit):
    # `assert_passes` reads like a normal assertion. On failure it raises an
    # AssertionError carrying the score, reason, and any violations — so a bad
    # eval looks like any other failing test.
    #
    # threshold=0.0 keeps this green under the offline mock (a wiring check).
    # Once you select a real provider above, raise it to a real bar, e.g. 0.7.
    llm_judge_kit.assert_passes(
        prompt="What is the capital of France?",
        response="The capital of France is Paris.",
        rubric="relevance",
        threshold=0.0,
    )


def test_rag_answer_is_grounded(llm_judge_kit):
    # `groundedness` checks the answer is supported by the supplied context —
    # the typical RAG guardrail. `score()` hands back the full verdict to inspect.
    result = llm_judge_kit.score(
        prompt="How tall is the Eiffel Tower?",
        response="About 330 metres.",
        rubric="groundedness",
        context="The Eiffel Tower stands 330 m tall including its antennas.",
    )
    assert 0.0 <= result.score <= 1.0  # always a normalized score
    print(f"score={result.score:.2f} reason={result.reason!r} violations={list(result.violations)}")
