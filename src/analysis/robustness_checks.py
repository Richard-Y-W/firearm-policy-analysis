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
        build_robustness_sample,
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
        build_robustness_sample,
        fit_twfe,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
TWFE_FILE = OUT_DIR / "twfe_robustness_results.csv"
LEAVE_ONE_OUT_FILE = OUT_DIR / "leave_one_state_out.csv"
PLACEBO_FILE = OUT_DIR / "placebo_never_treated.csv"
SUMMARY_FILE = OUT_DIR / "robustness_summary.csv"


def model_row(outcome: str, specification: str, result, extra=None) -> dict:
    extra = extra or {}
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    p_value = result.pvalues.get("post_permitless", np.nan)
    row = {
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS[outcome],
        "specification": specification,
        "coef_post_permitless": coef,
        "se_post_permitless": se,
        "p_post_permitless": p_value,
        "nobs": result.nobs,
        "r2": result.rsquared,
        "interpretation_flag": (
            "positive_p05"
            if pd.notna(p_value) and p_value < 0.05 and coef > 0
            else "negative_p05"
            if pd.notna(p_value) and p_value < 0.05 and coef < 0
            else "not_p05"
        ),
    }
    row.update(extra)
    return row


def run_twfe_robustness(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    specs = [
        ("baseline", "baseline", None, False, BASELINE_CONTROL_COLUMNS),
        ("exclude_covid", "exclude_covid", None, False, BASELINE_CONTROL_COLUMNS),
        ("pre_covid_only", "pre_covid_only", None, False, BASELINE_CONTROL_COLUMNS),
        ("population_weighted", "baseline", "population", False, BASELINE_CONTROL_COLUMNS),
        ("state_linear_trends", "baseline", None, True, BASELINE_CONTROL_COLUMNS),
        (
            "firearm_law_controls",
            "baseline",
            None,
            False,
            BASELINE_CONTROL_COLUMNS + FIREARM_LAW_CONTROL_COLUMNS,
        ),
    ]
    for outcome in OUTCOMES:
        for spec_name, sample_name, weight, state_trends, controls in specs:
            sample = build_robustness_sample(panel, sample_name)
            result = fit_twfe(
                sample,
                outcome,
                controls=controls,
                weights=weight,
                state_trends=state_trends,
            )
            rows.append(model_row(outcome, spec_name, result))
    return pd.DataFrame(rows)


def run_leave_one_out(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    adopter_states = sorted(panel.loc[panel["ever_adopter"] == 1, "State"].drop_duplicates())
    for outcome in OUTCOMES:
        for state in adopter_states:
            sample = panel.loc[panel["State"] != state].copy()
            result = fit_twfe(sample, outcome)
            rows.append(model_row(outcome, "leave_one_adopter_out", result, {"excluded_state": state}))
    return pd.DataFrame(rows)


def assign_placebo_years(never_panel: pd.DataFrame, shift: int, observed_years: list[int]) -> pd.DataFrame:
    states = sorted(never_panel["State"].drop_duplicates())
    mapping = {
        state: observed_years[(i + shift) % len(observed_years)]
        for i, state in enumerate(states)
    }
    out = never_panel.copy()
    out["permitless_year"] = out["State"].map(mapping)
    out["ever_adopter"] = 1
    out["post_permitless"] = (out["Year"] >= out["permitless_year"]).astype(int)
    out["years_since_permitless"] = out["Year"] - out["permitless_year"]
    return out


def run_placebo_never_treated(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    observed_years = sorted(panel["permitless_year"].dropna().astype(int).unique().tolist())
    never_panel = panel.loc[panel["ever_adopter"] == 0].copy()
    max_shifts = min(len(observed_years), len(never_panel["State"].drop_duplicates()))
    for outcome in OUTCOMES:
        for shift in range(max_shifts):
            placebo = assign_placebo_years(never_panel, shift, observed_years)
            result = fit_twfe(placebo, outcome)
            rows.append(model_row(outcome, "placebo_never_treated", result, {"placebo_shift": shift}))
    return pd.DataFrame(rows)


def summarize_robustness(twfe: pd.DataFrame, leave_one: pd.DataFrame, placebo: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in OUTCOMES:
        main = twfe.loc[(twfe["outcome"] == outcome) & (twfe["specification"] == "baseline")].iloc[0]
        specs = twfe.loc[twfe["outcome"] == outcome].copy()
        loo = leave_one.loc[leave_one["outcome"] == outcome].copy()
        pbo = placebo.loc[placebo["outcome"] == outcome].copy()

        placebo_abs = pbo["coef_post_permitless"].abs()
        observed_abs = abs(main["coef_post_permitless"])
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS[outcome],
                "baseline_coef": main["coef_post_permitless"],
                "baseline_p": main["p_post_permitless"],
                "twfe_specs_positive": int((specs["coef_post_permitless"] > 0).sum()),
                "twfe_specs_p05": int((specs["p_post_permitless"] < 0.05).sum()),
                "leave_one_min_coef": loo["coef_post_permitless"].min(),
                "leave_one_max_coef": loo["coef_post_permitless"].max(),
                "leave_one_sign_changes": int(
                    ((loo["coef_post_permitless"] > 0) != (main["coef_post_permitless"] > 0)).sum()
                ),
                "placebo_abs_median": placebo_abs.median(),
                "placebo_abs_p95": placebo_abs.quantile(0.95),
                "observed_exceeds_placebo_p95": bool(observed_abs > placebo_abs.quantile(0.95)),
                "interpretation_flag": (
                    "stable_positive"
                    if main["coef_post_permitless"] > 0
                    and (specs["coef_post_permitless"] > 0).all()
                    and loo["coef_post_permitless"].min() > 0
                    else "sensitivity_required"
                ),
            }
        )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    twfe = run_twfe_robustness(panel)
    leave_one = run_leave_one_out(panel)
    placebo = run_placebo_never_treated(panel)
    summary = summarize_robustness(twfe, leave_one, placebo)

    twfe.to_csv(TWFE_FILE, index=False)
    leave_one.to_csv(LEAVE_ONE_OUT_FILE, index=False)
    placebo.to_csv(PLACEBO_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"Wrote: {TWFE_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {LEAVE_ONE_OUT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {PLACEBO_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
