"""Command-line interface for env-doctor."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from .checks import CheckReport, validate_environment
from .dotenv import DotenvParseError, load_dotenv
from .schema import SchemaError, load_schema


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="env-doctor", description="Validate env vars against a schema")
    subparsers = parser.add_subparsers(dest="command")

    check_parser = subparsers.add_parser("check", help="Validate environment values against a schema")
    check_parser.add_argument("--schema", required=True, help="Path to env schema YAML file")
    check_parser.add_argument("--env", dest="env_path", help="Path to .env file (defaults to process env)")
    check_parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat unexpected variables as errors",
    )
    check_parser.set_defaults(handler=_run_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 2

    try:
        return int(args.handler(args))
    except (SchemaError, DotenvParseError) as exc:
        print(f"env-doctor: error: {exc}", file=sys.stderr)
        return 2


def _run_check(args: argparse.Namespace) -> int:
    schema = load_schema(args.schema)

    if args.env_path:
        environment = load_dotenv(args.env_path)
        source_name = args.env_path
    else:
        environment = dict(os.environ)
        source_name = "process environment"

    report = validate_environment(schema, environment, strict=args.strict)
    _print_report(report)
    print(f"env-doctor: checked {source_name} against {args.schema}")

    return report.exit_code(strict=args.strict)


def _print_report(report: CheckReport) -> None:
    for item in report.items:
        marker = _status_marker(item.status)
        print(f"{marker} {item.name:<24} {item.status:<10} {item.message}")

    ok_count = report.count("ok")
    missing_count = report.count("missing")
    invalid_count = report.count("invalid")
    unexpected_count = report.count("unexpected")
    print(
        "summary: "
        f"ok={ok_count}, missing={missing_count}, invalid={invalid_count}, unexpected={unexpected_count}, "
        f"errors={report.errors}, warnings={report.warnings}"
    )


def _status_marker(status: str) -> str:
    if status == "ok":
        return "✓"
    if status == "missing":
        return "✗"
    if status == "invalid":
        return "✗"
    if status == "unexpected":
        return "⚠"
    return "?"


if __name__ == "__main__":
    raise SystemExit(main())
