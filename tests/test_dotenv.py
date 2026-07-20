from __future__ import annotations

import textwrap

import pytest

from env_doctor.dotenv import DotenvParseError, load_dotenv, loads_dotenv


def test_loads_basic_assignments_comments_and_blank_lines() -> None:
    data = textwrap.dedent(
        """
        # top-level comment

        FOO=bar
        export BAR=baz
        EMPTY=

        # another comment
        PORT=8080
        """
    )

    parsed = loads_dotenv(data)

    assert parsed == {
        "FOO": "bar",
        "BAR": "baz",
        "EMPTY": "",
        "PORT": "8080",
    }


def test_parses_quoted_values_and_escaped_sequences() -> None:
    data = textwrap.dedent(
        r'''
        DB_URL="postgres://user:pass@localhost:5432/app#fragment"
        GREETING="hello\nworld"
        SINGLE='a value with spaces'
        COMMENTED="value # not a comment" # this is a comment
        '''
    )

    parsed = loads_dotenv(data)

    assert parsed["DB_URL"] == "postgres://user:pass@localhost:5432/app#fragment"
    assert parsed["GREETING"] == "hello\nworld"
    assert parsed["SINGLE"] == "a value with spaces"
    assert parsed["COMMENTED"] == "value # not a comment"


def test_inline_comment_handling_for_unquoted_values() -> None:
    data = textwrap.dedent(
        """
        A=one # trailing comment
        B=two#not-a-comment
        C=three   # trailing comment
        D=  spaced value   # keep inner spaces
        """
    )

    parsed = loads_dotenv(data)

    assert parsed["A"] == "one"
    assert parsed["B"] == "two#not-a-comment"
    assert parsed["C"] == "three"
    assert parsed["D"] == "spaced value"


def test_invalid_line_raises_parse_error() -> None:
    with pytest.raises(DotenvParseError, match="Expected KEY=value assignment"):
        loads_dotenv("NOT_AN_ASSIGNMENT")


def test_invalid_variable_name_raises_parse_error() -> None:
    with pytest.raises(DotenvParseError, match="Invalid variable name"):
        loads_dotenv("1BAD=value")


def test_unterminated_quoted_value_raises_parse_error() -> None:
    with pytest.raises(DotenvParseError, match="Unterminated quoted value"):
        loads_dotenv('KEY="missing-end')


def test_load_dotenv_from_file(tmp_path) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("A=1\nB=\n", encoding="utf-8")

    parsed = load_dotenv(dotenv_path)

    assert parsed == {"A": "1", "B": ""}
