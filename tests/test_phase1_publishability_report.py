import pandas as pd

from src.analysis.phase1_publishability_report import (
    build_arkansas_sensitivity_sentence,
    build_firearm_law_control_sentence,
    build_mechanism_summary_sentence,
    build_nonfirearm_confounder_sentence,
    build_policy_audit_status_sentence,
)


def test_build_policy_audit_status_sentence_reports_verified_and_partial_counts():
    status = pd.DataFrame(
        {
            "audit_status": [
                "source_verified",
                "partial",
                "baseline_permitless_verified",
                "ambiguous_reviewed",
                "not_adopted_verified",
                "not_adopted_needs_review",
            ],
            "state_count": [26, 1, 1, 1, 21, 0],
        }
    )

    sentence = build_policy_audit_status_sentence(status)

    assert "26 source-verified current-adopter rows" in sentence
    assert "1 partial row" in sentence
    assert "1 baseline-permitless row" in sentence
    assert "1 ambiguous reviewed row" in sentence
    assert "21 verified non-adopter rows" in sentence
    assert "0 rows remain marked `not_adopted_needs_review`" in sentence


def test_build_arkansas_sensitivity_sentence_reports_retained_signs():
    summary = pd.DataFrame(
        {
            "outcome_label": ["Firearm Suicide", "Firearm Homicide"],
            "sign_retained": [True, False],
            "p05_retained": [True, False],
        }
    )

    sentence = build_arkansas_sensitivity_sentence(summary)

    assert "1 of 2 outcomes retain the same sign" in sentence
    assert "1 retain p < 0.05" in sentence


def test_build_mechanism_summary_sentence_reports_key_counts():
    summary = pd.DataFrame(
        {
            "mechanism_field": [
                "training_requirement_removed",
                "training_requirement_removed",
                "background_check_permit_requirement_removed",
                "background_check_permit_requirement_removed",
                "violent_misdemeanor_permit_screen_removed",
            ],
            "mechanism_value": [
                "yes",
                "no_prior_training_requirement",
                "yes",
                "carry_permit_screen_removed_purchase_permit_retained",
                "permit_specific_misdemeanor_screen_removed",
            ],
            "state_count": [21, 5, 25, 1, 12],
        }
    )

    sentence = build_mechanism_summary_sentence(summary)

    assert "21 had a training requirement removed" in sentence
    assert "25 removed the carry-permit background-check screen" in sentence
    assert "12 removed a permit-specific misdemeanor-violence screen" in sentence


def test_build_firearm_law_control_sentence_reports_surviving_outcomes():
    summary = pd.DataFrame(
        {
            "outcome_label": ["Firearm Suicide", "Firearm Homicide"],
            "sign_retained": [True, True],
            "p05_retained": [True, False],
        }
    )

    sentence = build_firearm_law_control_sentence(summary)

    assert "2 of 2 outcomes retain the same coefficient sign" in sentence
    assert "1 retain p < 0.05" in sentence


def test_build_nonfirearm_confounder_sentence_reports_sample_windows():
    summary = pd.DataFrame(
        {
            "outcome_label": ["Firearm Suicide", "Total Suicide"],
            "health_access_p05_retained": [True, True],
            "overdose_p05_retained": [True, False],
            "health_access_overdose_p05_retained": [False, False],
        }
    )

    sentence = build_nonfirearm_confounder_sentence(summary)

    assert "2 of 2 outcomes retain p < 0.05 in the 2008-2023 health-access specification" in sentence
    assert "1 retain p < 0.05 in the 2019-2024 overdose specification" in sentence
