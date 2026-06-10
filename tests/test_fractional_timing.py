import pandas as pd

from src.analysis.fractional_timing import (
    add_fractional_treatment,
    compute_effective_year_fraction,
)


def test_compute_effective_year_fraction_uses_partial_months():
    assert compute_effective_year_fraction("2020-01-01") == 1.0
    assert compute_effective_year_fraction("2020-07-01") == 0.5
    assert round(compute_effective_year_fraction("2020-07-16"), 6) == round(
        (16 / 31 + 5) / 12,
        6,
    )


def test_add_fractional_treatment_only_partial_in_effective_year():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "A", "B", "B", "B"],
            "Year": [2019, 2020, 2021, 2019, 2020, 2021],
            "permitless_year": [2020, 2020, 2020, pd.NA, pd.NA, pd.NA],
            "post_permitless": [0, 1, 1, 0, 0, 0],
        }
    )
    audit = pd.DataFrame(
        {
            "State": ["A", "B"],
            "effective_date": ["2020-07-01", "not_applicable"],
            "audit_status": ["source_verified", "not_adopted_verified"],
        }
    )

    out = add_fractional_treatment(panel, audit)

    assert out.loc[(out["State"].eq("A")) & (out["Year"].eq(2019)), "fractional_post_permitless"].iloc[0] == 0
    assert out.loc[(out["State"].eq("A")) & (out["Year"].eq(2020)), "fractional_post_permitless"].iloc[0] == 0.5
    assert out.loc[(out["State"].eq("A")) & (out["Year"].eq(2021)), "fractional_post_permitless"].iloc[0] == 1
    assert out.loc[out["State"].eq("B"), "fractional_post_permitless"].sum() == 0
