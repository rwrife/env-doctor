"""Schema loading and normalization for env-doctor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_ALLOWED_TYPES = {"string", "int", "float", "bool", "url"}
_ALLOWED_KEYS = {"required", "type", "min", "max", "default", "secret"}


class SchemaError(ValueError):
    """Raised when an env schema is malformed or invalid."""


@dataclass(frozen=True)
class VariableDefinition:
    """Normalized definition for one environment variable."""

    name: str
    required: bool
    type: str
    min: int | float | None
    max: int | float | None
    secret: bool
    has_default: bool
    default: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Render a JSON-serializable representation."""
        data: dict[str, Any] = {
            "name": self.name,
            "required": self.required,
            "type": self.type,
            "secret": self.secret,
        }
        if self.min is not None:
            data["min"] = self.min
        if self.max is not None:
            data["max"] = self.max
        if self.has_default:
            data["default"] = self.default
        return data


@dataclass(frozen=True)
class EnvSchema:
    """Container for all normalized variable definitions."""

    variables: dict[str, VariableDefinition]

    def to_dict(self) -> dict[str, dict[str, Any]]:
        return {"variables": {name: spec.to_dict() for name, spec in self.variables.items()}}


def load_schema(path: str | Path) -> EnvSchema:
    """Load and validate an env schema from disk."""
    schema_path = Path(path)
    try:
        content = schema_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaError(f"Failed to read schema file '{schema_path}': {exc}") from exc
    return loads_schema(content, source=str(schema_path))


def loads_schema(content: str, source: str = "<string>") -> EnvSchema:
    """Load and validate an env schema from YAML text."""
    try:
        raw = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise SchemaError(f"Malformed YAML in schema {source}: {exc}") from exc

    if raw is None:
        raw = {}

    if not isinstance(raw, dict):
        raise SchemaError(f"Schema root must be a mapping in {source}.")

    raw_variables = raw.get("variables")
    if not isinstance(raw_variables, dict):
        raise SchemaError(f"Schema field 'variables' must be a mapping in {source}.")

    variables: dict[str, VariableDefinition] = {}

    for name, raw_spec in raw_variables.items():
        if not isinstance(name, str) or not name.strip():
            raise SchemaError(f"Variable names must be non-empty strings in {source}.")
        if not isinstance(raw_spec, dict):
            raise SchemaError(
                f"Definition for variable '{name}' must be a mapping in {source}."
            )

        unknown_keys = sorted(set(raw_spec.keys()) - _ALLOWED_KEYS)
        if unknown_keys:
            unknown_joined = ", ".join(unknown_keys)
            raise SchemaError(
                f"Variable '{name}' has unsupported field(s): {unknown_joined}."
            )

        var_type = raw_spec.get("type", "string")
        if not isinstance(var_type, str):
            raise SchemaError(f"Variable '{name}' field 'type' must be a string.")
        var_type = var_type.strip().lower()
        if var_type not in _ALLOWED_TYPES:
            allowed = ", ".join(sorted(_ALLOWED_TYPES))
            raise SchemaError(
                f"Variable '{name}' has invalid type '{var_type}'. Allowed types: {allowed}."
            )

        required = _read_bool(raw_spec, "required", name, default=False)
        secret = _read_bool(raw_spec, "secret", name, default=False)

        min_value = _read_optional_number(raw_spec, "min", name)
        max_value = _read_optional_number(raw_spec, "max", name)
        if min_value is not None and max_value is not None and min_value > max_value:
            raise SchemaError(
                f"Variable '{name}' has invalid bounds: min ({min_value}) is greater than max ({max_value})."
            )

        if (min_value is not None or max_value is not None) and var_type not in {"int", "float"}:
            raise SchemaError(
                f"Variable '{name}' uses min/max but type '{var_type}' is not numeric."
            )

        has_default = "default" in raw_spec
        default = raw_spec.get("default")

        variables[name] = VariableDefinition(
            name=name,
            required=required,
            type=var_type,
            min=min_value,
            max=max_value,
            secret=secret,
            has_default=has_default,
            default=default,
        )

    return EnvSchema(variables=variables)


def _read_bool(raw_spec: dict[str, Any], field: str, var_name: str, default: bool) -> bool:
    value = raw_spec.get(field, default)
    if isinstance(value, bool):
        return value
    raise SchemaError(f"Variable '{var_name}' field '{field}' must be true/false.")


def _read_optional_number(
    raw_spec: dict[str, Any], field: str, var_name: str
) -> int | float | None:
    if field not in raw_spec:
        return None
    value = raw_spec[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SchemaError(f"Variable '{var_name}' field '{field}' must be a number.")
    return value
