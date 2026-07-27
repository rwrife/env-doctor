"""Validation logic for checking environment values against a schema."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

from .schema import EnvSchema, VariableDefinition


@dataclass(frozen=True)
class CheckItem:
    """A single validation outcome for one environment variable."""

    name: str
    status: str  # ok | missing | invalid | unexpected
    message: str
    source: str  # env | default | schema
    value: Any = None

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "source": self.source,
        }
        if self.value is not None:
            data["value"] = self.value
        return data


@dataclass(frozen=True)
class CheckReport:
    """Aggregate result of validating an environment against a schema."""

    items: list[CheckItem]
    errors: int
    warnings: int

    def count(self, status: str) -> int:
        return sum(1 for item in self.items if item.status == status)

    def exit_code(self, strict: bool = False) -> int:
        if self.errors > 0:
            return 1
        if strict and self.warnings > 0:
            return 1
        return 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "counts": {
                "ok": self.count("ok"),
                "missing": self.count("missing"),
                "invalid": self.count("invalid"),
                "unexpected": self.count("unexpected"),
            },
            "items": [item.to_dict() for item in self.items],
        }


def validate_environment(
    schema: EnvSchema,
    environment: Mapping[str, Any],
    *,
    strict: bool = False,
) -> CheckReport:
    """Validate a mapping of env values against a loaded schema."""
    items: list[CheckItem] = []
    errors = 0
    warnings = 0

    schema_names = set(schema.variables.keys())

    for name, spec in schema.variables.items():
        if name in environment:
            raw = environment[name]
            ok, normalized, message = _validate_value(raw, spec)
            if ok:
                items.append(CheckItem(name=name, status="ok", message="ok", source="env", value=normalized))
            else:
                errors += 1
                items.append(
                    CheckItem(
                        name=name,
                        status="invalid",
                        message=message,
                        source="env",
                        value=raw,
                    )
                )
            continue

        if spec.has_default:
            ok, normalized, message = _validate_value(spec.default, spec)
            if ok:
                items.append(
                    CheckItem(
                        name=name,
                        status="ok",
                        message="ok (default applied)",
                        source="default",
                        value=normalized,
                    )
                )
            else:
                errors += 1
                items.append(
                    CheckItem(
                        name=name,
                        status="invalid",
                        message=f"invalid default: {message}",
                        source="default",
                        value=spec.default,
                    )
                )
            continue

        if spec.required:
            errors += 1
            items.append(
                CheckItem(
                    name=name,
                    status="missing",
                    message="required variable is not set",
                    source="schema",
                )
            )
        else:
            items.append(
                CheckItem(
                    name=name,
                    status="missing",
                    message="optional variable is not set",
                    source="schema",
                )
            )

    unexpected_names = sorted(set(environment.keys()) - schema_names)
    for name in unexpected_names:
        if strict:
            errors += 1
        else:
            warnings += 1
        items.append(
            CheckItem(
                name=name,
                status="unexpected",
                message="present but not declared in schema",
                source="env",
                value=environment[name],
            )
        )

    return CheckReport(items=items, errors=errors, warnings=warnings)


def _validate_value(value: Any, spec: VariableDefinition) -> tuple[bool, Any | None, str]:
    try:
        normalized = _coerce_type(value, spec.type)
    except ValueError as exc:
        return False, None, str(exc)

    if spec.type in {"int", "float"}:
        numeric = float(normalized)
        if spec.min is not None and numeric < spec.min:
            return False, None, f"value {normalized!r} is less than min {spec.min}"
        if spec.max is not None and numeric > spec.max:
            return False, None, f"value {normalized!r} is greater than max {spec.max}"

    return True, normalized, "ok"


def _coerce_type(value: Any, expected_type: str) -> Any:
    if expected_type == "string":
        if isinstance(value, str):
            return value
        return str(value)

    if expected_type == "int":
        if isinstance(value, bool):
            raise ValueError("expected int but got bool")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            if value.is_integer():
                return int(value)
            raise ValueError(f"expected int but got non-integer float {value!r}")
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("expected int but got empty string")
            try:
                return int(raw, 10)
            except ValueError as exc:
                raise ValueError(f"expected int but got {value!r}") from exc
        raise ValueError(f"expected int but got {type(value).__name__}")

    if expected_type == "float":
        if isinstance(value, bool):
            raise ValueError("expected float but got bool")
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                raise ValueError("expected float but got empty string")
            try:
                return float(raw)
            except ValueError as exc:
                raise ValueError(f"expected float but got {value!r}") from exc
        raise ValueError(f"expected float but got {type(value).__name__}")

    if expected_type == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            if value in {0, 1}:
                return bool(value)
            raise ValueError(f"expected bool but got integer {value!r}")
        if isinstance(value, str):
            raw = value.strip().lower()
            truthy = {"1", "true", "yes", "on"}
            falsy = {"0", "false", "no", "off"}
            if raw in truthy:
                return True
            if raw in falsy:
                return False
            raise ValueError(
                f"expected bool but got {value!r} (allowed: true/false/1/0/yes/no/on/off)"
            )
        raise ValueError(f"expected bool but got {type(value).__name__}")

    if expected_type == "url":
        if not isinstance(value, str):
            value = str(value)
        parsed = urlparse(value)
        if not parsed.scheme:
            raise ValueError(f"expected url but got {value!r} (missing scheme)")
        if not parsed.netloc and not parsed.path:
            raise ValueError(f"expected url but got {value!r} (missing host/path)")
        return value

    raise ValueError(f"unsupported type {expected_type!r}")
