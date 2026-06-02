import pandas as pd

from src.analysis.firearm_law_control_sensitivity import (
    build_firearm_law_control_summary,
    run_firearm_law_control_models,
)
from src.data.process_firearm_law_controls import (
    FIREARM_LAW_CONTROL_COLUMNS,
    build_firearm_law_controls,
)


def test_build_firearm_law_controls_combines_tufts_policy_pairs():
    raw = pd.DataFrame(
        {
            "state": ["A", "A"],
            "year": [1999, 2000],
            "permit": [0, 1],
            "permith": [1, 0],
            "waiting": [0, 0],
            "waitingh": [1, 0],
            "universal": [0, 0],
            "universalh": [0, 1],
            "universalpermit": [0, 0],
            "universalpermith": [1, 0],
            "gvro": [0, 0],
            "gvrolawenforcement": [0, 1],
            "locked": [1, 0],
            "nosyg": [1, 0],
            "dealer": [0, 0],
            "dealerh": [0, 1],
        }
    )

    controls = build_firearm_law_controls(raw, start_year=1999, end_year=2000)

    assert list(controls.columns) == ["State", "Year"] + FIREARM_LAW_CONTROL_COLUMNS
    first = controls.loc[controls["Year"] == 1999].iloc[0]
    second = controls.loc[controls["Year"] == 2000].iloc[0]
    assert first["permit_to_purchase"] == 1
    assert first["waiting_period"] == 1
    assert first["universal_background_check"] == 1
    assert first["stand_your_ground"] == 0
    assert second["erpo_red_flag"] == 1
    assert second["dealer_license"] == 1
    assert second["stand_your_ground"] == 1


def test_run_firearm_law_control_models_reports_baseline_and_controlled_specs():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2000, 2001, 2000, 2001, 2000, 2001],
            "post_permitless": [0, 1, 0, 0, 0, 0],
            "unemployment_rate": [4, 4, 5, 5, 6, 6],
            "income_pc": [10, 11, 12, 13, 14, 15],
            "firearm_suicide_rate_per_100k": [1, 3, 1, 2, 2, 2],
            "nonfirearm_suicide_rate_per_100k": [1, 2, 1, 1, 1, 1],
            "total_suicide_rate_per_100k": [2, 5, 2, 3, 3, 3],
            "firearm_homicide_rate_per_100k": [1, 1, 1, 1, 1, 1],
            "total_firearm_rate_per_100k": [2, 4, 2, 3, 3, 3],
            "permit_to_purchase": [0, 1, 0, 0, 1, 1],
            "waiting_period": [0, 0, 0, 0, 1, 1],
            "universal_background_check": [0, 1, 0, 0, 1, 1],
            "erpo_red_flag": [0, 0, 0, 0, 1, 1],
            "safe_storage": [0, 0, 0, 0, 1, 1],
            "stand_your_ground": [1, 1, 0, 0, 0, 0],
            "dealer_license": [0, 0, 0, 0, 1, 1],
        }
    )

    result = run_firearm_law_control_models(panel)

    assert set(result["specification"]) == {"baseline_controls", "firearm_law_controls"}
    assert set(result["outcome_label"]) == {
        "Firearm Suicide",
        "Non-Firearm Suicide",
        "Total Suicide",
        "Firearm Homicide",
        "Total Firearm Deaths",
    }


def test_build_firearm_law_control_summary_marks_retained_significance():
    results = pd.DataFrame(
        {
            "outcome": ["x", "x", "y", "y"],
            "outcome_label": ["X", "X", "Y", "Y"],
            "specification": [
                "baseline_controls",
                "firearm_law_controls",
                "baseline_controls",
                "firearm_law_controls",
            ],
            "coef_post_permitless": [1.0, 0.8, 1.0, -0.1],
            "p_post_permitless": [0.01, 0.04, 0.01, 0.70],
            "se_post_permitless": [0.1, 0.2, 0.1, 0.2],
            "nobs": [100, 100, 100, 100],
            "r2": [0.5, 0.6, 0.5, 0.6],
        }
    )

    summary = build_firearm_law_control_summary(results)

    retained = summary.loc[summary["outcome"] == "x"].iloc[0]
    attenuated = summary.loc[summary["outcome"] == "y"].iloc[0]
    assert retained["sign_retained"] == True
    assert retained["p05_retained"] == True
    assert retained["interpretation_flag"] == "survives_firearm_law_controls"
    assert attenuated["sign_retained"] == False
    assert attenuated["p05_retained"] == False
