"""Structured logging for llmjudge.

Libraries should not configure logging for the host app, so the ``llmjudge``
logger ships with a :class:`~logging.NullHandler` and emits nothing until the
app opts in. Each judgement is logged at DEBUG with structured fields nested
under a single ``llmjudge`` record attribute (so they never collide with stdlib
``LogRecord`` fields).
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger("llmjudge")
logger.addHandler(logging.NullHandler())


def get_logger() -> logging.Logger:
    """Return the package logger (``logging.getLogger("llmjudge")``)."""
    return logger


def log_judgement(**fields: Any) -> None:
    """Emit a structured DEBUG record describing one judgement."""
    logger.debug("judgement", extra={"llmjudge": fields})


class _StructuredFormatter(logging.Formatter):
    """Appends the structured ``llmjudge`` fields to the message as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        fields = getattr(record, "llmjudge", None)
        if fields:
            return f"{base} {json.dumps(fields, sort_keys=True, default=repr)}"
        return base


def enable_debug_logging(level: int = logging.DEBUG) -> logging.Handler:
    """Attach a structured stream handler to the package logger (dev convenience).

    Returns the handler so callers can remove it later. Intended for local
    debugging — production apps should configure logging themselves.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(_StructuredFormatter("%(name)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)
    return handler
