import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "gun ownership"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "TL-354-State-Level Estimates of Household Firearm Ownership.xlsx"

VALID_STATES = {
    "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
    "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
    "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
    "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
    "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
    "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island",
    "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Vermont",
    "Virginia", "Washington", "West Virginia", "Wisconsin", "Wyoming"
}

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing file: {RAW_FILE}")

    df = pd.read_excel(RAW_FILE, sheet_name="State-Level Data & Factor Score")
    print("Columns:", df.columns.tolist())

    df = df.rename(columns={
        "STATE": "State",
        "Year": "Year",
        "HFR": "gun_ownership"
    })

    df = df[df["State"].isin(VALID_STATES)].copy()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["gun_ownership"] = pd.to_numeric(df["gun_ownership"], errors="coerce")

    df = df[(df["Year"] >= 1999) & (df["Year"] <= 2016)].copy()

    df = df[["State", "Year", "gun_ownership"]].sort_values(["State", "Year"]).reset_index(drop=True)

    out_file = PROCESSED_DIR / "state_year_gun_ownership_1999_2016.csv"
    df.to_csv(out_file, index=False)

    print(f"Saved: {out_file}")
    print(df.head())
    print(f"\nRows: {len(df)}")
    print(f"States: {df['State'].nunique()}")
    print(f"Year range: {df['Year'].min()} to {df['Year'].max()}")

if __name__ == "__main__":
    main()