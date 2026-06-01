import pandas as pd
import pytest

from src.analysis.phase1_utils import (
    POLICY_AUDIT_COLUMNS,
    add_event_time_columns,
    build_cohort_att_table,
    build_robustness_sample,
    validate_policy_audit_verified_rows,
    validate_policy_audit_schema,
    validate_policy_year_consistency,
)


def test_validate_policy_audit_schema_rejects_missing_columns():
    table = pd.DataFrame({"State": ["A"], "permitless_year_current": [2020]})

    with pytest.raises(ValueError, match="missing required columns"):
        validate_policy_audit_schema(table)


def test_validate_policy_audit_schema_accepts_required_columns():
    table = pd.DataFrame([{col: "" for col in POLICY_AUDIT_COLUMNS}])
    table.loc[0, "State"] = "A"
    table.loc[0, "permitless_year_current"] = 2020
    table.loc[0, "audit_status"] = "needs_source"

    validated = validate_policy_audit_schema(table)

    assert list(validated.columns) == POLICY_AUDIT_COLUMNS


def test_validate_policy_audit_verified_rows_requires_legal_source_fields():
    table = pd.DataFrame([{col: "" for col in POLICY_AUDIT_COLUMNS}])
    table.loc[0, "State"] = "A"
    table.loc[0, "permitless_year_current"] = 2020
    table.loc[0, "audit_status"] = "source_verified"

    with pytest.raises(ValueError, match="source_verified rows missing required legal audit fields"):
        validate_policy_audit_verified_rows(table)


def test_validate_policy_audit_verified_rows_requires_non_adopter_source_fields():
    table = pd.DataFrame([{col: "" for col in POLICY_AUDIT_COLUMNS}])
    table.loc[0, "State"] = "A"
    table.loc[0, "audit_status"] = "not_adopted_verified"

    with pytest.raises(ValueError, match="not_adopted_verified rows missing required legal audit fields"):
        validate_policy_audit_verified_rows(table)


def test_build_robustness_sample_excludes_covid_years():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "A", "A"],
            "Year": [2019, 2020, 2021, 2022],
            "y": [1, 2, 3, 4],
        }
    )

    filtered = build_robustness_sample(panel, "exclude_covid")

    assert filtered["Year"].tolist() == [2019, 2022]


def test_build_robustness_sample_excludes_post_2019():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "A"],
            "Year": [2018, 2019, 2020],
            "y": [1, 2, 3],
        }
    )

    filtered = build_robustness_sample(panel, "pre_covid_only")

    assert filtered["Year"].tolist() == [2018, 2019]


def test_add_event_time_columns_marks_never_treated_as_missing():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B"],
            "Year": [2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, pd.NA, pd.NA],
        }
    )

    out = add_event_time_columns(panel)

    assert out.loc[out["State"] == "A", "event_time"].tolist() == [-1, 0]
    assert out.loc[out["State"] == "B", "event_time"].isna().all()


def test_validate_policy_year_consistency_counts_mismatches():
    panel_states = pd.DataFrame(
        {
            "State": ["A", "B"],
            "permitless_year": [2020.0, pd.NA],
        }
    )
    audit = pd.DataFrame(
        {
            "State": ["A", "B"],
            "permitless_year_current": [2021.0, pd.NA],
        }
    )

    summary = validate_policy_year_consistency(panel_states, audit)

    assert summary["year_mismatch"].sum() == 1


def test_build_cohort_att_table_returns_cohort_window_rows():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2019, 2020, 2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, pd.NA, pd.NA, pd.NA, pd.NA],
            "ever_adopter": [1, 1, 0, 0, 0, 0],
            "outcome": [2.0, 5.0, 1.0, 2.0, 1.0, 3.0],
        }
    )

    out = build_cohort_att_table(panel, "outcome", windows=(1,))

    assert out.loc[0, "cohort"] == 2020
    assert out.loc[0, "window"] == 1
    assert out.loc[0, "att"] == 1.5
