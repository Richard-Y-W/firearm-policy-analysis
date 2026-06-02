import numpy as np
import pandas as pd

from src.analysis.wrhc_change_score import build_change_scores, compute_change_score, welch_ttest


def test_compute_change_score_uses_pre_years_and_post_years_excluding_adoption_year():
    panel = pd.DataFrame(
        {
            "State": ["A"] * 5,
            "Year": [2018, 2019, 2020, 2021, 2022],
            "rate_per_100k": [1.0, 3.0, 100.0, 5.0, 9.0],
        }
    )

    assert compute_change_score(panel, "A", 2020, pre_k=2, post_k=2) == 5.0


def test_build_change_scores_uses_never_adopter_pseudo_windows():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B"],
            "Year": [2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, np.nan, np.nan],
            "rate_per_100k": [1.0, 4.0, 2.0, 3.0],
        }
    )

    adopters, controls = build_change_scores(panel, pre_k=1, post_k=0, latest_treatment_year=2020)

    assert adopters.empty
    assert controls.empty


def test_welch_ttest_returns_expected_difference():
    result = welch_ttest([2.0, 4.0, 6.0], [1.0, 2.0, 3.0])

    assert result["diff"] == 2.0
    assert result["n_adopters"] == 3
    assert result["n_controls"] == 3
