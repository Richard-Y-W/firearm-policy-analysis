import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "unemployment"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "Unemployment in America Per US State.csv"

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

    df = pd.read_csv(RAW_FILE)

    print("Columns found:")
    print(df.columns.tolist())

    # Expected Kaggle/BLS-style column names
    state_col = "State/Area"
    year_col = "Year"
    month_col = "Month"
    rate_col = "Percent (%) of Labor Force Unemployed in State/Area"

    missing = [c for c in [state_col, year_col, month_col, rate_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns: {missing}")

    # Keep only 50 states
    df = df[df[state_col].isin(VALID_STATES)].copy()

    # Clean numeric fields
    df[rate_col] = (
        df[rate_col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df[rate_col] = pd.to_numeric(df[rate_col], errors="coerce")
    df[year_col] = pd.to_numeric(df[year_col], errors="coerce")
    df[month_col] = pd.to_numeric(df[month_col], errors="coerce")

    # Monthly -> annual average
    annual = (
        df.groupby([state_col, year_col], as_index=False)[rate_col]
        .mean()
        .rename(columns={
            state_col: "State",
            year_col: "Year",
            rate_col: "unemployment_rate"
        })
        .sort_values(["State", "Year"])
        .reset_index(drop=True)
    )

    annual = annual[(annual["Year"] >= 1999) & (annual["Year"] <= 2024)].copy()

    out_file = PROCESSED_DIR / "state_year_unemployment_1999_2024.csv"
    annual.to_csv(out_file, index=False)

    print(f"Saved: {out_file}")
    print(annual.head())
    print(f"\nRows: {len(annual)}")
    print(f"States: {annual['State'].nunique()}")
    print(f"Year range: {annual['Year'].min()} to {annual['Year'].max()}")

if __name__ == "__main__":
    main()