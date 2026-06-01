import pandas as pd

from src.analysis.phase1_publishability_report import build_policy_audit_status_sentence


def test_build_policy_audit_status_sentence_reports_verified_and_partial_counts():
    status = pd.DataFrame(
        {
            "audit_status": [
                "source_verified",
                "partial",
                "baseline_permitless_verified",
                "ambiguous_reviewed",
                "not_adopted_needs_review",
            ],
            "state_count": [26, 1, 1, 1, 21],
        }
    )

    sentence = build_policy_audit_status_sentence(status)

    assert "26 source-verified current-adopter rows" in sentence
    assert "1 partial row" in sentence
    assert "1 baseline-permitless row" in sentence
    assert "1 ambiguous reviewed row" in sentence
    assert "21 rows remain marked `not_adopted_needs_review`" in sentence
