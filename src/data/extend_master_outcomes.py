import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"

MASTER_FILE = PROCESSED_DIR / "analysis_panel_master.csv"
HOMICIDE_FILE = PROCESSED_DIR / "analysis_panel_firearm_homicide_deaths_1999_2024.csv"
TOTAL_FIREARM_FILE = PROCESSED_DIR / "analysis_panel_total_firearm_deaths_1999_2024.csv"
FIREARM_LAW_CONTROLS_FILE = PROCESSED_DIR / "state_year_firearm_law_controls_1999_2024.csv"
NONFIREARM_CONFOUNDERS_FILE = PROCESSED_DIR / "state_year_nonfirearm_confounders_2008_2024.csv"

OUT_FILE = PROCESSED_DIR / "analysis_panel_full_outcomes.csv"


def main():
    master = pd.read_csv(MASTER_FILE)
    homicide = pd.read_csv(HOMICIDE_FILE)
    total_firearm = pd.read_csv(TOTAL_FIREARM_FILE)
    firearm_laws = pd.read_csv(FIREARM_LAW_CONTROLS_FILE)
    nonfirearm_confounders = pd.read_csv(NONFIREARM_CONFOUNDERS_FILE)

    homicide = homicide.rename(columns={
        "Deaths": "firearm_homicide_deaths",
        "rate_per_100k": "firearm_homicide_rate_per_100k"
    })[["State", "State Code", "Year", "firearm_homicide_deaths", "firearm_homicide_rate_per_100k"]]

    total_firearm = total_firearm.rename(columns={
        "Deaths": "total_firearm_deaths",
        "rate_per_100k": "total_firearm_rate_per_100k"
    })[["State", "State Code", "Year", "total_firearm_deaths", "total_firearm_rate_per_100k"]]

    full = master.merge(homicide, on=["State", "State Code", "Year"], how="left")
    full = full.merge(total_firearm, on=["State", "State Code", "Year"], how="left")
    full = full.merge(firearm_laws, on=["State", "Year"], how="left")
    full = full.merge(nonfirearm_confounders, on=["State", "Year"], how="left")

    full.to_csv(OUT_FILE, index=False)

    print(f"Saved: {OUT_FILE}")
    print(full.head())
    print(f"\nRows: {len(full)}")
    print(f"States: {full['State'].nunique()}")
    print(f"Years: {full['Year'].min()} to {full['Year'].max()}")

    key_vars = [
        "firearm_suicide_rate_per_100k",
        "nonfirearm_suicide_rate_per_100k",
        "total_suicide_rate_per_100k",
        "firearm_homicide_rate_per_100k",
        "total_firearm_rate_per_100k",
        "permit_to_purchase",
        "waiting_period",
        "universal_background_check",
        "erpo_red_flag",
        "safe_storage",
        "stand_your_ground",
        "dealer_license",
        "uninsured_under65_pct",
        "drug_overdose_rate_per_100k",
    ]
    print("\nMissing values:")
    print(full[key_vars].isna().sum())


if __name__ == "__main__":
    main()
