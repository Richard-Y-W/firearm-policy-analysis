from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import ROOT
except ModuleNotFoundError:
    from phase1_utils import ROOT


IN_FILE = ROOT / "outputs" / "tables" / "political_selection" / "state_level_political_selection_inputs.csv"
OUT_FILE = ROOT / "outputs" / "tables" / "political_selection" / "common_support_overlap.csv"

DEFAULT_COMMON_SUPPORT_VARIABLES = {
    "rep_vote_share_baseline": "Republican two-party vote share",
    "gun_ownership_baseline": "Household firearm ownership",
    "rurality": "Share nonmetro counties",
    "baseline_firearm_suicide": "Baseline firearm suicide",
}

DEFAULT_BASELINE_DEFINITIONS = {
    "rep_vote_share_baseline": "2012 two-party Republican presidential vote share when available; otherwise the latest available presidential vote-share value",
    "gun_ownership_baseline": "earliest available state firearm-ownership estimate in the clean primary panel",
    "rurality": "2013 USDA county rurality summary",
    "baseline_firearm_suicide": "mean pre-adoption firearm-suicide rate for adopters and mean rate through 2014 for non-adopters",
}


def build_common_support_table(
    state_level: pd.DataFrame,
    *,
    variables: dict[str, str] = DEFAULT_COMMON_SUPPORT_VARIABLES,
    baseline_definitions: dict[str, str] = DEFAULT_BASELINE_DEFINITIONS,
) -> pd.DataFrame:
    rows = []
    for variable, label in variables.items():
        use = state_level[["State", "ever_adopter", variable]].dropna().copy()
        adopters = use.loc[use["ever_adopter"].eq(1), variable]
        nonadopters = use.loc[use["ever_adopter"].eq(0), variable]
        if adopters.empty or nonadopters.empty:
            nonadopter_min = np.nan
            nonadopter_max = np.nan
            below = pd.Series(dtype=float)
            above = pd.Series(dtype=float)
        else:
            nonadopter_min = float(nonadopters.min())
            nonadopter_max = float(nonadopters.max())
            below = adopters[adopters < nonadopter_min]
            above = adopters[adopters > nonadopter_max]
        outside = int(len(below) + len(above))
        n_adopters = int(len(adopters))
        rows.append(
            {
                "variable": variable,
                "variable_label": label,
                "baseline_definition": baseline_definitions.get(variable, ""),
                "n_adopters": n_adopters,
                "n_nonadopters": int(len(nonadopters)),
                "nonadopter_min": nonadopter_min,
                "nonadopter_max": nonadopter_max,
                "adopter_min": float(adopters.min()) if not adopters.empty else np.nan,
                "adopter_max": float(adopters.max()) if not adopters.empty else np.nan,
                "n_adopters_below_nonadopter_min": int(len(below)),
                "n_adopters_above_nonadopter_max": int(len(above)),
                "n_adopters_outside_nonadopter_range": outside,
                "share_adopters_outside_nonadopter_range": (
                    outside / n_adopters if n_adopters else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def main():
    if not IN_FILE.exists():
        raise FileNotFoundError(
            f"Missing political selection inputs: {IN_FILE}. Run python3 -m src.analysis.run_all_analysis first."
        )
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    state_level = pd.read_csv(IN_FILE)
    out = build_common_support_table(state_level)
    out.to_csv(OUT_FILE, index=False)
    print(f"Wrote: {OUT_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
