from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "did"
DETAIL_FILE = OUT_DIR / "twfe_did_firearm_law_control_results.csv"
SUMMARY_FILE = OUT_DIR / "twfe_did_firearm_law_control_summary.csv"

BASELINE_CONTROL_COLUMNS = ["unemployment_rate", "income_pc"]
CONTROL_SPECS = {
    "baseline_controls": BASELINE_CONTROL_COLUMNS,
    "firearm_law_controls": BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS,
}


def model_row(outcome: str, specification: str, controls: list[str], result) -> dict:
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    p_value = result.pvalues.get("post_permitless", np.nan)
    return {
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS[outcome],
        "specification": specification,
        "control_count": len(controls),
        "controls": ";".join(controls),
        "coef_post_permitless": coef,
        "se_post_permitless": se,
        "p_post_permitless": p_value,
        "nobs": result.nobs,
        "r2": result.rsquared,
    }


def run_firearm_law_control_models(panel: pd.DataFrame) -> pd.DataFrame:
    missing = [
        col
        for col in set(BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS)
        if col not in panel.columns
    ]
    if missing:
        raise ValueError(f"Panel missing firearm-law control columns: {sorted(missing)}")

    rows = []
    for outcome in OUTCOMES:
        for specification, controls in CONTROL_SPECS.items():
            result = fit_twfe(panel, outcome, controls=controls)
            rows.append(model_row(outcome, specification, controls, result))
    return pd.DataFrame(rows)


def _spec_value(rows: pd.DataFrame, specification: str, column: str):
    match = rows.loc[rows["specification"].eq(specification), column]
    return match.iloc[0] if not match.empty else np.nan


def _same_nonzero_sign(primary: float, controlled: float) -> bool:
    if pd.isna(primary) or pd.isna(controlled) or primary == 0:
        return False
    return bool(np.sign(primary) == np.sign(controlled))


def build_firearm_law_control_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, outcome_rows in results.groupby("outcome", sort=False):
        baseline_coef = _spec_value(
            outcome_rows, "baseline_controls", "coef_post_permitless"
        )
        baseline_p = _spec_value(
            outcome_rows, "baseline_controls", "p_post_permitless"
        )
        controlled_coef = _spec_value(
            outcome_rows, "firearm_law_controls", "coef_post_permitless"
        )
        controlled_p = _spec_value(
            outcome_rows, "firearm_law_controls", "p_post_permitless"
        )
        sign_retained = _same_nonzero_sign(baseline_coef, controlled_coef)
        p05_retained = bool(
            pd.notna(baseline_p)
            and pd.notna(controlled_p)
            and baseline_p < 0.05
            and controlled_p < 0.05
        )
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": outcome_rows["outcome_label"].iloc[0],
                "baseline_coef": baseline_coef,
                "baseline_p": baseline_p,
                "controlled_coef": controlled_coef,
                "controlled_p": controlled_p,
                "controlled_delta": (
                    controlled_coef - baseline_coef
                    if pd.notna(controlled_coef) and pd.notna(baseline_coef)
                    else np.nan
                ),
                "sign_retained": sign_retained,
                "p05_retained": p05_retained,
                "interpretation_flag": (
                    "survives_firearm_law_controls"
                    if sign_retained and p05_retained
                    else "attenuated_by_firearm_law_controls"
                    if sign_retained
                    else "sign_changed_with_firearm_law_controls"
                ),
            }
        )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    detail = run_firearm_law_control_models(panel)
    summary = build_firearm_law_control_summary(detail)
    detail.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
