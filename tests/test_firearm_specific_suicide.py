import pandas as pd

from src.analysis.firearm_specific_suicide import (
    FIREARM_SPECIFIC_OUTCOME,
    add_firearm_specific_suicide_rate,
    run_firearm_specific_suicide_model,
)


def test_add_firearm_specific_suicide_rate_subtracts_nonfirearm_suicide():
    panel = pd.DataFrame(
        {
            "firearm_suicide_rate_per_100k": [12.0, 14.5],
            "nonfirearm_suicide_rate_per_100k": [3.0, 4.0],
        }
    )

    out = add_firearm_specific_suicide_rate(panel)

    assert out[FIREARM_SPECIFIC_OUTCOME].tolist() == [9.0, 10.5]


def test_run_firearm_specific_suicide_model_labels_despair_netted_row():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "Year": [2019, 2020] * 4,
            "post_permitless": [0, 1, 0, 1, 0, 0, 0, 0],
            "unemployment_rate": [4, 4, 5, 5, 6, 6, 7, 7],
            "income_pc": [10, 11, 12, 13, 14, 15, 16, 17],
            "firearm_suicide_rate_per_100k": [10, 13, 8, 10, 7, 7, 6, 6],
            "nonfirearm_suicide_rate_per_100k": [3, 4, 2, 2.5, 2, 2, 1, 1],
        }
    )

    out = run_firearm_specific_suicide_model(panel)

    assert out["outcome"].tolist() == [FIREARM_SPECIFIC_OUTCOME]
    assert out["specification"].tolist() == ["despair_netted_firearm_suicide_twfe"]
    assert out["interpretation"].str.contains("firearm suicide minus non-firearm suicide").all()
