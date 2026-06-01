import pandas as pd

from src.analysis.phase1_publishability_report import build_policy_audit_status_sentence


def test_build_policy_audit_status_sentence_reports_verified_and_partial_counts():
    status = pd.DataFrame(
        {
            "audit_status": ["source_verified", "partial", "not_adopted_needs_review"],
            "state_count": [23, 1, 26],
        }
    )

    sentence = build_policy_audit_status_sentence(status)

    assert "23 source-verified current-adopter rows" in sentence
    assert "1 partial row" in sentence
    assert "26 rows remain marked `not_adopted_needs_review`" in sentence
