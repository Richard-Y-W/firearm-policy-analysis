from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        add_event_time_columns,
        build_cohort_att_table,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        add_event_time_columns,
        build_cohort_att_table,
        fit_fixed_effect_regression,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "modern_did"
COHORT_ATT_FILE = OUT_DIR / "cohort_att_by_outcome.csv"
EVENT_TIME_FILE = OUT_DIR / "event_time_never_control_estimates.csv"
SUMMARY_FILE = OUT_DIR / "modern_did_summary.csv"


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    valid = values.notna() & weights.notna() & (weights > 0)
    if not valid.any():
        return np.nan
    return float(np.average(values.loc[valid], weights=weights.loc[valid]))


def build_all_cohort_att(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for outcome in OUTCOMES:
        out = build_cohort_att_table(panel, outcome, windows=(2, 3, 5))
        if not out.empty:
            frames.append(out)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def add_event_indicators(panel: pd.DataFrame, min_k=-5, max_k=5):
    d = add_event_time_columns(panel)
    d["event_time_capped"] = d["event_time"].clip(min_k, max_k)
    event_cols = []
    event_map = {}
    for k in range(min_k, max_k + 1):
        if k == -1:
            continue
        col = f"event_m{abs(k)}" if k < 0 else f"event_{k}"
        d[col] = ((d["ever_adopter"] == 1) & (d["event_time_capped"] == k)).astype(int)
        event_cols.append(col)
        event_map[col] = k
    return d, event_cols, event_map


def estimate_event_time_never_control(panel: pd.DataFrame) -> pd.DataFrame:
    d, event_cols, event_map = add_event_indicators(panel)
    rows = []
    for outcome in OUTCOMES:
        use_cols = [
            outcome,
            "State",
            "Year",
            "unemployment_rate",
            "income_pc",
        ] + event_cols
        reg_data = d[use_cols].dropna().copy()
        result = fit_fixed_effect_regression(
            reg_data,
            outcome,
            event_cols,
        )
        for col in event_cols:
            coef = result.params.get(col, np.nan)
            se = result.bse.get(col, np.nan)
            rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "event_time": event_map[col],
                    "term": col,
                    "coef": coef,
                    "se": se,
                    "p_value": result.pvalues.get(col, np.nan),
                    "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                    "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                    "nobs": result.nobs,
                    "r2": result.rsquared,
                }
            )
    return pd.DataFrame(rows).sort_values(["outcome", "event_time"])


def summarize_modern_did(cohort_att: pd.DataFrame, event_time: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome in OUTCOMES:
        cohort = cohort_att.loc[cohort_att["outcome"] == outcome].copy()
        event = event_time.loc[event_time["outcome"] == outcome].copy()
        row = {
            "outcome": outcome,
            "outcome_label": OUTCOME_LABELS[outcome],
        }
        for window in [2, 3, 5]:
            subset = cohort.loc[cohort["window"] == window]
            row[f"cohort_att_w{window}"] = weighted_average(
                subset["att"],
                subset["n_treated_states"],
            )
        pre = event.loc[event["event_time"] < -1]
        post = event.loc[event["event_time"] >= 0]
        row["event_post_mean_coef"] = post["coef"].mean()
        row["event_pretrend_min_p"] = pre["p_value"].min()
        row["pretrend_flag_p05"] = bool((pre["p_value"] < 0.05).any())
        if row["pretrend_flag_p05"]:
            row["interpretation_flag"] = "sensitivity_only_pretrend_signal"
        elif row["event_post_mean_coef"] > 0:
            row["interpretation_flag"] = "positive_post_adoption_sensitivity"
        else:
            row["interpretation_flag"] = "no_positive_post_adoption_sensitivity"
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    cohort_att = build_all_cohort_att(panel)
    event_time = estimate_event_time_never_control(panel)
    summary = summarize_modern_did(cohort_att, event_time)

    cohort_att.to_csv(COHORT_ATT_FILE, index=False)
    event_time.to_csv(EVENT_TIME_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"Wrote: {COHORT_ATT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {EVENT_TIME_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
