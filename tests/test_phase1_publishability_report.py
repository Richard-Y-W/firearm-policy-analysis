import pandas as pd

from src.analysis.phase1_publishability_report import (
    build_arkansas_sensitivity_sentence,
    build_firearm_law_control_sentence,
    build_mechanism_summary_sentence,
    build_mechanism_heterogeneity_sentence,
    build_modern_did_sentence,
    build_nonfirearm_confounder_sentence,
    build_phase3b2_data_availability_table,
    build_phase3b2_confounder_sentence,
    build_policy_audit_status_sentence,
    build_report,
    build_results_hierarchy_table,
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


def test_build_phase3b2_confounder_sentence_reports_short_window_controls():
    summary = pd.DataFrame(
        {
            "outcome_label": ["Firearm Suicide", "Total Suicide"],
            "demographic_poverty_p05_retained": [True, True],
            "mental_health_access_p05_retained": [False, False],
            "full_phase3b2_p05_retained": [False, False],
        }
    )

    sentence = build_phase3b2_confounder_sentence(summary)

    assert "2 of 2 outcomes retain p < 0.05 in the demographic-poverty specification" in sentence
    assert "short HRSA mental-health access specification" in sentence


def test_build_modern_did_sentence_names_not_yet_treated_dynamic_att():
    summary = pd.DataFrame(
        {
            "outcome_label": ["Firearm Suicide", "Firearm Homicide"],
            "not_yet_post_mean_att": [0.7, -0.1],
        }
    )

    sentence = build_modern_did_sentence(summary)

    assert "not-yet-treated control dynamic ATT" in sentence
    assert "1 of 2 outcomes have positive post-adoption dynamic ATT estimates" in sentence


def test_build_mechanism_heterogeneity_sentence_marks_results_exploratory():
    results = pd.DataFrame(
        {
            "mechanism_dimension": ["training_removed", "training_removed"],
            "outcome_label": ["Firearm Suicide", "Firearm Homicide"],
            "interaction_p": [0.03, 0.40],
        }
    )

    sentence = build_mechanism_heterogeneity_sentence(results)

    assert "exploratory" in sentence
    assert "1 of 2 policy-feature interactions have p < 0.05" in sentence
    assert "small mechanism-specific adopter groups" in sentence


def test_build_phase3b2_data_availability_table_marks_missing_confounder_inputs():
    table = build_phase3b2_data_availability_table(
        {
            "uninsured_under65_pct",
            "drug_overdose_rate_per_100k",
            "income_pc",
            "share_age_18_34",
            "share_age_35_64",
            "share_age_65plus",
            "share_black_nonhispanic",
            "share_hispanic",
            "poverty_rate",
            "mental_health_provider_rate_per_100k",
        }
    )

    status_by_domain = dict(zip(table["domain"], table["status"]))

    assert status_by_domain["health insurance access"] == "modeled"
    assert status_by_domain["substance-use/distress proxy"] == "modeled"
    assert status_by_domain["age structure"] == "modeled"
    assert status_by_domain["race/ethnicity"] == "modeled"
    assert status_by_domain["poverty"] == "modeled"
    assert status_by_domain["mental-health provider access"] == "modeled"


def test_build_results_hierarchy_table_separates_claims_from_diagnostics():
    hierarchy = build_results_hierarchy_table()

    assert hierarchy["evidence_tier"].tolist() == [
        "Primary outcome",
        "Secondary outcomes",
        "Sensitivity checks",
        "Exploratory checks",
        "Appendix-only diagnostics",
    ]
    primary = hierarchy.loc[hierarchy["evidence_tier"].eq("Primary outcome")].iloc[0]
    assert primary["manuscript_role"] == "central confirmatory claim"
    assert primary["items"] == "Firearm Suicide"
    assert primary["multiple_testing_role"] == "single prespecified primary outcome"

    exploratory = hierarchy.loc[hierarchy["evidence_tier"].eq("Exploratory checks")].iloc[0]
    assert "policy-feature heterogeneity" in exploratory["items"]
    assert exploratory["multiple_testing_role"] == "hypothesis-generating only"


def test_build_report_places_results_hierarchy_before_main_results():
    report = build_report()

    assert "## Results Hierarchy" in report
    assert report.index("## Results Hierarchy") < report.index("## Main TWFE Results")
    assert "central confirmatory claim" in report
