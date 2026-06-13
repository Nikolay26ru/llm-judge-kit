"""Tests for the dataset loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from llmjudge import Case, load_dataset
from llmjudge.errors import DatasetError


def test_load_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"id": "a", "prompt": "p1", "response": "r1"}\n'
        "\n"  # blank lines are skipped
        '{"prompt": "p2", "response": "r2", "context": "ctx", "extra": 1}\n'
    )
    cases = load_dataset(path)
    assert len(cases) == 2
    assert cases[0] == Case(prompt="p1", response="r1", id="a")
    assert cases[1].context == "ctx"
    assert cases[1].metadata == {"extra": 1}
    assert cases[1].id is None


def test_load_json_array(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    path.write_text('[{"prompt": "p", "response": "r", "reference": "gold"}]')
    cases = load_dataset(path)
    assert len(cases) == 1
    assert cases[0].reference == "gold"


def test_load_json_single_object(tmp_path: Path) -> None:
    path = tmp_path / "case.json"
    path.write_text('{"prompt": "p", "response": "r"}')
    assert len(load_dataset(path)) == 1


def test_non_string_fields_are_coerced(tmp_path: Path) -> None:
    path = tmp_path / "c.json"
    path.write_text('{"prompt": 42, "response": true, "id": 7}')
    case = load_dataset(path)[0]
    assert case.prompt == "42"
    assert case.response == "True"
    assert case.id == "7"


def test_missing_file_raises() -> None:
    with pytest.raises(DatasetError, match="not found"):
        load_dataset("/nonexistent/cases.jsonl")


def test_unsupported_extension_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.csv"
    path.write_text("prompt,response\n")
    with pytest.raises(DatasetError, match="unsupported"):
        load_dataset(path)


def test_invalid_jsonl_line_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text('{"prompt": "p", "response": "r"}\nnot json\n')
    with pytest.raises(DatasetError, match="line 2"):
        load_dataset(path)


def test_invalid_json_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    path.write_text("{not json")
    with pytest.raises(DatasetError, match="invalid JSON"):
        load_dataset(path)


def test_json_scalar_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    path.write_text("42")
    with pytest.raises(DatasetError, match="object or an array"):
        load_dataset(path)


def test_non_object_record_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.json"
    path.write_text('["not an object"]')
    with pytest.raises(DatasetError, match="not a JSON object"):
        load_dataset(path)


def test_missing_required_fields_raises(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text('{"prompt": "p"}\n')
    with pytest.raises(DatasetError, match="missing required"):
        load_dataset(path)
