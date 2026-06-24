from calendar import monthrange
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        POLICY_AUDIT_FILE,
        ROOT,
        fit_fixed_effect_regression,
        fit_twfe,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        POLICY_AUDIT_FILE,
        ROOT,
        fit_fixed_effect_regression,
        fit_twfe,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
DETAIL_FILE = OUT_DIR / "fractional_timing_results.csv"


def compute_effective_year_fraction(effective_date) -> float:
    """Return the fraction of the effective calendar year exposed after a law date."""
    dt = pd.to_datetime(effective_date, errors="coerce")
    if pd.isna(dt):
        return np.nan
    days_in_month = monthrange(int(dt.year), int(dt.month))[1]
    partial_month = (days_in_month - int(dt.day) + 1) / days_in_month
    full_months_after = 12 - int(dt.month)
    fraction = (partial_month + full_months_after) / 12
    return float(min(max(fraction, 0.0), 1.0))


def add_fractional_treatment(panel: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    required_panel = {"State", "Year", "permitless_year"}
    required_audit = {"State", "effective_date", "audit_status"}
    missing_panel = sorted(required_panel - set(panel.columns))
    missing_audit = sorted(required_audit - set(audit.columns))
    if missing_panel:
        raise ValueError(f"Panel missing columns for fractional timing: {missing_panel}")
    if missing_audit:
        raise ValueError(f"Policy audit missing columns for fractional timing: {missing_audit}")

    source_verified = audit.loc[audit["audit_status"].astype(str).eq("source_verified")].copy()
    source_verified["effective_year_fraction"] = source_verified["effective_date"].map(
        compute_effective_year_fraction
    )
    fractions = source_verified.set_index("State")["effective_year_fraction"]

    out = panel.copy()
    out["effective_year_fraction"] = out["State"].map(fractions)
    adoption_year = pd.to_numeric(out["permitless_year"], errors="coerce")
    year = pd.to_numeric(out["Year"], errors="coerce")

    out["fractional_post_permitless"] = 0.0
    out.loc[adoption_year.notna() & (year > adoption_year), "fractional_post_permitless"] = 1.0

    first_year = adoption_year.notna() & year.eq(adoption_year)
    first_year_fraction = out.loc[first_year, "effective_year_fraction"].fillna(1.0)
    out.loc[first_year, "fractional_post_permitless"] = first_year_fraction.astype(float)
    return out


def run_fractional_timing_models(
    panel: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    outcomes=None,
) -> pd.DataFrame:
    outcomes = outcomes or OUTCOMES
    data = add_fractional_treatment(panel, audit)
    rows = []

    for outcome in outcomes:
        baseline = fit_twfe(panel, outcome)
        fractional = fit_fixed_effect_regression(
            data,
            outcome,
            ["fractional_post_permitless"],
            controls=BASELINE_CONTROL_COLUMNS,
        )
        baseline_coef = baseline.params.get("post_permitless", np.nan)
        fractional_coef = fractional.params.get("fractional_post_permitless", np.nan)
        fractional_se = fractional.bse.get("fractional_post_permitless", np.nan)
        fractional_p = fractional.pvalues.get("fractional_post_permitless", np.nan)
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
                "specification": "fractional_year_treatment_timing",
                "coef_fractional_post_permitless": fractional_coef,
                "se_fractional_post_permitless": fractional_se,
                "p_fractional_post_permitless": fractional_p,
                "baseline_binary_coef_post_permitless": baseline_coef,
                "coef_difference_vs_binary": fractional_coef - baseline_coef,
                "nobs": fractional.nobs,
                "r2": fractional.rsquared,
                "interpretation_scope": "timing_sensitivity_fractional_first_year_exposure",
            }
        )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    audit = pd.read_csv(POLICY_AUDIT_FILE)
    detail = run_fractional_timing_models(panel, audit)
    detail.to_csv(DETAIL_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
