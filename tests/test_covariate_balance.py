import pandas as pd

from src.analysis.covariate_balance import (
    add_covariate_balance_weights,
    compute_balancing_weights,
)


def test_compute_balancing_weights_prioritizes_controls_closer_to_adopters():
    state_covariates = pd.DataFrame(
        {
            "State": ["T1", "T2", "C1", "C2", "C3"],
            "ever_adopter": [1, 1, 0, 0, 0],
            "baseline_firearm_suicide_rate": [10.0, 12.0, 2.0, 11.0, 20.0],
            "gun_ownership_baseline": [0.50, 0.52, 0.20, 0.51, 0.80],
        }
    )

    weights = compute_balancing_weights(
        state_covariates,
        ["baseline_firearm_suicide_rate", "gun_ownership_baseline"],
    )

    control = weights.loc[weights["ever_adopter"].eq(0)]
    assert round(control["covariate_balance_weight"].sum(), 6) == 2.0
    c2 = control.loc[control["State"].eq("C2"), "covariate_balance_weight"].iloc[0]
    c1 = control.loc[control["State"].eq("C1"), "covariate_balance_weight"].iloc[0]
    assert c2 > c1


def test_add_covariate_balance_weights_merges_state_weights_to_panel():
    panel = pd.DataFrame(
        {
            "State": ["T1", "T1", "C1", "C1"],
            "Year": [2019, 2020, 2019, 2020],
        }
    )
    weights = pd.DataFrame(
        {
            "State": ["T1", "C1"],
            "covariate_balance_weight": [1.0, 2.0],
        }
    )

    out = add_covariate_balance_weights(panel, weights)

    assert out.loc[out["State"].eq("T1"), "covariate_balance_weight"].tolist() == [1.0, 1.0]
    assert out.loc[out["State"].eq("C1"), "covariate_balance_weight"].tolist() == [2.0, 2.0]
