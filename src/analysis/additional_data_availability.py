from pathlib import Path

import pandas as pd

try:
    from src.analysis.phase1_utils import ROOT
except ModuleNotFoundError:
    from phase1_utils import ROOT


OUT_DIR = ROOT / "outputs" / "tables" / "data_availability"
AVAILABILITY_FILE = OUT_DIR / "additional_analysis_data_availability.csv"


DATA_REQUIREMENTS = [
    {
        "analysis": "negative_control_mortality",
        "patterns": [
            "data/processed/analysis_panel_negative_control_mortality_1999_2024.csv",
            "data/raw/cdc_wonder/*cancer*",
            "data/raw/cdc_wonder/*cardio*",
            "data/raw/cdc_wonder/*motor_vehicle*",
            "data/raw/cdc_wonder/*vehicle*",
        ],
        "required_local_inputs": "CDC WONDER state-year cancer, cardiovascular, or motor-vehicle mortality exports",
        "missing_next_step": "Run python3 -m src.data.fetch_cdc_wonder_exports or export the six files listed in docs/additional_cdc_wonder_export_specs.md, then run python3 -m src.analysis.additional_mortality_checks.",
        "available_next_step": "Run python3 -m src.analysis.additional_mortality_checks to refresh processed panels and TWFE result tables.",
    },
    {
        "analysis": "nics_handgun_proxy",
        "patterns": [
            "data/processed/state_year_nics_handgun_checks_*.csv",
            "data/raw/nics/*nics*",
            "data/raw/nics/*background*",
        ],
        "required_local_inputs": "State-month or state-year NICS handgun check counts",
        "missing_next_step": "Add an FBI NICS state-month file under data/raw/nics/ and process handgun checks to state-year rates.",
        "available_next_step": "Run python3 -m src.analysis.nics_mechanism to refresh the supplemental NICS mechanism table.",
    },
    {
        "analysis": "sex_age_stratification",
        "patterns": [
            "data/processed/analysis_panel_firearm_suicide_by_sex_age_1999_2024.csv",
            "data/raw/cdc_wonder/*sex*",
            "data/raw/cdc_wonder/*age_group*",
            "data/raw/cdc_wonder/*age-sex*",
        ],
        "required_local_inputs": "CDC WONDER firearm-suicide exports stratified by sex and broad age group",
        "missing_next_step": "Run python3 -m src.data.fetch_cdc_wonder_exports or export the two sex/age files listed in docs/additional_cdc_wonder_export_specs.md, then run python3 -m src.analysis.additional_mortality_checks.",
        "available_next_step": "Run python3 -m src.analysis.additional_mortality_checks to refresh sex/age suppression audit and TWFE result tables.",
    },
]


def _detect_files(root: Path, patterns: list[str]) -> list[str]:
    detected = []
    for pattern in patterns:
        detected.extend(str(path.relative_to(root)) for path in sorted(root.glob(pattern)))
    return sorted(set(detected))


def audit_additional_data_sources(root=ROOT) -> pd.DataFrame:
    root = Path(root)
    rows = []
    for requirement in DATA_REQUIREMENTS:
        detected = _detect_files(root, requirement["patterns"])
        status = (
            "local_data_detected"
            if detected
            else "missing_required_local_data"
        )
        next_step_key = (
            "available_next_step"
            if status == "local_data_detected"
            else "missing_next_step"
        )
        rows.append(
            {
                "analysis": requirement["analysis"],
                "availability_status": status,
                "required_local_inputs": requirement["required_local_inputs"],
                "detected_files": ";".join(detected),
                "next_step": requirement[next_step_key],
            }
        )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    availability = audit_additional_data_sources(ROOT)
    availability.to_csv(AVAILABILITY_FILE, index=False)
    print(f"Wrote: {AVAILABILITY_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
