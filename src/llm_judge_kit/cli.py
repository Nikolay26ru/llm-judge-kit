"""Command-line interface: ``llm-judge-kit eval | compare | report``.

Built on argparse (stdlib) so the platform layer adds no dependencies. The
default provider is ``mock`` so commands run offline out of the box.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from llm_judge_kit._version import __version__
from llm_judge_kit.benchmark import Report, run_benchmark
from llm_judge_kit.dataset import load_dataset
from llm_judge_kit.errors import LLMJudgeError
from llm_judge_kit.judge import Judge
from llm_judge_kit.reporting import load_report, render_html, render_json, render_markdown

_RENDERERS = {
    "json": render_json,
    "md": render_markdown,
    "markdown": render_markdown,
    "html": render_html,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-judge-kit", description="Provider-agnostic LLM-as-a-judge toolkit."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("eval", help="Judge a dataset and render a report.")
    ev.add_argument("dataset", help="Path to a .jsonl/.ndjson/.json dataset.")
    ev.add_argument("--provider", default="mock", help="Provider spec (default: mock).")
    ev.add_argument("--rubric", default="factuality", help="Rubric (default: factuality).")
    ev.add_argument("--threshold", type=float, default=0.5)
    ev.add_argument("--format", choices=["json", "md", "markdown", "html"], default="md")
    ev.add_argument("--output", "-o", default=None, help="Write to file (default: stdout).")
    ev.add_argument(
        "--fail-under",
        type=float,
        default=None,
        help="Exit non-zero if the pass rate is below this fraction.",
    )
    ev.set_defaults(func=_cmd_eval)

    cmp = sub.add_parser("compare", help="Compare several providers on one dataset.")
    cmp.add_argument("dataset", help="Path to a .jsonl/.ndjson/.json dataset.")
    cmp.add_argument(
        "--provider",
        action="append",
        required=True,
        dest="providers",
        help="Provider spec; repeat to compare several.",
    )
    cmp.add_argument("--rubric", default="factuality")
    cmp.add_argument("--threshold", type=float, default=0.5)
    cmp.set_defaults(func=_cmd_compare)

    rep = sub.add_parser("report", help="Re-render a saved JSON report.")
    rep.add_argument("report", help="JSON report from `eval --format json`.")
    rep.add_argument("--format", choices=["json", "md", "markdown", "html"], default="md")
    rep.add_argument("--output", "-o", default=None)
    rep.set_defaults(func=_cmd_report)

    return parser


def _emit(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text)


def _cmd_eval(args: argparse.Namespace) -> int:
    cases = load_dataset(args.dataset)
    judge = Judge(provider=args.provider, rubric=args.rubric, threshold=args.threshold)
    report = run_benchmark(
        judge,
        cases,
        provider=args.provider,
        rubric=args.rubric,
        threshold=args.threshold,
    )
    _emit(_RENDERERS[args.format](report), args.output)
    if args.fail_under is not None and report.pass_rate < args.fail_under:
        print(
            f"pass rate {report.pass_rate:.1%} is below --fail-under {args.fail_under:.1%}",
            file=sys.stderr,
        )
        return 1
    return 0


def _cmd_compare(args: argparse.Namespace) -> int:
    cases = load_dataset(args.dataset)
    reports: list[tuple[str, Report]] = []
    for spec in args.providers:
        judge = Judge(provider=spec, rubric=args.rubric, threshold=args.threshold)
        reports.append(
            (
                spec,
                run_benchmark(
                    judge,
                    cases,
                    provider=spec,
                    rubric=args.rubric,
                    threshold=args.threshold,
                ),
            )
        )
    print(_render_comparison(reports, args.rubric, args.threshold))
    return 0


def _render_comparison(reports: list[tuple[str, Report]], rubric: str, threshold: float) -> str:
    count = reports[0][1].count
    lines = [
        f"Comparison on rubric '{rubric}' (threshold {threshold:.2f}, {count} cases):",
        "",
        f"{'provider':<32} {'mean':>8} {'pass rate':>10}",
        f"{'-' * 32} {'-' * 8} {'-' * 10}",
    ]
    for spec, report in reports:
        lines.append(f"{spec:<32} {report.mean_score:>8.3f} {report.pass_rate:>9.1%}")
    return "\n".join(lines)


def _cmd_report(args: argparse.Namespace) -> int:
    report = load_report(args.report)
    _emit(_RENDERERS[args.format](report), args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``llm_judge_kit`` console script."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    command: Any = args.func
    try:
        return int(command(args))
    except (LLMJudgeError, OSError) as exc:
        # OSError covers foreseeable file mistakes: a missing -o directory, or
        # pointing eval/report at a directory instead of a file.
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
