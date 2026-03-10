import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs" / "tables"

total = pd.read_csv(TABLES / "welch_results_total_firearm_deaths.csv")
total["outcome"] = "Total firearm deaths"

homicide = pd.read_csv(TABLES / "welch_results_firearm_homicide_deaths.csv")
homicide["outcome"] = "Firearm homicide"

suicide = pd.read_csv(TABLES / "welch_results_firearm_suicide_deaths.csv")
suicide["outcome"] = "Firearm suicide"

combined = pd.concat([total, homicide, suicide])

combined = combined[
    ["outcome","window","n_adopters","n_controls","diff","p","ci_low","ci_high"]
]

combined.to_csv(TABLES / "combined_results.csv", index=False)

print(combined)