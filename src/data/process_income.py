import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "income"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "SAINC1__ALL_AREAS_1929_2024.csv"

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

def clean_state_name(x: str) -> str:
    x = str(x).strip()
    x = x.replace("*", "")
    x = x.replace("(NA)", "")
    x = x.replace("  ", " ")
    return x.strip()

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing file: {RAW_FILE}")

    df = pd.read_csv(RAW_FILE)
    print("Columns found:")
    print(df.columns.tolist())

    df["GeoName"] = df["GeoName"].apply(clean_state_name)
    df["Description"] = df["Description"].astype(str).str.strip()

    target_desc = "Per capita personal income (dollars) 2/"
    df = df[df["Description"] == target_desc].copy()

    df = df[df["GeoName"].isin(VALID_STATES)].copy()

    year_cols = [str(y) for y in range(1999, 2025)]
    df = df[["GeoName"] + year_cols].copy()

    df = df.melt(
        id_vars=["GeoName"],
        value_vars=year_cols,
        var_name="Year",
        value_name="income_pc"
    )

    df = df.rename(columns={"GeoName": "State"})
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["income_pc"] = pd.to_numeric(df["income_pc"], errors="coerce")

    df = df.sort_values(["State", "Year"]).reset_index(drop=True)

    out_file = PROCESSED_DIR / "state_year_income_1999_2024.csv"
    df.to_csv(out_file, index=False)

    print(f"Saved: {out_file}")
    print(df.head())
    print(f"\nRows: {len(df)}")
    print(f"States: {df['State'].nunique()}")
    print(f"Year range: {df['Year'].min()} to {df['Year'].max()}")
    print("\nStates found:")
    print(sorted(df["State"].unique()))

if __name__ == "__main__":
    main()