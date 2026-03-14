import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "rurality"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "ruralurbancodes2013.xls"

STATE_ABBR_TO_NAME = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming"
}

def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing file: {RAW_FILE}")

    df = pd.read_excel(RAW_FILE)
    print("Columns found:")
    print(df.columns.tolist())

    # Standard USDA RUCC 2013 file usually has columns like:
    # State, County_Name, FIPS, RUCC_2013
    # but column names can vary a bit, so normalize
    df.columns = [str(c).strip() for c in df.columns]

    # Try common column patterns
    state_col = None
    rucc_col = None

    for c in df.columns:
        cl = c.lower()
        if cl in ["state", "st", "state postal code"]:
            state_col = c
        if "rucc" in cl:
            rucc_col = c

    if state_col is None:
        raise ValueError(f"Could not identify state column from: {df.columns.tolist()}")
    if rucc_col is None:
        raise ValueError(f"Could not identify RUCC column from: {df.columns.tolist()}")

    df = df[[state_col, rucc_col]].copy()
    df = df.rename(columns={state_col: "state_raw", rucc_col: "rucc_2013"})

    df["state_raw"] = df["state_raw"].astype(str).str.strip()
    df["rucc_2013"] = pd.to_numeric(df["rucc_2013"], errors="coerce")
    df = df.dropna(subset=["state_raw", "rucc_2013"]).copy()

    # Convert abbreviations to full state names if needed
    df["State"] = df["state_raw"].map(STATE_ABBR_TO_NAME).fillna(df["state_raw"])

    # Keep only 50 states
    df = df[df["State"].isin(STATE_ABBR_TO_NAME.values())].copy()

    state_rurality = (
        df.groupby("State", as_index=False)
        .agg(
            mean_rucc_2013=("rucc_2013", "mean"),
            share_nonmetro_counties_2013=("rucc_2013", lambda x: (x >= 4).mean())
        )
        .sort_values("State")
        .reset_index(drop=True)
    )

    out_file = PROCESSED_DIR / "state_rurality_baseline_2013.csv"
    state_rurality.to_csv(out_file, index=False)

    print(f"Saved: {out_file}")
    print(state_rurality.head())
    print(f"\nRows: {len(state_rurality)}")
    print(f"States: {state_rurality['State'].nunique()}")

if __name__ == "__main__":
    main()