import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CDC_DIR = ROOT / "data" / "raw" / "cdc_wonder"
OUT_DIR = ROOT / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PERMITLESS_ADOPTION = {
    "Alaska": 2003,
    "Arizona": 2010,
    "Wyoming": 2011,
    "Kansas": 2015,
    "Mississippi": 2015,
    "Maine": 2015,
    "West Virginia": 2016,
    "Idaho": 2016,
    "Missouri": 2017,
    "New Hampshire": 2017,
    "North Dakota": 2017,
    "South Dakota": 2019,
    "Kentucky": 2019,
    "Oklahoma": 2019,
    "Montana": 2021,
    "Iowa": 2021,
    "Tennessee": 2021,
    "Texas": 2021,
    "Utah": 2021,
    "Georgia": 2022,
    "Indiana": 2022,
    "Ohio": 2022,
    "Alabama": 2023,
    "Florida": 2023,
}

def read_wonder_export(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, sep="\t", engine="python", dtype=str)
    df.columns = [c.strip().strip('"') for c in df.columns]

    df = df[df["State"].notna() & (df["State"] != "---")].copy()

    for c in ["Notes", "State", "State Code", "Year", "Year Code"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip().str.strip('"')

    for c in ["State Code", "Year", "Year Code", "Deaths", "Population"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df[~df["Notes"].astype(str).str.strip().eq("Total")].copy()
    df["rate_per_100k"] = df["Deaths"] / df["Population"] * 100000

    return df[["State", "State Code", "Year", "Deaths", "Population", "rate_per_100k"]].copy()

def main():
    old_file = CDC_DIR / "firearm_homicide_1999_2020.xls"
    new_file = CDC_DIR / "firearm_homicide_2018_2024_single_race.xls"

    if not old_file.exists():
        raise FileNotFoundError(f"Missing file: {old_file}")
    if not new_file.exists():
        raise FileNotFoundError(f"Missing file: {new_file}")

    old = read_wonder_export(old_file)
    new = read_wonder_export(new_file)

    old["source"] = "WONDER_1999_2020"
    new = new[new["Year"] >= 2021].copy()
    new["source"] = "WONDER_2018_2024_single_race"

    panel = pd.concat([old, new], ignore_index=True).sort_values(["State", "Year"]).reset_index(drop=True)
    panel["permitless_year"] = panel["State"].map(PERMITLESS_ADOPTION)

    panel.to_csv(OUT_DIR / "analysis_panel_firearm_homicide_deaths_1999_2024.csv", index=False)

    adoption_df = pd.DataFrame(
        [{"State": k, "permitless_year": v} for k, v in PERMITLESS_ADOPTION.items()]
    ).sort_values(["permitless_year", "State"])
    adoption_df.to_csv(OUT_DIR / "permitless_adoption_years.csv", index=False)

    print("Saved:")
    print(OUT_DIR / "analysis_panel_firearm_homicide_deaths_1999_2024.csv")
    print(OUT_DIR / "permitless_adoption_years.csv")
    print(panel.head())

if __name__ == "__main__":
    main()
