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


def build_report() -> str:
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    audit_status = pd.read_csv(TABLES / "policy_audit" / "policy_audit_status_counts.csv")
    mechanisms = pd.read_csv(POLICY_MECHANISM_FILE)
    modern = pd.read_csv(TABLES / "modern_did" / "modern_did_summary.csv")
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

    welch_view = welch.copy()
    welch_view["difference"] = welch_view["difference"].map(fmt_num)
    welch_view["p"] = welch_view["p_value"].map(fmt_p)
    welch_view = welch_view[["outcome_label", "window", "difference", "p"]]

    modern_view = modern.copy()
    for col in ["cohort_att_w2", "cohort_att_w3", "cohort_att_w5", "event_post_mean_coef", "event_pretrend_min_p"]:
        modern_view[col] = modern_view[col].map(fmt_num if col != "event_pretrend_min_p" else fmt_p)
    modern_view = modern_view[
        [
            "outcome_label",
            "cohort_att_w2",
            "cohort_att_w3",
            "cohort_att_w5",
            "event_post_mean_coef",
            "pretrend_flag_p05",
            "interpretation_flag",
        ]
    ]

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
        "- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.",
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
        "## Main TWFE Results",
        "",
        markdown_table(did_view, ["outcome_label", "coef", "p"]),
        "",
        "## Change-Score Results",
        "",
        markdown_table(welch_view, ["outcome_label", "window", "difference", "p"]),
        "",
        "## Modern Staggered-Adoption Sensitivity",
        "",
        "The cohort ATT columns compare cohort-specific treated changes with never-treated state changes. The event-time column is a never-treated-control fixed-effect sensitivity check; `pretrend_flag_p05` marks outcomes with at least one statistically significant pre-adoption coefficient.",
        "",
        markdown_table(
            modern_view,
            [
                "outcome_label",
                "cohort_att_w2",
                "cohort_att_w3",
                "cohort_att_w5",
                "event_post_mean_coef",
                "pretrend_flag_p05",
                "interpretation_flag",
            ],
        ),
        "",
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
        "Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2B adds recent within-panel adopters to the analytic treatment map and documents Vermont and Arkansas as non-clean adoption cases. Phase 2C keeps Arkansas out of the primary clean-adoption map and reports 2021 and 2023 Arkansas treatment-year sensitivities. The non-adopter audit pass verifies that the remaining untreated states do not have a statewide permitless concealed-carry adoption through the panel window, and the mechanism audit resolves clean-adopter coding for the main permit-screening fields. It still does not establish causal proof. External confounder expansion remains Phase 2 work.",
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
