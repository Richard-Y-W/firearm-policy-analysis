import pandas as pd

from src.analysis.nics_mechanism import run_nics_mechanism_models
from src.data.process_nics import parse_header_positions, parse_nics_state_line


def test_parse_nics_state_line_extracts_initial_handgun_and_permit_columns():
    header = (
        "    State / Territory   Permit        Recheck         Handgun        Long Gun"
        "         *Other      **Multiple      Admin       Handgun     Long Gun        *Other      Totals"
    )
    line = (
        "Alabama                   369,697          4,831        289,613"
        "        209,890         19,404        13,442            1          267"
        "           147            27      946,271"
    )
    positions = parse_header_positions(header)

    row = parse_nics_state_line(line, positions)

    assert row["State"] == "Alabama"
    assert row["permit_checks"] == 369697
    assert row["handgun_checks"] == 289613
    assert row["long_gun_checks"] == 209890
    assert row["total_checks"] == 946271


def test_run_nics_mechanism_models_estimates_handgun_proxy():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "Year": [2019, 2020] * 4,
            "post_permitless": [0, 1, 0, 1, 0, 0, 0, 0],
            "unemployment_rate": [4, 4, 5, 5, 6, 6, 7, 7],
            "income_pc": [10, 11, 12, 13, 14, 15, 16, 17],
        }
    )
    nics = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "Year": [2019, 2020] * 4,
            "handgun_checks_per_100k": [100, 150, 100, 130, 80, 82, 70, 71],
            "permit_checks_per_100k": [20, 5, 30, 10, 10, 10, 5, 5],
            "permit_recheck_checks_per_100k": [3, 1, 4, 1, 0, 0, 0, 0],
            "permit_and_recheck_checks_per_100k": [23, 6, 34, 11, 10, 10, 5, 5],
            "handgun_or_permit_checks_per_100k": [120, 170, 130, 160, 90, 92, 75, 76],
        }
    )

    out = run_nics_mechanism_models(panel, nics)

    assert set(out["nics_outcome"]) == {
        "handgun_checks_per_100k",
        "permit_checks_per_100k",
        "permit_recheck_checks_per_100k",
        "permit_and_recheck_checks_per_100k",
        "handgun_or_permit_checks_per_100k",
    }
    assert set(out["sample"]) == {"full_1999_2021", "exclude_2020_2021"}
    assert out.loc[out["sample"].eq("full_1999_2021"), "nobs"].min() == 8
    assert out.loc[out["sample"].eq("exclude_2020_2021"), "nobs"].min() == 4
