from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )


RAW_CDC_DIR = ROOT / "data" / "raw" / "cdc_wonder"
PROCESSED_DIR = ROOT / "data" / "processed"
NEGATIVE_CONTROL_PANEL = (
    PROCESSED_DIR / "analysis_panel_negative_control_mortality_1999_2024.csv"
)
SEX_AGE_PANEL = (
    PROCESSED_DIR / "analysis_panel_firearm_suicide_by_sex_age_1999_2024.csv"
)

NEGATIVE_OUT_DIR = ROOT / "outputs" / "tables" / "negative_controls"
HETEROGENEITY_OUT_DIR = ROOT / "outputs" / "tables" / "heterogeneity"
NEGATIVE_RESULTS_FILE = NEGATIVE_OUT_DIR / "negative_control_twfe_results.csv"
SEX_AGE_RESULTS_FILE = HETEROGENEITY_OUT_DIR / "firearm_suicide_sex_age_twfe_results.csv"
SEX_AGE_SUPPRESSION_AUDIT_FILE = (
    HETEROGENEITY_OUT_DIR / "firearm_suicide_sex_age_suppression_audit.csv"
)
MANUSCRIPT_TABLE_DIR = ROOT / "manuscript" / "tables"
NEGATIVE_CONTROL_LATEX = MANUSCRIPT_TABLE_DIR / "negative_control_mortality_table.tex"
SEX_AGE_LATEX = MANUSCRIPT_TABLE_DIR / "firearm_suicide_sex_age_summary_table.tex"
SEX_AGE_SUPPRESSION_LATEX = (
    MANUSCRIPT_TABLE_DIR / "firearm_suicide_sex_age_suppression_audit_table.tex"
)

NEGATIVE_CONTROL_EXPORTS = {
    "cancer": {
        "label": "Cancer mortality",
        "old": "negative_control_cancer_1999_2020.xls",
        "new": "negative_control_cancer_2018_2024_single_race.xls",
    },
    "cardiovascular": {
        "label": "Cardiovascular mortality",
        "old": "negative_control_cardiovascular_1999_2020.xls",
        "new": "negative_control_cardiovascular_2018_2024_single_race.xls",
    },
    "motor_vehicle": {
        "label": "Motor-vehicle mortality",
        "old": "negative_control_motor_vehicle_1999_2020.xls",
        "new": "negative_control_motor_vehicle_2018_2024_single_race.xls",
    },
}

NEGATIVE_CONTROL_OUTCOMES = {
    "cancer_rate_per_100k": "Cancer mortality",
    "cardiovascular_rate_per_100k": "Cardiovascular mortality",
    "motor_vehicle_rate_per_100k": "Motor-vehicle mortality",
}

SEX_AGE_EXPORTS = {
    "old": "firearm_suicide_by_sex_age_1999_2020.xls",
    "new": "firearm_suicide_by_sex_age_2018_2024_single_race.xls",
}

BROAD_AGE_GROUP_COMPONENTS = {
    "15-24": {"15-24 years"},
    "25-44": {"25-34 years", "35-44 years"},
    "45-64": {"45-54 years", "55-64 years"},
    "65+": {"65-74 years", "75-84 years", "85+ years"},
}


def read_wonder_export(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", engine="python", dtype=str)
    df.columns = [str(c).strip().strip('"') for c in df.columns]
    if "State" not in df.columns or "Year" not in df.columns:
        raise ValueError(f"WONDER export missing State/Year columns: {path}")

    df = df[df["State"].notna() & df["Year"].notna()].copy()
    df = df[df["State"].astype(str).str.strip().ne("---")].copy()
    if "Notes" in df.columns:
        df = df[~df["Notes"].astype(str).str.strip().str.strip('"').eq("Total")].copy()

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip().str.strip('"')

    for col in ["State Code", "Year", "Year Code", "Deaths", "Population"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Deaths" in df.columns and "Population" in df.columns:
        df["rate_per_100k"] = df["Deaths"] / df["Population"] * 100000
    return df


def _read_split_exports(raw_dir: Path, old_filename: str, new_filename: str) -> pd.DataFrame:
    old_file = raw_dir / old_filename
    new_file = raw_dir / new_filename
    missing = [str(path) for path in [old_file, new_file] if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing CDC WONDER exports: {missing}")

    old = read_wonder_export(old_file)
    old["source"] = "WONDER_1999_2020"
    new = read_wonder_export(new_file)
    new = new[new["Year"] >= 2021].copy()
    new["source"] = "WONDER_2018_2024_single_race"
    return pd.concat([old, new], ignore_index=True)


def build_negative_control_panel(raw_dir: Path = RAW_CDC_DIR) -> pd.DataFrame:
    pieces = []
    for stem, spec in NEGATIVE_CONTROL_EXPORTS.items():
        data = _read_split_exports(raw_dir, spec["old"], spec["new"])
        keep = data[["State", "State Code", "Year", "Deaths", "Population", "rate_per_100k"]].copy()
        keep = keep.rename(
            columns={
                "Deaths": f"{stem}_deaths",
                "Population": f"{stem}_population",
                "rate_per_100k": f"{stem}_rate_per_100k",
            }
        )
        pieces.append(keep)

    panel = pieces[0]
    for piece in pieces[1:]:
        panel = panel.merge(piece, on=["State", "State Code", "Year"], how="outer")
    return panel.sort_values(["State", "Year"]).reset_index(drop=True)


def _age_to_broad(age: str) -> str | None:
    age = str(age).strip()
    for broad, components in BROAD_AGE_GROUP_COMPONENTS.items():
        if age in components:
            return broad
    return None


def collapse_firearm_suicide_sex_age(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"State", "Year", "Sex", "Ten-Year Age Groups", "Deaths", "Population"}
    missing = sorted(required - set(raw.columns))
    if missing:
        raise ValueError(f"Sex/age WONDER export missing columns: {missing}")

    data = raw.copy()
    data["broad_age_group"] = data["Ten-Year Age Groups"].map(_age_to_broad)
    data = data[data["broad_age_group"].notna()].copy()

    grouped = (
        data.groupby(["State", "State Code", "Year", "Sex", "broad_age_group"], dropna=False)
        .agg(
            Deaths=("Deaths", "sum"),
            Population=("Population", "sum"),
            component_age_groups_observed=("Ten-Year Age Groups", "nunique"),
        )
        .reset_index()
    )
    grouped["rate_per_100k"] = grouped["Deaths"] / grouped["Population"] * 100000
    grouped["expected_component_age_groups"] = grouped["broad_age_group"].map(
        lambda age: len(BROAD_AGE_GROUP_COMPONENTS[age])
    )
    grouped["complete_broad_age_group"] = (
        grouped["component_age_groups_observed"]
        >= grouped["expected_component_age_groups"]
    )
    return grouped.sort_values(["State", "Year", "Sex", "broad_age_group"]).reset_index(drop=True)


def build_firearm_suicide_sex_age_panel(raw_dir: Path = RAW_CDC_DIR) -> pd.DataFrame:
    raw = _read_split_exports(raw_dir, SEX_AGE_EXPORTS["old"], SEX_AGE_EXPORTS["new"])
    return collapse_firearm_suicide_sex_age(raw)


def _result_row(
    result,
    *,
    stratification: str,
    outcome_label: str,
    sex: str | None = None,
    broad_age_group: str | None = None,
    n_states: int | None = None,
) -> dict:
    coef = result.params.get("post_permitless", np.nan)
    se = result.bse.get("post_permitless", np.nan)
    return {
        "stratification": stratification,
        "outcome_label": outcome_label,
        "sex": sex,
        "broad_age_group": broad_age_group,
        "coef_post_permitless": coef,
        "se_post_permitless": se,
        "p_post_permitless": result.pvalues.get("post_permitless", np.nan),
        "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
        "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
        "nobs": result.nobs,
        "n_states": n_states,
        "r2": result.rsquared,
    }


def run_negative_control_models(
    panel: pd.DataFrame,
    negative_controls: pd.DataFrame,
    *,
    outcomes: dict[str, str] = NEGATIVE_CONTROL_OUTCOMES,
) -> pd.DataFrame:
    data = panel.merge(negative_controls, on=["State", "Year"], how="left")
    rows = []
    for outcome, label in outcomes.items():
        result = fit_fixed_effect_regression(
            data,
            outcome,
            ["post_permitless"],
            controls=BASELINE_CONTROL_COLUMNS,
        )
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": label,
                "specification": "negative_control_twfe",
                **_result_row(
                    result,
                    stratification="negative_control",
                    outcome_label=label,
                    n_states=data.loc[data[outcome].notna(), "State"].nunique(),
                ),
            }
        )
    return pd.DataFrame(rows)


def _fit_rate_model(panel: pd.DataFrame, rates: pd.DataFrame):
    data = panel.merge(rates[["State", "Year", "rate_per_100k"]], on=["State", "Year"], how="left")
    return fit_fixed_effect_regression(
        data,
        "rate_per_100k",
        ["post_permitless"],
        controls=BASELINE_CONTROL_COLUMNS,
    ), data.loc[data["rate_per_100k"].notna(), "State"].nunique()


def _aggregate_rates(data: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = (
        data.groupby(group_cols, dropna=False)
        .agg(Deaths=("Deaths", "sum"), Population=("Population", "sum"))
        .reset_index()
    )
    out["rate_per_100k"] = out["Deaths"] / out["Population"] * 100000
    return out


def run_sex_age_models(panel: pd.DataFrame, strata: pd.DataFrame) -> pd.DataFrame:
    complete = strata[strata["complete_broad_age_group"].astype(bool)].copy()
    rows = []

    by_sex = _aggregate_rates(complete, ["State", "Year", "Sex"])
    for sex, rates in by_sex.groupby("Sex"):
        result, n_states = _fit_rate_model(panel, rates)
        rows.append(
            _result_row(
                result,
                stratification="sex",
                outcome_label=f"Firearm suicide, {sex}",
                sex=sex,
                n_states=n_states,
            )
        )

    by_age = _aggregate_rates(complete, ["State", "Year", "broad_age_group"])
    for broad_age_group, rates in by_age.groupby("broad_age_group"):
        result, n_states = _fit_rate_model(panel, rates)
        rows.append(
            _result_row(
                result,
                stratification="age",
                outcome_label=f"Firearm suicide, age {broad_age_group}",
                broad_age_group=broad_age_group,
                n_states=n_states,
            )
        )

    for (sex, broad_age_group), rates in complete.groupby(["Sex", "broad_age_group"]):
        result, n_states = _fit_rate_model(panel, rates)
        rows.append(
            _result_row(
                result,
                stratification="sex_age",
                outcome_label=f"Firearm suicide, {sex}, age {broad_age_group}",
                sex=sex,
                broad_age_group=broad_age_group,
                n_states=n_states,
            )
        )
    return pd.DataFrame(rows)


def build_sex_age_suppression_audit(
    panel: pd.DataFrame,
    strata: pd.DataFrame,
) -> pd.DataFrame:
    clean_cells = panel[["State", "Year"]].drop_duplicates().copy()
    clean_cells["_clean_cell"] = 1
    expected_clean_state_years = len(clean_cells)

    rows = []
    for (sex, broad_age_group), group in strata.groupby(["Sex", "broad_age_group"]):
        state_years = group[["State", "Year"]].drop_duplicates()
        complete = group[group["complete_broad_age_group"].astype(bool)].copy()
        complete_state_years = complete[["State", "Year"]].drop_duplicates()
        clean_complete = complete_state_years.merge(
            clean_cells,
            on=["State", "Year"],
            how="inner",
        )
        modeled_clean_state_years = len(clean_complete)
        observed_state_years = len(state_years)
        complete_count = len(complete_state_years)
        rows.append(
            {
                "sex": sex,
                "broad_age_group": broad_age_group,
                "expected_component_age_groups": int(
                    group["expected_component_age_groups"].max()
                ),
                "observed_state_years": observed_state_years,
                "complete_state_years": complete_count,
                "expected_clean_state_years": expected_clean_state_years,
                "modeled_clean_state_years": modeled_clean_state_years,
                "complete_share_of_observed": (
                    complete_count / observed_state_years
                    if observed_state_years
                    else np.nan
                ),
                "modeled_share_of_clean_expected": (
                    modeled_clean_state_years / expected_clean_state_years
                    if expected_clean_state_years
                    else np.nan
                ),
            }
        )

    order = {
        "Female": 0,
        "Male": 1,
    }
    age_order = {age: idx for idx, age in enumerate(BROAD_AGE_GROUP_COMPONENTS)}
    audit = pd.DataFrame(rows)
    audit["_sex_order"] = audit["sex"].map(order).fillna(99)
    audit["_age_order"] = audit["broad_age_group"].map(age_order).fillna(99)
    return (
        audit.sort_values(["_sex_order", "_age_order", "sex", "broad_age_group"])
        .drop(columns=["_sex_order", "_age_order"])
        .reset_index(drop=True)
    )


def _format_p_value(p_value) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "$<0.001$"
    return f"{p_value:.3f}"


def build_negative_control_latex(results: pd.DataFrame) -> str:
    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{\\textbf{Negative-control mortality estimates.}}",
        "\\label{tab:negative_controls}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Outcome & Coef. & SE & $p$ & N \\\\",
        "\\midrule",
    ]
    for _, row in results.iterrows():
        lines.append(
            f"{row['outcome_label']} & "
            f"{row['coef_post_permitless']:.3f} & "
            f"{row['se_post_permitless']:.3f} & "
            f"{_format_p_value(row['p_post_permitless'])} & "
            f"{int(row['nobs'])} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def build_sex_age_latex(results: pd.DataFrame) -> str:
    selected = results[
        (
            results["stratification"].eq("sex")
            & results["sex"].isin(["Female", "Male"])
        )
        | (
            results["stratification"].eq("sex_age")
            & results["sex"].eq("Male")
            & results["broad_age_group"].isin(["15-24", "25-44", "45-64", "65+"])
        )
    ].copy()

    def label(row):
        if row["stratification"] == "sex":
            return f"{row['sex']}, modeled adult ages"
        return f"Male, age {row['broad_age_group']}"

    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{\\textbf{Firearm-suicide estimates by sex and broad age group.}}",
        "\\label{tab:sex_age}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Stratum & Coef. & SE & $p$ & N \\\\",
        "\\midrule",
    ]
    for _, row in selected.iterrows():
        lines.append(
            f"{label(row)} & "
            f"{row['coef_post_permitless']:.3f} & "
            f"{row['se_post_permitless']:.3f} & "
            f"{_format_p_value(row['p_post_permitless'])} & "
            f"{int(row['nobs'])} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def build_sex_age_suppression_latex(audit: pd.DataFrame) -> str:
    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{\\textbf{CDC WONDER sex/age suppression audit.}}",
        "\\label{tab:sex_age_suppression}",
        "\\begin{tabular}{lrrrr}",
        "\\toprule",
        "Stratum & Modeled clean cells & Expected clean cells & Share & Complete WONDER cells \\\\",
        "\\midrule",
    ]
    for _, row in audit.iterrows():
        share = row["modeled_share_of_clean_expected"] * 100
        lines.append(
            f"{row['sex']}, age {row['broad_age_group']} & "
            f"{int(row['modeled_clean_state_years'])} & "
            f"{int(row['expected_clean_state_years'])} & "
            f"{share:.1f}\\% & "
            f"{int(row['complete_state_years'])} \\\\"
        )
    lines.extend(
        [
            "\\bottomrule",
            "\\end{tabular}",
            "\\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    NEGATIVE_OUT_DIR.mkdir(parents=True, exist_ok=True)
    HETEROGENEITY_OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPT_TABLE_DIR.mkdir(parents=True, exist_ok=True)

    panel = load_panel()

    negative_controls = build_negative_control_panel()
    negative_controls.to_csv(NEGATIVE_CONTROL_PANEL, index=False)
    negative_results = run_negative_control_models(panel, negative_controls)
    negative_results.to_csv(NEGATIVE_RESULTS_FILE, index=False)
    NEGATIVE_CONTROL_LATEX.write_text(build_negative_control_latex(negative_results))

    sex_age = build_firearm_suicide_sex_age_panel()
    sex_age.to_csv(SEX_AGE_PANEL, index=False)
    sex_age_results = run_sex_age_models(panel, sex_age)
    sex_age_results.to_csv(SEX_AGE_RESULTS_FILE, index=False)
    SEX_AGE_LATEX.write_text(build_sex_age_latex(sex_age_results))
    sex_age_suppression = build_sex_age_suppression_audit(panel, sex_age)
    sex_age_suppression.to_csv(SEX_AGE_SUPPRESSION_AUDIT_FILE, index=False)
    SEX_AGE_SUPPRESSION_LATEX.write_text(
        build_sex_age_suppression_latex(sex_age_suppression)
    )

    print(f"Wrote: {NEGATIVE_CONTROL_PANEL.relative_to(Path.cwd())}")
    print(f"Wrote: {NEGATIVE_RESULTS_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {NEGATIVE_CONTROL_LATEX.relative_to(Path.cwd())}")
    print(f"Wrote: {SEX_AGE_PANEL.relative_to(Path.cwd())}")
    print(f"Wrote: {SEX_AGE_RESULTS_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SEX_AGE_LATEX.relative_to(Path.cwd())}")
    print(f"Wrote: {SEX_AGE_SUPPRESSION_AUDIT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SEX_AGE_SUPPRESSION_LATEX.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
