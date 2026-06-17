from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        build_robustness_sample,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        build_robustness_sample,
        fit_fixed_effect_regression,
        load_panel,
    )


NICS_FILE = ROOT / "data" / "processed" / "state_year_nics_handgun_checks_1999_2021.csv"
OUT_DIR = ROOT / "outputs" / "tables" / "mechanism"
DETAIL_FILE = OUT_DIR / "nics_handgun_proxy_results.csv"

NICS_OUTCOMES = {
    "handgun_checks_per_100k": "NICS Handgun Checks per 100k",
    "permit_checks_per_100k": "NICS Permit Checks per 100k",
    "permit_recheck_checks_per_100k": "NICS Permit Rechecks per 100k",
    "permit_and_recheck_checks_per_100k": "NICS Permit plus Recheck Checks per 100k",
    "handgun_or_permit_checks_per_100k": "NICS Handgun or Permit Checks per 100k",
}

NICS_SAMPLES = {
    "full_1999_2021": "Full parsed NICS panel, 1999-2021",
    "exclude_2020_2021": "Excludes 2020-2021 to reduce COVID-period background-check distortions",
}


def add_missing_nics_rates(nics: pd.DataFrame) -> pd.DataFrame:
    out = nics.copy()
    if "population" not in out.columns:
        return out
    for count_col, rate_col in [
        ("permit_checks", "permit_checks_per_100k"),
        ("permit_recheck_checks", "permit_recheck_checks_per_100k"),
        ("permit_and_recheck_checks", "permit_and_recheck_checks_per_100k"),
        ("handgun_or_permit_checks", "handgun_or_permit_checks_per_100k"),
        ("handgun_checks", "handgun_checks_per_100k"),
    ]:
        if rate_col not in out.columns and count_col in out.columns:
            out[rate_col] = out[count_col] / out["population"] * 100000
    return out


def run_nics_mechanism_models(
    panel: pd.DataFrame,
    nics: pd.DataFrame,
) -> pd.DataFrame:
    nics = add_missing_nics_rates(nics)
    data = panel.merge(
        nics[["State", "Year"] + list(NICS_OUTCOMES)],
        on=["State", "Year"],
        how="left",
    )
    rows = []
    for sample, sample_note in NICS_SAMPLES.items():
        sample_data = (
            build_robustness_sample(data, "exclude_covid")
            if sample == "exclude_2020_2021"
            else data.copy()
        )
        for outcome, label in NICS_OUTCOMES.items():
            result = fit_fixed_effect_regression(
                sample_data,
                outcome,
                ["post_permitless"],
                controls=BASELINE_CONTROL_COLUMNS,
            )
            coef = result.params.get("post_permitless", np.nan)
            se = result.bse.get("post_permitless", np.nan)
            rows.append(
                {
                    "nics_outcome": outcome,
                    "nics_outcome_label": label,
                    "sample": sample,
                    "sample_note": sample_note,
                    "specification": "twfe_nics_mechanism_proxy",
                    "coef_post_permitless": coef,
                    "se_post_permitless": se,
                    "p_post_permitless": result.pvalues.get("post_permitless", np.nan),
                    "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                    "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                    "nobs": result.nobs,
                    "r2": result.rsquared,
                    "interpretation_scope": "mechanism_proxy_nics_checks_not_firearm_sales",
                    "coverage_note": "NICS proxy covers 1999-2021 because 2022-2024 pages in the official year-by-state PDF did not extract cleanly with local tools.",
                }
            )
    return pd.DataFrame(rows)


def main():
    if not NICS_FILE.exists():
        raise FileNotFoundError(
            f"Missing processed NICS file: {NICS_FILE}. Run python3 -m src.data.process_nics first."
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    nics = pd.read_csv(NICS_FILE)
    detail = run_nics_mechanism_models(panel, nics)
    detail.to_csv(DETAIL_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
