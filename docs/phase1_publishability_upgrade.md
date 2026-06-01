# Phase 1 Publishability Upgrade

## Purpose

Phase 1 addresses credibility and novelty gaps in the original permitless-carry analysis without expanding into a full new external-data project. It keeps the original first-pass analysis intact and adds auditable treatment coding, staggered-adoption sensitivity estimates, and robustness checks.

## New Files

- `data/policy/permitless_carry_legal_audit.csv`: one-row-per-state legal audit scaffold.
- `src/analysis/policy_audit.py`: validates the policy audit table against the panel treatment years.
- `src/analysis/modern_did.py`: writes cohort ATT and never-treated-control event-time sensitivity outputs.
- `src/analysis/robustness_checks.py`: writes COVID, weighting, state-trend, leave-one-out, and placebo robustness outputs.
- `src/analysis/phase1_publishability_report.py`: consolidates Phase 1 findings into Markdown.
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
python3 src/analysis/phase1_publishability_report.py
```

Run tests:

```bash
python3 -m pytest
```

## Interpretation

Phase 1 strengthens the project by making the treatment definition auditable and by adding sensitivity checks that are more appropriate for staggered policy timing than a single TWFE coefficient alone. The strongest positive pattern remains in firearm suicide, total suicide, and total firearm deaths. Firearm homicide remains statistically weak.

The result should still be described as associational. Several event-time checks show pre-adoption signals, and state-specific linear trends attenuate several suicide estimates. The policy audit table is currently a scaffold: all states are marked `needs_source` until the legal source fields are verified.

## Phase 2 Work

Phase 2 should add data that require separate source vetting and harmonization:

- Verified legal sources for state policy coding, including bill/statute, enactment date, effective date, concealed/open-carry scope, age threshold, training requirement, and permit-screening changes.
- Other firearm-law controls, including waiting periods, permit-to-purchase, ERPO, safe storage, and stand-your-ground laws.
- Suicide-relevant confounders, including opioid mortality, mental-health access, demographics, and economic shocks.
- A manuscript-level methods appendix that describes legal coding decisions and estimator assumptions.
