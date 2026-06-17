from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.additional_mortality_checks import read_wonder_export
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from additional_mortality_checks import read_wonder_export
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )


RAW_CDC_DIR = ROOT / "data" / "raw" / "cdc_wonder"
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_DIR = ROOT / "outputs" / "tables" / "negative_controls"
MANUSCRIPT_TABLE_DIR = ROOT / "manuscript" / "tables"

EXTRA_NEGATIVE_CONTROL_PANEL = (
    PROCESSED_DIR / "analysis_panel_extra_negative_control_mortality_1999_2024.csv"
)
EXTRA_NEGATIVE_RESULTS_FILE = OUT_DIR / "extra_negative_control_twfe_results.csv"
EXTRA_NEGATIVE_LATEX_FILE = MANUSCRIPT_TABLE_DIR / "extra_negative_control_mortality_table.tex"

EXTRA_NEGATIVE_CONTROL_EXPORTS = {
    "falls": {
        "label": "Fall mortality",
        "old": "negative_control_falls_1999_2020.xls",
        "new": "negative_control_falls_2018_2024_single_race.xls",
    },
    "non_transport_injury_excluding_falls_poisoning": {
        "label": "Other non-transport injury excluding falls/poisoning",
        "old": "negative_control_non_transport_injury_excluding_falls_poisoning_1999_2020.xls",
        "new": "negative_control_non_transport_injury_excluding_falls_poisoning_2018_2024_single_race.xls",
    },
    "accidental_poisoning": {
        "label": "Accidental poisoning mortality",
        "old": "negative_control_accidental_poisoning_1999_2020.xls",
        "new": "negative_control_accidental_poisoning_2018_2024_single_race.xls",
    },
}


def _read_split_exports(raw_dir: Path, stem: str, old_filename: str, new_filename: str) -> pd.DataFrame:
    old_file = raw_dir / old_filename
    new_file = raw_dir / new_filename
    missing = [path.name for path in [old_file, new_file] if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing extra negative-control CDC WONDER exports for {stem}: {missing}"
        )

    old = read_wonder_export(old_file)
    old["source"] = "WONDER_1999_2020"
    new = read_wonder_export(new_file)
    new = new[new["Year"] >= 2021].copy()
    new["source"] = "WONDER_2018_2024_single_race"
    return pd.concat([old, new], ignore_index=True)


def build_extra_negative_control_panel(raw_dir: Path = RAW_CDC_DIR) -> pd.DataFrame:
    pieces = []
    for stem, spec in EXTRA_NEGATIVE_CONTROL_EXPORTS.items():
        data = _read_split_exports(raw_dir, stem, spec["old"], spec["new"])
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


def run_extra_negative_control_models(
    panel: pd.DataFrame,
    negative_controls: pd.DataFrame,
) -> pd.DataFrame:
    data = panel.merge(negative_controls, on=["State", "Year"], how="left")
    rows = []
    for stem, spec in EXTRA_NEGATIVE_CONTROL_EXPORTS.items():
        outcome = f"{stem}_rate_per_100k"
        result = fit_fixed_effect_regression(
            data,
            outcome,
            ["post_permitless"],
            controls=BASELINE_CONTROL_COLUMNS,
        )
        coef = result.params.get("post_permitless", np.nan)
        se = result.bse.get("post_permitless", np.nan)
        rows.append(
            {
                "outcome": outcome,
                "outcome_label": spec["label"],
                "specification": "extra_negative_control_twfe",
                "coef_post_permitless": coef,
                "se_post_permitless": se,
                "p_post_permitless": result.pvalues.get("post_permitless", np.nan),
                "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
                "nobs": result.nobs,
                "r2": result.rsquared,
            }
        )
    return pd.DataFrame(rows)


def _format_p_value(p_value) -> str:
    if pd.isna(p_value):
        return ""
    if p_value < 0.001:
        return "$<0.001$"
    return f"{p_value:.3f}"


def build_extra_negative_control_latex(results: pd.DataFrame) -> str:
    lines = [
        "\\begin{table}[H]",
        "\\centering",
        "\\caption{\\textbf{Additional injury and accidental-poisoning mortality estimates.}}",
        "\\label{tab:extra_negative_controls}",
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


def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    MANUSCRIPT_TABLE_DIR.mkdir(parents=True, exist_ok=True)
    panel = build_extra_negative_control_panel()
    panel.to_csv(EXTRA_NEGATIVE_CONTROL_PANEL, index=False)
    results = run_extra_negative_control_models(load_panel(), panel)
    results.to_csv(EXTRA_NEGATIVE_RESULTS_FILE, index=False)
    EXTRA_NEGATIVE_LATEX_FILE.write_text(build_extra_negative_control_latex(results))
    print(f"Wrote: {EXTRA_NEGATIVE_CONTROL_PANEL.relative_to(Path.cwd())}")
    print(f"Wrote: {EXTRA_NEGATIVE_RESULTS_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {EXTRA_NEGATIVE_LATEX_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
