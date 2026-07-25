"""Diffing helpers for environment variable mappings."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping


_SECRET_HINTS = (
    "SECRET",
    "TOKEN",
    "PASSWORD",
    "PASS",
    "PWD",
    "PRIVATE",
    "API_KEY",
    "ACCESS_KEY",
    "AUTH",
    "CREDENTIAL",
)


@dataclass(frozen=True)
class DiffEntry:
    """Represents one key-level difference between two env mappings."""

    kind: str
    key: str
    a_value: str | None
    b_value: str | None


@dataclass(frozen=True)
class DiffReport:
    """Collection of drift entries."""

    entries: tuple[DiffEntry, ...]

    @property
    def added(self) -> int:
        return sum(1 for entry in self.entries if entry.kind == "added")

    @property
    def removed(self) -> int:
        return sum(1 for entry in self.entries if entry.kind == "removed")

    @property
    def changed(self) -> int:
        return sum(1 for entry in self.entries if entry.kind == "changed")

    @property
    def has_drift(self) -> bool:
        return bool(self.entries)


def diff_environments(a_env: Mapping[str, str], b_env: Mapping[str, str]) -> DiffReport:
    """Compare two environment mappings and return added/removed/changed entries."""
    entries: list[DiffEntry] = []

    a_keys = set(a_env)
    b_keys = set(b_env)

    for key in sorted(a_keys - b_keys):
        entries.append(DiffEntry(kind="removed", key=key, a_value=a_env[key], b_value=None))

    for key in sorted(b_keys - a_keys):
        entries.append(DiffEntry(kind="added", key=key, a_value=None, b_value=b_env[key]))

    for key in sorted(a_keys & b_keys):
        if a_env[key] != b_env[key]:
            entries.append(DiffEntry(kind="changed", key=key, a_value=a_env[key], b_value=b_env[key]))

    return DiffReport(entries=tuple(entries))


def format_value(key: str, value: str | None) -> str:
    """Format a value for display, masking likely secrets."""
    if value is None:
        return "<missing>"
    if value == "":
        return "<empty>"
    if _looks_sensitive(key):
        return "***"
    return value


def _looks_sensitive(key: str) -> bool:
    upper = key.upper()
    return any(hint in upper for hint in _SECRET_HINTS)
