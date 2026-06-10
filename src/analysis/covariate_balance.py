from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import minimize

try:
    from src.analysis.phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        OUTCOMES,
        OUTCOME_LABELS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
DETAIL_FILE = OUT_DIR / "covariate_balanced_twfe_results.csv"
WEIGHTS_FILE = OUT_DIR / "covariate_balance_state_weights.csv"
DIAGNOSTIC_FILE = OUT_DIR / "covariate_balance_diagnostics.csv"

DEFAULT_BALANCE_COLUMNS = [
    "baseline_firearm_suicide_rate",
    "gun_ownership_baseline",
    "share_nonmetro_counties_2013",
    "rep_vote_share_baseline",
    "baseline_income_pc",
    "baseline_unemployment_rate",
]


def _first_nonmissing(series: pd.Series):
    values = series.dropna()
    if values.empty:
        return np.nan
    return values.iloc[0]


def _baseline_slice(group: pd.DataFrame) -> pd.DataFrame:
    permitless_year = pd.to_numeric(group["permitless_year"], errors="coerce").dropna()
    if not permitless_year.empty:
        baseline = group.loc[group["Year"] < float(permitless_year.iloc[0])]
    else:
        baseline = group.loc[group["Year"] <= 2014]
    if baseline.empty:
        return group
    return baseline


def build_state_covariate_table(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for state, group in panel.sort_values(["State", "Year"]).groupby("State"):
        baseline = _baseline_slice(group)
        votes = group[["Year", "rep_vote_share_2party"]].dropna().drop_duplicates()
        if votes.empty:
            rep_vote = np.nan
        elif 2012 in votes["Year"].values:
            rep_vote = votes.loc[votes["Year"].eq(2012), "rep_vote_share_2party"].iloc[0]
        else:
            rep_vote = votes.sort_values("Year")["rep_vote_share_2party"].iloc[-1]

        rows.append(
            {
                "State": state,
                "ever_adopter": int(group["ever_adopter"].max()),
                "permitless_year": _first_nonmissing(group["permitless_year"]),
                "baseline_firearm_suicide_rate": baseline[
                    "firearm_suicide_rate_per_100k"
                ].mean(),
                "gun_ownership_baseline": _first_nonmissing(group["gun_ownership"]),
                "share_nonmetro_counties_2013": _first_nonmissing(
                    group["share_nonmetro_counties_2013"]
                ),
                "rep_vote_share_baseline": rep_vote,
                "baseline_income_pc": baseline["income_pc"].mean(),
                "baseline_unemployment_rate": baseline["unemployment_rate"].mean(),
                "n_baseline_years": int(len(baseline)),
            }
        )
    return pd.DataFrame(rows)


def _standardized_design(table: pd.DataFrame, covariates: list[str]) -> pd.DataFrame:
    x = table[covariates].astype(float)
    center = x.mean()
    scale = x.std(ddof=0).replace(0, 1)
    return (x - center) / scale


def _distance_fallback(
    treated: pd.DataFrame,
    controls: pd.DataFrame,
    covariates: list[str],
) -> np.ndarray:
    combined = pd.concat([treated, controls], ignore_index=True)
    z = _standardized_design(combined, covariates)
    target = z.iloc[: len(treated)].mean(axis=0).to_numpy()
    control_z = z.iloc[len(treated) :].to_numpy()
    distance = np.sqrt(((control_z - target) ** 2).sum(axis=1))
    inverse = 1 / np.clip(distance, 1e-6, None)
    return inverse / inverse.sum() * len(treated)


def compute_balancing_weights(
    state_covariates: pd.DataFrame,
    covariates: list[str] = None,
    *,
    balance_penalty: float = 100.0,
) -> pd.DataFrame:
    covariates = covariates or DEFAULT_BALANCE_COLUMNS
    required = {"State", "ever_adopter"} | set(covariates)
    missing = sorted(required - set(state_covariates.columns))
    if missing:
        raise ValueError(f"State covariate table missing columns: {missing}")

    usable = state_covariates.dropna(subset=covariates).copy()
    treated = usable.loc[usable["ever_adopter"].eq(1)].copy()
    controls = usable.loc[usable["ever_adopter"].eq(0)].copy()
    if treated.empty or controls.empty:
        raise ValueError("Balancing weights require treated and control states")

    combined = pd.concat([treated, controls], ignore_index=True)
    z = _standardized_design(combined, covariates)
    target = z.iloc[: len(treated)].mean(axis=0).to_numpy()
    control_z = z.iloc[len(treated) :].to_numpy()
    n_treated = len(treated)
    n_controls = len(controls)
    base = np.repeat(n_treated / n_controls, n_controls)

    def objective(weights):
        weighted_mean = control_z.T @ weights / weights.sum()
        balance_loss = ((weighted_mean - target) ** 2).sum()
        distance_loss = ((weights - base) ** 2).sum()
        return 0.5 * distance_loss + balance_penalty * balance_loss

    constraints = [{"type": "eq", "fun": lambda weights: weights.sum() - n_treated}]
    bounds = [(1e-6, float(n_treated))] * n_controls
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message="Values in x were outside bounds during a minimize step",
            category=RuntimeWarning,
        )
        result = minimize(objective, base, method="SLSQP", bounds=bounds, constraints=constraints)
    control_weights = (
        result.x if result.success and np.isfinite(result.x).all()
        else _distance_fallback(treated, controls, covariates)
    )

    out = state_covariates[["State", "ever_adopter"]].copy()
    out["covariate_balance_weight"] = 0.0
    out["balance_status"] = "excluded_missing_balance_covariate"
    out.loc[out["State"].isin(treated["State"]), "covariate_balance_weight"] = 1.0
    out.loc[out["State"].isin(treated["State"]), "balance_status"] = "adopter_unit_weight"
    for state, weight in zip(controls["State"], control_weights):
        out.loc[out["State"].eq(state), "covariate_balance_weight"] = float(weight)
        out.loc[out["State"].eq(state), "balance_status"] = (
            "optimized_control_weight" if result.success else "distance_fallback_control_weight"
        )
    return out


def add_covariate_balance_weights(panel: pd.DataFrame, weights: pd.DataFrame) -> pd.DataFrame:
    if "covariate_balance_weight" not in weights.columns:
        raise ValueError("Weights table missing covariate_balance_weight")
    out = panel.merge(weights[["State", "covariate_balance_weight"]], on="State", how="left")
    out["covariate_balance_weight"] = out["covariate_balance_weight"].fillna(0.0)
    return out


def build_balance_diagnostics(
    state_covariates: pd.DataFrame,
    weights: pd.DataFrame,
    covariates: list[str] = None,
) -> pd.DataFrame:
    covariates = covariates or DEFAULT_BALANCE_COLUMNS
    table = state_covariates.merge(
        weights[["State", "covariate_balance_weight"]],
        on="State",
        how="left",
    )
    rows = []
    treated = table.loc[table["ever_adopter"].eq(1)].copy()
    controls = table.loc[table["ever_adopter"].eq(0)].copy()
    for covariate in covariates:
        treated_values = treated[covariate].dropna()
        control_values = controls[covariate].dropna()
        control_weighted = controls.loc[
            controls[covariate].notna() & controls["covariate_balance_weight"].gt(0)
        ]
        pooled_sd = table[covariate].std(ddof=0)
        if not np.isfinite(pooled_sd) or pooled_sd == 0:
            pooled_sd = np.nan
        weighted_mean = np.average(
            control_weighted[covariate],
            weights=control_weighted["covariate_balance_weight"],
        ) if not control_weighted.empty else np.nan
        treated_mean = treated_values.mean()
        control_mean = control_values.mean()
        control_min = control_values.min()
        control_max = control_values.max()
        rows.append(
            {
                "covariate": covariate,
                "adopter_mean": treated_mean,
                "control_unweighted_mean": control_mean,
                "control_weighted_mean": weighted_mean,
                "control_min": control_min,
                "control_max": control_max,
                "adopter_mean_outside_control_range": bool(
                    pd.notna(treated_mean)
                    and pd.notna(control_min)
                    and pd.notna(control_max)
                    and (treated_mean < control_min or treated_mean > control_max)
                ),
                "standardized_difference_unweighted": (
                    (treated_mean - control_mean) / pooled_sd
                    if pd.notna(pooled_sd)
                    else np.nan
                ),
                "standardized_difference_weighted": (
                    (treated_mean - weighted_mean) / pooled_sd
                    if pd.notna(pooled_sd)
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def run_covariate_balanced_models(panel: pd.DataFrame, *, outcomes=None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    outcomes = outcomes or OUTCOMES
    state_covariates = build_state_covariate_table(panel)
    weights = compute_balancing_weights(state_covariates, DEFAULT_BALANCE_COLUMNS)
    diagnostics = build_balance_diagnostics(state_covariates, weights, DEFAULT_BALANCE_COLUMNS)
    data = add_covariate_balance_weights(panel, weights)

    rows = []
    for outcome in outcomes:
        result = fit_fixed_effect_regression(
            data,
            outcome,
            ["post_permitless"],
            weights="covariate_balance_weight",
        )
        coef = result.params.get("post_permitless", np.nan)
        se = result.bse.get("post_permitless", np.nan)
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
                "specification": "covariate_balanced_twfe",
                "coef_post_permitless": coef,
                "se_post_permitless": se,
                "p_post_permitless": result.pvalues.get("post_permitless", np.nan),
                "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "nobs": result.nobs,
                "r2": result.rsquared,
                "interpretation_scope": "covariate_balanced_comparison_sensitivity",
            }
        )
    return pd.DataFrame(rows), weights, diagnostics


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    detail, weights, diagnostics = run_covariate_balanced_models(panel)
    detail.to_csv(DETAIL_FILE, index=False)
    weights.to_csv(WEIGHTS_FILE, index=False)
    diagnostics.to_csv(DIAGNOSTIC_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {WEIGHTS_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {DIAGNOSTIC_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
