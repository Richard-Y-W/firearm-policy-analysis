import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.process_phase3b2_confounders import (
    build_acs_demographic_controls,
    build_hrsa_mental_health_provider_controls,
    build_phase3b2_confounders,
    build_population_estimate_demographic_controls,
    build_saipe_poverty_controls,
)


def test_build_acs_demographic_controls_computes_age_and_race_ethnicity_shares():
    raw = pd.DataFrame(
        {
            "NAME": ["Alabama", "District of Columbia"],
            "state": ["01", "11"],
            "Year": [2024, 2024],
            "B01001_001E": [1000, 700],
            "B03002_001E": [1000, 700],
            "B03002_003E": [600, 250],
            "B03002_004E": [200, 300],
            "B03002_006E": [50, 40],
            "B03002_012E": [100, 80],
            **{column: [0, 0] for column in [
                "B01001_003E", "B01001_004E", "B01001_005E", "B01001_006E",
                "B01001_027E", "B01001_028E", "B01001_029E", "B01001_030E",
                "B01001_013E", "B01001_014E", "B01001_015E", "B01001_016E",
                "B01001_017E", "B01001_018E", "B01001_019E", "B01001_037E",
                "B01001_038E", "B01001_039E", "B01001_040E", "B01001_041E",
                "B01001_042E", "B01001_043E", "B01001_020E", "B01001_021E",
                "B01001_022E", "B01001_023E", "B01001_024E", "B01001_025E",
                "B01001_044E", "B01001_045E", "B01001_046E", "B01001_047E",
                "B01001_048E", "B01001_049E",
            ]},
            "B01001_007E": [20, 10],
            "B01001_008E": [30, 10],
            "B01001_009E": [10, 10],
            "B01001_010E": [40, 10],
            "B01001_011E": [50, 10],
            "B01001_012E": [60, 10],
            "B01001_031E": [20, 10],
            "B01001_032E": [30, 10],
            "B01001_033E": [10, 10],
            "B01001_034E": [40, 10],
            "B01001_035E": [50, 10],
            "B01001_036E": [60, 10],
        }
    )

    out = build_acs_demographic_controls([raw])

    assert out["State"].tolist() == ["Alabama"]
    row = out.iloc[0]
    assert row["Year"] == 2024
    assert row["share_age_18_34"] == 0.42
    assert row["share_white_nonhispanic"] == 0.60
    assert row["share_black_nonhispanic"] == 0.20
    assert row["share_hispanic"] == 0.10


def test_build_saipe_poverty_controls_uses_state_poverty_rate():
    raw = pd.DataFrame(
        {
            "NAME": ["Alabama", "District of Columbia"],
            "YEAR": ["2024", "2024"],
            "SAEPOVRTALL_PT": ["14.1", "13.0"],
            "state": ["01", "11"],
        }
    )

    out = build_saipe_poverty_controls([raw])

    assert out["State"].tolist() == ["Alabama"]
    assert out["Year"].tolist() == [2024]
    assert out["poverty_rate"].tolist() == [14.1]


def test_build_population_estimate_demographic_controls_uses_public_census_files():
    raw = pd.DataFrame(
        {
            "STATE": [1, 1, 1, 1, 1, 1],
            "NAME": ["Alabama"] * 6,
            "SEX": [0, 0, 0, 0, 0, 0],
            "ORIGIN": [0, 0, 1, 1, 1, 2],
            "RACE": [1, 2, 1, 2, 4, 1],
            "AGE": [18, 18, 18, 18, 18, 18],
            "POPESTIMATE2024": [600, 400, 500, 200, 50, 100],
        }
    )

    out = build_population_estimate_demographic_controls([raw])

    row = out.iloc[0]
    assert row["State"] == "Alabama"
    assert row["Year"] == 2024
    assert row["share_age_18_34"] == 1.0
    assert row["share_white_nonhispanic"] == 0.50
    assert row["share_black_nonhispanic"] == 0.20
    assert row["share_hispanic"] == 0.10


def test_build_hrsa_mental_health_provider_controls_uses_provider_counts_and_population():
    raw = pd.DataFrame(
        {
            "fips_st": ["01", "11"],
            "st_abbrev": ["AL", "DC"],
            "psychol_23": ["100", "50"],
            "conslrs_23": ["200", "50"],
            "socwk_23": ["300", "50"],
            "popn_pums_23": ["1000000", "500000"],
        }
    )

    out = build_hrsa_mental_health_provider_controls([raw])

    assert out["State"].tolist() == ["Alabama"]
    row = out.iloc[0]
    assert row["Year"] == 2023
    assert row["mental_health_provider_count"] == 600
    assert row["mental_health_provider_rate_per_100k"] == 60.0


def test_build_phase3b2_confounders_combines_demographics_poverty_and_provider_access():
    demographics = pd.DataFrame(
        {
            "State": ["Alabama"],
            "Year": [2023],
            "share_age_18_34": [0.25],
            "share_age_35_64": [0.50],
            "share_age_65plus": [0.18],
            "share_white_nonhispanic": [0.60],
            "share_black_nonhispanic": [0.20],
            "share_hispanic": [0.10],
        }
    )
    poverty = pd.DataFrame({"State": ["Alabama"], "Year": [2023], "poverty_rate": [14.1]})
    providers = pd.DataFrame(
        {
            "State": ["Alabama"],
            "Year": [2023],
            "mental_health_provider_count": [600],
            "mental_health_provider_rate_per_100k": [60.0],
        }
    )

    out = build_phase3b2_confounders(
        demographics,
        poverty,
        providers,
        states=["Alabama"],
        years=[2023],
    )

    row = out.iloc[0]
    assert row["phase3b2_demographic_poverty_complete"] == True
    assert row["phase3b2_full_complete"] == True
