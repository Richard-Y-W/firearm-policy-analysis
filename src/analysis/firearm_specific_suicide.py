from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
DETAIL_FILE = OUT_DIR / "firearm_specific_suicide_results.csv"

FIREARM_SPECIFIC_OUTCOME = "firearm_minus_nonfirearm_suicide_rate_per_100k"


def add_firearm_specific_suicide_rate(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out[FIREARM_SPECIFIC_OUTCOME] = (
        out["firearm_suicide_rate_per_100k"]
        - out["nonfirearm_suicide_rate_per_100k"]
    )
    return out


def run_firearm_specific_suicide_model(panel: pd.DataFrame) -> pd.DataFrame:
    data = add_firearm_specific_suicide_rate(panel)
    result = fit_fixed_effect_regression(
        data,
        FIREARM_SPECIFIC_OUTCOME,
        ["post_permitless"],
        controls=BASELINE_CONTROL_COLUMNS,
    )
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    return pd.DataFrame(
        [
            {
                "outcome": FIREARM_SPECIFIC_OUTCOME,
                "outcome_label": "Firearm suicide minus non-firearm suicide",
                "specification": "despair_netted_firearm_suicide_twfe",
                "coef_post_permitless": coef,
                "se_post_permitless": se,
                "p_post_permitless": result.pvalues.get("post_permitless", np.nan),
                "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "nobs": result.nobs,
                "r2": result.rsquared,
                "interpretation": "TWFE estimate for firearm suicide minus non-firearm suicide; included as a firearm-specific check against generalized suicide/despair movement.",
            }
        ]
    )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    detail = run_firearm_specific_suicide_model(load_panel())
    detail.to_csv(DETAIL_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
