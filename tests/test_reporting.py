"""Tests for report rendering and round-tripping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmjudge import (
    Case,
    Judge,
    MockProvider,
    load_report,
    render_html,
    render_json,
    render_markdown,
    run_benchmark,
)
from llmjudge.errors import DatasetError
from llmjudge.reporting import report_to_dict


def _report(score: float = 0.7, *, text: str | None = None, rubric: str = "relevance"):
    provider = MockProvider(text=text) if text else MockProvider(fixed_score=score)
    judge = Judge(provider=provider, rubric=rubric)
    cases = [Case(prompt="p", response="r", id="c1")]
    return run_benchmark(judge, cases, provider="mock", rubric=rubric, threshold=0.5)


def test_report_to_dict_shape() -> None:
    data = report_to_dict(_report(0.7))
    assert data["provider"] == "mock"
    assert data["summary"]["count"] == 1
    assert data["cases"][0]["id"] == "c1"
    assert data["cases"][0]["score"] == pytest.approx(0.7)
    assert data["cases"][0]["passed"] is True


def test_json_round_trips(tmp_path: Path) -> None:
    report = _report(0.7)
    path = tmp_path / "report.json"
    path.write_text(render_json(report))
    loaded = load_report(path)
    assert loaded.provider == "mock"
    assert loaded.rubric == "relevance"
    assert loaded.count == 1
    assert loaded.results[0].case.id == "c1"
    assert loaded.results[0].result.score == pytest.approx(0.7)


def test_render_json_is_valid_json() -> None:
    parsed = json.loads(render_json(_report(0.5)))
    assert parsed["summary"]["count"] == 1


def test_markdown_has_summary_and_rows() -> None:
    md = render_markdown(_report(0.9))
    assert "# LLMJudge report" in md
    assert "mean score" in md
    assert "| 1 | c1 | 0.900 | PASS |" in md


def test_markdown_escapes_pipes_and_newlines() -> None:
    md = render_markdown(_report(text='{"score": 0.5, "reason": "a|b\\nc"}'))
    assert "a\\|b c" in md


def test_html_escapes_reason() -> None:
    html_out = render_html(_report(text='{"score": 0.5, "reason": "<script>x</script>"}'))
    assert "&lt;script&gt;" in html_out
    assert "<script>" not in html_out


def test_html_has_table() -> None:
    html_out = render_html(_report(0.9))
    assert "<table>" in html_out
    assert "PASS" in html_out


def test_load_report_missing_file() -> None:
    with pytest.raises(DatasetError, match="not found"):
        load_report("/nonexistent/report.json")


def test_load_report_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "r.json"
    path.write_text("{not json")
    with pytest.raises(DatasetError, match="invalid report JSON"):
        load_report(path)


def test_load_report_non_object(tmp_path: Path) -> None:
    path = tmp_path / "r.json"
    path.write_text("[]")
    with pytest.raises(DatasetError, match="must be a JSON object"):
        load_report(path)


def test_load_report_malformed(tmp_path: Path) -> None:
    path = tmp_path / "r.json"
    path.write_text('{"provider": "mock"}')  # missing rubric/threshold/cases
    with pytest.raises(DatasetError, match="malformed report"):
        load_report(path)
