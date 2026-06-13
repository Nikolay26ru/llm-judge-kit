"""Tests for ConsensusJudge and Judge.consensus."""

from __future__ import annotations

import pytest

from llmjudge import ConsensusJudge, Judge, MockProvider
from llmjudge.errors import ConfigurationError


def _judge(score: float) -> Judge:
    return Judge(provider=MockProvider(fixed_score=score), rubric="relevance")


def test_mean_aggregation() -> None:
    result = ConsensusJudge([_judge(0.4), _judge(0.6)]).score("p", "r")
    assert result.score == pytest.approx(0.5)
    assert result.metadata["members"] == 2
    assert result.metadata["aggregate"] == "mean"


def test_median_aggregation() -> None:
    judges = [_judge(0.2), _judge(0.4), _judge(0.9)]
    result = ConsensusJudge(judges, aggregate="median").score("p", "r")
    assert result.score == pytest.approx(0.4)


def test_full_agreement_is_high_confidence() -> None:
    result = ConsensusJudge([_judge(0.9), _judge(0.9), _judge(0.9)]).score("p", "r")
    assert result.confidence == pytest.approx(1.0)
    assert result.metadata["spread"] == pytest.approx(0.0)


def test_disagreement_lowers_confidence() -> None:
    result = ConsensusJudge([_judge(0.0), _judge(1.0)]).score("p", "r")
    assert result.confidence == pytest.approx(0.0)  # spread 0.5 -> 1 - 2*0.5


def test_single_member_uses_member_confidence() -> None:
    # One judge has no agreement signal, so consensus reports the member's own
    # confidence (the mock reports 0.9), not a spurious 1.0.
    result = ConsensusJudge([_judge(0.7)]).score("p", "r")
    assert result.score == pytest.approx(0.7)
    assert result.confidence == pytest.approx(0.9)
    assert result.metadata["spread"] == pytest.approx(0.0)


def test_majority_violations_kept_minority_dropped() -> None:
    # fixed_score < 0.5 makes the mock report ["mock_violation"].
    majority = ConsensusJudge([_judge(0.1), _judge(0.1), _judge(0.9)]).score("p", "r")
    assert majority.violations == ("mock_violation",)  # 2/3 reported
    minority = ConsensusJudge([_judge(0.1), _judge(0.9), _judge(0.9)]).score("p", "r")
    assert minority.violations == ()  # 1/3 reported


def test_evidence_is_order_preserving_union() -> None:
    j1 = Judge(
        provider=MockProvider(text='{"score": 0.5, "evidence": ["a", "b"]}'),
        rubric="relevance",
    )
    j2 = Judge(
        provider=MockProvider(text='{"score": 0.5, "evidence": ["b", "c"]}'),
        rubric="relevance",
    )
    assert ConsensusJudge([j1, j2]).score("p", "r").evidence == ("a", "b", "c")


def test_votes_recorded_in_metadata() -> None:
    result = ConsensusJudge([_judge(0.4), _judge(0.6)]).score("p", "r")
    votes = result.metadata["votes"]
    assert [v["score"] for v in votes] == [0.4, 0.6]
    assert all(v["provider"] == "mock" for v in votes)


def test_call_alias() -> None:
    cj = ConsensusJudge([_judge(0.5)])
    assert cj("p", "r").score == cj.score("p", "r").score


def test_passed_uses_threshold() -> None:
    cj = ConsensusJudge([_judge(0.6)], threshold=0.5)
    assert cj.passed("p", "r") is True
    strict = ConsensusJudge([_judge(0.6)], threshold=0.8)
    assert strict.passed("p", "r") is False


def test_empty_judges_raises() -> None:
    with pytest.raises(ConfigurationError, match="at least one"):
        ConsensusJudge([])


def test_bad_aggregate_raises() -> None:
    with pytest.raises(ConfigurationError, match="mean"):
        ConsensusJudge([_judge(0.5)], aggregate="mode")  # type: ignore[arg-type]


def test_judge_consensus_classmethod() -> None:
    judge = Judge.consensus(["mock", "mock", "mock"], rubric="factuality")
    assert isinstance(judge, ConsensusJudge)
    result = judge.score("What is 2+2?", "4")
    assert 0.0 <= result.score <= 1.0
    assert result.rubric == "factuality"


def test_judge_consensus_defaults_to_factuality() -> None:
    judge = Judge.consensus(["mock"])
    assert judge.score("p", "r").rubric == "factuality"
