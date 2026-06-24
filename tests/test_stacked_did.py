import numpy as np
import pandas as pd

from src.analysis.modern_did import build_stacked_did_panel, estimate_stacked_did


def test_build_stacked_did_panel_uses_controls_untreated_through_stack_window():
    panel = pd.DataFrame(
        {
            "State": ["A"] * 4 + ["B"] * 4 + ["C"] * 4,
            "Year": [2019, 2020, 2021, 2022] * 3,
            "permitless_year": [2020] * 4 + [2022] * 4 + [pd.NA] * 4,
            "ever_adopter": [1] * 8 + [0] * 4,
            "post_permitless": [0, 1, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0],
            "outcome": np.arange(12, dtype=float),
            "unemployment_rate": [4.0] * 12,
            "income_pc": [50000.0] * 12,
        }
    )

    stacked = build_stacked_did_panel(panel, pre_window=1, post_window=1)
    early = stacked.loc[stacked["stack_cohort"].eq(2020)]

    assert set(early["State"]) == {"A", "B", "C"}
    assert early.loc[early["State"].eq("A"), "stack_treated_state"].max() == 1
    assert early.loc[early["State"].eq("B"), "stack_treated_state"].max() == 0
    assert early["Year"].min() == 2019
    assert early["Year"].max() == 2021


def test_estimate_stacked_did_returns_treatment_row():
    rows = []
    for state, adopt in [("A", 2020), ("B", 2021), ("C", None), ("D", None)]:
        for year in range(2018, 2023):
            post = int(adopt is not None and year >= adopt)
            rows.append(
                {
                    "State": state,
                    "Year": year,
                    "permitless_year": adopt,
                    "ever_adopter": int(adopt is not None),
                    "post_permitless": post,
                    "outcome": 2.0 + 1.5 * post + 0.1 * (year - 2018),
                    "unemployment_rate": 4.0,
                    "income_pc": 50000.0,
                }
            )
    panel = pd.DataFrame(rows)

    result = estimate_stacked_did(panel, "outcome", pre_window=1, post_window=1)

    assert result["outcome"] == "outcome"
    assert np.isfinite(result["coef_stacked_treatment"])
    assert result["n_stacks"] == 2
