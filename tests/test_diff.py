from __future__ import annotations

from env_doctor.diffing import diff_environments, format_value


def test_diff_environments_reports_added_removed_and_changed() -> None:
    baseline = {
        "UNCHANGED": "same",
        "REMOVED_ONLY": "gone",
        "CHANGED": "before",
    }
    target = {
        "UNCHANGED": "same",
        "ADDED_ONLY": "new",
        "CHANGED": "after",
    }

    report = diff_environments(baseline, target)

    assert report.added == 1
    assert report.removed == 1
    assert report.changed == 1
    assert report.has_drift is True

    by_kind = {(entry.kind, entry.key): entry for entry in report.entries}
    assert by_kind[("added", "ADDED_ONLY")].b_value == "new"
    assert by_kind[("removed", "REMOVED_ONLY")].a_value == "gone"
    assert by_kind[("changed", "CHANGED")].a_value == "before"
    assert by_kind[("changed", "CHANGED")].b_value == "after"


def test_format_value_masks_secret_like_keys() -> None:
    assert format_value("DATABASE_PASSWORD", "super-secret") == "***"
    assert format_value("API_TOKEN", "abc123") == "***"
    assert format_value("APP_NAME", "env-doctor") == "env-doctor"
    assert format_value("EMPTY", "") == "<empty>"
    assert format_value("MISSING", None) == "<missing>"
