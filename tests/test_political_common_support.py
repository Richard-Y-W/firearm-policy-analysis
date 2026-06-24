import pandas as pd

from src.analysis.political_common_support import build_common_support_table


def test_build_common_support_table_counts_adopters_outside_nonadopter_range():
    state_level = pd.DataFrame(
        {
            "State": ["A", "B", "C", "D", "E"],
            "ever_adopter": [1, 1, 1, 0, 0],
            "rep_vote_share_baseline": [0.30, 0.55, 0.80, 0.40, 0.60],
            "baseline_firearm_suicide": [9.0, 10.0, 11.0, 6.0, 12.0],
        }
    )

    out = build_common_support_table(
        state_level,
        variables={
            "rep_vote_share_baseline": "Republican two-party vote share",
            "baseline_firearm_suicide": "Baseline firearm suicide",
        },
        baseline_definitions={
            "rep_vote_share_baseline": "test baseline",
            "baseline_firearm_suicide": "test firearm suicide baseline",
        },
    )

    politics = out.loc[out["variable"].eq("rep_vote_share_baseline")].iloc[0]
    assert politics["baseline_definition"] == "test baseline"
    assert politics["n_adopters"] == 3
    assert politics["n_adopters_below_nonadopter_min"] == 1
    assert politics["n_adopters_above_nonadopter_max"] == 1
    assert politics["n_adopters_outside_nonadopter_range"] == 2
    assert politics["share_adopters_outside_nonadopter_range"] == 2 / 3

    baseline = out.loc[out["variable"].eq("baseline_firearm_suicide")].iloc[0]
    assert baseline["n_adopters_outside_nonadopter_range"] == 0
