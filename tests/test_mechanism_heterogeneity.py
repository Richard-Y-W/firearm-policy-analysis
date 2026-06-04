import pandas as pd

from src.analysis.mechanism_heterogeneity import (
    MECHANISM_SPECS,
    add_mechanism_indicators,
    run_mechanism_heterogeneity_models,
)


def test_add_mechanism_indicators_uses_source_verified_adopter_rows_only():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2019, 2020, 2019, 2020, 2019, 2020],
            "post_permitless": [0, 1, 0, 1, 0, 0],
        }
    )
    audit = pd.DataFrame(
        {
            "State": ["A", "B", "C"],
            "audit_status": ["source_verified", "ambiguous_reviewed", "not_adopted_verified"],
            "training_requirement_removed": ["yes", "yes", "no"],
            "background_check_permit_requirement_removed": ["yes", "yes", "no"],
            "violent_misdemeanor_permit_screen_removed": [
                "permit_specific_misdemeanor_screen_removed",
                "permit_specific_misdemeanor_screen_removed",
                "no",
            ],
        }
    )

    out = add_mechanism_indicators(panel, audit)

    assert out.loc[out["State"].eq("A"), "training_removed"].max() == 1
    assert out.loc[out["State"].eq("B"), "training_removed"].max() == 0
    assert out.loc[out["State"].eq("C"), "training_removed"].max() == 0
    assert out.loc[out["State"].eq("A"), "post_training_removed"].tolist() == [0, 1]


def test_run_mechanism_heterogeneity_models_reports_exploratory_interactions():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C", "D", "D"],
            "Year": [2019, 2020] * 4,
            "post_permitless": [0, 1, 0, 1, 0, 0, 0, 0],
            "unemployment_rate": [4, 4, 5, 5, 6, 6, 7, 7],
            "income_pc": [10, 11, 12, 13, 14, 15, 16, 17],
            "outcome": [1, 4, 1, 2, 1, 1, 2, 2],
        }
    )
    audit = pd.DataFrame(
        {
            "State": ["A", "B", "C", "D"],
            "audit_status": [
                "source_verified",
                "source_verified",
                "not_adopted_verified",
                "not_adopted_verified",
            ],
            "training_requirement_removed": ["yes", "no_prior_training_requirement", "no", "no"],
            "background_check_permit_requirement_removed": ["yes", "yes", "no", "no"],
            "violent_misdemeanor_permit_screen_removed": [
                "permit_specific_misdemeanor_screen_removed",
                "eligibility_standard_retained_no_precarry_check",
                "no",
                "no",
            ],
        }
    )

    result = run_mechanism_heterogeneity_models(
        panel,
        audit,
        outcomes=["outcome"],
        outcome_labels={"outcome": "Outcome"},
    )

    assert set(result["mechanism_dimension"]) == set(MECHANISM_SPECS)
    assert "comparison_warning" in result.columns
    assert result["sparse_comparison"].all()
    assert set(result["interpretation_scope"]) == {
        "exploratory_sparse_comparison_do_not_interpret_as_mechanism"
    }
    assert result["interaction_term"].str.startswith("post_").all()
