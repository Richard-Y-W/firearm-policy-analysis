from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        apply_clean_primary_sample,
        fit_twfe,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        apply_clean_primary_sample,
        fit_twfe,
        load_panel,
    )


ARKANSAS_SENSITIVITY_YEARS = {
    "arkansas_2021": 2021,
    "arkansas_2023": 2023,
}
MISSISSIPPI_SENSITIVITY_SCENARIO = "mississippi_retained_year"

OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
DETAIL_FILE = OUT_DIR / "arkansas_treatment_sensitivity.csv"
SUMMARY_FILE = OUT_DIR / "arkansas_treatment_sensitivity_summary.csv"


def assign_arkansas_treatment_year(panel: pd.DataFrame, year: int) -> pd.DataFrame:
    out = panel.copy()
    mask = out["State"].eq("Arkansas")
    out.loc[mask, "permitless_year"] = year
    out.loc[mask, "ever_adopter"] = 1
    out.loc[mask, "post_permitless"] = (out.loc[mask, "Year"] >= year).astype(int)
    out.loc[mask, "years_since_permitless"] = out.loc[mask, "Year"] - year
    return out


def add_states_from_raw_panel(panel: pd.DataFrame, raw_panel: pd.DataFrame, states: list[str]) -> pd.DataFrame:
    additions = raw_panel.loc[raw_panel["State"].isin(states)].copy()
    base = panel.loc[~panel["State"].isin(states)].copy()
    return (
        pd.concat([base, additions], ignore_index=True)
        .sort_values(["State", "Year"])
        .reset_index(drop=True)
    )


def model_row(outcome: str, specification: str, result, arkansas_year=None) -> dict:
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    p_value = result.pvalues.get("post_permitless", np.nan)
    return {
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS[outcome],
        "specification": specification,
        "arkansas_year": arkansas_year if arkansas_year is not None else "",
        "coef_post_permitless": coef,
        "se_post_permitless": se,
        "p_post_permitless": p_value,
        "nobs": result.nobs,
        "r2": result.rsquared,
    }


def run_arkansas_sensitivity(panel: pd.DataFrame) -> pd.DataFrame:
    raw_panel = load_panel(clean_primary=False)
    clean_panel = apply_clean_primary_sample(raw_panel)
    primary_panel = apply_clean_primary_sample(panel)
    scenarios = [("primary_excluded", None, primary_panel)]
    mississippi_panel = add_states_from_raw_panel(clean_panel, raw_panel, ["Mississippi"])
    scenarios.append((MISSISSIPPI_SENSITIVITY_SCENARIO, None, mississippi_panel))
    scenarios.extend(
        (name, year, assign_arkansas_treatment_year(add_states_from_raw_panel(clean_panel, raw_panel, ["Arkansas"]), year))
        for name, year in ARKANSAS_SENSITIVITY_YEARS.items()
    )
    scenarios.extend(
        (
            f"{MISSISSIPPI_SENSITIVITY_SCENARIO}_{name}",
            year,
            assign_arkansas_treatment_year(
                add_states_from_raw_panel(clean_panel, raw_panel, ["Arkansas", "Mississippi"]),
                year,
            ),
        )
        for name, year in ARKANSAS_SENSITIVITY_YEARS.items()
    )

    rows = []
    for outcome in OUTCOMES:
        for scenario_name, arkansas_year, scenario_panel in scenarios:
            result = fit_twfe(scenario_panel, outcome)
            rows.append(model_row(outcome, scenario_name, result, arkansas_year))
    return pd.DataFrame(rows)


def _scenario_value(rows: pd.DataFrame, specification: str, column: str):
    match = rows.loc[rows["specification"].eq(specification), column]
    return match.iloc[0] if not match.empty else np.nan


def _same_nonzero_sign(primary: float, *values: float) -> bool:
    if pd.isna(primary) or primary == 0:
        return False
    primary_sign = np.sign(primary)
    return bool(
        all(pd.notna(value) and np.sign(value) == primary_sign for value in values)
    )


def _all_p05(*values: float) -> bool:
    return bool(all(pd.notna(value) and value < 0.05 for value in values))


def build_sensitivity_summary(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, outcome_rows in results.groupby("outcome", sort=False):
        primary_coef = _scenario_value(
            outcome_rows, "primary_excluded", "coef_post_permitless"
        )
        primary_p = _scenario_value(
            outcome_rows, "primary_excluded", "p_post_permitless"
        )
        coef_2021 = _scenario_value(
            outcome_rows, "arkansas_2021", "coef_post_permitless"
        )
        p_2021 = _scenario_value(
            outcome_rows, "arkansas_2021", "p_post_permitless"
        )
        coef_2023 = _scenario_value(
            outcome_rows, "arkansas_2023", "coef_post_permitless"
        )
        p_2023 = _scenario_value(
            outcome_rows, "arkansas_2023", "p_post_permitless"
        )

        rows.append(
            {
                "outcome": outcome,
                "outcome_label": outcome_rows["outcome_label"].iloc[0],
                "primary_coef": primary_coef,
                "primary_p": primary_p,
                "arkansas_2021_coef": coef_2021,
                "arkansas_2021_p": p_2021,
                "arkansas_2021_delta": round(coef_2021 - primary_coef, 12),
                "arkansas_2023_coef": coef_2023,
                "arkansas_2023_p": p_2023,
                "arkansas_2023_delta": round(coef_2023 - primary_coef, 12),
                "sign_retained": _same_nonzero_sign(primary_coef, coef_2021, coef_2023),
                "p05_retained": _all_p05(primary_p, p_2021, p_2023),
            }
        )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel(clean_primary=True)
    detail = run_arkansas_sensitivity(panel)
    summary = build_sensitivity_summary(detail)
    detail.to_csv(DETAIL_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
