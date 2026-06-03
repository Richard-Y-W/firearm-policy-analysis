from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        FIREARM_LAW_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_twfe,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "did"
DETAIL_FILE = OUT_DIR / "twfe_did_nonfirearm_confounder_results.csv"
SUMMARY_FILE = OUT_DIR / "twfe_did_nonfirearm_confounder_summary.csv"

HEALTH_ACCESS_COLUMN = "uninsured_under65_pct"
OVERDOSE_COLUMN = "drug_overdose_rate_per_100k"

CONTROL_SPECS = {
    "baseline_controls": BASELINE_CONTROL_COLUMNS,
    "firearm_law_controls": BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS,
    "health_access_controls": (
        BASELINE_CONTROL_COLUMNS
        + FIREARM_LAW_CONTROL_COLUMNS
        + [HEALTH_ACCESS_COLUMN]
    ),
    "overdose_controls": (
        BASELINE_CONTROL_COLUMNS
        + FIREARM_LAW_CONTROL_COLUMNS
        + [OVERDOSE_COLUMN]
    ),
    "health_access_overdose_controls": (
        BASELINE_CONTROL_COLUMNS
        + FIREARM_LAW_CONTROL_COLUMNS
        + [HEALTH_ACCESS_COLUMN, OVERDOSE_COLUMN]
    ),
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


def run_nonfirearm_confounder_models(panel: pd.DataFrame) -> pd.DataFrame:
    missing = [
        col
        for col in set(BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS)
        | {HEALTH_ACCESS_COLUMN, OVERDOSE_COLUMN}
        if col not in panel.columns
    ]
    if missing:
        raise ValueError(
            f"Panel missing non-firearm confounder columns: {sorted(missing)}"
        )

    rows = []
    for outcome in OUTCOMES:
        for specification, controls in CONTROL_SPECS.items():
            result = fit_twfe(panel, outcome, controls=controls)
            rows.append(model_row(outcome, specification, controls, result))
    return pd.DataFrame(rows)


def _spec_value(rows: pd.DataFrame, specification: str, column: str):
    match = rows.loc[rows["specification"].eq(specification), column]
    return match.iloc[0] if not match.empty else np.nan


def _same_nonzero_sign(reference: float, value: float) -> bool:
    if pd.isna(reference) or pd.isna(value) or reference == 0:
        return False
    return bool(np.sign(reference) == np.sign(value))


def _p05_retained(reference_p: float, value_p: float) -> bool:
    return bool(
        pd.notna(reference_p)
        and pd.notna(value_p)
        and reference_p < 0.05
        and value_p < 0.05
    )


def build_nonfirearm_confounder_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, outcome_rows in results.groupby("outcome", sort=False):
        ref_coef = _spec_value(
            outcome_rows, "firearm_law_controls", "coef_post_permitless"
        )
        ref_p = _spec_value(
            outcome_rows, "firearm_law_controls", "p_post_permitless"
        )
        row = {
            "outcome": outcome,
            "outcome_label": outcome_rows["outcome_label"].iloc[0],
            "firearm_law_coef": ref_coef,
            "firearm_law_p": ref_p,
        }
        for specification, prefix in [
            ("health_access_controls", "health_access"),
            ("overdose_controls", "overdose"),
            ("health_access_overdose_controls", "health_access_overdose"),
        ]:
            coef = _spec_value(outcome_rows, specification, "coef_post_permitless")
            p_value = _spec_value(outcome_rows, specification, "p_post_permitless")
            nobs = _spec_value(outcome_rows, specification, "nobs")
            row[f"{prefix}_coef"] = coef
            row[f"{prefix}_p"] = p_value
            row[f"{prefix}_nobs"] = nobs
            row[f"{prefix}_sign_retained"] = _same_nonzero_sign(ref_coef, coef)
            row[f"{prefix}_p05_retained"] = _p05_retained(ref_p, p_value)
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    detail = run_nonfirearm_confounder_models(panel)
    summary = build_nonfirearm_confounder_summary(detail)
    detail.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
