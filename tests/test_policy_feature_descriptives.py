import pandas as pd

from src.analysis.policy_feature_descriptives import (
    build_feature_stratified_event_means,
    build_policy_bundle_table,
)


def test_build_policy_bundle_table_counts_three_permit_process_features():
    audit = pd.DataFrame(
        {
            "State": ["A", "B", "C"],
            "audit_status": ["source_verified", "source_verified", "not_adopted_verified"],
            "training_requirement_removed": ["yes", "no_prior_training_requirement", "no"],
            "background_check_permit_requirement_removed": ["yes", "yes", "no"],
            "violent_misdemeanor_permit_screen_removed": [
                "permit_specific_misdemeanor_screen_removed",
                "eligibility_standard_retained_no_precarry_check",
                "no",
            ],
        }
    )

    out = build_policy_bundle_table(audit)

    assert set(out["State"]) == {"A", "B"}
    assert out.loc[out["State"].eq("A"), "policy_bundle_index"].iloc[0] == 3
    assert out.loc[out["State"].eq("B"), "policy_bundle_index"].iloc[0] == 1


def test_build_feature_stratified_event_means_uses_source_verified_adopters():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2019, 2020, 2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, 2020, 2020, pd.NA, pd.NA],
            "firearm_suicide_rate_per_100k": [5.0, 7.0, 4.0, 4.5, 3.0, 3.0],
        }
    )
    bundle = pd.DataFrame(
        {
            "State": ["A", "B"],
            "training_removed": [1, 0],
            "permit_background_check_removed": [1, 1],
            "misdemeanor_screen_removed": [1, 0],
            "policy_bundle_index": [3, 1],
        }
    )

    out = build_feature_stratified_event_means(panel, bundle, min_event_time=-1, max_event_time=0)

    assert set(out["feature"]) >= {"training_removed", "policy_bundle_index"}
    assert set(out["event_time"]) == {-1, 0}
    assert out["n_states"].min() == 1
