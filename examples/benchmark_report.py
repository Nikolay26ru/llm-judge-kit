"""Benchmark a judge over an in-memory dataset and print a Markdown report.

Deterministic with a mock. From the CLI this is:
    llm-judge-kit eval cases.jsonl --provider openai:gpt-5 --rubric factuality
"""

from llm_judge_kit import Case, Judge, MockProvider, render_markdown, run_benchmark

cases = [
    Case(prompt="What is the capital of France?", response="Paris.", id="c1"),
    Case(prompt="What is 2 + 2?", response="5", id="c2"),
]

judge = Judge(provider=MockProvider(fixed_score=0.85), rubric="factuality")
report = run_benchmark(judge, cases, provider="mock", rubric="factuality", threshold=0.5)

print(render_markdown(report))
print(f"pass rate: {report.pass_rate:.0%}  mean: {report.mean_score:.3f}")
