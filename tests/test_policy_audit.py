import pandas as pd

from src.analysis.policy_audit import build_policy_mechanism_summary


def test_build_policy_mechanism_summary_counts_source_verified_fields():
    audit = pd.DataFrame(
        {
            "audit_status": ["source_verified", "source_verified", "partial"],
            "training_requirement_removed": ["yes", "no_prior_training_requirement", "partial"],
            "background_check_permit_requirement_removed": ["yes", "yes", "partial"],
            "violent_misdemeanor_permit_screen_removed": [
                "yes_permit_screen_removed",
                "no_distinct_permit_screen_identified",
                "partial",
            ],
        }
    )

    summary = build_policy_mechanism_summary(audit)

    assert summary.to_dict("records") == [
        {
            "mechanism_field": "training_requirement_removed",
            "mechanism_value": "yes",
            "state_count": 1,
        },
        {
            "mechanism_field": "training_requirement_removed",
            "mechanism_value": "no_prior_training_requirement",
            "state_count": 1,
        },
        {
            "mechanism_field": "background_check_permit_requirement_removed",
            "mechanism_value": "yes",
            "state_count": 2,
        },
        {
            "mechanism_field": "violent_misdemeanor_permit_screen_removed",
            "mechanism_value": "yes_permit_screen_removed",
            "state_count": 1,
        },
        {
            "mechanism_field": "violent_misdemeanor_permit_screen_removed",
            "mechanism_value": "no_distinct_permit_screen_identified",
            "state_count": 1,
        },
    ]
