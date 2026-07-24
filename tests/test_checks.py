from __future__ import annotations

import textwrap

from env_doctor.checks import validate_environment
from env_doctor.schema import loads_schema


def test_validate_environment_reports_all_statuses() -> None:
    schema = loads_schema(
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
                max: 65535
              DEBUG:
                type: bool
                default: false
              CALLBACK_URL:
                type: url
              REQUIRED_TOKEN:
                required: true
                type: string
            """
        )
    )

    report = validate_environment(
        schema,
        {
            "APP_NAME": "env-doctor",
            "PORT": "abc",
            "EXTRA_VAR": "surprise",
        },
    )

    status_by_name = {item.name: item.status for item in report.items}

    assert status_by_name["APP_NAME"] == "ok"
    assert status_by_name["PORT"] == "invalid"
    assert status_by_name["DEBUG"] == "ok"  # default applied
    assert status_by_name["CALLBACK_URL"] == "missing"
    assert status_by_name["REQUIRED_TOKEN"] == "missing"
    assert status_by_name["EXTRA_VAR"] == "unexpected"

    assert report.errors == 2  # PORT invalid + REQUIRED_TOKEN missing
    assert report.warnings == 1  # EXTRA_VAR unexpected


def test_validate_environment_type_and_range_checks() -> None:
    schema = loads_schema(
        textwrap.dedent(
            """
            variables:
              ENABLE_FEATURE:
                required: true
                type: bool
              RATIO:
                required: true
                type: float
                min: 0.0
                max: 1.0
              SERVICE_URL:
                required: true
                type: url
            """
        )
    )

    report = validate_environment(
        schema,
        {
            "ENABLE_FEATURE": "yes",
            "RATIO": "1.5",
            "SERVICE_URL": "not-a-url",
        },
    )

    status_by_name = {item.name: item.status for item in report.items}
    assert status_by_name["ENABLE_FEATURE"] == "ok"
    assert status_by_name["RATIO"] == "invalid"
    assert status_by_name["SERVICE_URL"] == "invalid"
    assert report.errors == 2
