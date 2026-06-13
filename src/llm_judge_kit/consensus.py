"""Consensus judging: combine several judges into one verdict.

A :class:`ConsensusJudge` runs each member judge and aggregates their scores
(mean or median). Its ``confidence`` is derived from *agreement* — tight scores
mean high confidence, a wide spread means low confidence — which is exactly the
signal a single judge cannot give you.
"""

from __future__ import annotations

import statistics
from collections import Counter
from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

from llm_judge_kit.errors import ConfigurationError
from llm_judge_kit.types import JudgeResult

if TYPE_CHECKING:
    from llm_judge_kit.judge import Judge

Aggregate = Literal["mean", "median"]


class ConsensusJudge:
    """Aggregates several judges' verdicts into one.

    Args:
        judges: The member judges (anything with a ``score`` method); usually
            built via :meth:`llm_judge_kit.Judge.consensus`.
        threshold: Default pass/fail cutoff used by :meth:`passed`.
        aggregate: How to combine member scores — ``"mean"`` or ``"median"``.

    Raises:
        ConfigurationError: If ``judges`` is empty or ``aggregate`` is unknown.
    """

    def __init__(
        self,
        judges: Sequence[Judge],
        *,
        threshold: float = 0.5,
        aggregate: Aggregate = "mean",
    ) -> None:
        members = list(judges)
        if not members:
            raise ConfigurationError("ConsensusJudge needs at least one judge.")
        if aggregate not in ("mean", "median"):
            raise ConfigurationError(f"aggregate must be 'mean' or 'median', got {aggregate!r}.")
        self.judges = members
        self.threshold = threshold
        self.aggregate: Aggregate = aggregate

    def score(
        self,
        prompt: str,
        response: str,
        **kwargs: Any,
    ) -> JudgeResult:
        """Run every member judge and return the aggregated verdict."""
        results = [judge.score(prompt, response, **kwargs) for judge in self.judges]
        scores = [r.score for r in results]
        if self.aggregate == "mean":
            aggregate_score = statistics.fmean(scores)
        else:
            aggregate_score = statistics.median(scores)
        if len(scores) > 1:
            spread = statistics.pstdev(scores)
            confidence = max(0.0, min(1.0, 1.0 - 2.0 * spread))
        else:
            # A single judge trivially "agrees" with itself, so there is no
            # agreement signal — fall back to its own self-reported confidence.
            spread = 0.0
            confidence = results[0].confidence

        # A violation counts if a strict majority of members reported it.
        counts: Counter[str] = Counter(v for r in results for v in set(r.violations))
        majority = len(results) / 2
        violations = tuple(sorted(v for v, c in counts.items() if c > majority))

        # Evidence is the order-preserving union across members.
        seen: set[str] = set()
        evidence: list[str] = []
        for r in results:
            for item in r.evidence:
                if item not in seen:
                    seen.add(item)
                    evidence.append(item)

        votes = [
            {
                "provider": r.metadata.get("provider"),
                "model": r.metadata.get("model"),
                "score": r.score,
                "confidence": r.confidence,
            }
            for r in results
        ]
        metadata: dict[str, Any] = {
            "votes": votes,
            "scores": scores,
            "spread": spread,
            "aggregate": self.aggregate,
            "members": len(results),
        }
        return JudgeResult(
            score=aggregate_score,
            confidence=confidence,
            reason=(
                f"Consensus of {len(results)} judges "
                f"({self.aggregate}={aggregate_score:.3f}, spread={spread:.3f})."
            ),
            evidence=tuple(evidence),
            violations=violations,
            rubric=results[0].rubric,
            metadata=metadata,
        )

    __call__ = score

    def passed(self, prompt: str, response: str, **kwargs: Any) -> bool:
        """Convenience: aggregate and compare against ``threshold``."""
        return self.score(prompt, response, **kwargs).passed(self.threshold)
