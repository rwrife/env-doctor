"""Schema scaffolding helpers for env-doctor init."""

from __future__ import annotations

import re
from collections.abc import Mapping
from urllib.parse import urlparse

import yaml

_BOOL_LITERALS = {"true", "false", "yes", "no", "on", "off"}
_INT_PATTERN = re.compile(r"[+-]?\d+")


def schema_yaml_from_environment(environment: Mapping[str, str]) -> str:
    """Render a starter env.schema.yaml document inferred from env values."""
    variables: dict[str, dict[str, object]] = {}

    for name in sorted(environment.keys()):
        variables[name] = {
            "required": True,
            "type": infer_type(environment[name]),
        }

    document = {"variables": variables}
    return yaml.safe_dump(document, sort_keys=False)


def infer_type(value: str) -> str:
    """Infer one of: int, bool, url, string."""
    raw = value.strip()

    if _looks_like_int(raw):
        return "int"

    if _looks_like_bool(raw):
        return "bool"

    if _looks_like_url(raw):
        return "url"

    return "string"


def _looks_like_bool(value: str) -> bool:
    return value.lower() in _BOOL_LITERALS


def _looks_like_int(value: str) -> bool:
    return bool(_INT_PATTERN.fullmatch(value))


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return bool(parsed.scheme and (parsed.netloc or parsed.path))
