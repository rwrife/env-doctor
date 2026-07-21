from __future__ import annotations

import textwrap

from env_doctor.cli import main


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
