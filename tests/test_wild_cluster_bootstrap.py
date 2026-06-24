import numpy as np
import pandas as pd

from src.analysis.wild_cluster_bootstrap import wild_cluster_bootstrap_twfe


def _panel():
    rows = []
    states = ["A", "B", "C", "D", "E", "F"]
    years = list(range(2018, 2024))
    for state_idx, state in enumerate(states):
        adoption_year = 2020 if state_idx < 3 else None
        for year in years:
            post = int(adoption_year is not None and year >= adoption_year)
            rows.append(
                {
                    "State": state,
                    "Year": year,
                    "post_permitless": post,
                    "unemployment_rate": 4.0 + 0.1 * state_idx,
                    "income_pc": 45000 + 500 * state_idx,
                    "outcome": 1.2 * post + 0.2 * state_idx + 0.05 * (year - 2018),
                }
            )
    return pd.DataFrame(rows)


def test_wild_cluster_bootstrap_twfe_returns_reproducible_cluster_p_value():
    panel = _panel()

    first = wild_cluster_bootstrap_twfe(panel, "outcome", reps=31, seed=123)
    second = wild_cluster_bootstrap_twfe(panel, "outcome", reps=31, seed=123)

    assert np.isfinite(first["coef_post_permitless"])
    assert 0 <= first["wild_cluster_p_post_permitless"] <= 1
    assert first["wild_cluster_p_post_permitless"] == second["wild_cluster_p_post_permitless"]
    assert first["n_bootstrap"] == 31
    assert first["n_clusters"] == 6
