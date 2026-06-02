import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from src.analysis.phase1_utils import fit_fixed_effect_regression, fit_twfe


def _synthetic_panel():
    rows = []
    states = ["A", "B", "C", "D", "E", "F"]
    years = list(range(2018, 2024))
    for state_idx, state in enumerate(states):
        adoption_year = 2020 + (state_idx % 2) if state_idx < 4 else None
        for year in years:
            post = int(adoption_year is not None and year >= adoption_year)
            unemployment = 4.0 + 0.2 * state_idx + 0.05 * (year - 2018)
            income = 42000 + 850 * state_idx + 175 * (year - 2018)
            outcome = (
                2.5
                + 1.75 * post
                + 0.15 * unemployment
                + 0.00002 * income
                + 0.35 * state_idx
                + 0.18 * (year - 2018)
            )
            rows.append(
                {
                    "State": state,
                    "Year": year,
                    "post_permitless": post,
                    "unemployment_rate": unemployment,
                    "income_pc": income,
                    "outcome": outcome,
                    "population": 1_000_000 + 10_000 * state_idx,
                }
            )
    return pd.DataFrame(rows)


def test_fit_twfe_coefficients_match_statsmodels_ols_fixed_effects():
    data = _synthetic_panel()

    custom = fit_twfe(data, "outcome")
    statsmodels_result = smf.ols(
        "outcome ~ post_permitless + unemployment_rate + income_pc + C(State) + C(Year)",
        data=data,
    ).fit(cov_type="cluster", cov_kwds={"groups": data["State"]})

    for term in ["post_permitless", "unemployment_rate", "income_pc"]:
        assert np.isclose(custom.params[term], statsmodels_result.params[term])

    assert custom.nobs == statsmodels_result.nobs


def test_weighted_fixed_effect_regression_returns_finite_treatment_estimate():
    data = _synthetic_panel()

    result = fit_fixed_effect_regression(
        data,
        "outcome",
        ["post_permitless"],
        weights="population",
    )

    assert np.isfinite(result.params["post_permitless"])
    assert np.isfinite(result.bse["post_permitless"])
