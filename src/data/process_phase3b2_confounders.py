from __future__ import annotations

from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen
import json
import zipfile

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_FILE = (
    ROOT
    / "data"
    / "processed"
    / "state_year_phase3b2_confounders_2005_2024.csv"
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

FIPS_TO_STATE = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}

ACS_BASE_URL = "https://api.census.gov/data/{year}/acs/acs1"
POP_ESTIMATE_URLS = [
    "https://www2.census.gov/programs-surveys/popest/datasets/2000-2010/intercensal/state/st-est00int-alldata.csv",
    "https://www2.census.gov/programs-surveys/popest/datasets/2010-2019/state/detail/sc-est2019-alldata6.csv",
    "https://www2.census.gov/programs-surveys/popest/datasets/2020-2024/state/asrh/sc-est2024-alldata6.csv",
]
SAIPE_DATASET_URL = (
    "https://www2.census.gov/programs-surveys/saipe/datasets/"
    "{year}/{year}-state-and-county/est{yy}all.txt"
)
HRSA_BASE_URL = "https://data.hrsa.gov"

HRSA_AHRF_STATE_CSV_PATHS = [
    "/DataDownload/StaticDocuments/AHRF_SN_CSV_2022-2023.zip",
    "/DataDownload/StaticDocuments/AHRF%20SN%202023-2024%20CSV.zip",
    "/DataDownload/AHRF/AHRF_SN_2024-2025_CSV.zip",
]

UNDER18_COLUMNS = [
    "B01001_003E",
    "B01001_004E",
    "B01001_005E",
    "B01001_006E",
    "B01001_027E",
    "B01001_028E",
    "B01001_029E",
    "B01001_030E",
]
AGE_18_34_COLUMNS = [
    "B01001_007E",
    "B01001_008E",
    "B01001_009E",
    "B01001_010E",
    "B01001_011E",
    "B01001_012E",
    "B01001_031E",
    "B01001_032E",
    "B01001_033E",
    "B01001_034E",
    "B01001_035E",
    "B01001_036E",
]
AGE_35_64_COLUMNS = [
    "B01001_013E",
    "B01001_014E",
    "B01001_015E",
    "B01001_016E",
    "B01001_017E",
    "B01001_018E",
    "B01001_019E",
    "B01001_037E",
    "B01001_038E",
    "B01001_039E",
    "B01001_040E",
    "B01001_041E",
    "B01001_042E",
    "B01001_043E",
]
AGE_65PLUS_COLUMNS = [
    "B01001_020E",
    "B01001_021E",
    "B01001_022E",
    "B01001_023E",
    "B01001_024E",
    "B01001_025E",
    "B01001_044E",
    "B01001_045E",
    "B01001_046E",
    "B01001_047E",
    "B01001_048E",
    "B01001_049E",
]
ACS_AGE_COLUMNS = ["B01001_001E"] + UNDER18_COLUMNS + AGE_18_34_COLUMNS + AGE_35_64_COLUMNS + AGE_65PLUS_COLUMNS
ACS_RACE_COLUMNS = [
    "B03002_001E",
    "B03002_003E",
    "B03002_004E",
    "B03002_006E",
    "B03002_012E",
]


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace({".": pd.NA, "": pd.NA}), errors="coerce")


def _sum_columns(data: pd.DataFrame, columns: list[str]) -> pd.Series:
    return data[columns].apply(_numeric).sum(axis=1, min_count=1)


def _state_from_fips(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(2).map(FIPS_TO_STATE)


def _fetch_census_dataframe(url: str, params: dict[str, str]) -> pd.DataFrame:
    query = urlencode(params, safe=",:*")
    with urlopen(f"{url}?{query}", timeout=45) as response:
        payload = response.read()
    text = payload.decode("utf-8", errors="replace").strip()
    if not text.startswith("["):
        raise ValueError(f"Census API returned non-JSON response for {url}")
    rows = json.loads(text)
    return pd.DataFrame(rows[1:], columns=rows[0])


def fetch_acs_demographic_year(year: int) -> pd.DataFrame:
    url = ACS_BASE_URL.format(year=year)
    try:
        age = _fetch_census_dataframe(
            url,
            {
                "get": ",".join(["NAME"] + ACS_AGE_COLUMNS),
                "for": "state:*",
            },
        )
        race = _fetch_census_dataframe(
            url,
            {
                "get": ",".join(["NAME"] + ACS_RACE_COLUMNS),
                "for": "state:*",
            },
        )
    except (HTTPError, URLError, ValueError):
        return pd.DataFrame()
    merged = age.merge(race, on=["NAME", "state"], how="inner")
    merged["Year"] = year
    return merged


def fetch_saipe_poverty_year(year: int) -> pd.DataFrame:
    url = SAIPE_DATASET_URL.format(year=year, yy=str(year)[-2:])
    with urlopen(url, timeout=45) as response:
        lines = response.read().decode("latin1", errors="replace").splitlines()

    rows = []
    for line in lines:
        tokens = line.split()
        if len(tokens) < 6:
            continue
        state_fips, county_fips = tokens[0], tokens[1]
        if county_fips != "0":
            continue
        state = FIPS_TO_STATE.get(state_fips)
        if state is None:
            continue
        rows.append(
            {
                "NAME": state,
                "YEAR": year,
                "SAEPOVRTALL_PT": tokens[5],
                "state": state_fips,
            }
        )
    return pd.DataFrame(rows)


def fetch_population_estimate_demographic_file(url: str) -> pd.DataFrame:
    with urlopen(url, timeout=90) as response:
        payload = response.read()
    return pd.read_csv(BytesIO(payload), low_memory=False)


def _year_columns(raw: pd.DataFrame) -> list[str]:
    columns = []
    for col in raw.columns:
        if col.startswith("POPESTIMATE") and col.replace("POPESTIMATE", "").isdigit():
            year = int(col.replace("POPESTIMATE", ""))
            if 2005 <= year <= 2024:
                columns.append(col)
    return columns


def _estimate_column_to_year(column: str) -> int:
    return int(column.replace("POPESTIMATE", ""))


def _popest_count(
    data: pd.DataFrame,
    year_col: str,
    *,
    origin: int | None = None,
    race: int | None = None,
    ages: list[int] | None = None,
    age_weights: dict[int, float] | None = None,
) -> pd.DataFrame:
    d = data.copy()
    if origin is not None:
        d = d.loc[d["ORIGIN"].eq(origin)]
    if race is not None:
        d = d.loc[d["RACE"].eq(race)]
    age_col = "AGE" if "AGE" in d.columns else "AGEGRP"
    if ages is not None:
        d = d.loc[d[age_col].isin(ages)].copy()
    if age_weights:
        weights = d[age_col].map(age_weights).fillna(1.0)
        values = _numeric(d[year_col]) * weights
    else:
        values = _numeric(d[year_col])
    temp = pd.DataFrame({"State": d["State"], "value": values})
    return temp.groupby("State", as_index=False)["value"].sum()


def _ratio(
    numerator: pd.DataFrame,
    denominator: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    out = numerator.merge(denominator, on="State", how="left", suffixes=("_num", "_den"))
    out[column] = out["value_num"] / out["value_den"]
    return out[["State", column]]


def _modern_popest_rows(raw: pd.DataFrame, year_col: str) -> pd.DataFrame:
    base = raw.loc[(raw["SEX"].eq(0)) & (raw["STATE"].gt(0))].copy()
    base["State"] = _state_from_fips(base["STATE"])
    base = base.loc[base["State"].isin(VALID_STATES)].copy()

    denominator = _popest_count(base, year_col, origin=0, ages=list(range(0, 86)))
    rows = pd.DataFrame({"State": denominator["State"]})
    rows["Year"] = _estimate_column_to_year(year_col)

    for name, ages in [
        ("share_age_under18", list(range(0, 18))),
        ("share_age_18_34", list(range(18, 35))),
        ("share_age_35_64", list(range(35, 65))),
        ("share_age_65plus", list(range(65, 86))),
    ]:
        rows = rows.merge(
            _ratio(_popest_count(base, year_col, origin=0, ages=ages), denominator, name),
            on="State",
            how="left",
        )

    for name, race in [
        ("share_white_nonhispanic", 1),
        ("share_black_nonhispanic", 2),
        ("share_asian_nonhispanic", 4),
    ]:
        rows = rows.merge(
            _ratio(
                _popest_count(base, year_col, origin=1, race=race, ages=list(range(0, 86))),
                denominator,
                name,
            ),
            on="State",
            how="left",
        )

    rows = rows.merge(
        _ratio(
            _popest_count(base, year_col, origin=2, ages=list(range(0, 86))),
            denominator,
            "share_hispanic",
        ),
        on="State",
        how="left",
    )
    return rows


def _intercensal_popest_rows(raw: pd.DataFrame, year_col: str) -> pd.DataFrame:
    base = raw.loc[(raw["SEX"].eq(0)) & (raw["STATE"].gt(0))].copy()
    base["State"] = _state_from_fips(base["STATE"])
    base = base.loc[base["State"].isin(VALID_STATES)].copy()

    denominator = _popest_count(base, year_col, origin=0, race=0, ages=[0])
    rows = pd.DataFrame({"State": denominator["State"]})
    rows["Year"] = _estimate_column_to_year(year_col)

    age_specs = [
        ("share_age_under18", [1, 2, 3, 4], {4: 0.6}),
        ("share_age_18_34", [4, 5, 6, 7], {4: 0.4}),
        ("share_age_35_64", list(range(8, 14)), None),
        ("share_age_65plus", list(range(14, 19)), None),
    ]
    for name, ages, weights in age_specs:
        rows = rows.merge(
            _ratio(
                _popest_count(
                    base,
                    year_col,
                    origin=0,
                    race=0,
                    ages=ages,
                    age_weights=weights,
                ),
                denominator,
                name,
            ),
            on="State",
            how="left",
        )

    for name, race in [
        ("share_white_nonhispanic", 1),
        ("share_black_nonhispanic", 2),
        ("share_asian_nonhispanic", 4),
    ]:
        rows = rows.merge(
            _ratio(
                _popest_count(base, year_col, origin=1, race=race, ages=[0]),
                denominator,
                name,
            ),
            on="State",
            how="left",
        )

    rows = rows.merge(
        _ratio(
            _popest_count(base, year_col, origin=2, race=0, ages=[0]),
            denominator,
            "share_hispanic",
        ),
        on="State",
        how="left",
    )
    return rows


def build_population_estimate_demographic_controls(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for raw in [frame for frame in frames if frame is not None and not frame.empty]:
        required = ["STATE", "NAME", "SEX", "ORIGIN", "RACE"]
        age_col = "AGE" if "AGE" in raw.columns else "AGEGRP" if "AGEGRP" in raw.columns else None
        missing = [col for col in required if col not in raw.columns]
        if age_col is None:
            missing.append("AGE or AGEGRP")
        if missing:
            raise ValueError(f"Census population estimate data missing columns: {missing}")

        for year_col in _year_columns(raw):
            if age_col == "AGE":
                rows.append(_modern_popest_rows(raw, year_col))
            else:
                rows.append(_intercensal_popest_rows(raw, year_col))

    if not rows:
        return pd.DataFrame(
            columns=[
                "State",
                "Year",
                "share_age_under18",
                "share_age_18_34",
                "share_age_35_64",
                "share_age_65plus",
                "share_white_nonhispanic",
                "share_black_nonhispanic",
                "share_asian_nonhispanic",
                "share_hispanic",
            ]
        )

    out = pd.concat(rows, ignore_index=True)
    out = out.sort_values(["State", "Year"]).drop_duplicates(["State", "Year"], keep="last")
    return out.reset_index(drop=True)


def fetch_hrsa_ahrf_state_release(path: str) -> pd.DataFrame:
    with urlopen(f"{HRSA_BASE_URL}{path}", timeout=90) as response:
        payload = response.read()
    with zipfile.ZipFile(BytesIO(payload)) as archive:
        csv_name = next(name for name in archive.namelist() if name.lower().endswith(".csv"))
        with archive.open(csv_name) as file_obj:
            return pd.read_csv(file_obj, low_memory=False)


def build_acs_demographic_controls(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame(
            columns=[
                "State",
                "Year",
                "share_age_under18",
                "share_age_18_34",
                "share_age_35_64",
                "share_age_65plus",
                "share_white_nonhispanic",
                "share_black_nonhispanic",
                "share_asian_nonhispanic",
                "share_hispanic",
            ]
        )

    raw = pd.concat(frames, ignore_index=True)
    required = ["NAME", "Year", "state"] + ACS_AGE_COLUMNS + ACS_RACE_COLUMNS
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"ACS demographic data missing columns: {missing}")

    total_age = _numeric(raw["B01001_001E"])
    total_race = _numeric(raw["B03002_001E"])
    out = pd.DataFrame(
        {
            "State": raw["NAME"].astype(str).str.strip(),
            "Year": _numeric(raw["Year"]).astype("Int64"),
            "share_age_under18": _sum_columns(raw, UNDER18_COLUMNS) / total_age,
            "share_age_18_34": _sum_columns(raw, AGE_18_34_COLUMNS) / total_age,
            "share_age_35_64": _sum_columns(raw, AGE_35_64_COLUMNS) / total_age,
            "share_age_65plus": _sum_columns(raw, AGE_65PLUS_COLUMNS) / total_age,
            "share_white_nonhispanic": _numeric(raw["B03002_003E"]) / total_race,
            "share_black_nonhispanic": _numeric(raw["B03002_004E"]) / total_race,
            "share_asian_nonhispanic": _numeric(raw["B03002_006E"]) / total_race,
            "share_hispanic": _numeric(raw["B03002_012E"]) / total_race,
        }
    )
    out = out.loc[out["State"].isin(VALID_STATES)].copy()
    out = out.dropna(subset=["Year"])
    out["Year"] = out["Year"].astype(int)
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def build_saipe_poverty_controls(frames: list[pd.DataFrame]) -> pd.DataFrame:
    frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not frames:
        return pd.DataFrame(columns=["State", "Year", "poverty_rate"])

    raw = pd.concat(frames, ignore_index=True)
    required = ["NAME", "YEAR", "SAEPOVRTALL_PT"]
    missing = [col for col in required if col not in raw.columns]
    if missing:
        raise ValueError(f"SAIPE poverty data missing columns: {missing}")

    out = pd.DataFrame(
        {
            "State": raw["NAME"].astype(str).str.strip(),
            "Year": _numeric(raw["YEAR"]).astype("Int64"),
            "poverty_rate": _numeric(raw["SAEPOVRTALL_PT"]),
        }
    )
    out = out.loc[out["State"].isin(VALID_STATES)].copy()
    out = out.dropna(subset=["Year", "poverty_rate"])
    out["Year"] = out["Year"].astype(int)
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def _provider_years(columns: list[str]) -> list[int]:
    years = []
    for col in columns:
        if col.startswith("psychol_") and col.rsplit("_", 1)[-1].isdigit():
            suffix = col.rsplit("_", 1)[-1]
            year = 2000 + int(suffix)
            if all(f"{prefix}_{suffix}" in columns for prefix in ["conslrs", "socwk", "popn_pums"]):
                years.append(year)
    return sorted(set(years))


def build_hrsa_mental_health_provider_controls(frames: list[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for raw in [frame for frame in frames if frame is not None and not frame.empty]:
        columns = list(raw.columns)
        if "fips_st" not in columns:
            raise ValueError("HRSA AHRF state data missing column: fips_st")
        for year in _provider_years(columns):
            suffix = str(year - 2000).zfill(2)
            count_cols = [f"psychol_{suffix}", f"conslrs_{suffix}", f"socwk_{suffix}"]
            pop_col = f"popn_pums_{suffix}"
            temp = pd.DataFrame(
                {
                    "State": _state_from_fips(raw["fips_st"]),
                    "Year": year,
                    "mental_health_provider_count": _sum_columns(raw, count_cols),
                    "mental_health_access_population": _numeric(raw[pop_col]),
                }
            )
            temp["mental_health_provider_rate_per_100k"] = (
                temp["mental_health_provider_count"]
                / temp["mental_health_access_population"]
                * 100000
            ).round(6)
            rows.append(temp)

    if not rows:
        return pd.DataFrame(
            columns=[
                "State",
                "Year",
                "mental_health_provider_count",
                "mental_health_access_population",
                "mental_health_provider_rate_per_100k",
            ]
        )

    out = pd.concat(rows, ignore_index=True)
    out = out.loc[out["State"].isin(VALID_STATES)].copy()
    out = out.dropna(subset=["Year", "mental_health_provider_rate_per_100k"])
    out["Year"] = out["Year"].astype(int)
    out = out.sort_values(["State", "Year"]).drop_duplicates(["State", "Year"], keep="last")
    return out.reset_index(drop=True)


def build_phase3b2_confounders(
    demographics: pd.DataFrame,
    poverty: pd.DataFrame,
    providers: pd.DataFrame,
    *,
    states: list[str] | None = None,
    years: list[int] | range | None = None,
) -> pd.DataFrame:
    states = sorted(VALID_STATES if states is None else states)
    years = list(range(2005, 2025) if years is None else years)
    skeleton = pd.MultiIndex.from_product(
        [states, years],
        names=["State", "Year"],
    ).to_frame(index=False)

    out = skeleton.merge(demographics, on=["State", "Year"], how="left")
    out = out.merge(poverty, on=["State", "Year"], how="left")
    out = out.merge(providers, on=["State", "Year"], how="left")

    demographic_poverty_columns = [
        "share_age_18_34",
        "share_age_35_64",
        "share_age_65plus",
        "share_black_nonhispanic",
        "share_hispanic",
        "poverty_rate",
    ]
    full_columns = demographic_poverty_columns + [
        "mental_health_provider_rate_per_100k"
    ]
    out["phase3b2_demographic_poverty_complete"] = out[
        demographic_poverty_columns
    ].notna().all(axis=1)
    out["phase3b2_full_complete"] = out[full_columns].notna().all(axis=1)
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def validate_phase3b2_confounders(table: pd.DataFrame) -> pd.DataFrame:
    required = [
        "State",
        "Year",
        "share_age_18_34",
        "share_age_35_64",
        "share_age_65plus",
        "share_black_nonhispanic",
        "share_hispanic",
        "poverty_rate",
        "mental_health_provider_rate_per_100k",
        "phase3b2_demographic_poverty_complete",
        "phase3b2_full_complete",
    ]
    missing = [col for col in required if col not in table.columns]
    if missing:
        raise ValueError(f"Phase 3B2 confounder table missing columns: {missing}")
    if table.duplicated(["State", "Year"]).any():
        raise ValueError("Phase 3B2 confounder table has duplicate state-year rows")
    if table["State"].nunique() != 50:
        raise ValueError("Phase 3B2 confounder table must include 50 states")
    if table["Year"].min() != 2005 or table["Year"].max() != 2024:
        raise ValueError("Phase 3B2 confounder table must cover 2005-2024")
    return table.copy()


def main():
    demographic_frames = [
        fetch_population_estimate_demographic_file(url) for url in POP_ESTIMATE_URLS
    ]
    saipe_frames = [fetch_saipe_poverty_year(year) for year in range(2005, 2025)]
    hrsa_frames = [fetch_hrsa_ahrf_state_release(path) for path in HRSA_AHRF_STATE_CSV_PATHS]

    demographics = build_population_estimate_demographic_controls(demographic_frames)
    poverty = build_saipe_poverty_controls(saipe_frames)
    providers = build_hrsa_mental_health_provider_controls(hrsa_frames)
    confounders = build_phase3b2_confounders(demographics, poverty, providers)
    confounders = validate_phase3b2_confounders(confounders)

    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    confounders.to_csv(PROCESSED_FILE, index=False)
    print(f"Saved: {PROCESSED_FILE.relative_to(Path.cwd())}")
    print(f"Rows: {len(confounders)}")
    print(f"States: {confounders['State'].nunique()}")
    print(f"Years: {confounders['Year'].min()} to {confounders['Year'].max()}")
    print("Complete rows:")
    print(
        confounders[
            [
                "phase3b2_demographic_poverty_complete",
                "phase3b2_full_complete",
            ]
        ].sum()
    )


if __name__ == "__main__":
    main()
