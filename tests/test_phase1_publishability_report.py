import pandas as pd

from src.analysis.phase1_publishability_report import (
    build_arkansas_sensitivity_sentence,
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
