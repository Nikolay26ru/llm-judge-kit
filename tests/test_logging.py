"""Tests for structured logging."""

from __future__ import annotations

import logging

import pytest

from llmjudge import Judge, MockProvider, enable_debug_logging, get_logger


def test_judge_emits_structured_judgement(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG, logger="llmjudge")
    Judge(provider=MockProvider(fixed_score=0.7), rubric="relevance").score("p", "r")
    records = [r for r in caplog.records if r.message == "judgement"]
    assert records, "no judgement record emitted"
    fields = records[0].llmjudge  # type: ignore[attr-defined]
    assert fields["score"] == 0.7
    assert fields["provider"] == "mock"
    assert fields["rubric"] == "relevance"


def test_get_logger_is_package_logger() -> None:
    assert get_logger().name == "llmjudge"


def test_enable_debug_logging_attaches_handler() -> None:
    logger = get_logger()
    handler = enable_debug_logging()
    try:
        assert handler in logger.handlers
        assert logger.level == logging.DEBUG
    finally:
        logger.removeHandler(handler)


def test_structured_formatter_appends_fields() -> None:
    handler = enable_debug_logging()
    try:
        record = logging.LogRecord("llmjudge", logging.DEBUG, __file__, 1, "judgement", None, None)
        record.llmjudge = {"score": 0.5}  # type: ignore[attr-defined]
        formatted = handler.format(record)
        assert "judgement" in formatted
        assert '"score": 0.5' in formatted
    finally:
        get_logger().removeHandler(handler)


def test_structured_formatter_without_fields_returns_base() -> None:
    handler = enable_debug_logging()
    try:
        record = logging.LogRecord(
            "llmjudge", logging.INFO, __file__, 1, "plain message", None, None
        )
        formatted = handler.format(record)
        assert formatted.endswith("plain message")
        assert "{" not in formatted
    finally:
        get_logger().removeHandler(handler)
