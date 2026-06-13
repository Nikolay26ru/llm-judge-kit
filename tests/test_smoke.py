"""Scaffold smoke test: the package imports and exposes a version."""

from __future__ import annotations

import llmjudge


def test_package_imports() -> None:
    assert isinstance(llmjudge.__version__, str)
    assert llmjudge.__version__.count(".") >= 2
