from io import BytesIO
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen
import zipfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FILE = (
    ROOT
    / "data"
    / "processed"
    / "state_year_nonfirearm_confounders_2008_2024.csv"
)

VALID_STATES = {
    "Alabama",
    "Alaska",
    "Arizona",
    "Arkansas",
    "California",
    "Colorado",
    "Connecticut",
    "Delaware",
    "Florida",
    "Georgia",
    "Hawaii",
    "Idaho",
    "Illinois",
    "Indiana",
    "Iowa",
    "Kansas",
    "Kentucky",
    "Louisiana",
    "Maine",
    "Maryland",
    "Massachusetts",
    "Michigan",
    "Minnesota",
    "Mississippi",
    "Missouri",
    "Montana",
    "Nebraska",
    "Nevada",
    "New Hampshire",
    "New Jersey",
    "New Mexico",
    "New York",
    "North Carolina",
    "North Dakota",
    "Ohio",
    "Oklahoma",
    "Oregon",
    "Pennsylvania",
    "Rhode Island",
    "South Carolina",
    "South Dakota",
    "Tennessee",
    "Texas",
    "Utah",
    "Vermont",
    "Virginia",
    "Washington",
    "West Virginia",
    "Wisconsin",
    "Wyoming",
}

SAHIE_BASE_URL = (
    "https://www2.census.gov/programs-surveys/sahie/datasets/"
    "time-series/estimates-acs/sahie-{year}-csv.zip"
)
CDC_STATE_INJURY_ENDPOINT = "https://data.cdc.gov/resource/fpsi-y8tj.json"


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def build_sahie_uninsured_controls(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=["State", "Year", "uninsured_under65_pct"])

    raw = pd.concat(frames, ignore_index=True)
    required = [
        "year",
        "countyfips",
        "geocat",
        "agecat",
        "racecat",
        "sexcat",
        "iprcat",
        "PCTUI",
        "state_name",
    ]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"SAHIE data missing columns: {missing}")

    state_total = raw.loc[
        (_numeric(raw["countyfips"]).eq(0))
        & (_numeric(raw["geocat"]).eq(40))
        & (_numeric(raw["agecat"]).eq(0))
        & (_numeric(raw["racecat"]).eq(0))
        & (_numeric(raw["sexcat"]).eq(0))
        & (_numeric(raw["iprcat"]).eq(0))
    ].copy()
    out = pd.DataFrame(
        {
            "State": state_total["state_name"].astype(str).str.strip(),
            "Year": _numeric(state_total["year"]).astype("Int64"),
            "uninsured_under65_pct": _numeric(state_total["PCTUI"]),
        }
    )
    out = out.loc[out["State"].isin(VALID_STATES)].copy()
    out = out.dropna(subset=["Year", "uninsured_under65_pct"])
    out["Year"] = out["Year"].astype(int)
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def build_drug_overdose_controls(raw: pd.DataFrame) -> pd.DataFrame:
    required = ["name", "period", "intent", "rate"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"CDC overdose data missing columns: {missing}")

    data = raw.loc[
        raw["intent"].astype(str).eq("Drug_OD")
        & raw["period"].astype(str).str.fullmatch(r"\d{4}")
    ].copy()
    out = pd.DataFrame(
        {
            "State": data["name"].astype(str).str.strip(),
            "Year": _numeric(data["period"]).astype("Int64"),
            "drug_overdose_rate_per_100k": _numeric(data["rate"]),
        }
    )
    out = out.loc[out["State"].isin(VALID_STATES)].copy()
    out = out.dropna(subset=["Year", "drug_overdose_rate_per_100k"])
    out["Year"] = out["Year"].astype(int)
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def fetch_sahie_year(year: int) -> pd.DataFrame:
    url = SAHIE_BASE_URL.format(year=year)
    with urlopen(url, timeout=60) as response:
        payload = response.read()
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        csv_name = next(name for name in archive.namelist() if name.endswith(".csv"))
        with archive.open(csv_name) as file_obj:
            lines = file_obj.read().decode("latin1").splitlines()
        header_index = next(
            i for i, line in enumerate(lines) if line.startswith("year,")
        )
        return pd.read_csv(
            BytesIO("\n".join(lines[header_index:]).encode("latin1")),
            low_memory=False,
        )


def fetch_cdc_drug_overdose() -> pd.DataFrame:
    query = urlencode(
        {
            "$select": "name,period,intent,rate,count_sup",
            "$where": "intent='Drug_OD'",
            "$limit": "5000",
        }
    )
    with urlopen(f"{CDC_STATE_INJURY_ENDPOINT}?{query}", timeout=30) as response:
        return pd.read_json(response)


def build_nonfirearm_confounders(
    uninsured: pd.DataFrame,
    overdose: pd.DataFrame,
) -> pd.DataFrame:
    years = range(2008, 2025)
    skeleton = pd.MultiIndex.from_product(
        [sorted(VALID_STATES), years],
        names=["State", "Year"],
    ).to_frame(index=False)
    out = skeleton.merge(uninsured, on=["State", "Year"], how="left")
    out = out.merge(overdose, on=["State", "Year"], how="left")
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def validate_nonfirearm_confounders(table: pd.DataFrame) -> pd.DataFrame:
    required = [
        "State",
        "Year",
        "uninsured_under65_pct",
        "drug_overdose_rate_per_100k",
    ]
    missing = [col for col in required if col not in table.columns]
    if missing:
        raise ValueError(f"Non-firearm confounder table missing columns: {missing}")
    if table.duplicated(["State", "Year"]).any():
        raise ValueError("Non-firearm confounder table has duplicate state-year rows")
    if table["State"].nunique() != 50:
        raise ValueError("Non-firearm confounder table must include 50 states")
    if table["Year"].min() != 2008 or table["Year"].max() != 2024:
        raise ValueError("Non-firearm confounder table must cover 2008-2024")
    return table.copy()


def main():
    sahie_frames = [fetch_sahie_year(year) for year in range(2008, 2024)]
    uninsured = build_sahie_uninsured_controls(sahie_frames)
    overdose = build_drug_overdose_controls(fetch_cdc_drug_overdose())
    confounders = build_nonfirearm_confounders(uninsured, overdose)
    confounders = validate_nonfirearm_confounders(confounders)
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    confounders.to_csv(PROCESSED_FILE, index=False)
    print(f"Saved: {PROCESSED_FILE.relative_to(Path.cwd())}")
    print(f"Rows: {len(confounders)}")
    print(f"States: {confounders['State'].nunique()}")
    print(f"Years: {confounders['Year'].min()} to {confounders['Year'].max()}")
    print("Missing values:")
    print(confounders[required_columns()].isna().sum())


def required_columns() -> list[str]:
    return ["uninsured_under65_pct", "drug_overdose_rate_per_100k"]


if __name__ == "__main__":
    main()
