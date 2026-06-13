"""Consensus judging — combine several judges; confidence comes from agreement.

Offline/deterministic with mocks. In production use real specs:

    judge = Judge.consensus(
        ["openai:gpt-5", "anthropic:claude-opus-4-8"], rubric="factuality"
    )
"""

from llm_judge_kit import ConsensusJudge, Judge, MockProvider

panel = ConsensusJudge(
    [
        Judge(provider=MockProvider(fixed_score=0.82), rubric="factuality"),
        Judge(provider=MockProvider(fixed_score=0.88), rubric="factuality"),
        Judge(provider=MockProvider(fixed_score=0.80), rubric="factuality"),
    ]
)

result = panel.score("What is the capital of France?", "Paris.")
print(f"score={result.score:.3f}  confidence={result.confidence:.3f}")
print(f"votes={[v['score'] for v in result.metadata['votes']]}")
