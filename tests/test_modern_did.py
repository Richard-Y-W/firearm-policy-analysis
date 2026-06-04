import pandas as pd

from src.analysis.modern_did import (
    aggregate_dynamic_att,
    build_cohort_time_att,
)


def test_build_cohort_time_att_uses_not_yet_treated_controls_until_adoption():
    panel = pd.DataFrame(
        {
            "State": ["A"] * 3 + ["B"] * 3 + ["C"] * 3,
            "Year": [2019, 2020, 2021] * 3,
            "permitless_year": [2020, 2020, 2020, 2021, 2021, 2021, pd.NA, pd.NA, pd.NA],
            "outcome": [10.0, 14.0, 16.0, 10.0, 11.0, 13.0, 20.0, 20.0, 20.0],
        }
    )

    att = build_cohort_time_att(panel, "outcome", min_event_time=0, max_event_time=1)

    early_event_0 = att.loc[
        (att["cohort"].eq(2020)) & (att["event_time"].eq(0))
    ].iloc[0]
    assert early_event_0["n_control_states"] == 2
    assert early_event_0["treated_change"] == 4.0
    assert early_event_0["control_change"] == 0.5
    assert early_event_0["att"] == 3.5

    early_event_1 = att.loc[
        (att["cohort"].eq(2020)) & (att["event_time"].eq(1))
    ].iloc[0]
    assert early_event_1["n_control_states"] == 1
    assert early_event_1["control_states"] == "C"
    assert early_event_1["att"] == 6.0


def test_aggregate_dynamic_att_weights_by_treated_state_count():
    att = pd.DataFrame(
        {
            "outcome": ["outcome", "outcome"],
            "outcome_label": ["Outcome", "Outcome"],
            "event_time": [0, 0],
            "att": [2.0, 8.0],
            "n_treated_states": [1, 3],
            "n_control_states": [5, 5],
        }
    )

    dynamic = aggregate_dynamic_att(att)

    row = dynamic.iloc[0]
    assert row["event_time"] == 0
    assert row["weighted_att"] == 6.5
    assert row["n_cohorts"] == 2
    assert row["n_treated_states"] == 4
