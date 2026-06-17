from pathlib import Path
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOME_LABELS,
        OUTCOMES,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOME_LABELS,
        OUTCOMES,
        load_panel,
    )


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
OUT_FILE = OUT_DIR / "wild_cluster_bootstrap_results.csv"


def _twfe_formula(outcome: str, controls: list[str], *, include_treatment: bool) -> str:
    terms = []
    if include_treatment:
        terms.append("post_permitless")
    terms.extend(controls)
    terms.extend(["C(State)", "C(Year)"])
    return f"{outcome} ~ " + " + ".join(terms)


def _cluster_robust_t_value(y: np.ndarray, x: np.ndarray, term_idx: int, groups: np.ndarray) -> float:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        xtx_inv = np.linalg.pinv(x.T @ x)
        beta = xtx_inv @ x.T @ y
        residual = y - x @ beta

    meat = np.zeros((x.shape[1], x.shape[1]))
    for cluster in np.unique(groups):
        idx = groups == cluster
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            score = x[idx].T @ residual[idx]
        meat += np.outer(score, score)

    nobs = x.shape[0]
    k = x.shape[1]
    n_clusters = len(np.unique(groups))
    correction = 1.0
    if n_clusters > 1 and nobs > k:
        correction = (n_clusters / (n_clusters - 1)) * ((nobs - 1) / (nobs - k))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        cov = correction * xtx_inv @ meat @ xtx_inv
    se = float(np.sqrt(max(cov[term_idx, term_idx], 0)))
    if se == 0 or not np.isfinite(se):
        return np.nan
    return float(beta[term_idx] / se)


def wild_cluster_bootstrap_twfe(
    panel: pd.DataFrame,
    outcome: str,
    *,
    controls: list[str] = BASELINE_CONTROL_COLUMNS,
    reps: int = 999,
    seed: int = 20260617,
) -> dict:
    use_cols = [outcome, "post_permitless", "State", "Year"] + list(controls)
    data = panel[use_cols].dropna().copy()
    if data["State"].nunique() < 2:
        raise ValueError("Wild cluster bootstrap requires at least two state clusters")

    full = smf.ols(_twfe_formula(outcome, list(controls), include_treatment=True), data=data).fit(
        cov_type="cluster",
        cov_kwds={"groups": data["State"]},
    )
    restricted = smf.ols(
        _twfe_formula(outcome, list(controls), include_treatment=False),
        data=data,
    ).fit()

    x = np.asarray(full.model.exog, dtype=float)
    term_idx = full.model.exog_names.index("post_permitless")
    groups = data["State"].to_numpy()
    clusters = np.unique(groups)
    rng = np.random.default_rng(seed)

    observed_t = float(full.tvalues["post_permitless"])
    bootstrap_t = []
    fitted_null = np.asarray(restricted.fittedvalues, dtype=float)
    residual_null = np.asarray(restricted.resid, dtype=float)

    for _ in range(reps):
        signs = rng.choice([-1.0, 1.0], size=len(clusters))
        sign_by_cluster = dict(zip(clusters, signs))
        weights = np.array([sign_by_cluster[state] for state in groups])
        y_star = fitted_null + residual_null * weights
        t_star = _cluster_robust_t_value(y_star, x, term_idx, groups)
        if np.isfinite(t_star):
            bootstrap_t.append(t_star)

    if bootstrap_t:
        bootstrap_t = np.asarray(bootstrap_t)
        p_boot = float((np.sum(np.abs(bootstrap_t) >= abs(observed_t)) + 1) / (len(bootstrap_t) + 1))
    else:
        p_boot = np.nan

    return {
        "outcome": outcome,
        "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
        "coef_post_permitless": float(full.params["post_permitless"]),
        "se_post_permitless": float(full.bse["post_permitless"]),
        "p_post_permitless": float(full.pvalues["post_permitless"]),
        "wild_cluster_p_post_permitless": p_boot,
        "observed_t_post_permitless": observed_t,
        "nobs": float(full.nobs),
        "n_clusters": int(len(clusters)),
        "n_bootstrap": int(len(bootstrap_t)),
        "requested_bootstrap": int(reps),
        "bootstrap_weight": "rademacher",
        "bootstrap_null": "restricted",
        "seed": int(seed),
    }


def run_wild_cluster_bootstrap(panel: pd.DataFrame, *, reps: int = 999, seed: int = 20260617) -> pd.DataFrame:
    rows = [
        wild_cluster_bootstrap_twfe(panel, outcome, reps=reps, seed=seed)
        for outcome in OUTCOMES
    ]
    return pd.DataFrame(rows)


def main() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel(clean_primary=True)
    results = run_wild_cluster_bootstrap(panel)
    results.to_csv(OUT_FILE, index=False)
    print(f"Wrote: {OUT_FILE.relative_to(ROOT)}")
    return results


if __name__ == "__main__":
    main()
