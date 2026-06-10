from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RAW_FILE = ROOT / "data" / "raw" / "nics" / "nics_firearm_checks_year_by_state_type.txt"
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
OUT_FILE = ROOT / "data" / "processed" / "state_year_nics_handgun_checks_1999_2021.csv"

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


def parse_header_positions(header_line: str) -> dict:
    handgun_positions = []
    start = 0
    while True:
        position = header_line.find("Handgun", start)
        if position < 0:
            break
        handgun_positions.append(position)
        start = position + 1
    if len(handgun_positions) < 2:
        raise ValueError("NICS header does not contain enough Handgun columns")

    positions = {
        "state": 0,
        "permit": header_line.index("Permit"),
        "recheck": header_line.index("Recheck"),
        "handgun": handgun_positions[0],
        "long_gun": header_line.index("Long Gun", handgun_positions[0]),
        "other": header_line.index("*Other"),
        "multiple": header_line.index("**Multiple"),
        "admin": header_line.index("Admin"),
        "prepawn_handgun": handgun_positions[1],
    }
    return positions


def _parse_int(text: str) -> int:
    cleaned = str(text).replace(",", "").strip()
    if not cleaned:
        return 0
    return int(cleaned)


def parse_nics_state_line(line: str, positions: dict) -> dict:
    state = line[: positions["permit"]].strip()
    if state not in VALID_STATES:
        raise ValueError(f"Not a 50-state NICS row: {state}")
    totals = re.findall(r"\d[\d,]*", line)
    total_checks = _parse_int(totals[-1]) if totals else 0
    return {
        "State": state,
        "permit_checks": _parse_int(line[positions["permit"] : positions["recheck"]]),
        "permit_recheck_checks": _parse_int(line[positions["recheck"] : positions["handgun"]]),
        "handgun_checks": _parse_int(line[positions["handgun"] : positions["long_gun"]]),
        "long_gun_checks": _parse_int(line[positions["long_gun"] : positions["other"]]),
        "other_checks": _parse_int(line[positions["other"] : positions["multiple"]]),
        "multiple_checks": _parse_int(line[positions["multiple"] : positions["admin"]]),
        "admin_checks": _parse_int(line[positions["admin"] : positions["prepawn_handgun"]]),
        "total_checks": total_checks,
    }


def parse_nics_text(text: str) -> pd.DataFrame:
    rows = []
    current_year = None
    positions = None
    for line in text.splitlines():
        year_match = re.search(r"\bYear\s+(\d{4})\b", line)
        if year_match:
            current_year = int(year_match.group(1))
            positions = None
            continue
        if current_year is None:
            continue
        if "State / Territory" in line and "Recheck" in line and "Handgun" in line:
            positions = parse_header_positions(line)
            continue
        if positions is None:
            continue
        state_name = line[: positions["permit"]].strip()
        if state_name in VALID_STATES:
            row = parse_nics_state_line(line, positions)
            row["Year"] = current_year
            rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def build_state_year_nics_panel(raw: pd.DataFrame, mortality_panel: pd.DataFrame) -> pd.DataFrame:
    use = raw.loc[raw["Year"].between(1999, 2021) & raw["State"].isin(VALID_STATES)].copy()
    use["handgun_or_permit_checks"] = use["handgun_checks"] + use["permit_checks"]
    pop = mortality_panel[["State", "Year", "population"]].drop_duplicates(["State", "Year"])
    out = use.merge(pop, on=["State", "Year"], how="left")
    out["handgun_checks_per_100k"] = out["handgun_checks"] / out["population"] * 100000
    out["handgun_or_permit_checks_per_100k"] = (
        out["handgun_or_permit_checks"] / out["population"] * 100000
    )
    return out.sort_values(["State", "Year"]).reset_index(drop=True)


def main():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Missing NICS text export: {RAW_FILE}")
    text = RAW_FILE.read_text(errors="ignore")
    raw = parse_nics_text(text)
    panel = pd.read_csv(PANEL_FILE)
    out = build_state_year_nics_panel(raw, panel)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)
    print(f"Wrote: {OUT_FILE.relative_to(Path.cwd())}")
    print(f"Rows: {len(out)}")
    print(f"States: {out['State'].nunique()}")
    print(f"Years: {int(out['Year'].min())} to {int(out['Year'].max())}")


if __name__ == "__main__":
    main()
