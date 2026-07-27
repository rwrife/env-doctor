"""Command-line interface for env-doctor."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence

from .checks import CheckReport, validate_environment
from .diffing import diff_environments, format_value
from .dotenv import DotenvParseError, load_dotenv
from .schema import SchemaError, load_schema
from .scaffold import schema_yaml_from_environment


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
    check_parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON report",
    )
    check_parser.set_defaults(handler=_run_check)

    diff_parser = subparsers.add_parser("diff", help="Compare two env files and report drift")
    diff_parser.add_argument("--a", dest="a_path", required=True, help="Baseline .env file path")
    diff_parser.add_argument("--b", dest="b_path", required=True, help="Target .env file path")
    diff_parser.set_defaults(handler=_run_diff)

    init_parser = subparsers.add_parser("init", help="Generate a starter schema from a .env file")
    init_parser.add_argument("--from", dest="from_path", required=True, help="Source .env file path")
    init_parser.set_defaults(handler=_run_init)

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
    if args.json_output:
        payload = report.to_dict()
        payload["strict"] = bool(args.strict)
        payload["schema"] = args.schema
        payload["source"] = source_name
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_report(report)
        print(f"env-doctor: checked {source_name} against {args.schema}")

    return report.exit_code(strict=args.strict)


def _run_diff(args: argparse.Namespace) -> int:
    a_env = load_dotenv(args.a_path)
    b_env = load_dotenv(args.b_path)
    report = diff_environments(a_env, b_env)

    _print_diff_report(report, a_label=args.a_path, b_label=args.b_path)
    print(f"env-doctor: compared {args.a_path} to {args.b_path}")

    return 1 if report.has_drift else 0


def _run_init(args: argparse.Namespace) -> int:
    environment = load_dotenv(args.from_path)
    schema_yaml = schema_yaml_from_environment(environment)
    print(schema_yaml, end="")
    return 0


def _print_diff_report(report, a_label: str, b_label: str) -> None:
    if not report.entries:
        print(f"✓ no drift detected between {a_label} and {b_label}")
        return

    for entry in report.entries:
        marker = _diff_marker(entry.kind)
        if entry.kind == "added":
            print(f"{marker} {entry.key:<24} added    in {b_label}={format_value(entry.key, entry.b_value)}")
            continue
        if entry.kind == "removed":
            print(f"{marker} {entry.key:<24} removed  from {a_label}={format_value(entry.key, entry.a_value)}")
            continue

        print(
            f"{marker} {entry.key:<24} changed  "
            f"{a_label}={format_value(entry.key, entry.a_value)} -> "
            f"{b_label}={format_value(entry.key, entry.b_value)}"
        )

    print(
        "summary: "
        f"added={report.added}, removed={report.removed}, changed={report.changed}, "
        f"drift={len(report.entries)}"
    )


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


def _diff_marker(kind: str) -> str:
    if kind == "added":
        return "+"
    if kind == "removed":
        return "-"
    if kind == "changed":
        return "~"
    return "?"


if __name__ == "__main__":
    raise SystemExit(main())
