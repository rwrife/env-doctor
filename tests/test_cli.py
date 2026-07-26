from __future__ import annotations

import textwrap

from env_doctor.cli import main
from env_doctor.schema import load_schema


def test_cli_check_returns_nonzero_when_errors_exist(tmp_path, capsys) -> None:
    schema_path = tmp_path / "env.schema.yaml"
    schema_path.write_text(
        textwrap.dedent(
            """
            variables:
              APP_NAME:
                required: true
                type: string
              PORT:
                required: true
                type: int
                min: 1
                max: 10
              DEBUG:
                type: bool
                default: false
            """
        ),
        encoding="utf-8",
    )

    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text("APP_NAME=demo\nPORT=999\nEXTRA=1\n", encoding="utf-8")

    exit_code = main(["check", "--schema", str(schema_path), "--env", str(dotenv_path)])

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "PORT" in captured and "invalid" in captured
    assert "EXTRA" in captured and "unexpected" in captured
    assert "DEBUG" in captured and "ok" in captured


def test_cli_check_uses_process_environment_when_env_not_provided(tmp_path, monkeypatch) -> None:
    schema_path = tmp_path / "env.schema.yaml"
    schema_path.write_text(
        textwrap.dedent(
            """
            variables:
              CI:
                required: true
                type: bool
            """
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("CI", "true")

    exit_code = main(["check", "--schema", str(schema_path)])
    assert exit_code == 0


def test_cli_diff_reports_added_removed_changed_and_masks_secrets(tmp_path, capsys) -> None:
    baseline = tmp_path / ".env.example"
    baseline.write_text(
        "A=1\nB=2\nAPI_TOKEN=oldtoken\n",
        encoding="utf-8",
    )
    target = tmp_path / ".env"
    target.write_text(
        "A=1\nC=3\nAPI_TOKEN=newtoken\n",
        encoding="utf-8",
    )

    exit_code = main(["diff", "--a", str(baseline), "--b", str(target)])

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "B" in captured and "removed" in captured
    assert "C" in captured and "added" in captured
    assert "API_TOKEN" in captured and "changed" in captured
    assert "newtoken" not in captured
    assert "oldtoken" not in captured
    assert "***" in captured


def test_cli_diff_returns_zero_when_no_drift(tmp_path, capsys) -> None:
    baseline = tmp_path / "a.env"
    target = tmp_path / "b.env"
    baseline.write_text("A=1\nB=2\n", encoding="utf-8")
    target.write_text("A=1\nB=2\n", encoding="utf-8")

    exit_code = main(["diff", "--a", str(baseline), "--b", str(target)])

    captured = capsys.readouterr().out
    assert exit_code == 0
    assert "no drift detected" in captured


def test_cli_init_infers_types_and_round_trips_into_check(tmp_path, capsys) -> None:
    dotenv_path = tmp_path / ".env"
    dotenv_path.write_text(
        "PORT=8080\nDEBUG=true\nDATABASE_URL=https://example.com/db\nAPP_NAME=demo\n",
        encoding="utf-8",
    )

    exit_code = main(["init", "--from", str(dotenv_path)])
    generated_schema = capsys.readouterr().out

    assert exit_code == 0

    schema_path = tmp_path / "env.schema.yaml"
    schema_path.write_text(generated_schema, encoding="utf-8")

    parsed_schema = load_schema(schema_path)
    assert parsed_schema.variables["PORT"].type == "int"
    assert parsed_schema.variables["DEBUG"].type == "bool"
    assert parsed_schema.variables["DATABASE_URL"].type == "url"
    assert parsed_schema.variables["APP_NAME"].type == "string"
    assert all(spec.required for spec in parsed_schema.variables.values())

    check_exit_code = main(["check", "--schema", str(schema_path), "--env", str(dotenv_path)])
    assert check_exit_code == 0
