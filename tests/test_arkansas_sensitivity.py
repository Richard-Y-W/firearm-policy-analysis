import pandas as pd

from src.analysis.arkansas_sensitivity import (
    ARKANSAS_SENSITIVITY_YEARS,
    assign_arkansas_treatment_year,
    build_sensitivity_summary,
)


def test_arkansas_sensitivity_years_are_prespecified():
    assert ARKANSAS_SENSITIVITY_YEARS == {
        "arkansas_2021": 2021,
        "arkansas_2023": 2023,
    }


def test_assign_arkansas_treatment_year_changes_only_arkansas():
    panel = pd.DataFrame(
        {
            "State": ["Arkansas", "Arkansas", "Texas", "Texas"],
            "Year": [2020, 2023, 2020, 2023],
            "permitless_year": [pd.NA, pd.NA, 2021, 2021],
            "ever_adopter": [0, 0, 1, 1],
            "post_permitless": [0, 0, 0, 1],
            "years_since_permitless": [pd.NA, pd.NA, -1, 2],
        }
    )

    recoded = assign_arkansas_treatment_year(panel, 2021)

    assert panel.loc[panel["State"] == "Arkansas", "permitless_year"].isna().all()
    assert recoded.loc[recoded["State"] == "Arkansas", "permitless_year"].tolist() == [2021, 2021]
    assert recoded.loc[recoded["State"] == "Arkansas", "ever_adopter"].tolist() == [1, 1]
    assert recoded.loc[recoded["State"] == "Arkansas", "post_permitless"].tolist() == [0, 1]
    assert recoded.loc[recoded["State"] == "Arkansas", "years_since_permitless"].tolist() == [-1, 2]
    assert recoded.loc[recoded["State"] == "Texas", "permitless_year"].tolist() == [2021, 2021]


def test_build_sensitivity_summary_compares_against_primary():
    results = pd.DataFrame(
        {
            "outcome": ["firearm_suicide_rate_per_100k"] * 3,
            "outcome_label": ["Firearm Suicide"] * 3,
            "specification": ["primary_excluded", "arkansas_2021", "arkansas_2023"],
            "coef_post_permitless": [1.0, 1.2, 0.9],
            "p_post_permitless": [0.01, 0.02, 0.03],
        }
    )

    summary = build_sensitivity_summary(results)

    assert summary.loc[0, "primary_coef"] == 1.0
    assert summary.loc[0, "arkansas_2021_coef"] == 1.2
    assert summary.loc[0, "arkansas_2023_coef"] == 0.9
    assert summary.loc[0, "arkansas_2021_delta"] == 0.2
    assert summary.loc[0, "arkansas_2023_delta"] == -0.1
    assert bool(summary.loc[0, "sign_retained"]) is True
