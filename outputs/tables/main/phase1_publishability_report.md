# Phase 1 Publishability Report

## What Changed

- Added an auditable permitless-carry policy table with one row per state.
- Added Phase 2A source checks for current-adopter legal timing and carry-scope fields.
- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.
- Added robustness checks for COVID-period exclusion, pre-2020 restriction, population weighting, state trends, leave-one-adopter-out influence, and placebo timing among never-treated states.
- Corrected the stale README change-score p-values against committed output tables.

## Policy Audit Status

The policy audit table contains 50 states. Phase 2A adds 23 source-verified current-adopter rows and 1 partial row; 26 rows remain marked `not_adopted_needs_review`. Partial and not-yet-reviewed rows should not be treated as final legal coding.

| audit_status | state_count |
| --- | --- |
| not_adopted_needs_review | 26 |
| source_verified | 23 |
| partial | 1 |

## Main TWFE Results

| outcome_label | coef | p |
| --- | --- | --- |
| Firearm Suicide | 1.277 | <0.001 |
| Non-Firearm Suicide | 0.313 | 0.031 |
| Total Suicide | 1.589 | <0.001 |
| Firearm Homicide | -0.054 | 0.886 |
| Total Firearm Deaths | 1.376 | 0.004 |

## Change-Score Results

| outcome_label | window | difference | p |
| --- | --- | --- | --- |
| Firearm Homicide | 2 | 0.150 | 0.389 |
| Firearm Homicide | 3 | 0.243 | 0.216 |
| Firearm Homicide | 5 | 0.221 | 0.370 |
| Firearm Suicide | 2 | 0.720 | <0.001 |
| Firearm Suicide | 3 | 0.653 | <0.001 |
| Firearm Suicide | 5 | 0.731 | <0.001 |
| Non-Firearm Suicide | 2 | 0.223 | 0.283 |
| Non-Firearm Suicide | 3 | 0.149 | 0.380 |
| Non-Firearm Suicide | 5 | 0.029 | 0.873 |
| Total Firearm Deaths | 2 | 0.777 | 0.009 |
| Total Firearm Deaths | 3 | 0.869 | 0.003 |
| Total Firearm Deaths | 5 | 0.962 | 0.003 |
| Total Suicide | 2 | 0.943 | 0.001 |
| Total Suicide | 3 | 0.802 | <0.001 |
| Total Suicide | 5 | 0.760 | 0.002 |

## Modern Staggered-Adoption Sensitivity

The cohort ATT columns compare cohort-specific treated changes with never-treated state changes. The event-time column is a never-treated-control fixed-effect sensitivity check; `pretrend_flag_p05` marks outcomes with at least one statistically significant pre-adoption coefficient.

| outcome_label | cohort_att_w2 | cohort_att_w3 | cohort_att_w5 | event_post_mean_coef | pretrend_flag_p05 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 0.661 | 0.602 | 0.682 | 0.611 | True | sensitivity_only_pretrend_signal |
| Non-Firearm Suicide | 0.270 | 0.238 | 0.199 | 0.127 | False | positive_post_adoption_sensitivity |
| Total Suicide | 0.931 | 0.839 | 0.880 | 0.738 | True | sensitivity_only_pretrend_signal |
| Firearm Homicide | 0.201 | 0.106 | 0.116 | -0.066 | False | no_positive_post_adoption_sensitivity |
| Total Firearm Deaths | 0.552 | 0.629 | 0.698 | 0.595 | True | sensitivity_only_pretrend_signal |

## Robustness Summary

The state-trend specification attenuates several suicide estimates, so the strongest responsible claim remains associational. Firearm homicide remains unstable and statistically weak across the Phase 1 checks.

| outcome_label | baseline_coef | baseline_p | twfe_specs_p05 | leave_one_min_coef | leave_one_max_coef | observed_exceeds_placebo_p95 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.277 | <0.001 | 4 | 1.145 | 1.373 | True | stable_positive |
| Non-Firearm Suicide | 0.313 | 0.031 | 1 | 0.269 | 0.371 | True | stable_positive |
| Total Suicide | 1.589 | <0.001 | 4 | 1.431 | 1.744 | True | stable_positive |
| Firearm Homicide | -0.054 | 0.886 | 0 | -0.248 | 0.145 | False | sensitivity_required |
| Total Firearm Deaths | 1.376 | 0.004 | 4 | 1.160 | 1.635 | True | stable_positive |

## Interpretation Boundary

Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2A source-checks current-adopter legal timing and core carry-scope fields, but it does not change the analytic treatment years or establish causal proof. Non-adopter coding, detailed statutory screening fields, and external confounder expansion remain Phase 2 work.
