import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "cdc_wonder"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

TOTAL_OLD = RAW_DIR / "total_suicides_1999_2020.xls"
TOTAL_NEW = RAW_DIR / "total_suicides_2018_2024.xls"
FIREARM_SUICIDE_PANEL = PROCESSED_DIR / "analysis_panel_firearm_suicide_deaths_1999_2024.csv"


def read_wonder_export(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", engine="python", dtype=str)
    df.columns = [c.strip().strip('"') for c in df.columns]

    # Keep real state rows only
    df = df[df["State"].notna() & (df["State"] != "---")].copy()

    for c in ["Notes", "State", "State Code", "Year", "Year Code", "Deaths", "Population"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.strip('"')

    # Remove total rows if present
    if "Notes" in df.columns:
        df = df[~df["Notes"].fillna("").str.strip().eq("Total")].copy()

    # Numeric conversion
    for c in ["State Code", "Year", "Year Code", "Deaths", "Population"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Drop bad rows
    df = df.dropna(subset=["State", "State Code", "Year", "Deaths", "Population"]).copy()

    # Recompute rate for consistency
    df["rate_per_100k"] = df["Deaths"] / df["Population"] * 100000

    return df[["State", "State Code", "Year", "Deaths", "Population", "rate_per_100k"]].copy()


def main():
    if not TOTAL_OLD.exists():
        raise FileNotFoundError(f"Missing file: {TOTAL_OLD}")
    if not TOTAL_NEW.exists():
        raise FileNotFoundError(f"Missing file: {TOTAL_NEW}")
    if not FIREARM_SUICIDE_PANEL.exists():
        raise FileNotFoundError(f"Missing file: {FIREARM_SUICIDE_PANEL}")

    old = read_wonder_export(TOTAL_OLD)
    new = read_wonder_export(TOTAL_NEW)

    old["source"] = "WONDER_1999_2020"
    new = new[new["Year"] >= 2021].copy()
    new["source"] = "WONDER_2018_2024_single_race"

    total_panel = (
        pd.concat([old, new], ignore_index=True)
        .sort_values(["State", "Year"])
        .reset_index(drop=True)
    )

    # Bring in permitless year from existing firearm suicide panel
    firearm = pd.read_csv(FIREARM_SUICIDE_PANEL)
    permitless_map = firearm[["State", "permitless_year"]].drop_duplicates()

    total_panel = total_panel.merge(permitless_map, on="State", how="left")

    total_out = PROCESSED_DIR / "analysis_panel_total_suicide_deaths_1999_2024.csv"
    total_panel.to_csv(total_out, index=False)

    # Build non-firearm suicide panel
    firearm_subset = firearm[
        ["State", "State Code", "Year", "Deaths", "Population", "rate_per_100k", "source", "permitless_year"]
    ].copy()

    merged = total_panel.merge(
        firearm_subset,
        on=["State", "State Code", "Year"],
        how="inner",
        suffixes=("_total_suicide", "_firearm_suicide"),
    )

    merged["Deaths"] = merged["Deaths_total_suicide"] - merged["Deaths_firearm_suicide"]
    merged["Population"] = merged["Population_total_suicide"]
    merged["rate_per_100k"] = (
        merged["rate_per_100k_total_suicide"] - merged["rate_per_100k_firearm_suicide"]
    )
    merged["source"] = "derived_total_minus_firearm"
    merged["permitless_year"] = merged["permitless_year_total_suicide"]

    nonfirearm_panel = merged[
        ["State", "State Code", "Year", "Deaths", "Population", "rate_per_100k", "source", "permitless_year"]
    ].copy()

    nonfirearm_out = PROCESSED_DIR / "analysis_panel_nonfirearm_suicide_deaths_1999_2024.csv"
    nonfirearm_panel.to_csv(nonfirearm_out, index=False)

    print(f"Saved: {total_out}")
    print(f"Saved: {nonfirearm_out}")
    print("\nTotal suicide panel preview:")
    print(total_panel.head())
    print("\nNon-firearm suicide panel preview:")
    print(nonfirearm_panel.head())


if __name__ == "__main__":
    main()