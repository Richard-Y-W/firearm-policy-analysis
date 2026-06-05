import pandas as pd

from src.analysis.ageadj_sensitivity import (
    AGEADJ_OUTCOMES,
    build_summary,
    run_ageadj_models,
)


def test_ageadj_models_run_on_current_panel_outputs():
    panel = pd.read_csv("data/processed/analysis_panel_full_outcomes.csv")

    missing = [col for col in AGEADJ_OUTCOMES if col not in panel.columns]

    assert missing == []

    detail = run_ageadj_models(panel)
    summary = build_summary(detail)

    assert set(detail["specification"]) == {"baseline_controls", "firearm_law_controls"}
    assert len(summary) == len(AGEADJ_OUTCOMES)
    assert summary["baseline_coef"].notna().all()
    assert summary["same_direction_as_crude"].all()
