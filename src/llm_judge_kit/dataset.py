"""Evaluation dataset loading.

A dataset is a list of :class:`Case` records (a prompt + the response to judge,
optionally with context/reference). Supported on-disk formats: JSON Lines
(``.jsonl`` / ``.ndjson``) and JSON (``.json``, an array of objects or a single
object). Only ``prompt`` and ``response`` are required per record; any extra
keys are kept in ``metadata``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from llm_judge_kit.errors import DatasetError

_KNOWN_FIELDS = frozenset({"prompt", "response", "context", "reference", "id"})


@dataclass(frozen=True)
class Case:
    """One evaluation record.

    Attributes:
        prompt: The task/instruction given to the evaluated model.
        response: The model output to judge.
        context: Authoritative source material (for grounded rubrics).
        reference: A gold/expected answer, if available.
        id: Stable identifier for the case (defaults to its row index).
        metadata: Any extra fields from the source record.
    """

    prompt: str
    response: str
    context: str | None = None
    reference: str | None = None
    id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict, hash=False)


def load_dataset(path: str | Path) -> list[Case]:
    """Load a dataset from ``.jsonl``/``.ndjson`` or ``.json``.

    Raises:
        DatasetError: If the file is missing, has an unsupported extension,
            contains invalid JSON, or a record lacks ``prompt``/``response``.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise DatasetError(f"dataset not found: {file_path}")
    text = file_path.read_text(encoding="utf-8")
    suffix = file_path.suffix.lower()
    if suffix in (".jsonl", ".ndjson"):
        records = _parse_jsonl(text)
    elif suffix == ".json":
        records = _parse_json(text)
    else:
        raise DatasetError(
            f"unsupported dataset extension {file_path.suffix!r}; use .json or .jsonl"
        )
    return [_to_case(record, index) for index, record in enumerate(records)]


def _parse_jsonl(text: str) -> list[Any]:
    records: list[Any] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise DatasetError(f"invalid JSON on line {lineno}: {exc}") from exc
    return records


def _parse_json(text: str) -> list[Any]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise DatasetError(f"invalid JSON: {exc}") from exc
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise DatasetError("a .json dataset must be an object or an array of objects")


def _to_case(record: Any, index: int) -> Case:
    if not isinstance(record, dict):
        raise DatasetError(f"record {index} is not a JSON object")
    # Treat a missing OR null prompt/response as missing — coercing null to the
    # literal string "None" would silently judge nonsense.
    if record.get("prompt") is None or record.get("response") is None:
        raise DatasetError(f"record {index} is missing required 'prompt'/'response'")
    metadata = {k: v for k, v in record.items() if k not in _KNOWN_FIELDS}
    return Case(
        prompt=str(record["prompt"]),
        response=str(record["response"]),
        context=_opt_str(record.get("context")),
        reference=_opt_str(record.get("reference")),
        id=_opt_str(record.get("id")),
        metadata=metadata,
    )


def _opt_str(value: Any) -> str | None:
    return None if value is None else str(value)
