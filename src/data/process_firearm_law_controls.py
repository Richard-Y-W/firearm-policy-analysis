from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = (
    ROOT
    / "data"
    / "raw"
    / "firearm_laws"
    / "tufts_state_firearm_law_database_1976_2024.xlsx"
)
PROCESSED_FILE = (
    ROOT
    / "data"
    / "processed"
    / "state_year_firearm_law_controls_1999_2024.csv"
)

FIREARM_LAW_CONTROL_COLUMNS = [
    "permit_to_purchase",
    "waiting_period",
    "universal_background_check",
    "erpo_red_flag",
    "safe_storage",
    "stand_your_ground",
    "dealer_license",
]

TUFTS_SOURCE_COLUMNS = [
    "state",
    "year",
    "permit",
    "permith",
    "waiting",
    "waitingh",
    "universal",
    "universalh",
    "universalpermit",
    "universalpermith",
    "gvro",
    "gvrolawenforcement",
    "locked",
    "nosyg",
    "dealer",
    "dealerh",
]


def _max_binary(row: pd.DataFrame, columns: list[str]) -> pd.Series:
    return row[columns].astype(int).max(axis=1)


def build_firearm_law_controls(
    raw: pd.DataFrame,
    *,
    start_year: int = 1999,
    end_year: int = 2024,
) -> pd.DataFrame:
    missing = [col for col in TUFTS_SOURCE_COLUMNS if col not in raw.columns]
    if missing:
        raise ValueError(f"Tufts firearm-law database missing columns: {missing}")

    data = raw[TUFTS_SOURCE_COLUMNS].copy()
    data = data.rename(columns={"state": "State", "year": "Year"})
    data = data.loc[data["Year"].between(start_year, end_year)].copy()

    for col in TUFTS_SOURCE_COLUMNS:
        if col in {"state", "year"}:
            continue
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0).astype(int)

    out = data[["State", "Year"]].copy()
    out["permit_to_purchase"] = _max_binary(data, ["permit", "permith"])
    out["waiting_period"] = _max_binary(data, ["waiting", "waitingh"])
    out["universal_background_check"] = _max_binary(
        data,
        ["universal", "universalh", "universalpermit", "universalpermith"],
    )
    out["erpo_red_flag"] = _max_binary(data, ["gvro", "gvrolawenforcement"])
    out["safe_storage"] = data["locked"].astype(int)
    out["stand_your_ground"] = 1 - data["nosyg"].astype(int)
    out["dealer_license"] = _max_binary(data, ["dealer", "dealerh"])

    out = out[["State", "Year"] + FIREARM_LAW_CONTROL_COLUMNS]
    out = out.sort_values(["State", "Year"]).reset_index(drop=True)
    return out


def validate_firearm_law_controls(controls: pd.DataFrame) -> pd.DataFrame:
    missing = [
        col
        for col in ["State", "Year"] + FIREARM_LAW_CONTROL_COLUMNS
        if col not in controls.columns
    ]
    if missing:
        raise ValueError(f"Firearm-law controls missing columns: {missing}")

    duplicate = controls.duplicated(["State", "Year"])
    if duplicate.any():
        dupes = controls.loc[duplicate, ["State", "Year"]].to_dict("records")
        raise ValueError(f"Firearm-law controls duplicate state-year rows: {dupes}")

    years = sorted(controls["Year"].dropna().astype(int).unique())
    if years != list(range(1999, 2025)):
        raise ValueError(
            "Firearm-law controls must cover every year from 1999 through 2024"
        )

    n_states = controls["State"].nunique()
    if n_states != 50:
        raise ValueError(f"Firearm-law controls must cover 50 states, found {n_states}")

    for col in FIREARM_LAW_CONTROL_COLUMNS:
        values = set(pd.to_numeric(controls[col], errors="coerce").dropna().astype(int))
        if not values.issubset({0, 1}):
            raise ValueError(f"{col} must be binary 0/1, found {sorted(values)}")

    return controls.copy()


def main():
    raw = pd.read_excel(RAW_FILE, sheet_name="results")
    controls = build_firearm_law_controls(raw)
    controls = validate_firearm_law_controls(controls)
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    controls.to_csv(PROCESSED_FILE, index=False)
    print(f"Saved: {PROCESSED_FILE.relative_to(Path.cwd())}")
    print(f"Rows: {len(controls)}")
    print(f"States: {controls['State'].nunique()}")
    print(f"Years: {controls['Year'].min()} to {controls['Year'].max()}")


if __name__ == "__main__":
    main()
