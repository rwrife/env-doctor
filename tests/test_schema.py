from __future__ import annotations

import textwrap

import pytest

from env_doctor.schema import SchemaError, load_schema, loads_schema


def test_loads_valid_schema() -> None:
    schema_text = textwrap.dedent(
        """
        variables:
          DATABASE_URL:
            required: true
            type: url
            secret: true
          PORT:
            required: true
            type: int
            min: 1
            max: 65535
          DEBUG:
            type: bool
            default: false
        """
    )

    schema = loads_schema(schema_text)

    assert set(schema.variables.keys()) == {"DATABASE_URL", "PORT", "DEBUG"}

    db = schema.variables["DATABASE_URL"]
    assert db.required is True
    assert db.type == "url"
    assert db.secret is True
    assert db.has_default is False

    port = schema.variables["PORT"]
    assert port.type == "int"
    assert port.min == 1
    assert port.max == 65535

    debug = schema.variables["DEBUG"]
    assert debug.type == "bool"
    assert debug.has_default is True
    assert debug.default is False


def test_load_schema_from_file(tmp_path) -> None:
    path = tmp_path / "env.schema.yaml"
    path.write_text(
        textwrap.dedent(
            """
            variables:
              API_KEY:
                required: true
                type: string
                secret: true
            """
        ),
        encoding="utf-8",
    )

    schema = load_schema(path)
    assert "API_KEY" in schema.variables


def test_invalid_yaml_raises_schema_error() -> None:
    bad_yaml = "variables: [not: valid"

    with pytest.raises(SchemaError, match="Malformed YAML"):
        loads_schema(bad_yaml)


def test_invalid_type_raises_clear_error() -> None:
    schema_text = textwrap.dedent(
        """
        variables:
          PORT:
            type: integer
        """
    )

    with pytest.raises(SchemaError, match="invalid type 'integer'"):
        loads_schema(schema_text)


def test_invalid_min_type_raises_clear_error() -> None:
    schema_text = textwrap.dedent(
        """
        variables:
          PORT:
            type: int
            min: low
        """
    )

    with pytest.raises(SchemaError, match="field 'min' must be a number"):
        loads_schema(schema_text)


def test_non_mapping_variables_field_raises() -> None:
    schema_text = textwrap.dedent(
        """
        variables:
          - PORT
        """
    )

    with pytest.raises(SchemaError, match="field 'variables' must be a mapping"):
        loads_schema(schema_text)
