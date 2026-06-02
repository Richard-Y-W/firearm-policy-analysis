# Phase 1 Publishability Report

## What Changed

- Added an auditable permitless-carry policy table with one row per state.
- Added Phase 2B legal edge-case handling for recent adopters, Vermont, and Arkansas.
- Added Phase 2C Arkansas sensitivity checks that recode Arkansas as 2021 and 2023 while keeping the primary model excluded.
- Verified non-adopter rows through the 1999-2024 panel window and documented the treatment rule in a legal-coding appendix.
- Resolved clean-adopter mechanism fields for training, carry-permit background checks, and misdemeanor-violence permit screening.
- Added Phase 3A external firearm-law controls from the Tufts State Firearm Law Database.
- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.
- Added robustness checks for COVID-period exclusion, pre-2020 restriction, population weighting, state trends, leave-one-adopter-out influence, and placebo timing among never-treated states.
- Corrected the stale README change-score p-values against committed output tables.

## Policy Audit Status

The policy audit table contains 50 states. The current audit records 26 source-verified current-adopter rows, 1 partial row, 1 baseline-permitless row, 1 ambiguous reviewed row, and 21 verified non-adopter rows; 0 rows remain marked `not_adopted_needs_review`. Partial, ambiguous, and baseline rows should not be treated as clean within-panel adoption events.

| audit_status | state_count |
| --- | --- |
| source_verified | 26 |
| not_adopted_verified | 21 |
| ambiguous_reviewed | 1 |
| partial | 1 |
| baseline_permitless_verified | 1 |

## Policy Mechanism Summary

Among the 26 clean source-verified adopter rows, 21 had a training requirement removed, 25 removed the carry-permit background-check screen, and 12 removed a permit-specific misdemeanor-violence screen. 7 rows retain permit-style eligibility standards but no longer require an application before carry.

| mechanism_field | mechanism_value | state_count |
| --- | --- | --- |
| training_requirement_removed | no_prior_training_requirement | 5 |
| training_requirement_removed | yes | 21 |
| background_check_permit_requirement_removed | yes | 25 |
| background_check_permit_requirement_removed | carry_permit_screen_removed_purchase_permit_retained | 1 |
| violent_misdemeanor_permit_screen_removed | precarry_check_removed_state_prohibitions_retained | 2 |
| violent_misdemeanor_permit_screen_removed | permit_specific_misdemeanor_screen_removed | 12 |
| violent_misdemeanor_permit_screen_removed | no_distinct_misdemeanor_screen_identified | 1 |
| violent_misdemeanor_permit_screen_removed | eligibility_standard_retained_no_precarry_check | 7 |
| violent_misdemeanor_permit_screen_removed | dangerousness_review_removed_no_distinct_misdemeanor_screen | 1 |
| violent_misdemeanor_permit_screen_removed | precarry_check_removed_purchase_screen_retained | 1 |
| violent_misdemeanor_permit_screen_removed | suitable_person_review_removed | 1 |
| violent_misdemeanor_permit_screen_removed | partial_violent_misdemeanor_restriction_retained | 1 |

## Main TWFE Results

| outcome_label | coef | p |
| --- | --- | --- |
| Firearm Suicide | 1.263 | <0.001 |
| Non-Firearm Suicide | 0.312 | 0.032 |
| Total Suicide | 1.576 | <0.001 |
| Firearm Homicide | -0.072 | 0.846 |
| Total Firearm Deaths | 1.341 | 0.004 |

## External Firearm-Law Controls

The external firearm-law control check adds controls for permit-to-purchase laws, waiting periods, universal background checks, ERPO/red-flag laws, safe-storage laws, stand-your-ground laws, and dealer licensing. 5 of 5 outcomes retain the same coefficient sign, and 3 retain p < 0.05 after those controls are added.

| outcome_label | baseline_coef | baseline_p | controlled_coef | controlled_p | controlled_delta | sign_retained | p05_retained | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.263 | <0.001 | 0.994 | <0.001 | -0.269 | True | True | survives_firearm_law_controls |
| Non-Firearm Suicide | 0.312 | 0.032 | 0.229 | 0.103 | -0.083 | True | False | attenuated_by_firearm_law_controls |
| Total Suicide | 1.576 | <0.001 | 1.223 | <0.001 | -0.352 | True | True | survives_firearm_law_controls |
| Firearm Homicide | -0.072 | 0.846 | -0.138 | 0.708 | -0.067 | True | False | attenuated_by_firearm_law_controls |
| Total Firearm Deaths | 1.341 | 0.004 | 0.956 | 0.024 | -0.385 | True | True | survives_firearm_law_controls |

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
| Firearm Suicide | 1.263 | <0.001 | 5 | 1.135 | 1.356 | True | stable_positive |
| Non-Firearm Suicide | 0.312 | 0.032 | 1 | 0.269 | 0.370 | True | stable_positive |
| Total Suicide | 1.576 | <0.001 | 6 | 1.420 | 1.727 | True | stable_positive |
| Firearm Homicide | -0.072 | 0.846 | 0 | -0.258 | 0.120 | False | sensitivity_required |
| Total Firearm Deaths | 1.341 | 0.004 | 4 | 1.129 | 1.592 | True | stable_positive |

## Arkansas Treatment-Year Sensitivity

The Arkansas sensitivity check keeps Arkansas excluded in the primary model and recodes it as 2021 and 2023 in alternate runs. 5 of 5 outcomes retain the same sign across both Arkansas codings, and 4 retain p < 0.05 across both codings.

| outcome_label | primary_coef | arkansas_2021_coef | arkansas_2021_delta | arkansas_2023_coef | arkansas_2023_delta | sign_retained | p05_retained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.263 | 1.261 | -0.002 | 1.277 | 0.013 | True | True |
| Non-Firearm Suicide | 0.312 | 0.333 | 0.021 | 0.324 | 0.012 | True | True |
| Total Suicide | 1.576 | 1.595 | 0.019 | 1.601 | 0.025 | True | True |
| Firearm Homicide | -0.072 | -0.031 | 0.041 | -0.066 | 0.006 | True | False |
| Total Firearm Deaths | 1.341 | 1.369 | 0.028 | 1.353 | 0.012 | True | True |

## Interpretation Boundary

Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2B adds recent within-panel adopters to the analytic treatment map and documents Vermont and Arkansas as non-clean adoption cases. Phase 2C keeps Arkansas out of the primary clean-adoption map and reports 2021 and 2023 Arkansas treatment-year sensitivities. The non-adopter audit pass verifies that the remaining untreated states do not have a statewide permitless concealed-carry adoption through the panel window, and the mechanism audit resolves clean-adopter coding for the main permit-screening fields. Phase 3A adds external firearm-law controls to test whether the main association survives adjustment for other state gun laws. It still does not establish causal proof. Non-firearm confounder expansion remains Phase 3 work.
