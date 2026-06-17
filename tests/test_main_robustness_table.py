import pandas as pd

from src.analysis.main_robustness_table import (
    build_firearm_suicide_robustness_rows,
    format_p_value,
)


def test_format_p_value_uses_threshold_for_small_values():
    assert format_p_value(0.0004) == "$<0.001$"
    assert format_p_value(0.01234) == "0.012"


def test_build_firearm_suicide_robustness_rows_combines_four_estimators():
    twfe = pd.DataFrame(
        {
            "outcome": ["firearm_suicide_rate_per_100k"],
            "coef_post_permitless": [1.39],
            "se_post_permitless": [0.22],
            "p_post_permitless": [0.0001],
            "nobs": [1222],
        }
    )
    fractional = pd.DataFrame(
        {
            "outcome": ["firearm_suicide_rate_per_100k"],
            "coef_fractional_post_permitless": [1.53],
            "se_fractional_post_permitless": [0.24],
            "p_fractional_post_permitless": [0.0001],
            "nobs": [1222],
        }
    )
    stacked = pd.DataFrame(
        {
            "outcome": ["firearm_suicide_rate_per_100k"],
            "coef_stacked_treatment": [0.67],
            "se_stacked_treatment": [0.14],
            "p_stacked_treatment": [0.0001],
            "nobs": [3446],
        }
    )
    balanced = pd.DataFrame(
        {
            "outcome": ["firearm_suicide_rate_per_100k"],
            "coef_post_permitless": [0.89],
            "se_post_permitless": [0.30],
            "p_post_permitless": [0.003],
            "nobs": [1222],
        }
    )
    firearm_specific = pd.DataFrame(
        {
            "outcome": ["firearm_minus_nonfirearm_suicide_rate_per_100k"],
            "coef_post_permitless": [0.98],
            "se_post_permitless": [0.24],
            "p_post_permitless": [0.0001],
            "nobs": [1222],
        }
    )

    rows = build_firearm_suicide_robustness_rows(
        twfe,
        fractional,
        stacked,
        balanced,
        firearm_specific,
    )

    assert rows["specification"].tolist() == [
        "Binary TWFE",
        "Fractional-year TWFE",
        "Stacked DiD",
        "Covariate-balanced TWFE",
        "Firearm minus non-firearm suicide TWFE",
    ]
    assert rows["estimate"].tolist() == [1.39, 1.53, 0.67, 0.89, 0.98]
