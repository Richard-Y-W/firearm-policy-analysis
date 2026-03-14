import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
OUT_FILE = PROCESSED_DIR / "analysis_panel_master.csv"

def main():
    firearm = pd.read_csv(PROCESSED_DIR / "analysis_panel_firearm_suicide_deaths_1999_2024.csv")
    total_suicide = pd.read_csv(PROCESSED_DIR / "analysis_panel_total_suicide_deaths_1999_2024.csv")
    nonfirearm = pd.read_csv(PROCESSED_DIR / "analysis_panel_nonfirearm_suicide_deaths_1999_2024.csv")
    unemployment = pd.read_csv(PROCESSED_DIR / "state_year_unemployment_1999_2024.csv")
    income = pd.read_csv(PROCESSED_DIR / "state_year_income_1999_2024.csv")
    gun = pd.read_csv(PROCESSED_DIR / "state_year_gun_ownership_1999_2016.csv")
    rurality = pd.read_csv(PROCESSED_DIR / "state_rurality_baseline_2013.csv")
    politics = pd.read_csv(PROCESSED_DIR / "state_year_presidential_vote_share_2000_2020.csv")

    # Base panel from firearm suicide
    panel = firearm[[
        "State", "State Code", "Year", "Deaths", "Population", "rate_per_100k", "permitless_year"
    ]].copy().rename(columns={
        "Deaths": "firearm_suicide_deaths",
        "Population": "population",
        "rate_per_100k": "firearm_suicide_rate_per_100k"
    })

    # Merge total suicide
    total_suicide = total_suicide[[
        "State", "Year", "Deaths", "rate_per_100k"
    ]].copy().rename(columns={
        "Deaths": "total_suicide_deaths",
        "rate_per_100k": "total_suicide_rate_per_100k"
    })
    panel = panel.merge(total_suicide, on=["State", "Year"], how="left")

    # Merge non-firearm suicide
    nonfirearm = nonfirearm[[
        "State", "Year", "Deaths", "rate_per_100k"
    ]].copy().rename(columns={
        "Deaths": "nonfirearm_suicide_deaths",
        "rate_per_100k": "nonfirearm_suicide_rate_per_100k"
    })
    panel = panel.merge(nonfirearm, on=["State", "Year"], how="left")

    # Merge unemployment
    unemployment = unemployment.rename(columns={"unemployment_rate": "unemployment_rate"})
    panel = panel.merge(unemployment, on=["State", "Year"], how="left")

    # Merge income
    panel = panel.merge(income, on=["State", "Year"], how="left")

    # Merge gun ownership
    panel = panel.merge(gun, on=["State", "Year"], how="left")
    panel = panel.sort_values(["State","Year"])
    panel["gun_ownership"] = panel.groupby("State")["gun_ownership"].ffill()

    # Merge rurality
    panel = panel.merge(rurality, on="State", how="left")

    # Merge politics only on election years first
    panel = panel.merge(politics, on=["State", "Year"], how="left")

    # Forward-fill presidential vote share within state
    panel = panel.sort_values(["State", "Year"]).reset_index(drop=True)
    panel["rep_vote_share_2party"] = panel.groupby("State")["rep_vote_share_2party"].ffill()
    panel["rep_vote_share_2party"] = panel.groupby("State")["rep_vote_share_2party"].ffill()
    panel["rep_vote_share_2party"] = panel.groupby("State")["rep_vote_share_2party"].bfill()

    # Create treatment indicators
    panel["ever_adopter"] = panel["permitless_year"].notna().astype(int)
    panel["post_permitless"] = (
        panel["permitless_year"].notna() & (panel["Year"] >= panel["permitless_year"])
    ).astype(int)

    panel["years_since_permitless"] = panel["Year"] - panel["permitless_year"]

    # Keep nice order
    cols = [
        "State", "State Code", "Year",
        "population",
        "firearm_suicide_deaths", "firearm_suicide_rate_per_100k",
        "total_suicide_deaths", "total_suicide_rate_per_100k",
        "nonfirearm_suicide_deaths", "nonfirearm_suicide_rate_per_100k",
        "unemployment_rate", "income_pc", "gun_ownership",
        "mean_rucc_2013", "share_nonmetro_counties_2013",
        "rep_vote_share_2party",
        "permitless_year", "ever_adopter", "post_permitless", "years_since_permitless"
    ]
    VALID_STATES = {
        "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut",
        "Delaware","Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa",
        "Kansas","Kentucky","Louisiana","Maine","Maryland","Massachusetts","Michigan",
        "Minnesota","Mississippi","Missouri","Montana","Nebraska","Nevada",
        "New Hampshire","New Jersey","New Mexico","New York","North Carolina",
        "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island",
        "South Carolina","South Dakota","Tennessee","Texas","Utah","Vermont",
        "Virginia","Washington","West Virginia","Wisconsin","Wyoming"
        }

    panel = panel[panel["State"].isin(VALID_STATES)].copy()
    panel = panel[cols]

    panel.to_csv(OUT_FILE, index=False)

    print(f"Saved: {OUT_FILE}")
    print(panel.head())
    print(f"\nRows: {len(panel)}")
    print(f"States: {panel['State'].nunique()}")
    print(f"Years: {panel['Year'].min()} to {panel['Year'].max()}")

    print("\nMissing values by key variable:")
    key_vars = [
        "firearm_suicide_rate_per_100k",
        "total_suicide_rate_per_100k",
        "nonfirearm_suicide_rate_per_100k",
        "unemployment_rate",
        "income_pc",
        "gun_ownership",
        "mean_rucc_2013",
        "rep_vote_share_2party"
    ]
    print(panel[key_vars].isna().sum())

if __name__ == "__main__":
    main()