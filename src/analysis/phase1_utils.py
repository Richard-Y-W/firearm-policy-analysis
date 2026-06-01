from pathlib import Path
from typing import Optional

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


def load_panel() -> pd.DataFrame:
    return pd.read_csv(PANEL_FILE).sort_values(["State", "Year"]).reset_index(drop=True)


def validate_policy_audit_schema(table: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in POLICY_AUDIT_COLUMNS if col not in table.columns]
    if missing:
        raise ValueError(f"Policy audit table missing required columns: {missing}")
    return table[POLICY_AUDIT_COLUMNS].copy()


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


def fit_twfe(
    data: pd.DataFrame,
    outcome: str,
    *,
    weights: Optional[str] = None,
    state_trends: bool = False,
):
    import statsmodels.formula.api as smf

    terms = ["post_permitless", "unemployment_rate", "income_pc", "C(State)", "C(Year)"]
    use_cols = [outcome, "post_permitless", "unemployment_rate", "income_pc", "State", "Year"]
    if weights:
        use_cols.append(weights)
    d = data[use_cols].dropna().copy()

    if state_trends:
        d["centered_year"] = d["Year"] - d["Year"].min()
        terms.append("C(State):centered_year")

    formula = f"{outcome} ~ {' + '.join(terms)}"
    if weights:
        return smf.wls(formula, data=d, weights=d[weights]).fit(
            cov_type="cluster",
            cov_kwds={"groups": d["State"]},
        )
    return smf.ols(formula, data=d).fit(
        cov_type="cluster",
        cov_kwds={"groups": d["State"]},
    )
