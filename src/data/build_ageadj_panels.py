"""
Build age-adjusted outcome panels from CDC WONDER exports.

These panels are sensitivity checks alongside the primary crude-rate models.
Age adjustment uses the 2000 U.S. Standard Population (as supplied by WONDER).
"Unreliable" cells (<=9 deaths) are set to NaN.
"""
import pandas as pd
from pathlib import Path

try:
    from src.data.permitless_policy import PERMITLESS_ADOPTION
except ModuleNotFoundError:
    from permitless_policy import PERMITLESS_ADOPTION

ROOT = Path(__file__).resolve().parents[2]
CDC_DIR = ROOT / "data" / "raw" / "cdc_wonder"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (old_file, new_file, output_stem, output_col_prefix)
OUTCOMES = [
    (
        "firearm_suicide_1999_2020_ageadj.xls",
        "firearm_suicide_2018_2024_ageadj.xls",
        "analysis_panel_firearm_suicide_ageadj_1999_2024.csv",
        "firearm_suicide",
    ),
    (
        "total_suicide_1999_2020_ageadj.xls",
        "total_suicide_2018_2024_ageadj.xls",
        "analysis_panel_total_suicide_ageadj_1999_2024.csv",
        "total_suicide",
    ),
    (
        "total_firearm_1999_2020_ageadj.xls",
        "total_firearm_2018_2024_ageadj.xls",
        "analysis_panel_total_firearm_ageadj_1999_2024.csv",
        "total_firearm",
    ),
    (
        "firearm_homicide_1999_2020_ageadj.xls",
        "firearm_homicide_2018_2024_ageadj.xls",
        "analysis_panel_firearm_homicide_ageadj_1999_2024.csv",
        "firearm_homicide",
    ),
]


def _parse_rate(series: pd.Series) -> pd.Series:
    """Convert CDC WONDER rate column to float; Suppressed/Unreliable -> NaN."""
    cleaned = series.astype(str).str.strip().str.strip('"')
    cleaned = cleaned.replace({"Suppressed": None, "Unreliable": None,
                               "Not Applicable": None, "Missing": None, "nan": None})
    return pd.to_numeric(cleaned, errors="coerce")


def read_wonder_ageadj(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", engine="python", dtype=str)
    df.columns = [c.strip().strip('"') for c in df.columns]

    # Drop notes rows (Total aggregates and footer lines)
    df = df[df["State"].notna()].copy()
    df = df[~df["Notes"].fillna("").astype(str).str.strip().eq("Total")].copy()
    df = df[~df["State"].astype(str).str.strip().str.startswith("Total")].copy()

    for col in ["State", "State Code", "Year"]:
        df[col] = df[col].astype(str).str.strip().str.strip('"')

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Deaths"] = pd.to_numeric(
        df["Deaths"].astype(str).str.strip().str.strip('"'), errors="coerce"
    )
    df["Population"] = pd.to_numeric(
        df["Population"].astype(str).str.strip().str.strip('"'), errors="coerce"
    )
    df["crude_rate_wonder"] = _parse_rate(df["Crude Rate"])
    df["ageadj_rate_per_100k"] = _parse_rate(df["Age Adjusted Rate"])

    df = df.dropna(subset=["State", "Year"]).copy()

    return df[["State", "State Code", "Year", "Deaths", "Population",
               "crude_rate_wonder", "ageadj_rate_per_100k"]].copy()


def build_panel(old_path: Path, new_path: Path) -> pd.DataFrame:
    old = read_wonder_ageadj(old_path)
    new = read_wonder_ageadj(new_path)

    old["source"] = "WONDER_1999_2020"
    new = new[new["Year"] >= 2021].copy()
    new["source"] = "WONDER_2018_2024_age_adjusted"

    panel = (
        pd.concat([old, new], ignore_index=True)
        .sort_values(["State", "Year"])
        .reset_index(drop=True)
    )
    panel["permitless_year"] = panel["State"].map(PERMITLESS_ADOPTION)
    return panel


def main():
    for old_name, new_name, out_name, prefix in OUTCOMES:
        old_path = CDC_DIR / old_name
        new_path = CDC_DIR / new_name

        if not old_path.exists():
            raise FileNotFoundError(f"Missing: {old_path}")
        if not new_path.exists():
            raise FileNotFoundError(f"Missing: {new_path}")

        panel = build_panel(old_path, new_path)

        n_total = len(panel)
        n_missing_ageadj = panel["ageadj_rate_per_100k"].isna().sum()
        n_states = panel["State"].nunique()
        years = f"{int(panel['Year'].min())}-{int(panel['Year'].max())}"

        out_path = OUT_DIR / out_name
        panel.to_csv(out_path, index=False)

        print(f"[{prefix}] saved {out_path.name}")
        print(f"  rows={n_total}, states={n_states}, years={years}")
        print(f"  ageadj NaN (Unreliable/Suppressed): {n_missing_ageadj} / {n_total}")


if __name__ == "__main__":
    main()
