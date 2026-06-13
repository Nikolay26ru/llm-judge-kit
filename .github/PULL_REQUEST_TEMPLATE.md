<!-- Thanks for contributing to llm-judge-kit! -->

## Summary

<!-- What does this change, and why? -->

## Checklist

- [ ] The gate passes locally:
      `uv run ruff check . && uv run ruff format --check . && uv run mypy src && uv run pytest --cov=llm_judge_kit`
- [ ] Tests added or updated; coverage stays ≥ 95%
- [ ] No new **required** runtime dependency in the core (real providers stay
      behind optional extras)
- [ ] Public API changes are recorded in `CHANGELOG.md` (and `docs/api.md` if the
      public surface changed)
- [ ] Docs / examples updated if behavior changed

## Related issues

<!-- e.g. "Closes #123" -->
