from pathlib import Path
from typing import Optional
import math
import warnings

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
POLICY_AUDIT_FILE = ROOT / "data" / "policy" / "permitless_carry_legal_audit.csv"

OUTCOMES = [
    "firearm_suicide_rate_per_100k",
    "nonfirearm_suicide_rate_per_100k",
    "total_suicide_rate_per_100k",
    "firearm_homicide_rate_per_100k",
    "total_firearm_rate_per_100k",
]

OUTCOME_LABELS = {
    "firearm_suicide_rate_per_100k": "Firearm Suicide",
    "nonfirearm_suicide_rate_per_100k": "Non-Firearm Suicide",
    "total_suicide_rate_per_100k": "Total Suicide",
    "firearm_homicide_rate_per_100k": "Firearm Homicide",
    "total_firearm_rate_per_100k": "Total Firearm Deaths",
}

POLICY_AUDIT_COLUMNS = [
    "State",
    "permitless_year_current",
    "bill_or_statute",
    "enactment_date",
    "effective_date",
    "permitless_concealed",
    "permitless_open",
    "constitutional_carry_label",
    "minimum_age",
    "training_requirement_removed",
    "background_check_permit_requirement_removed",
    "violent_misdemeanor_permit_screen_removed",
    "source_url",
    "coding_notes",
    "audit_status",
]

VERIFIED_POLICY_AUDIT_REQUIRED_FIELDS = [
    "bill_or_statute",
    "enactment_date",
    "effective_date",
    "permitless_concealed",
    "permitless_open",
    "constitutional_carry_label",
    "minimum_age",
    "training_requirement_removed",
    "background_check_permit_requirement_removed",
    "violent_misdemeanor_permit_screen_removed",
    "source_url",
    "coding_notes",
]

POLICY_AUDIT_MECHANISM_FIELDS = [
    "training_requirement_removed",
    "background_check_permit_requirement_removed",
    "violent_misdemeanor_permit_screen_removed",
]

VERIFIED_POLICY_AUDIT_STATUSES = {
    "source_verified",
    "not_adopted_verified",
}


class RegressionResult:
    def __init__(self, params, bse, pvalues, nobs, rsquared):
        self.params = params
        self.bse = bse
        self.pvalues = pvalues
        self.nobs = nobs
        self.rsquared = rsquared


def load_panel() -> pd.DataFrame:
    return pd.read_csv(PANEL_FILE).sort_values(["State", "Year"]).reset_index(drop=True)


def validate_policy_audit_schema(table: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in POLICY_AUDIT_COLUMNS if col not in table.columns]
    if missing:
        raise ValueError(f"Policy audit table missing required columns: {missing}")
    return table[POLICY_AUDIT_COLUMNS].copy()


def validate_policy_audit_verified_rows(table: pd.DataFrame) -> pd.DataFrame:
    audit = validate_policy_audit_schema(table)
    statuses = audit["audit_status"].astype(str).str.strip()
    verified = statuses.isin(VERIFIED_POLICY_AUDIT_STATUSES)
    if not verified.any():
        return audit

    missing_by_status = {}
    for row_number, row in audit.loc[verified].iterrows():
        status = str(row["audit_status"]).strip()
        missing_fields = [
            field
            for field in VERIFIED_POLICY_AUDIT_REQUIRED_FIELDS
            if str(row[field]).strip() == ""
        ]
        if missing_fields:
            missing_by_status.setdefault(status, []).append(
                f"{row.get('State', row_number)}: {', '.join(missing_fields)}"
            )

    if missing_by_status:
        statuses = sorted(missing_by_status)
        details = "; ".join(
            f"{status}: {'; '.join(missing_by_status[status])}"
            for status in statuses
        )
        status_label = statuses[0] if len(statuses) == 1 else "verified legal audit"
        raise ValueError(
            f"{status_label} rows missing required legal audit fields: "
            f"{details}"
        )
    return audit


def validate_policy_audit_mechanism_rows(table: pd.DataFrame) -> pd.DataFrame:
    audit = validate_policy_audit_schema(table)
    source_verified = audit["audit_status"].astype(str).str.strip().eq("source_verified")
    unresolved_rows = []
    for row_number, row in audit.loc[source_verified].iterrows():
        unresolved_fields = [
            field
            for field in POLICY_AUDIT_MECHANISM_FIELDS
            if str(row[field]).strip() in {"", "needs_statute_review"}
        ]
        if unresolved_fields:
            unresolved_rows.append(
                f"{row.get('State', row_number)}: {', '.join(unresolved_fields)}"
            )

    if unresolved_rows:
        details = "; ".join(unresolved_rows)
        raise ValueError(
            "source_verified mechanism fields still unresolved: "
            f"{details}"
        )
    return audit


def validate_policy_year_consistency(panel_states: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    panel_years = panel_states[["State", "permitless_year"]].drop_duplicates("State").copy()
    audit_years = audit[["State", "permitless_year_current"]].copy()
    if "audit_status" in audit.columns:
        audit_years["audit_status"] = audit["audit_status"]
    else:
        audit_years["audit_status"] = "missing"

    merged = panel_years.merge(audit_years, on="State", how="outer")
    panel = pd.to_numeric(merged["permitless_year"], errors="coerce")
    audit_year = pd.to_numeric(merged["permitless_year_current"], errors="coerce")
    merged["year_mismatch"] = ~(
        (panel.isna() & audit_year.isna())
        | (panel.fillna(-1).astype(float) == audit_year.fillna(-1).astype(float))
    )
    return merged


def build_robustness_sample(panel: pd.DataFrame, specification: str) -> pd.DataFrame:
    if specification == "baseline":
        return panel.copy()
    if specification == "exclude_covid":
        return panel.loc[~panel["Year"].isin([2020, 2021])].copy()
    if specification == "pre_covid_only":
        return panel.loc[panel["Year"] <= 2019].copy()
    raise ValueError(f"Unknown robustness specification: {specification}")


def add_event_time_columns(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["event_time"] = out["Year"] - out["permitless_year"]
    out.loc[out["permitless_year"].isna(), "event_time"] = np.nan
    out["cohort"] = out["permitless_year"]
    return out


def build_cohort_att_table(panel: pd.DataFrame, outcome: str, windows=(2, 3, 5)) -> pd.DataFrame:
    rows = []
    cohorts = sorted(panel["permitless_year"].dropna().astype(int).unique())
    for cohort in cohorts:
        treated_states = panel.loc[panel["permitless_year"] == cohort, "State"].drop_duplicates()
        controls = panel.loc[panel["permitless_year"].isna(), "State"].drop_duplicates()
        for window in windows:
            pre_years = list(range(cohort - window, cohort))
            post_years = list(range(cohort, cohort + window))
            treated = panel.loc[panel["State"].isin(treated_states)]
            control = panel.loc[panel["State"].isin(controls)]
            t_pre = treated.loc[treated["Year"].isin(pre_years), outcome].mean()
            t_post = treated.loc[treated["Year"].isin(post_years), outcome].mean()
            c_pre = control.loc[control["Year"].isin(pre_years), outcome].mean()
            c_post = control.loc[control["Year"].isin(post_years), outcome].mean()
            if pd.notna(t_pre) and pd.notna(t_post) and pd.notna(c_pre) and pd.notna(c_post):
                rows.append(
                    {
                        "outcome": outcome,
                        "outcome_label": OUTCOME_LABELS.get(outcome, outcome),
                        "cohort": cohort,
                        "window": window,
                        "n_treated_states": int(len(treated_states)),
                        "n_control_states": int(len(controls)),
                        "treated_change": t_post - t_pre,
                        "control_change": c_post - c_pre,
                        "att": (t_post - t_pre) - (c_post - c_pre),
                    }
                )
    return pd.DataFrame(rows)


def _normal_pvalues(t_values: np.ndarray) -> np.ndarray:
    return np.array([math.erfc(abs(float(t)) / math.sqrt(2)) if np.isfinite(t) else np.nan for t in t_values])


def fit_fixed_effect_regression(
    data: pd.DataFrame,
    outcome: str,
    treatment_terms,
    *,
    weights: Optional[str] = None,
    state_trends: bool = False,
    controls=("unemployment_rate", "income_pc"),
):
    use_cols = [outcome, "State", "Year"] + list(treatment_terms) + list(controls)
    if weights:
        use_cols.append(weights)
    d = data[use_cols].dropna().copy()

    columns = ["intercept"] + list(treatment_terms) + list(controls)
    x_parts = [pd.Series(1.0, index=d.index, name="intercept")]
    for col in list(treatment_terms) + list(controls):
        x_parts.append(pd.to_numeric(d[col], errors="coerce").astype(float).rename(col))

    state_dummies = pd.get_dummies(d["State"], prefix="state", drop_first=True, dtype=float)
    year_dummies = pd.get_dummies(d["Year"].astype(int), prefix="year", drop_first=True, dtype=float)
    x_parts.extend([state_dummies, year_dummies])
    columns.extend(state_dummies.columns.tolist())
    columns.extend(year_dummies.columns.tolist())

    if state_trends:
        centered_year = d["Year"] - d["Year"].min()
        trend_dummies = pd.get_dummies(d["State"], prefix="state_trend", drop_first=True, dtype=float)
        trend_dummies = trend_dummies.multiply(centered_year.to_numpy(), axis=0)
        x_parts.append(trend_dummies)
        columns.extend(trend_dummies.columns.tolist())

    x_df = pd.concat(x_parts, axis=1).astype(float)
    x_df = x_df.loc[:, columns]
    y = pd.to_numeric(d[outcome], errors="coerce").astype(float).to_numpy()
    x = x_df.to_numpy()

    if weights:
        w = pd.to_numeric(d[weights], errors="coerce").astype(float).to_numpy()
        sqrt_w = np.sqrt(w / np.nanmean(w))
        x_fit = x * sqrt_w[:, None]
        y_fit = y * sqrt_w
    else:
        sqrt_w = np.ones_like(y)
        x_fit = x
        y_fit = y

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        xtx_inv = np.linalg.pinv(x_fit.T @ x_fit)
        beta = xtx_inv @ x_fit.T @ y_fit
        residual = y - x @ beta

    meat = np.zeros((x.shape[1], x.shape[1]))
    clusters = d["State"].to_numpy()
    for cluster in np.unique(clusters):
        idx = clusters == cluster
        xg = x[idx] * sqrt_w[idx, None]
        ug = residual[idx] * sqrt_w[idx]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            score = xg.T @ ug
        meat += np.outer(score, score)

    nobs = int(len(y))
    k = x.shape[1]
    g = len(np.unique(clusters))
    correction = 1.0
    if g > 1 and nobs > k:
        correction = (g / (g - 1)) * ((nobs - 1) / (nobs - k))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        cov = correction * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    with np.errstate(divide="ignore", invalid="ignore"):
        t_values = beta / se
    pvalues = _normal_pvalues(t_values)

    y_mean = np.average(y, weights=sqrt_w**2)
    ss_res = float(np.sum((sqrt_w * residual) ** 2))
    ss_tot = float(np.sum((sqrt_w * (y - y_mean)) ** 2))
    r2 = np.nan if ss_tot == 0 else 1 - ss_res / ss_tot

    return RegressionResult(
        params=pd.Series(beta, index=x_df.columns),
        bse=pd.Series(se, index=x_df.columns),
        pvalues=pd.Series(pvalues, index=x_df.columns),
        nobs=float(nobs),
        rsquared=r2,
    )


def fit_twfe(
    data: pd.DataFrame,
    outcome: str,
    *,
    weights: Optional[str] = None,
    state_trends: bool = False,
):
    return fit_fixed_effect_regression(
        data,
        outcome,
        ["post_permitless"],
        weights=weights,
        state_trends=state_trends,
    )
