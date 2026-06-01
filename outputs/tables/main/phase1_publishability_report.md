# Phase 1 Publishability Report

## What Changed

- Added an auditable permitless-carry policy table with one row per state.
- Added Phase 2B legal edge-case handling for recent adopters, Vermont, and Arkansas.
- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.
- Added robustness checks for COVID-period exclusion, pre-2020 restriction, population weighting, state trends, leave-one-adopter-out influence, and placebo timing among never-treated states.
- Corrected the stale README change-score p-values against committed output tables.

## Policy Audit Status

The policy audit table contains 50 states. Phase 2B records 26 source-verified current-adopter rows, 1 partial row, 1 baseline-permitless row, and 1 ambiguous reviewed row; 21 rows remain marked `not_adopted_needs_review`. Partial, ambiguous, baseline, and not-yet-reviewed rows should not be treated as clean within-panel adoption events.

| audit_status | state_count |
| --- | --- |
| source_verified | 26 |
| not_adopted_needs_review | 21 |
| ambiguous_reviewed | 1 |
| partial | 1 |
| baseline_permitless_verified | 1 |

## Main TWFE Results

| outcome_label | coef | p |
| --- | --- | --- |
| Firearm Suicide | 1.263 | <0.001 |
| Non-Firearm Suicide | 0.312 | 0.032 |
| Total Suicide | 1.576 | <0.001 |
| Firearm Homicide | -0.072 | 0.846 |
| Total Firearm Deaths | 1.341 | 0.004 |

## Change-Score Results

| outcome_label | window | difference | p |
| --- | --- | --- | --- |
| Firearm Homicide | 2 | 0.016 | 0.944 |
| Firearm Homicide | 3 | 0.081 | 0.757 |
| Firearm Homicide | 5 | 0.112 | 0.686 |
| Firearm Suicide | 2 | 0.641 | 0.001 |
| Firearm Suicide | 3 | 0.603 | <0.001 |
| Firearm Suicide | 5 | 0.674 | <0.001 |
| Non-Firearm Suicide | 2 | 0.219 | 0.250 |
| Non-Firearm Suicide | 3 | 0.151 | 0.343 |
| Non-Firearm Suicide | 5 | 0.033 | 0.847 |
| Total Firearm Deaths | 2 | 0.561 | 0.117 |
| Total Firearm Deaths | 3 | 0.645 | 0.088 |
| Total Firearm Deaths | 5 | 0.779 | 0.042 |
| Total Suicide | 2 | 0.860 | 0.002 |
| Total Suicide | 3 | 0.754 | <0.001 |
| Total Suicide | 5 | 0.707 | 0.004 |

## Modern Staggered-Adoption Sensitivity

The cohort ATT columns compare cohort-specific treated changes with never-treated state changes. The event-time column is a never-treated-control fixed-effect sensitivity check; `pretrend_flag_p05` marks outcomes with at least one statistically significant pre-adoption coefficient.

| outcome_label | cohort_att_w2 | cohort_att_w3 | cohort_att_w5 | event_post_mean_coef | pretrend_flag_p05 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 0.591 | 0.553 | 0.627 | 0.617 | True | sensitivity_only_pretrend_signal |
| Non-Firearm Suicide | 0.263 | 0.232 | 0.199 | 0.154 | False | positive_post_adoption_sensitivity |
| Total Suicide | 0.854 | 0.785 | 0.827 | 0.772 | True | sensitivity_only_pretrend_signal |
| Firearm Homicide | 0.085 | -0.011 | 0.037 | -0.142 | False | no_positive_post_adoption_sensitivity |
| Total Firearm Deaths | 0.391 | 0.454 | 0.557 | 0.530 | True | sensitivity_only_pretrend_signal |

## Robustness Summary

The state-trend specification attenuates several suicide estimates, so the strongest responsible claim remains associational. Firearm homicide remains unstable and statistically weak across the Phase 1 checks.

| outcome_label | baseline_coef | baseline_p | twfe_specs_p05 | leave_one_min_coef | leave_one_max_coef | observed_exceeds_placebo_p95 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.263 | <0.001 | 4 | 1.135 | 1.356 | True | stable_positive |
| Non-Firearm Suicide | 0.312 | 0.032 | 1 | 0.269 | 0.370 | True | stable_positive |
| Total Suicide | 1.576 | <0.001 | 5 | 1.420 | 1.727 | True | stable_positive |
| Firearm Homicide | -0.072 | 0.846 | 0 | -0.258 | 0.120 | False | sensitivity_required |
| Total Firearm Deaths | 1.341 | 0.004 | 3 | 1.129 | 1.592 | True | stable_positive |

## Interpretation Boundary

Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2B adds recent within-panel adopters to the analytic treatment map and documents Vermont and Arkansas as non-clean adoption cases. It still does not establish causal proof. Remaining non-adopter coding, detailed statutory screening fields, and external confounder expansion remain Phase 2 work.
