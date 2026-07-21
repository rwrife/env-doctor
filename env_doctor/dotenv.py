"""Small dependency-free parser for .env files."""

from __future__ import annotations

from pathlib import Path


class DotenvParseError(ValueError):
    """Raised when a .env file contains malformed syntax."""


def load_dotenv(path: str | Path) -> dict[str, str]:
    """Load and parse a .env file from disk."""
    dotenv_path = Path(path)
    try:
        content = dotenv_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DotenvParseError(f"Failed to read dotenv file '{dotenv_path}': {exc}") from exc
    return loads_dotenv(content, source=str(dotenv_path))


def loads_dotenv(content: str, source: str = "<string>") -> dict[str, str]:
    """Parse dotenv text into a mapping of key/value pairs."""
    result: dict[str, str] = {}

    for line_number, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        candidate = line.lstrip()
        if candidate.startswith("export "):
            candidate = candidate[len("export ") :].lstrip()

        key, value = _parse_assignment(candidate, source=source, line_number=line_number)
        result[key] = value

    return result


def _parse_assignment(candidate: str, source: str, line_number: int) -> tuple[str, str]:
    if "=" not in candidate:
        raise DotenvParseError(_error(source, line_number, "Expected KEY=value assignment."))

    key_part, value_part = candidate.split("=", 1)
    key = key_part.strip()

    if not key:
        raise DotenvParseError(_error(source, line_number, "Missing variable name before '='."))
    if not _is_valid_key(key):
        raise DotenvParseError(
            _error(
                source,
                line_number,
                (
                    f"Invalid variable name '{key}'. "
                    "Use letters, digits, and underscores; first character cannot be a digit."
                ),
            )
        )

    value = _parse_value(value_part, source=source, line_number=line_number)
    return key, value


def _parse_value(value_part: str, source: str, line_number: int) -> str:
    remainder = value_part.lstrip()
    if remainder == "":
        return ""

    if remainder[0] in {'"', "'"}:
        return _parse_quoted_value(remainder, source=source, line_number=line_number)

    return _parse_unquoted_value(remainder)


def _parse_quoted_value(remainder: str, source: str, line_number: int) -> str:
    quote = remainder[0]
    idx = 1
    escaped = False
    buffer: list[str] = []

    while idx < len(remainder):
        char = remainder[idx]

        if quote == '"':
            if escaped:
                buffer.append(_decode_escape(char))
                escaped = False
                idx += 1
                continue
            if char == "\\":
                escaped = True
                idx += 1
                continue
            if char == '"':
                value = "".join(buffer)
                trailer = remainder[idx + 1 :].strip()
                if trailer and not trailer.startswith("#"):
                    raise DotenvParseError(
                        _error(
                            source,
                            line_number,
                            "Unexpected characters after quoted value.",
                        )
                    )
                return value

            buffer.append(char)
            idx += 1
            continue

        # Single-quoted: no escape processing.
        if char == "'":
            value = "".join(buffer)
            trailer = remainder[idx + 1 :].strip()
            if trailer and not trailer.startswith("#"):
                raise DotenvParseError(
                    _error(source, line_number, "Unexpected characters after quoted value.")
                )
            return value
        buffer.append(char)
        idx += 1

    raise DotenvParseError(_error(source, line_number, "Unterminated quoted value."))


def _parse_unquoted_value(remainder: str) -> str:
    comment_index: int | None = None
    for idx, char in enumerate(remainder):
        if char == "#" and (idx == 0 or remainder[idx - 1].isspace()):
            comment_index = idx
            break

    if comment_index is None:
        return remainder.strip()
    return remainder[:comment_index].rstrip()


def _decode_escape(char: str) -> str:
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        '"': '"',
        "\\": "\\",
    }
    return escapes.get(char, char)


def _is_valid_key(key: str) -> bool:
    if key[0].isdigit():
        return False
    return all(ch.isalnum() or ch == "_" for ch in key)


def _error(source: str, line_number: int, message: str) -> str:
    return f"{source}:{line_number}: {message}"
