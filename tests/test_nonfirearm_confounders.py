import pandas as pd

from src.analysis.nonfirearm_confounder_sensitivity import (
    build_nonfirearm_confounder_summary,
    run_nonfirearm_confounder_models,
)
from src.data.process_nonfirearm_confounders import (
    build_drug_overdose_controls,
    build_sahie_uninsured_controls,
)


def test_build_sahie_uninsured_controls_selects_state_under65_all_groups():
    raw = pd.DataFrame(
        {
            "year": [2023, 2023, 2023],
            "statefips": [1, 1, 11],
            "countyfips": [0, 0, 0],
            "geocat": [40, 40, 40],
            "agecat": [0, 1, 0],
            "racecat": [0, 0, 0],
            "sexcat": [0, 0, 0],
            "iprcat": [0, 0, 0],
            "PCTUI": ["10.2", "12.5", "4.0"],
            "state_name": ["Alabama", "Alabama", "District of Columbia"],
        }
    )

    out = build_sahie_uninsured_controls([raw])

    assert out["State"].tolist() == ["Alabama"]
    assert out["Year"].tolist() == [2023]
    assert out["uninsured_under65_pct"].tolist() == [10.2]


def test_build_drug_overdose_controls_selects_annual_drug_od_rates():
    raw = pd.DataFrame(
        {
            "name": ["Alabama", "Alabama", "District of Columbia", "Alabama"],
            "period": ["2024", "TTM", "2024", "2024"],
            "intent": ["Drug_OD", "Drug_OD", "Drug_OD", "FA_Deaths"],
            "rate": ["35.1", "99.9", "12.0", "23.0"],
            "count_sup": ["100", "200", "10", "20"],
        }
    )

    out = build_drug_overdose_controls(raw)

    assert out["State"].tolist() == ["Alabama"]
    assert out["Year"].tolist() == [2024]
    assert out["drug_overdose_rate_per_100k"].tolist() == [35.1]


def test_run_nonfirearm_confounder_models_reports_expected_specs():
    panel = pd.DataFrame(
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
            "uninsured_under65_pct": [10, 11, 9, 9, 8, 8],
            "drug_overdose_rate_per_100k": [20, 21, 18, 19, 17, 18],
        }
    )

    result = run_nonfirearm_confounder_models(panel)

    assert set(result["specification"]) == {
        "baseline_controls",
        "firearm_law_controls",
        "health_access_controls",
        "overdose_controls",
        "health_access_overdose_controls",
    }


def test_build_nonfirearm_confounder_summary_uses_firearm_law_as_reference():
    results = pd.DataFrame(
        {
            "outcome": ["x", "x", "x"],
            "outcome_label": ["X", "X", "X"],
            "specification": [
                "firearm_law_controls",
                "health_access_controls",
                "overdose_controls",
            ],
            "coef_post_permitless": [1.0, 0.8, 0.3],
            "p_post_permitless": [0.01, 0.04, 0.20],
            "se_post_permitless": [0.1, 0.2, 0.2],
            "nobs": [100, 80, 30],
            "r2": [0.5, 0.6, 0.7],
        }
    )

    summary = build_nonfirearm_confounder_summary(results)

    row = summary.iloc[0]
    assert row["firearm_law_coef"] == 1.0
    assert row["health_access_p05_retained"] == True
    assert row["overdose_p05_retained"] == False
