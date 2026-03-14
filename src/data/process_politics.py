import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "politics"
PROCESSED_DIR = ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = RAW_DIR / "1976-2020-president.csv"

STATE_PO_TO_NAME = {
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

    df = pd.read_csv(RAW_FILE)
    print("Columns found:")
    print(df.columns.tolist())

    # Keep presidential election years relevant to your study
    df = df[(df["year"] >= 2000) & (df["year"] <= 2020)].copy()

    # Use postal abbreviation column, not the raw state field
    df["state_po"] = df["state_po"].astype(str).str.strip().str.upper()
    df = df[df["state_po"].isin(STATE_PO_TO_NAME.keys())].copy()

    # Keep only Democrat / Republican
    df["party_simplified"] = df["party_simplified"].astype(str).str.strip().str.upper()
    df = df[df["party_simplified"].isin(["DEMOCRAT", "REPUBLICAN"])].copy()

    # Sum votes within state-year-party
    grouped = (
        df.groupby(["state_po", "year", "party_simplified"], as_index=False)["candidatevotes"]
        .sum()
    )

    pivot = grouped.pivot_table(
        index=["state_po", "year"],
        columns="party_simplified",
        values="candidatevotes",
        fill_value=0
    ).reset_index()

    pivot.columns.name = None

    if "REPUBLICAN" not in pivot.columns:
        pivot["REPUBLICAN"] = 0
    if "DEMOCRAT" not in pivot.columns:
        pivot["DEMOCRAT"] = 0

    pivot["two_party_votes"] = pivot["REPUBLICAN"] + pivot["DEMOCRAT"]
    pivot["rep_vote_share_2party"] = pivot["REPUBLICAN"] / pivot["two_party_votes"]
    pivot["State"] = pivot["state_po"].map(STATE_PO_TO_NAME)
    pivot["Year"] = pivot["year"]

    out = pivot[["State", "Year", "rep_vote_share_2party"]].sort_values(["State", "Year"]).reset_index(drop=True)

    out_file = PROCESSED_DIR / "state_year_presidential_vote_share_2000_2020.csv"
    out.to_csv(out_file, index=False)

    print(f"Saved: {out_file}")
    print(out.head())
    print(f"\nRows: {len(out)}")
    print(f"States: {out['State'].nunique()}")
    print(f"Years: {sorted(out['Year'].unique())}")

if __name__ == "__main__":
    main()