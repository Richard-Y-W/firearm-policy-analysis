"""
Age-adjusted outcome sensitivity analysis.

Runs the same TWFE specification as the primary models but substitutes
age-adjusted rates (2000 U.S. Standard Population) for crude rates.
Firearm suicide and total suicide are the primary sensitivity targets.
Firearm homicide age-adjusted rates have more missing data (~17% of
state-years suppressed as Unreliable by CDC) and results should be
interpreted cautiously.
"""
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )

OUT_DIR = ROOT / "outputs" / "tables" / "did"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DETAIL_FILE = OUT_DIR / "twfe_did_ageadj_sensitivity_results.csv"
SUMMARY_FILE = OUT_DIR / "twfe_did_ageadj_sensitivity_summary.csv"

# Parallel to OUTCOMES in phase1_utils but using age-adjusted columns
AGEADJ_OUTCOMES = [
    "firearm_suicide_ageadj_rate_per_100k",
    "total_suicide_ageadj_rate_per_100k",
    "total_firearm_ageadj_rate_per_100k",
    "firearm_homicide_ageadj_rate_per_100k",
]

AGEADJ_LABELS = {
    "firearm_suicide_ageadj_rate_per_100k": "Firearm Suicide (Age-Adjusted)",
    "total_suicide_ageadj_rate_per_100k": "Total Suicide (Age-Adjusted)",
    "total_firearm_ageadj_rate_per_100k": "Total Firearm Deaths (Age-Adjusted)",
    "firearm_homicide_ageadj_rate_per_100k": "Firearm Homicide (Age-Adjusted)",
}

# Crude-rate counterparts for side-by-side comparison
CRUDE_COUNTERPARTS = {
    "firearm_suicide_ageadj_rate_per_100k": "firearm_suicide_rate_per_100k",
    "total_suicide_ageadj_rate_per_100k": "total_suicide_rate_per_100k",
    "total_firearm_ageadj_rate_per_100k": "total_firearm_rate_per_100k",
    "firearm_homicide_ageadj_rate_per_100k": "firearm_homicide_rate_per_100k",
}

CONTROL_SPECS = {
    "baseline_controls": BASELINE_CONTROL_COLUMNS,
    "firearm_law_controls": BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS,
}


def model_row(outcome: str, specification: str, controls: list, result, crude_result) -> dict:
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    p = result.pvalues.get("post_permitless", np.nan)
    crude_coef = crude_result.params.get("post_permitless", np.nan) if crude_result else np.nan
    same_sign = (
        not pd.isna(coef)
        and not pd.isna(crude_coef)
        and np.sign(coef) == np.sign(crude_coef)
    )
    return {
        "outcome": outcome,
        "outcome_label": AGEADJ_LABELS[outcome],
        "specification": specification,
        "coef_post_permitless": coef,
        "se_post_permitless": se,
        "p_post_permitless": p,
        "ci_lo": coef - 1.96 * se,
        "ci_hi": coef + 1.96 * se,
        "nobs": result.nobs,
        "r2": result.rsquared,
        "crude_coef": crude_coef,
        "same_direction_as_crude": same_sign,
    }


def run_ageadj_models(panel: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in AGEADJ_OUTCOMES if c not in panel.columns]
    if missing:
        raise ValueError(f"Panel missing age-adjusted columns: {missing}")

    rows = []
    for outcome in AGEADJ_OUTCOMES:
        crude_col = CRUDE_COUNTERPARTS[outcome]
        for specification, controls in CONTROL_SPECS.items():
            result = fit_twfe(panel, outcome, controls=controls)
            crude_result = fit_twfe(panel, crude_col, controls=controls) if crude_col in panel.columns else None
            rows.append(model_row(outcome, specification, controls, result, crude_result))
    return pd.DataFrame(rows)


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in AGEADJ_OUTCOMES:
        sub = detail[detail["outcome"] == outcome]
        base = sub[sub["specification"] == "baseline_controls"].squeeze()
        law = sub[sub["specification"] == "firearm_law_controls"].squeeze()
        rows.append({
            "outcome_label": AGEADJ_LABELS[outcome],
            "baseline_coef": base.get("coef_post_permitless", np.nan),
            "baseline_se": base.get("se_post_permitless", np.nan),
            "baseline_p": base.get("p_post_permitless", np.nan),
            "law_controls_coef": law.get("coef_post_permitless", np.nan),
            "law_controls_se": law.get("se_post_permitless", np.nan),
            "law_controls_p": law.get("p_post_permitless", np.nan),
            "crude_coef": base.get("crude_coef", np.nan),
            "same_direction_as_crude": base.get("same_direction_as_crude", False),
            "nobs": base.get("nobs", np.nan),
        })
    return pd.DataFrame(rows)


def main():
    panel = load_panel()

    if "post_permitless" not in panel.columns:
        panel["post_permitless"] = (
            panel["Year"] >= panel["permitless_year"]
        ).astype(float)
        panel.loc[panel["permitless_year"].isna(), "post_permitless"] = 0.0

    detail = run_ageadj_models(panel)
    summary = build_summary(detail)

    detail.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"Saved: {DETAIL_FILE.name}")
    print(f"Saved: {SUMMARY_FILE.name}")
    print()
    print(summary[[
        "outcome_label", "baseline_coef", "baseline_se", "baseline_p",
        "crude_coef", "same_direction_as_crude"
    ]].to_string(index=False))


if __name__ == "__main__":
    main()
