import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.phase3b2_confounder_sensitivity import (
    build_phase3b2_confounder_summary,
    run_phase3b2_confounder_models,
)


def _panel():
    return pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2022, 2023, 2022, 2023, 2022, 2023],
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
            "share_age_18_34": [0.25, 0.26, 0.24, 0.24, 0.23, 0.23],
            "share_age_35_64": [0.50, 0.49, 0.51, 0.51, 0.52, 0.52],
            "share_age_65plus": [0.18, 0.19, 0.17, 0.18, 0.20, 0.21],
            "share_black_nonhispanic": [0.20, 0.20, 0.10, 0.10, 0.05, 0.05],
            "share_hispanic": [0.10, 0.10, 0.09, 0.09, 0.08, 0.08],
            "poverty_rate": [14, 13, 12, 12, 10, 10],
            "mental_health_provider_rate_per_100k": [60, 61, 55, 56, 70, 71],
        }
    )


def test_run_phase3b2_confounder_models_reports_expected_specs():
    result = run_phase3b2_confounder_models(_panel())

    assert set(result["specification"]) == {
        "baseline_controls",
        "firearm_law_controls",
        "demographic_poverty_controls",
        "mental_health_access_controls",
        "full_phase3b2_controls",
    }


def test_build_phase3b2_confounder_summary_uses_firearm_law_as_reference():
    results = pd.DataFrame(
        {
            "outcome": ["x", "x", "x"],
            "outcome_label": ["X", "X", "X"],
            "specification": [
                "firearm_law_controls",
                "demographic_poverty_controls",
                "full_phase3b2_controls",
            ],
            "coef_post_permitless": [1.0, 0.8, 0.3],
            "p_post_permitless": [0.01, 0.04, 0.20],
            "se_post_permitless": [0.1, 0.2, 0.2],
            "nobs": [100, 80, 30],
            "r2": [0.5, 0.6, 0.7],
        }
    )

    summary = build_phase3b2_confounder_summary(results)

    row = summary.iloc[0]
    assert row["firearm_law_coef"] == 1.0
    assert row["demographic_poverty_p05_retained"] == True
    assert row["full_phase3b2_p05_retained"] == False
