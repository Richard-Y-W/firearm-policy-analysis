# Phase 1 Publishability Upgrade

## Purpose

Phase 1 addresses credibility and novelty gaps in the original permitless-carry analysis without expanding into a full new external-data project. It keeps the original first-pass analysis intact and adds auditable treatment coding, staggered-adoption sensitivity estimates, and robustness checks.

## New Files

- `data/policy/permitless_carry_legal_audit.csv`: one-row-per-state legal audit table.
- `src/analysis/policy_audit.py`: validates the policy audit table against the panel treatment years.
- `src/analysis/modern_did.py`: writes cohort ATT and never-treated-control event-time sensitivity outputs.
- `src/analysis/robustness_checks.py`: writes COVID, weighting, state-trend, leave-one-out, and placebo robustness outputs.
- `src/analysis/arkansas_sensitivity.py`: writes Arkansas 2021 and 2023 treatment-year sensitivity outputs.
- `src/analysis/phase1_publishability_report.py`: consolidates Phase 1 findings into Markdown.
- `docs/legal_coding_appendix.md`: summarizes the treatment rule, legal-audit statuses, and edge-case handling.
- `outputs/tables/policy_audit/policy_mechanism_summary.csv`: summarizes clean-adopter mechanism coding.
- `outputs/tables/robustness/arkansas_treatment_sensitivity.csv`: detailed Arkansas scenario estimates.
- `outputs/tables/robustness/arkansas_treatment_sensitivity_summary.csv`: outcome-level Arkansas sensitivity summary.
- `outputs/tables/main/phase1_publishability_report.md`: generated Phase 1 summary report.

## Reproduction

Run the original analysis first if the main outputs need to be regenerated:

```bash
python3 src/analysis/run_all_analysis.py
```

Then run the Phase 1 layer:

```bash
python3 src/analysis/policy_audit.py
python3 src/analysis/modern_did.py
python3 src/analysis/robustness_checks.py
python3 src/analysis/arkansas_sensitivity.py
python3 src/analysis/phase1_publishability_report.py
```

Run tests:

```bash
python3 -m pytest
```

## Interpretation

Phase 1 strengthens the project by making the treatment definition auditable and by adding sensitivity checks that are more appropriate for staggered policy timing than a single TWFE coefficient alone. The strongest positive pattern remains in firearm suicide, total suicide, and total firearm deaths. Firearm homicide remains statistically weak.

The result should still be described as associational. Several event-time checks show pre-adoption signals, and state-specific linear trends attenuate several suicide estimates. Phase 2B source-checks current-adopter legal timing and adds Nebraska, Louisiana, and South Carolina to the within-panel treatment map. Vermont is recorded as baseline permitless. Phase 2C keeps Arkansas out of the clean annual treatment map, then recodes it as 2021 and 2023 in sensitivity runs. Those Arkansas alternatives retain the same coefficient sign for all five main TWFE outcomes; firearm homicide remains statistically weak. The follow-on non-adopter audit pass verifies the remaining untreated states through 2024, and Phase 2D resolves clean-adopter mechanism fields for training, carry-permit background checks, and misdemeanor-violence permit screening.

## Phase 2 Work

The remaining Phase 2 work requires separate source vetting and harmonization:

- Other firearm-law controls, including waiting periods, permit-to-purchase, ERPO, safe storage, and stand-your-ground laws.
- Suicide-relevant confounders, including opioid mortality, mental-health access, demographics, and economic shocks.
- A manuscript-level methods appendix that expands the legal-coding appendix and describes estimator assumptions.
