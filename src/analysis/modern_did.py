from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
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
        BASELINE_CONTROL_COLUMNS,
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
COHORT_TIME_ATT_FILE = OUT_DIR / "cohort_time_att_not_yet_controls.csv"
DYNAMIC_ATT_FILE = OUT_DIR / "dynamic_att_not_yet_controls.csv"
STACKED_DID_FILE = OUT_DIR / "stacked_did_results.csv"
SUMMARY_FILE = OUT_DIR / "modern_did_summary.csv"


def weighted_average(values: pd.Series, weights: pd.Series) -> float:
    valid = values.notna() & weights.notna() & (weights > 0)
    if not valid.any():
        return np.nan
    return float(np.average(values.loc[valid], weights=weights.loc[valid]))


def _state_change_table(
    panel: pd.DataFrame,
    outcome: str,
    baseline_year: int,
    target_year: int,
) -> pd.DataFrame:
    use = panel.loc[
        panel["Year"].isin([baseline_year, target_year]),
        ["State", "Year", "permitless_year", outcome],
    ].copy()
    values = use.pivot_table(index="State", columns="Year", values=outcome, aggfunc="mean")
    if baseline_year not in values.columns or target_year not in values.columns:
        return pd.DataFrame(columns=["State", "permitless_year", "change"])

    adoption = (
        panel[["State", "permitless_year"]]
        .drop_duplicates("State")
        .set_index("State")["permitless_year"]
    )
    out = values[[baseline_year, target_year]].dropna().copy()
    out["change"] = out[target_year] - out[baseline_year]
    out["permitless_year"] = adoption.reindex(out.index)
    return out.reset_index()[["State", "permitless_year", "change"]]


def build_cohort_time_att(
    panel: pd.DataFrame,
    outcome: str,
    *,
    min_event_time: int = -5,
    max_event_time: int = 5,
) -> pd.DataFrame:
    rows = []
    cohorts = sorted(panel["permitless_year"].dropna().astype(int).unique())
    min_year = int(panel["Year"].min())
    max_year = int(panel["Year"].max())

    for cohort in cohorts:
        baseline_year = cohort - 1
        cohort_states = sorted(
            panel.loc[panel["permitless_year"].eq(cohort), "State"]
            .drop_duplicates()
            .tolist()
        )
        for event_time in range(min_event_time, max_event_time + 1):
            if event_time == -1:
                continue
            target_year = cohort + event_time
            if target_year < min_year or target_year > max_year:
                continue

            changes = _state_change_table(panel, outcome, baseline_year, target_year)
            if changes.empty:
                continue

            treated = changes.loc[changes["State"].isin(cohort_states)].copy()
            latest_required_untreated_year = max(baseline_year, target_year)
            controls = changes.loc[
                (~changes["State"].isin(cohort_states))
                & (
                    changes["permitless_year"].isna()
                    | (changes["permitless_year"] > latest_required_untreated_year)
                )
            ].copy()
            if treated.empty or controls.empty:
                continue

            treated_change = float(treated["change"].mean())
            control_change = float(controls["change"].mean())
            rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
                    "cohort": cohort,
                    "baseline_year": baseline_year,
                    "target_year": target_year,
                    "event_time": event_time,
                    "n_treated_states": int(len(treated)),
                    "n_control_states": int(len(controls)),
                    "treated_states": ";".join(sorted(treated["State"].tolist())),
                    "control_states": ";".join(sorted(controls["State"].tolist())),
                    "treated_change": treated_change,
                    "control_change": control_change,
                    "att": treated_change - control_change,
                }
            )

    return pd.DataFrame(rows).sort_values(["outcome", "cohort", "event_time"]).reset_index(drop=True)


def aggregate_dynamic_att(cohort_time_att: pd.DataFrame) -> pd.DataFrame:
    if cohort_time_att.empty:
        return pd.DataFrame(
            columns=[
                "outcome",
                "outcome_label",
                "event_time",
                "weighted_att",
                "n_cohorts",
                "n_treated_states",
                "min_control_states",
            ]
        )

    rows = []
    for keys, group in cohort_time_att.groupby(["outcome", "outcome_label", "event_time"], sort=True):
        outcome, outcome_label, event_time = keys
        n_cohorts = int(group["cohort"].nunique()) if "cohort" in group else int(len(group))
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": outcome_label,
                "event_time": int(event_time),
                "weighted_att": weighted_average(group["att"], group["n_treated_states"]),
                "n_cohorts": n_cohorts,
                "n_treated_states": int(group["n_treated_states"].sum()),
                "min_control_states": int(group["n_control_states"].min()),
            }
        )
    return pd.DataFrame(rows).sort_values(["outcome", "event_time"]).reset_index(drop=True)


def build_all_cohort_att(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for outcome in OUTCOMES:
        out = build_cohort_att_table(panel, outcome, windows=(2, 3, 5))
        if not out.empty:
            frames.append(out)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_all_cohort_time_att(panel: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for outcome in OUTCOMES:
        out = build_cohort_time_att(panel, outcome, min_event_time=-5, max_event_time=5)
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


def build_stacked_did_panel(
    panel: pd.DataFrame,
    *,
    pre_window: int = 5,
    post_window: int = 5,
) -> pd.DataFrame:
    rows = []
    cohorts = sorted(panel["permitless_year"].dropna().astype(int).unique())
    min_year = int(panel["Year"].min())
    max_year = int(panel["Year"].max())

    for cohort in cohorts:
        start_year = max(min_year, cohort - pre_window)
        end_year = min(max_year, cohort + post_window)
        treated_states = sorted(
            panel.loc[panel["permitless_year"].eq(cohort), "State"]
            .drop_duplicates()
            .tolist()
        )
        control_states = sorted(
            panel.loc[
                (~panel["State"].isin(treated_states))
                & (
                    panel["permitless_year"].isna()
                    | (panel["permitless_year"] > end_year)
                ),
                "State",
            ]
            .drop_duplicates()
            .tolist()
        )
        if not treated_states or not control_states:
            continue

        stack = panel.loc[
            panel["State"].isin(treated_states + control_states)
            & panel["Year"].between(start_year, end_year)
        ].copy()
        if stack.empty:
            continue
        stack["stack_cohort"] = cohort
        stack["stack_state"] = stack["stack_cohort"].astype(str) + "_" + stack["State"].astype(str)
        stack["stack_year"] = stack["stack_cohort"].astype(str) + "_" + stack["Year"].astype(str)
        stack["stack_treated_state"] = stack["State"].isin(treated_states).astype(int)
        stack["stack_post"] = (stack["Year"] >= cohort).astype(int)
        stack["stacked_treatment"] = stack["stack_treated_state"] * stack["stack_post"]
        rows.append(stack)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True).sort_values(
        ["stack_cohort", "State", "Year"]
    ).reset_index(drop=True)


def estimate_stacked_did(
    panel: pd.DataFrame,
    outcome: str,
    *,
    pre_window: int = 5,
    post_window: int = 5,
    controls=BASELINE_CONTROL_COLUMNS,
) -> dict:
    stacked = build_stacked_did_panel(
        panel,
        pre_window=pre_window,
        post_window=post_window,
    )
    if stacked.empty:
        return {
            "outcome": outcome,
            "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
            "specification": "stacked_did",
            "pre_window": pre_window,
            "post_window": post_window,
            "coef_stacked_treatment": np.nan,
            "se_stacked_treatment": np.nan,
            "p_stacked_treatment": np.nan,
            "nobs": 0,
            "r2": np.nan,
            "n_stacks": 0,
            "n_treated_states": 0,
            "n_control_states": 0,
            "interpretation_scope": "stacked_did_no_valid_stacks",
        }

    use_cols = [
        outcome,
        "State",
        "stack_state",
        "stack_year",
        "stack_cohort",
        "stack_treated_state",
        "stacked_treatment",
    ] + list(controls)
    data = stacked[use_cols].dropna().copy()
    formula = (
        f"{outcome} ~ stacked_treatment"
        + (" + " + " + ".join(controls) if controls else "")
        + " + C(stack_state) + C(stack_year)"
    )
    model = smf.ols(formula, data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["State"]},
    )
    coef = model.params.get("stacked_treatment", np.nan)
    se = model.bse.get("stacked_treatment", np.nan)
    return {
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
        "specification": "stacked_did",
        "pre_window": pre_window,
        "post_window": post_window,
        "coef_stacked_treatment": coef,
        "se_stacked_treatment": se,
        "p_stacked_treatment": model.pvalues.get("stacked_treatment", np.nan),
        "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
        "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
        "nobs": model.nobs,
        "r2": model.rsquared,
        "n_stacks": int(data["stack_cohort"].nunique()),
        "n_treated_states": int(
            data.loc[data["stack_treated_state"].eq(1), "State"].nunique()
        ),
        "n_control_states": int(
            data.loc[data["stack_treated_state"].eq(0), "State"].nunique()
        ),
        "interpretation_scope": "stacked_did_cohort_window_sensitivity",
    }


def estimate_all_stacked_did(panel: pd.DataFrame) -> pd.DataFrame:
    rows = [estimate_stacked_did(panel, outcome) for outcome in OUTCOMES]
    return pd.DataFrame(rows)


def summarize_modern_did(
    cohort_att: pd.DataFrame,
    event_time: pd.DataFrame,
    dynamic_att: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    rows = []
    for outcome in OUTCOMES:
        cohort = cohort_att.loc[cohort_att["outcome"] == outcome].copy()
        event = event_time.loc[event_time["outcome"] == outcome].copy()
        dynamic = (
            dynamic_att.loc[dynamic_att["outcome"] == outcome].copy()
            if dynamic_att is not None and not dynamic_att.empty
            else pd.DataFrame()
        )
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
        if dynamic.empty:
            row["not_yet_post_mean_att"] = np.nan
            row["not_yet_pre_mean_att"] = np.nan
            row["not_yet_dynamic_rows"] = 0
        else:
            row["not_yet_post_mean_att"] = dynamic.loc[
                dynamic["event_time"] >= 0, "weighted_att"
            ].mean()
            row["not_yet_pre_mean_att"] = dynamic.loc[
                dynamic["event_time"] < -1, "weighted_att"
            ].mean()
            row["not_yet_dynamic_rows"] = int(len(dynamic))
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
    cohort_time_att = build_all_cohort_time_att(panel)
    dynamic_att = aggregate_dynamic_att(cohort_time_att)
    stacked_did = estimate_all_stacked_did(panel)
    summary = summarize_modern_did(cohort_att, event_time, dynamic_att)

    cohort_att.to_csv(COHORT_ATT_FILE, index=False)
    event_time.to_csv(EVENT_TIME_FILE, index=False)
    cohort_time_att.to_csv(COHORT_TIME_ATT_FILE, index=False)
    dynamic_att.to_csv(DYNAMIC_ATT_FILE, index=False)
    stacked_did.to_csv(STACKED_DID_FILE, index=False)
    summary.to_csv(SUMMARY_FILE, index=False)

    print(f"Wrote: {COHORT_ATT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {EVENT_TIME_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {COHORT_TIME_ATT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {DYNAMIC_ATT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {STACKED_DID_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
