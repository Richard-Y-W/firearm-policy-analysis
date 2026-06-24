import numpy as np
import pandas as pd

from src.analysis.additional_mortality_checks import (
    build_sex_age_suppression_audit,
    build_sex_age_suppression_latex,
    collapse_firearm_suicide_sex_age,
    run_negative_control_models,
    run_sex_age_models,
)


def _panel():
    rows = []
    for state_idx, state in enumerate(["A", "B", "C", "D"]):
        adopt = 2020 if state in {"A", "B"} else np.nan
        for year in [2019, 2020, 2021]:
            rows.append(
                {
                    "State": state,
                    "Year": year,
                    "post_permitless": int(pd.notna(adopt) and year >= adopt),
                    "unemployment_rate": 4.0 + state_idx,
                    "income_pc": 50000 + 1000 * state_idx + year,
                }
            )
    return pd.DataFrame(rows)


def test_run_negative_control_models_returns_one_row_per_outcome():
    panel = _panel()
    controls = panel[["State", "Year"]].copy()
    controls["cancer_rate_per_100k"] = np.linspace(100, 120, len(controls))
    controls["cardiovascular_rate_per_100k"] = np.linspace(200, 220, len(controls))

    out = run_negative_control_models(
        panel,
        controls,
        outcomes={
            "cancer_rate_per_100k": "Cancer",
            "cardiovascular_rate_per_100k": "Cardiovascular",
        },
    )

    assert out["outcome"].tolist() == [
        "cancer_rate_per_100k",
        "cardiovascular_rate_per_100k",
    ]
    assert out["nobs"].min() == len(panel)


def test_collapse_firearm_suicide_sex_age_builds_broad_adult_groups():
    raw = pd.DataFrame(
        {
            "State": ["A", "A", "A", "A"],
            "State Code": [1, 1, 1, 1],
            "Year": [2020, 2020, 2020, 2020],
            "Sex": ["Male", "Male", "Male", "Female"],
            "Ten-Year Age Groups": [
                "25-34 years",
                "35-44 years",
                "45-54 years",
                "25-34 years",
            ],
            "Deaths": [10, 15, 20, 5],
            "Population": [100000, 110000, 120000, 130000],
        }
    )

    out = collapse_firearm_suicide_sex_age(raw)
    male_25_44 = out[
        out["Sex"].eq("Male") & out["broad_age_group"].eq("25-44")
    ].iloc[0]

    assert male_25_44["Deaths"] == 25
    assert male_25_44["Population"] == 210000
    assert np.isclose(male_25_44["rate_per_100k"], 25 / 210000 * 100000)
    assert male_25_44["component_age_groups_observed"] == 2
    assert male_25_44["complete_broad_age_group"]


def test_run_sex_age_models_includes_sex_age_and_collapsed_strata():
    panel = _panel()
    rows = []
    for _, row in panel.iterrows():
        for sex in ["Male", "Female"]:
            for age in ["25-44", "45-64"]:
                rows.append(
                    {
                        "State": row["State"],
                        "Year": row["Year"],
                        "Sex": sex,
                        "broad_age_group": age,
                        "Deaths": 10 + row["post_permitless"],
                        "Population": 100000,
                        "rate_per_100k": 10 + row["post_permitless"],
                        "complete_broad_age_group": True,
                    }
                )
    strata = pd.DataFrame(rows)

    out = run_sex_age_models(panel, strata)

    assert {"sex", "age", "sex_age"}.issubset(set(out["stratification"]))
    assert set(out["sex"].dropna()) == {"Male", "Female"}
    assert {"25-44", "45-64"}.issubset(set(out["broad_age_group"].dropna()))


def test_build_sex_age_suppression_audit_counts_complete_clean_cells():
    panel = _panel()
    strata = []
    for _, row in panel.iterrows():
        strata.append(
            {
                "State": row["State"],
                "Year": row["Year"],
                "Sex": "Male",
                "broad_age_group": "25-44",
                "component_age_groups_observed": 2,
                "expected_component_age_groups": 2,
                "complete_broad_age_group": True,
            }
        )
    strata.append(
        {
            "State": "A",
            "Year": 2019,
            "Sex": "Female",
            "broad_age_group": "65+",
            "component_age_groups_observed": 2,
            "expected_component_age_groups": 3,
            "complete_broad_age_group": False,
        }
    )
    strata.append(
        {
            "State": "A",
            "Year": 2020,
            "Sex": "Female",
            "broad_age_group": "65+",
            "component_age_groups_observed": 3,
            "expected_component_age_groups": 3,
            "complete_broad_age_group": True,
        }
    )

    audit = build_sex_age_suppression_audit(panel, pd.DataFrame(strata))
    male = audit[
        audit["sex"].eq("Male") & audit["broad_age_group"].eq("25-44")
    ].iloc[0]
    female_older = audit[
        audit["sex"].eq("Female") & audit["broad_age_group"].eq("65+")
    ].iloc[0]

    assert male["expected_clean_state_years"] == len(panel)
    assert male["observed_state_years"] == len(panel)
    assert male["modeled_clean_state_years"] == len(panel)
    assert male["modeled_share_of_clean_expected"] == 1.0
    assert female_older["observed_state_years"] == 2
    assert female_older["complete_state_years"] == 1
    assert female_older["modeled_clean_state_years"] == 1
    assert np.isclose(female_older["modeled_share_of_clean_expected"], 1 / len(panel))


def test_build_sex_age_suppression_latex_labels_availability_table():
    audit = pd.DataFrame(
        {
            "sex": ["Female"],
            "broad_age_group": ["65+"],
            "modeled_clean_state_years": [151],
            "expected_clean_state_years": [1222],
            "modeled_share_of_clean_expected": [151 / 1222],
            "complete_state_years": [187],
        }
    )

    latex = build_sex_age_suppression_latex(audit)

    assert "\\label{tab:sex_age_suppression}" in latex
    assert "Female, age 65+" in latex
    assert "12.4\\%" in latex
