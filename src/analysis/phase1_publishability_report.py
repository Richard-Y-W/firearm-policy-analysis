from pathlib import Path

import pandas as pd

try:
    from src.analysis.phase1_utils import ROOT
except ModuleNotFoundError:
    from phase1_utils import ROOT


TABLES = ROOT / "outputs" / "tables"
OUT_FILE = TABLES / "main" / "phase1_publishability_report.md"
ARKANSAS_SENSITIVITY_FILE = (
    TABLES / "robustness" / "arkansas_treatment_sensitivity_summary.csv"
)
POLICY_MECHANISM_FILE = TABLES / "policy_audit" / "policy_mechanism_summary.csv"
FIREARM_LAW_CONTROL_FILE = (
    TABLES / "did" / "twfe_did_firearm_law_control_summary.csv"
)
NONFIREARM_CONFOUNDER_FILE = (
    TABLES / "did" / "twfe_did_nonfirearm_confounder_summary.csv"
)
PHASE3B2_CONFOUNDER_FILE = (
    TABLES / "did" / "twfe_did_phase3b2_confounder_summary.csv"
)
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
MECHANISM_HETEROGENEITY_FILE = (
    TABLES / "mechanism" / "mechanism_heterogeneity_results.csv"
)


def fmt_p(value) -> str:
    if pd.isna(value):
        return "NA"
    value = float(value)
    if value < 0.001:
        return "<0.001"
    return f"{value:.3f}"


def fmt_num(value) -> str:
    if pd.isna(value):
        return "NA"
    return f"{float(value):.3f}"


def markdown_table(df: pd.DataFrame, columns: list[str]) -> str:
    shown = df[columns].copy()
    lines = []
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for _, row in shown.iterrows():
        lines.append("| " + " | ".join(str(row[col]) for col in columns) + " |")
    return "\n".join(lines)


def build_results_hierarchy_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "evidence_tier": "Primary outcome",
                "items": "Firearm Suicide",
                "manuscript_role": "central confirmatory claim",
                "interpretation_boundary": "main mortality claim",
                "multiple_testing_role": "single prespecified primary outcome",
                "placement": "main text",
            },
            {
                "evidence_tier": "Secondary outcomes",
                "items": "Total Suicide; Non-Firearm Suicide; Firearm Homicide; Total Firearm Deaths",
                "manuscript_role": "specificity and outcome-family interpretation",
                "interpretation_boundary": "supports or limits the primary claim",
                "multiple_testing_role": "main outcome family",
                "placement": "main text",
            },
            {
                "evidence_tier": "Sensitivity checks",
                "items": "firearm-law controls; health-access and overdose controls; staggered-adoption checks; Arkansas recoding; leave-one-out; placebo timing",
                "manuscript_role": "design credibility and robustness",
                "interpretation_boundary": "tests stability, not additional headline effects",
                "multiple_testing_role": "diagnostic sensitivity layer",
                "placement": "main text summary with appendix detail",
            },
            {
                "evidence_tier": "Exploratory checks",
                "items": "policy-feature heterogeneity; rurality, gun-ownership, and baseline-risk heterogeneity",
                "manuscript_role": "mechanism and boundary exploration",
                "interpretation_boundary": "sample-size limited and hypothesis-generating",
                "multiple_testing_role": "hypothesis-generating only",
                "placement": "secondary results or appendix",
            },
            {
                "evidence_tier": "Appendix-only diagnostics",
                "items": "cohort ATT rows; event-time rows; full legal source table; full robustness grids",
                "manuscript_role": "audit trail and transparency",
                "interpretation_boundary": "not interpreted as independent discoveries",
                "multiple_testing_role": "not treated as confirmatory tests",
                "placement": "appendix",
            },
        ]
    )


def _audit_count(audit_status: pd.DataFrame, status: str) -> int:
    return int(
        audit_status.loc[audit_status["audit_status"] == status, "state_count"].sum()
    )


def build_policy_audit_status_sentence(audit_status: pd.DataFrame) -> str:
    total_audit = int(audit_status["state_count"].sum())
    verified = _audit_count(audit_status, "source_verified")
    partial = _audit_count(audit_status, "partial")
    baseline = _audit_count(audit_status, "baseline_permitless_verified")
    ambiguous = _audit_count(audit_status, "ambiguous_reviewed")
    non_adopter_verified = _audit_count(audit_status, "not_adopted_verified")
    needs_source = _audit_count(audit_status, "needs_source")
    not_reviewed = _audit_count(audit_status, "not_adopted_needs_review")

    partial_text = "1 partial row" if partial == 1 else f"{partial} partial rows"
    baseline_text = (
        "1 baseline-permitless row"
        if baseline == 1
        else f"{baseline} baseline-permitless rows"
    )
    ambiguous_text = (
        "1 ambiguous reviewed row"
        if ambiguous == 1
        else f"{ambiguous} ambiguous reviewed rows"
    )
    non_adopter_text = (
        "1 verified non-adopter row"
        if non_adopter_verified == 1
        else f"{non_adopter_verified} verified non-adopter rows"
    )
    non_clean_categories = "Partial, ambiguous, and baseline rows"
    if not_reviewed:
        non_clean_categories = "Partial, ambiguous, baseline, and not-yet-reviewed rows"
    return (
        f"The policy audit table contains {total_audit} states. "
        f"The current audit records {verified} source-verified current-adopter rows, "
        f"{partial_text}, {baseline_text}, {ambiguous_text}, and "
        f"{non_adopter_text}; "
        f"{not_reviewed} rows remain marked "
        "`not_adopted_needs_review`."
        + (
            f" {needs_source} rows still need initial source coding."
            if needs_source
            else ""
        )
        + f" {non_clean_categories} should not be treated as clean within-panel adoption events."
    )


def build_arkansas_sensitivity_sentence(summary: pd.DataFrame) -> str:
    total = int(len(summary))
    sign_retained = int(summary["sign_retained"].fillna(False).sum())
    p05_retained = int(summary["p05_retained"].fillna(False).sum())
    return (
        "The Arkansas sensitivity check keeps Arkansas excluded in the primary "
        "model and recodes it as 2021 and 2023 in alternate runs. "
        f"{sign_retained} of {total} outcomes retain the same sign across both "
        f"Arkansas codings, and {p05_retained} retain p < 0.05 across both "
        "codings."
    )


def _mechanism_count(summary: pd.DataFrame, field: str, value: str) -> int:
    return int(
        summary.loc[
            (summary["mechanism_field"] == field)
            & (summary["mechanism_value"] == value),
            "state_count",
        ].sum()
    )


def build_mechanism_summary_sentence(summary: pd.DataFrame) -> str:
    training_removed = _mechanism_count(
        summary, "training_requirement_removed", "yes"
    )
    background_removed = _mechanism_count(
        summary, "background_check_permit_requirement_removed", "yes"
    )
    misdemeanor_removed = _mechanism_count(
        summary,
        "violent_misdemeanor_permit_screen_removed",
        "permit_specific_misdemeanor_screen_removed",
    )
    retained_eligibility = _mechanism_count(
        summary,
        "violent_misdemeanor_permit_screen_removed",
        "eligibility_standard_retained_no_precarry_check",
    )
    return (
        f"Among the 26 clean source-verified adopter rows, {training_removed} "
        "had a training requirement removed, "
        f"{background_removed} removed the carry-permit background-check screen, "
        f"and {misdemeanor_removed} removed a permit-specific "
        "misdemeanor-violence screen. "
        f"{retained_eligibility} rows retain permit-style eligibility standards "
        "but no longer require an application before carry."
    )


def build_firearm_law_control_sentence(summary: pd.DataFrame) -> str:
    total = int(len(summary))
    sign_retained = int(summary["sign_retained"].fillna(False).sum())
    p05_retained = int(summary["p05_retained"].fillna(False).sum())
    return (
        "The external firearm-law control check adds controls for "
        "permit-to-purchase laws, waiting periods, universal background checks, "
        "ERPO/red-flag laws, safe-storage laws, stand-your-ground laws, and "
        "dealer licensing. "
        f"{sign_retained} of {total} outcomes retain the same coefficient sign, "
        f"and {p05_retained} retain p < 0.05 after those controls are added."
    )


def build_nonfirearm_confounder_sentence(summary: pd.DataFrame) -> str:
    total = int(len(summary))
    health_access = int(summary["health_access_p05_retained"].fillna(False).sum())
    overdose = int(summary["overdose_p05_retained"].fillna(False).sum())
    combined = int(
        summary["health_access_overdose_p05_retained"].fillna(False).sum()
    )
    return (
        "The non-firearm confounder check adds Census SAHIE uninsured rates "
        "as a health-access proxy and CDC drug-overdose mortality as a "
        "substance-use/distress proxy. "
        f"{health_access} of {total} outcomes retain p < 0.05 in the "
        "2008-2023 health-access specification, "
        f"{overdose} retain p < 0.05 in the 2019-2024 overdose specification, "
        f"and {combined} retain p < 0.05 in the narrower 2019-2023 combined "
        "specification."
    )


def build_phase3b2_confounder_sentence(summary: pd.DataFrame) -> str:
    total = int(len(summary))
    demographic_poverty = int(
        summary["demographic_poverty_p05_retained"].fillna(False).sum()
    )
    mental_health = int(
        summary["mental_health_access_p05_retained"].fillna(False).sum()
    )
    full = int(summary["full_phase3b2_p05_retained"].fillna(False).sum())
    return (
        "The Phase 3B2 confounder check adds Census Population Estimates "
        "state age and race/ethnicity shares, Census SAIPE poverty rates, "
        "and HRSA AHRF mental-health provider access. "
        f"{demographic_poverty} of {total} outcomes retain p < 0.05 in the "
        "demographic-poverty specification, "
        f"{mental_health} retain p < 0.05 in the short HRSA mental-health "
        "access specification, and "
        f"{full} retain p < 0.05 in the combined short-window Phase 3B2 "
        "specification."
    )


def build_modern_did_sentence(summary: pd.DataFrame) -> str:
    total = int(len(summary))
    if "not_yet_post_mean_att" in summary:
        positive_dynamic = int((summary["not_yet_post_mean_att"] > 0).fillna(False).sum())
    else:
        positive_dynamic = 0
    return (
        "The modern staggered-adoption check reports cohort-window ATT estimates, "
        "a not-yet-treated control dynamic ATT, and a never-treated-control "
        "event-time fixed-effect sensitivity check. "
        f"{positive_dynamic} of {total} outcomes have positive post-adoption "
        "dynamic ATT estimates. `pretrend_flag_p05` marks outcomes with at "
        "least one statistically significant pre-adoption event-time coefficient."
    )


def build_mechanism_heterogeneity_sentence(results: pd.DataFrame) -> str:
    total = int(len(results))
    p05 = int((results["interaction_p"] < 0.05).fillna(False).sum())
    sparse = (
        int(results["sparse_comparison"].fillna(False).sum())
        if "sparse_comparison" in results
        else 0
    )
    return (
        "The policy-feature heterogeneity models are exploratory because "
        "permitless-carry mechanism fields create small mechanism-specific "
        "adopter groups. "
        f"{p05} of {total} policy-feature interactions have p < 0.05; "
        f"{sparse} have sparse or unavailable source-verified comparison groups. "
        "These rows should be interpreted as boundary checks, not as "
        "independent confirmatory findings."
    )


def build_phase3b2_data_availability_table(available_columns) -> pd.DataFrame:
    available = set(available_columns)

    def status_for(candidates: list[str]) -> str:
        return "modeled" if any(col in available for col in candidates) else "missing source input"

    return pd.DataFrame(
        [
            {
                "domain": "health insurance access",
                "target_columns": "uninsured_under65_pct",
                "status": status_for(["uninsured_under65_pct"]),
                "current_role": "Phase 3B modeled proxy",
                "needed_source": "already processed from Census SAHIE",
            },
            {
                "domain": "substance-use/distress proxy",
                "target_columns": "drug_overdose_rate_per_100k",
                "status": status_for(["drug_overdose_rate_per_100k"]),
                "current_role": "Phase 3B modeled proxy",
                "needed_source": "already processed from CDC overdose data",
            },
            {
                "domain": "age structure",
                "target_columns": "share_age_18_34; share_age_35_64; share_age_65plus",
                "status": status_for(
                    ["share_age_18_34", "share_age_35_64", "share_age_65plus", "median_age"]
                ),
                "current_role": "Phase 3B2 modeled confounder",
                "needed_source": "Census Population Estimates state age distribution",
            },
            {
                "domain": "race/ethnicity",
                "target_columns": "share_black_nonhispanic; share_hispanic; share_white_nonhispanic",
                "status": status_for(
                    ["share_black", "share_hispanic", "share_white_nonhispanic"]
                ),
                "current_role": "Phase 3B2 modeled confounder",
                "needed_source": "Census Population Estimates state race and ethnicity distribution",
            },
            {
                "domain": "poverty",
                "target_columns": "poverty_rate",
                "status": status_for(["poverty_rate", "saipe_poverty_rate"]),
                "current_role": "Phase 3B2 modeled confounder",
                "needed_source": "Census SAIPE state-year poverty estimates",
            },
            {
                "domain": "mental-health provider access",
                "target_columns": "mental_health_provider_rate_per_100k",
                "status": status_for(
                    [
                        "mental_health_provider_rate",
                        "mental_health_hpsa_score",
                        "mental_health_provider_per_100k",
                        "mental_health_provider_rate_per_100k",
                    ]
                ),
                "current_role": "Phase 3B2 short-window modeled confounder",
                "needed_source": "HRSA AHRF state/national workforce counts",
            },
        ]
    )


def build_report() -> str:
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    hierarchy = build_results_hierarchy_table()
    panel_columns = pd.read_csv(PANEL_FILE, nrows=0).columns
    phase3b2_availability = build_phase3b2_data_availability_table(panel_columns)
    audit_status = pd.read_csv(TABLES / "policy_audit" / "policy_audit_status_counts.csv")
    mechanisms = pd.read_csv(POLICY_MECHANISM_FILE)
    firearm_law_controls = (
        pd.read_csv(FIREARM_LAW_CONTROL_FILE)
        if FIREARM_LAW_CONTROL_FILE.exists()
        else pd.DataFrame()
    )
    nonfirearm_confounders = (
        pd.read_csv(NONFIREARM_CONFOUNDER_FILE)
        if NONFIREARM_CONFOUNDER_FILE.exists()
        else pd.DataFrame()
    )
    phase3b2_confounders = (
        pd.read_csv(PHASE3B2_CONFOUNDER_FILE)
        if PHASE3B2_CONFOUNDER_FILE.exists()
        else pd.DataFrame()
    )
    modern = pd.read_csv(TABLES / "modern_did" / "modern_did_summary.csv")
    mechanism_heterogeneity = (
        pd.read_csv(MECHANISM_HETEROGENEITY_FILE)
        if MECHANISM_HETEROGENEITY_FILE.exists()
        else pd.DataFrame()
    )
    robust = pd.read_csv(TABLES / "robustness" / "robustness_summary.csv")
    arkansas = (
        pd.read_csv(ARKANSAS_SENSITIVITY_FILE)
        if ARKANSAS_SENSITIVITY_FILE.exists()
        else pd.DataFrame()
    )

    did_view = did.copy()
    did_view["coef"] = did_view["coef_post_permitless"].map(fmt_num)
    did_view["p"] = did_view["p_post_permitless"].map(fmt_p)
    did_view = did_view[["outcome_label", "coef", "p"]]

    if not firearm_law_controls.empty:
        firearm_law_view = firearm_law_controls.copy()
        for col in [
            "baseline_coef",
            "baseline_p",
            "controlled_coef",
            "controlled_p",
            "controlled_delta",
        ]:
            firearm_law_view[col] = firearm_law_view[col].map(
                fmt_p if col.endswith("_p") else fmt_num
            )
        firearm_law_view = firearm_law_view[
            [
                "outcome_label",
                "baseline_coef",
                "baseline_p",
                "controlled_coef",
                "controlled_p",
                "controlled_delta",
                "sign_retained",
                "p05_retained",
                "interpretation_flag",
            ]
        ]
    else:
        firearm_law_view = pd.DataFrame()

    if not nonfirearm_confounders.empty:
        nonfirearm_view = nonfirearm_confounders.copy()
        for col in [
            "firearm_law_coef",
            "firearm_law_p",
            "health_access_coef",
            "health_access_p",
            "overdose_coef",
            "overdose_p",
            "health_access_overdose_coef",
            "health_access_overdose_p",
        ]:
            nonfirearm_view[col] = nonfirearm_view[col].map(
                fmt_p if col.endswith("_p") else fmt_num
            )
        nonfirearm_view = nonfirearm_view[
            [
                "outcome_label",
                "firearm_law_coef",
                "firearm_law_p",
                "health_access_coef",
                "health_access_p",
                "health_access_p05_retained",
                "overdose_coef",
                "overdose_p",
                "overdose_p05_retained",
                "health_access_overdose_coef",
                "health_access_overdose_p",
                "health_access_overdose_p05_retained",
            ]
        ]
    else:
        nonfirearm_view = pd.DataFrame()

    if not phase3b2_confounders.empty:
        phase3b2_view = phase3b2_confounders.copy()
        for col in [
            "firearm_law_coef",
            "firearm_law_p",
            "demographic_poverty_coef",
            "demographic_poverty_p",
            "mental_health_access_coef",
            "mental_health_access_p",
            "full_phase3b2_coef",
            "full_phase3b2_p",
        ]:
            phase3b2_view[col] = phase3b2_view[col].map(
                fmt_p if col.endswith("_p") else fmt_num
            )
        phase3b2_view = phase3b2_view[
            [
                "outcome_label",
                "firearm_law_coef",
                "firearm_law_p",
                "demographic_poverty_coef",
                "demographic_poverty_p",
                "demographic_poverty_p05_retained",
                "mental_health_access_coef",
                "mental_health_access_p",
                "mental_health_access_p05_retained",
                "full_phase3b2_coef",
                "full_phase3b2_p",
                "full_phase3b2_p05_retained",
            ]
        ]
    else:
        phase3b2_view = pd.DataFrame()

    welch_view = welch.copy()
    welch_view["difference"] = welch_view["difference"].map(fmt_num)
    welch_view["p"] = welch_view["p_value"].map(fmt_p)
    welch_view = welch_view[["outcome_label", "window", "difference", "p"]]

    modern_view = modern.copy()
    for col in [
        "not_yet_post_mean_att",
        "not_yet_pre_mean_att",
        "not_yet_dynamic_rows",
    ]:
        if col not in modern_view:
            modern_view[col] = pd.NA
    for col in [
        "cohort_att_w2",
        "cohort_att_w3",
        "cohort_att_w5",
        "not_yet_post_mean_att",
        "not_yet_pre_mean_att",
        "event_post_mean_coef",
        "event_pretrend_min_p",
    ]:
        modern_view[col] = modern_view[col].map(fmt_num if col != "event_pretrend_min_p" else fmt_p)
    modern_view["not_yet_dynamic_rows"] = modern_view["not_yet_dynamic_rows"].map(
        lambda value: "NA" if pd.isna(value) else str(int(value))
    )
    modern_view = modern_view[
        [
            "outcome_label",
            "cohort_att_w2",
            "cohort_att_w3",
            "cohort_att_w5",
            "not_yet_post_mean_att",
            "not_yet_pre_mean_att",
            "not_yet_dynamic_rows",
            "event_post_mean_coef",
            "pretrend_flag_p05",
            "interpretation_flag",
        ]
    ]

    if not mechanism_heterogeneity.empty:
        mechanism_heterogeneity_view = mechanism_heterogeneity.copy()
        for col in ["sparse_comparison", "comparison_warning"]:
            if col not in mechanism_heterogeneity_view:
                mechanism_heterogeneity_view[col] = pd.NA
        for col in [
            "main_post_coef",
            "interaction_coef",
            "interaction_se",
            "interaction_p",
        ]:
            mechanism_heterogeneity_view[col] = mechanism_heterogeneity_view[col].map(
                fmt_p if col == "interaction_p" else fmt_num
            )
        mechanism_heterogeneity_view = mechanism_heterogeneity_view[
            [
                "outcome_label",
                "mechanism_dimension",
                "main_post_coef",
                "interaction_coef",
                "interaction_se",
                "interaction_p",
                "n_mechanism_states",
                "n_other_states",
                "sparse_comparison",
                "comparison_warning",
                "interpretation_scope",
            ]
        ]
    else:
        mechanism_heterogeneity_view = pd.DataFrame()

    robust_view = robust.copy()
    for col in ["baseline_coef", "baseline_p", "leave_one_min_coef", "leave_one_max_coef", "placebo_abs_p95"]:
        robust_view[col] = robust_view[col].map(fmt_p if col == "baseline_p" else fmt_num)
    robust_view = robust_view[
        [
            "outcome_label",
            "baseline_coef",
            "baseline_p",
            "twfe_specs_p05",
            "leave_one_min_coef",
            "leave_one_max_coef",
            "observed_exceeds_placebo_p95",
            "interpretation_flag",
        ]
    ]

    if not arkansas.empty:
        arkansas_view = arkansas.copy()
        for col in [
            "primary_coef",
            "arkansas_2021_coef",
            "arkansas_2021_delta",
            "arkansas_2023_coef",
            "arkansas_2023_delta",
        ]:
            arkansas_view[col] = arkansas_view[col].map(fmt_num)
        arkansas_view = arkansas_view[
            [
                "outcome_label",
                "primary_coef",
                "arkansas_2021_coef",
                "arkansas_2021_delta",
                "arkansas_2023_coef",
                "arkansas_2023_delta",
                "sign_retained",
                "p05_retained",
            ]
        ]
    else:
        arkansas_view = pd.DataFrame()

    lines = [
        "# Phase 1 Publishability Report",
        "",
        "## What Changed",
        "",
        "- Added an auditable permitless-carry policy table with one row per state.",
        "- Added Phase 2B legal edge-case handling for recent adopters, Vermont, and Arkansas.",
        "- Added Phase 2C Arkansas sensitivity checks that recode Arkansas as 2021 and 2023 while keeping the primary model excluded.",
        "- Verified non-adopter rows through the 1999-2024 panel window and documented the treatment rule in a legal-coding appendix.",
        "- Resolved clean-adopter mechanism fields for training, carry-permit background checks, and misdemeanor-violence permit screening.",
        "- Added Phase 3A external firearm-law controls from the Tufts State Firearm Law Database.",
        "- Added Phase 3B non-firearm confounder controls for health insurance access and drug-overdose mortality.",
        "- Added Phase 3B2 controls for state age structure, race/ethnicity, poverty, and HRSA mental-health provider access.",
        "- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.",
        "- Added a results hierarchy that separates the primary claim, secondary outcomes, sensitivity checks, exploratory checks, and appendix-only diagnostics.",
        "- Added exploratory policy-feature heterogeneity models for training removal, carry-permit background-check removal, and misdemeanor-screen removal.",
        "- Added robustness checks for COVID-period exclusion, pre-2020 restriction, population weighting, state trends, leave-one-adopter-out influence, and placebo timing among never-treated states.",
        "- Corrected the stale README change-score p-values against committed output tables.",
        "",
        "## Policy Audit Status",
        "",
        build_policy_audit_status_sentence(audit_status),
        "",
        markdown_table(audit_status, ["audit_status", "state_count"]),
        "",
        "## Policy Mechanism Summary",
        "",
        build_mechanism_summary_sentence(mechanisms),
        "",
        markdown_table(
            mechanisms,
            ["mechanism_field", "mechanism_value", "state_count"],
        ),
        "",
        "## Results Hierarchy",
        "",
        "The hierarchy below defines which estimates support the central claim and which estimates function as diagnostics. This keeps the main inference tied to the prespecified firearm-suicide outcome while using the broader result set to test specificity, stability, and boundary conditions.",
        "",
        markdown_table(
            hierarchy,
            [
                "evidence_tier",
                "items",
                "manuscript_role",
                "interpretation_boundary",
                "multiple_testing_role",
                "placement",
            ],
        ),
        "",
        "## Main TWFE Results",
        "",
        markdown_table(did_view, ["outcome_label", "coef", "p"]),
        "",
    ]

    if not firearm_law_view.empty:
        lines.extend(
            [
                "## External Firearm-Law Controls",
                "",
                build_firearm_law_control_sentence(firearm_law_controls),
                "",
                markdown_table(
                    firearm_law_view,
                    [
                        "outcome_label",
                        "baseline_coef",
                        "baseline_p",
                        "controlled_coef",
                        "controlled_p",
                        "controlled_delta",
                        "sign_retained",
                        "p05_retained",
                        "interpretation_flag",
                    ],
                ),
                "",
            ]
        )

    if not nonfirearm_view.empty:
        lines.extend(
            [
                "## Non-Firearm Confounder Controls",
                "",
                build_nonfirearm_confounder_sentence(nonfirearm_confounders),
                "",
                markdown_table(
                    nonfirearm_view,
                    [
                        "outcome_label",
                        "firearm_law_coef",
                        "firearm_law_p",
                        "health_access_coef",
                        "health_access_p",
                        "health_access_p05_retained",
                        "overdose_coef",
                        "overdose_p",
                        "overdose_p05_retained",
                        "health_access_overdose_coef",
                        "health_access_overdose_p",
                        "health_access_overdose_p05_retained",
                    ],
                ),
                "",
                "The overdose specifications use shorter samples because CDC's state injury and overdose dataset provides annual `Drug_OD` rates for 2019-2024. The combined health-access and overdose specification is therefore a narrow recent-window sensitivity, not a full-panel replacement.",
                "",
            ]
        )

    if not phase3b2_view.empty:
        lines.extend(
            [
                "## Phase 3B2 Demographic, Poverty, And Mental-Health Controls",
                "",
                build_phase3b2_confounder_sentence(phase3b2_confounders),
                "",
                markdown_table(
                    phase3b2_view,
                    [
                        "outcome_label",
                        "firearm_law_coef",
                        "firearm_law_p",
                        "demographic_poverty_coef",
                        "demographic_poverty_p",
                        "demographic_poverty_p05_retained",
                        "mental_health_access_coef",
                        "mental_health_access_p",
                        "mental_health_access_p05_retained",
                        "full_phase3b2_coef",
                        "full_phase3b2_p",
                        "full_phase3b2_p05_retained",
                    ],
                ),
                "",
                "The demographic-poverty specification uses Census Population Estimates state demographic shares and Census SAIPE poverty rates. The 2005-2009 age-structure controls use intercensal grouped-age approximations for the 18-34 category. The mental-health and full Phase 3B2 specifications use a short HRSA AHRF state/national workforce window, so they are sensitivity checks rather than replacements for the full-panel primary model.",
                "",
            ]
        )

    lines.extend(
        [
            "## Phase 3B2 Data Availability",
            "",
            "The table below documents which Phase 3B/3B2 confounder domains are available in the current panel and which source family supports each domain.",
            "",
            markdown_table(
                phase3b2_availability,
                [
                    "domain",
                    "target_columns",
                    "status",
                    "current_role",
                    "needed_source",
                ],
            ),
            "",
        ]
    )

    lines.extend(
        [
            "## Change-Score Results",
            "",
            markdown_table(welch_view, ["outcome_label", "window", "difference", "p"]),
            "",
            "## Modern Staggered-Adoption Sensitivity",
            "",
            build_modern_did_sentence(modern),
            "",
            markdown_table(
                modern_view,
                [
                    "outcome_label",
                    "cohort_att_w2",
                    "cohort_att_w3",
                    "cohort_att_w5",
                    "not_yet_post_mean_att",
                    "not_yet_pre_mean_att",
                    "not_yet_dynamic_rows",
                    "event_post_mean_coef",
                    "pretrend_flag_p05",
                    "interpretation_flag",
                ],
            ),
            "",
        ]
    )

    if not mechanism_heterogeneity_view.empty:
        lines.extend(
            [
                "## Exploratory Policy-Feature Heterogeneity",
                "",
                build_mechanism_heterogeneity_sentence(mechanism_heterogeneity),
                "",
                markdown_table(
                    mechanism_heterogeneity_view,
                    [
                        "outcome_label",
                        "mechanism_dimension",
                        "main_post_coef",
                        "interaction_coef",
                        "interaction_se",
                        "interaction_p",
                        "n_mechanism_states",
                        "n_other_states",
                        "sparse_comparison",
                        "comparison_warning",
                        "interpretation_scope",
                    ],
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Robustness Summary",
            "",
            "The state-trend specification attenuates several suicide estimates, so the strongest responsible claim remains associational. Firearm homicide remains unstable and statistically weak across the Phase 1 checks.",
            "",
            markdown_table(
                robust_view,
                [
                    "outcome_label",
                    "baseline_coef",
                    "baseline_p",
                    "twfe_specs_p05",
                    "leave_one_min_coef",
                    "leave_one_max_coef",
                    "observed_exceeds_placebo_p95",
                    "interpretation_flag",
                ],
            ),
            "",
        ]
    )

    if not arkansas_view.empty:
        lines.extend(
            [
                "## Arkansas Treatment-Year Sensitivity",
                "",
                build_arkansas_sensitivity_sentence(arkansas),
                "",
                markdown_table(
                    arkansas_view,
                    [
                        "outcome_label",
                        "primary_coef",
                        "arkansas_2021_coef",
                        "arkansas_2021_delta",
                        "arkansas_2023_coef",
                        "arkansas_2023_delta",
                        "sign_retained",
                        "p05_retained",
                    ],
                ),
                "",
            ]
        )

    lines.extend(
        [
        "## Interpretation Boundary",
        "",
        "Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2B adds recent within-panel adopters to the analytic treatment map and documents Vermont and Arkansas as non-clean adoption cases. Phase 2C keeps Arkansas out of the primary clean-adoption map and reports 2021 and 2023 Arkansas treatment-year sensitivities. The non-adopter audit pass verifies that the remaining untreated states do not have a statewide permitless concealed-carry adoption through the panel window, and the mechanism audit resolves clean-adopter coding for the main permit-screening fields. Phase 3A adds external firearm-law controls to test whether the main association survives adjustment for other state gun laws. Phase 3B adds health-access and overdose controls to test whether the suicide signal survives selected non-firearm confounders. Phase 3B2 adds demographic, poverty, and mental-health-provider controls; the demographic-poverty results preserve the firearm-suicide signal, while the short HRSA mental-health window is too limited to serve as a full-panel replacement. The expanded evidence still does not establish causal proof.",
        "",
        ]
    )
    return "\n".join(lines)


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    report = build_report()
    OUT_FILE.write_text(report, encoding="utf-8")
    print(f"Wrote: {OUT_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
