from pathlib import Path

import pandas as pd

try:
    from src.analysis.phase1_utils import ROOT
except ModuleNotFoundError:
    from phase1_utils import ROOT


OUT_DIR = ROOT / "outputs" / "tables" / "robustness"
CSV_FILE = OUT_DIR / "firearm_suicide_main_robustness_table.csv"
TEX_FILE = ROOT / "manuscript" / "tables" / "firearm_suicide_main_robustness_table.tex"

TWFE_FILE = ROOT / "outputs" / "tables" / "did" / "twfe_did_main_results.csv"
FRACTIONAL_FILE = OUT_DIR / "fractional_timing_results.csv"
STACKED_FILE = ROOT / "outputs" / "tables" / "modern_did" / "stacked_did_results.csv"
BALANCED_FILE = OUT_DIR / "covariate_balanced_twfe_results.csv"

FIREARM_SUICIDE = "firearm_suicide_rate_per_100k"


def _one_row(table: pd.DataFrame) -> pd.Series:
    rows = table.loc[table["outcome"].eq(FIREARM_SUICIDE)]
    if rows.empty:
        raise ValueError(f"Missing firearm-suicide row for {FIREARM_SUICIDE}")
    return rows.iloc[0]


def format_p_value(value) -> str:
    value = float(value)
    if value < 0.001:
        return "$<0.001$"
    return f"{value:.3f}"


def build_firearm_suicide_robustness_rows(
    twfe: pd.DataFrame,
    fractional: pd.DataFrame,
    stacked: pd.DataFrame,
    balanced: pd.DataFrame,
) -> pd.DataFrame:
    twfe_row = _one_row(twfe)
    fractional_row = _one_row(fractional)
    stacked_row = _one_row(stacked)
    balanced_row = _one_row(balanced)
    return pd.DataFrame(
        [
            {
                "specification": "Binary TWFE",
                "estimate": twfe_row["coef_post_permitless"],
                "se": twfe_row["se_post_permitless"],
                "p_value": twfe_row["p_post_permitless"],
                "nobs": twfe_row["nobs"],
                "interpretation": "Headline annual treatment coding",
            },
            {
                "specification": "Fractional-year TWFE",
                "estimate": fractional_row["coef_fractional_post_permitless"],
                "se": fractional_row["se_fractional_post_permitless"],
                "p_value": fractional_row["p_fractional_post_permitless"],
                "nobs": fractional_row["nobs"],
                "interpretation": "Effective-year exposure prorated by law date",
            },
            {
                "specification": "Stacked DiD",
                "estimate": stacked_row["coef_stacked_treatment"],
                "se": stacked_row["se_stacked_treatment"],
                "p_value": stacked_row["p_stacked_treatment"],
                "nobs": stacked_row["nobs"],
                "interpretation": "Cohort stacks with not-yet-treated controls",
            },
            {
                "specification": "Covariate-balanced TWFE",
                "estimate": balanced_row["coef_post_permitless"],
                "se": balanced_row["se_post_permitless"],
                "p_value": balanced_row["p_post_permitless"],
                "nobs": balanced_row["nobs"],
                "interpretation": "Non-adopters reweighted toward adopter covariates",
            },
        ]
    )


def build_latex_table(rows: pd.DataFrame) -> str:
    body = []
    for row in rows.itertuples(index=False):
        body.append(
            " & ".join(
                [
                    str(row.specification),
                    f"{float(row.estimate):.3f}",
                    f"{float(row.se):.3f}",
                    format_p_value(row.p_value),
                    f"{int(float(row.nobs))}",
                    str(row.interpretation),
                ]
            )
            + r" \\"
        )
    body_text = "\n".join(body)
    return rf"""\begin{{table}}[H]
\centering
\caption{{\textbf{{Primary firearm-suicide robustness estimates.}}}}
\label{{tab:main_robustness}}
\begin{{threeparttable}}
\small
\begin{{tabular}}{{@{{}}p{{0.24\linewidth}}rrrrp{{0.31\linewidth}}@{{}}}}
\toprule
Specification & Estimate & SE & $p$ & N & Interpretation \\
\midrule
{body_text}
\bottomrule
\end{{tabular}}
\begin{{tablenotes}}
\small
\item Estimates are deaths per 100,000 residents. All rows estimate the firearm-suicide outcome. TWFE rows include state and year fixed effects, unemployment, per-capita income, and state-clustered standard errors. The stacked DiD row uses 5-year pre/post cohort stacks with not-yet-treated controls.
\end{{tablenotes}}
\end{{threeparttable}}
\end{{table}}
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    rows = build_firearm_suicide_robustness_rows(
        pd.read_csv(TWFE_FILE),
        pd.read_csv(FRACTIONAL_FILE),
        pd.read_csv(STACKED_FILE),
        pd.read_csv(BALANCED_FILE),
    )
    rows.to_csv(CSV_FILE, index=False)
    TEX_FILE.write_text(build_latex_table(rows), encoding="utf-8")
    print(f"Wrote: {CSV_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {TEX_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
