# Phase 1 Publishability Report

## What Changed

- Added an auditable permitless-carry policy table with one row per state.
- Added Phase 2B legal edge-case handling for recent adopters, Vermont, and Arkansas.
- Added Phase 2C Arkansas sensitivity checks that recode Arkansas as 2021 and 2023 while keeping the primary model excluded.
- Verified non-adopter rows through the 1999-2024 panel window and documented the treatment rule in a legal-coding appendix.
- Resolved clean-adopter mechanism fields for training, carry-permit background checks, and misdemeanor-violence permit screening.
- Added Phase 3A external firearm-law controls from the Tufts State Firearm Law Database.
- Added Phase 3B non-firearm confounder controls for health insurance access and drug-overdose mortality.
- Added Phase 3B2 controls for state age structure, race/ethnicity, poverty, and HRSA mental-health provider access.
- Added cohort-based staggered-adoption sensitivity estimates and never-treated-control event-time estimates.
- Added a results hierarchy that separates the primary claim, secondary outcomes, sensitivity checks, exploratory checks, and appendix-only diagnostics.
- Added exploratory policy-feature heterogeneity models for training removal, carry-permit background-check removal, and misdemeanor-screen removal.
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

## Results Hierarchy

The hierarchy below defines which estimates support the central claim and which estimates function as diagnostics. This keeps the main inference tied to the prespecified firearm-suicide outcome while using the broader result set to test specificity, stability, and boundary conditions.

| evidence_tier | items | manuscript_role | interpretation_boundary | multiple_testing_role | placement |
| --- | --- | --- | --- | --- | --- |
| Primary outcome | Firearm Suicide | central confirmatory claim | main mortality claim | single prespecified primary outcome | main text |
| Secondary outcomes | Total Suicide; Non-Firearm Suicide; Firearm Homicide; Total Firearm Deaths | specificity and outcome-family interpretation | supports or limits the primary claim | main outcome family | main text |
| Sensitivity checks | firearm-law controls; health-access and overdose controls; staggered-adoption checks; Arkansas recoding; leave-one-out; placebo timing | design credibility and robustness | tests stability, not additional headline effects | diagnostic sensitivity layer | main text summary with appendix detail |
| Exploratory checks | policy-feature heterogeneity; rurality, gun-ownership, and baseline-risk heterogeneity | mechanism and boundary exploration | sample-size limited and hypothesis-generating | hypothesis-generating only | secondary results or appendix |
| Appendix-only diagnostics | cohort ATT rows; event-time rows; full legal source table; full robustness grids | audit trail and transparency | not interpreted as independent discoveries | not treated as confirmatory tests | appendix |

## Main TWFE Results

| outcome_label | coef | p |
| --- | --- | --- |
| Firearm Suicide | 1.391 | <0.001 |
| Non-Firearm Suicide | 0.415 | 0.003 |
| Total Suicide | 1.805 | <0.001 |
| Firearm Homicide | -0.234 | 0.489 |
| Total Firearm Deaths | 1.271 | 0.008 |

## External Firearm-Law Controls

The external firearm-law control check adds controls for permit-to-purchase laws, waiting periods, universal background checks, ERPO/red-flag laws, safe-storage laws, stand-your-ground laws, and dealer licensing. 5 of 5 outcomes retain the same coefficient sign, and 4 retain p < 0.05 after those controls are added.

| outcome_label | baseline_coef | baseline_p | controlled_coef | controlled_p | controlled_delta | sign_retained | p05_retained | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.391 | <0.001 | 1.096 | <0.001 | -0.294 | True | True | survives_firearm_law_controls |
| Non-Firearm Suicide | 0.415 | 0.003 | 0.330 | 0.012 | -0.085 | True | True | survives_firearm_law_controls |
| Total Suicide | 1.805 | <0.001 | 1.426 | <0.001 | -0.379 | True | True | survives_firearm_law_controls |
| Firearm Homicide | -0.234 | 0.489 | -0.316 | 0.340 | -0.082 | True | False | attenuated_by_firearm_law_controls |
| Total Firearm Deaths | 1.271 | 0.008 | 0.863 | 0.043 | -0.408 | True | True | survives_firearm_law_controls |

## Non-Firearm Confounder Controls

The non-firearm confounder check adds Census SAHIE uninsured rates as a health-access proxy and CDC drug-overdose mortality as a substance-use/distress proxy. 2 of 5 outcomes retain p < 0.05 in the 2008-2023 health-access specification, 0 retain p < 0.05 in the 2019-2024 overdose specification, and 1 retain p < 0.05 in the narrower 2019-2023 combined specification.

| outcome_label | firearm_law_coef | firearm_law_p | health_access_coef | health_access_p | health_access_p05_retained | overdose_coef | overdose_p | overdose_p05_retained | health_access_overdose_coef | health_access_overdose_p | health_access_overdose_p05_retained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.096 | <0.001 | 0.707 | <0.001 | True | 0.492 | 0.060 | False | 0.600 | 0.079 | False |
| Non-Firearm Suicide | 0.330 | 0.012 | 0.236 | 0.175 | False | -0.107 | 0.480 | False | -0.168 | 0.354 | False |
| Total Suicide | 1.426 | <0.001 | 0.943 | <0.001 | True | 0.384 | 0.204 | False | 0.432 | 0.234 | False |
| Firearm Homicide | -0.316 | 0.340 | -0.181 | 0.509 | False | -0.104 | 0.580 | False | 0.103 | 0.552 | False |
| Total Firearm Deaths | 0.863 | 0.043 | 0.503 | 0.095 | False | 0.316 | 0.328 | False | 0.676 | 0.035 | True |

The overdose specifications use shorter samples because CDC's state injury and overdose dataset provides annual `Drug_OD` rates for 2019-2024. The combined health-access and overdose specification is therefore a narrow recent-window sensitivity, not a full-panel replacement.

## Phase 3B2 Demographic, Poverty, And Mental-Health Controls

The Phase 3B2 confounder check adds Census Population Estimates state age and race/ethnicity shares, Census SAIPE poverty rates, and HRSA AHRF mental-health provider access. 2 of 5 outcomes retain p < 0.05 in the demographic-poverty specification, 0 retain p < 0.05 in the short HRSA mental-health access specification, and 0 retain p < 0.05 in the combined short-window Phase 3B2 specification.

| outcome_label | firearm_law_coef | firearm_law_p | demographic_poverty_coef | demographic_poverty_p | demographic_poverty_p05_retained | mental_health_access_coef | mental_health_access_p | mental_health_access_p05_retained | full_phase3b2_coef | full_phase3b2_p | full_phase3b2_p05_retained |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.096 | <0.001 | 0.695 | <0.001 | True | 0.116 | 0.744 | False | 0.176 | 0.633 | False |
| Non-Firearm Suicide | 0.330 | 0.012 | 0.153 | 0.301 | False | 0.105 | 0.686 | False | 0.077 | 0.769 | False |
| Total Suicide | 1.426 | <0.001 | 0.848 | <0.001 | True | 0.221 | 0.660 | False | 0.253 | 0.625 | False |
| Firearm Homicide | -0.316 | 0.340 | -0.347 | 0.182 | False | -0.137 | 0.621 | False | -0.055 | 0.878 | False |
| Total Firearm Deaths | 0.863 | 0.043 | 0.374 | 0.246 | False | 0.047 | 0.910 | False | 0.211 | 0.672 | False |

The demographic-poverty specification uses Census Population Estimates state demographic shares and Census SAIPE poverty rates. The 2005-2009 age-structure controls use intercensal grouped-age approximations for the 18-34 category. The mental-health and full Phase 3B2 specifications use a short HRSA AHRF state/national workforce window, so they are sensitivity checks rather than replacements for the full-panel primary model.

## Phase 3B2 Data Availability

The table below documents which Phase 3B/3B2 confounder domains are available in the current panel and which source family supports each domain.

| domain | target_columns | status | current_role | needed_source |
| --- | --- | --- | --- | --- |
| health insurance access | uninsured_under65_pct | modeled | Phase 3B modeled proxy | already processed from Census SAHIE |
| substance-use/distress proxy | drug_overdose_rate_per_100k | modeled | Phase 3B modeled proxy | already processed from CDC overdose data |
| age structure | share_age_18_34; share_age_35_64; share_age_65plus | modeled | Phase 3B2 modeled confounder | Census Population Estimates state age distribution |
| race/ethnicity | share_black_nonhispanic; share_hispanic; share_white_nonhispanic | modeled | Phase 3B2 modeled confounder | Census Population Estimates state race and ethnicity distribution |
| poverty | poverty_rate | modeled | Phase 3B2 modeled confounder | Census SAIPE state-year poverty estimates |
| mental-health provider access | mental_health_provider_rate_per_100k | modeled | Phase 3B2 short-window modeled confounder | HRSA AHRF state/national workforce counts |

## Change-Score Results

| outcome_label | window | difference | p |
| --- | --- | --- | --- |
| Firearm Homicide | 2 | -0.034 | 0.881 |
| Firearm Homicide | 3 | 0.024 | 0.928 |
| Firearm Homicide | 5 | 0.035 | 0.899 |
| Firearm Suicide | 2 | 0.658 | 0.001 |
| Firearm Suicide | 3 | 0.634 | <0.001 |
| Firearm Suicide | 5 | 0.699 | <0.001 |
| Non-Firearm Suicide | 2 | 0.214 | 0.279 |
| Non-Firearm Suicide | 3 | 0.134 | 0.419 |
| Non-Firearm Suicide | 5 | 0.047 | 0.792 |
| Total Firearm Deaths | 2 | 0.537 | 0.146 |
| Total Firearm Deaths | 3 | 0.617 | 0.113 |
| Total Firearm Deaths | 5 | 0.718 | 0.064 |
| Total Suicide | 2 | 0.872 | 0.003 |
| Total Suicide | 3 | 0.767 | <0.001 |
| Total Suicide | 5 | 0.746 | 0.004 |

## Modern Staggered-Adoption Sensitivity

The modern staggered-adoption check reports cohort-window ATT estimates, a not-yet-treated control dynamic ATT, and a never-treated-control event-time fixed-effect sensitivity check. 4 of 5 outcomes have positive post-adoption dynamic ATT estimates. `pretrend_flag_p05` marks outcomes with at least one statistically significant pre-adoption event-time coefficient.

| outcome_label | cohort_att_w2 | cohort_att_w3 | cohort_att_w5 | not_yet_post_mean_att | not_yet_pre_mean_att | not_yet_dynamic_rows | event_post_mean_coef | pretrend_flag_p05 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 0.601 | 0.577 | 0.641 | 0.387 | -0.352 | 10 | 0.651 | True | sensitivity_only_pretrend_signal |
| Non-Firearm Suicide | 0.270 | 0.239 | 0.241 | 0.077 | -0.155 | 10 | 0.209 | False | positive_post_adoption_sensitivity |
| Total Suicide | 0.871 | 0.816 | 0.882 | 0.464 | -0.507 | 10 | 0.861 | True | sensitivity_only_pretrend_signal |
| Firearm Homicide | -0.004 | -0.107 | -0.106 | -0.157 | 0.092 | 10 | -0.326 | False | no_positive_post_adoption_sensitivity |
| Total Firearm Deaths | 0.382 | 0.435 | 0.493 | 0.200 | -0.259 | 10 | 0.381 | True | sensitivity_only_pretrend_signal |

## Exploratory Policy-Feature Heterogeneity

The policy-feature heterogeneity models are exploratory because permitless-carry mechanism fields create small mechanism-specific adopter groups. 0 of 15 policy-feature interactions have p < 0.05; 5 have sparse or unavailable source-verified comparison groups. These rows should be interpreted as boundary checks, not as independent confirmatory findings.

| outcome_label | mechanism_dimension | main_post_coef | interaction_coef | interaction_se | interaction_p | n_mechanism_states | n_other_states | sparse_comparison | comparison_warning | interpretation_scope |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | training_removed | 1.200 | 0.227 | 0.309 | 0.462 | 21 | 5 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Firearm Suicide | permit_background_check_removed | NA | NA | NA | NA | 26 | 0 | True | no_source_verified_comparison_group | exploratory_sparse_comparison_do_not_interpret_as_mechanism |
| Firearm Suicide | misdemeanor_screen_removed | 1.429 | -0.083 | 0.375 | 0.826 | 12 | 14 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Non-Firearm Suicide | training_removed | 0.493 | -0.093 | 0.304 | 0.759 | 21 | 5 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Non-Firearm Suicide | permit_background_check_removed | NA | NA | NA | NA | 26 | 0 | True | no_source_verified_comparison_group | exploratory_sparse_comparison_do_not_interpret_as_mechanism |
| Non-Firearm Suicide | misdemeanor_screen_removed | 0.282 | 0.288 | 0.198 | 0.146 | 12 | 14 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Total Suicide | training_removed | 1.693 | 0.134 | 0.457 | 0.769 | 21 | 5 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Total Suicide | permit_background_check_removed | NA | NA | NA | NA | 26 | 0 | True | no_source_verified_comparison_group | exploratory_sparse_comparison_do_not_interpret_as_mechanism |
| Total Suicide | misdemeanor_screen_removed | 1.711 | 0.205 | 0.480 | 0.669 | 12 | 14 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Firearm Homicide | training_removed | 0.375 | -0.702 | 0.398 | 0.078 | 21 | 5 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Firearm Homicide | permit_background_check_removed | NA | NA | NA | NA | 26 | 0 | True | no_source_verified_comparison_group | exploratory_sparse_comparison_do_not_interpret_as_mechanism |
| Firearm Homicide | misdemeanor_screen_removed | -0.577 | 0.675 | 0.495 | 0.172 | 12 | 14 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Total Firearm Deaths | training_removed | 1.560 | -0.343 | 0.528 | 0.516 | 21 | 5 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |
| Total Firearm Deaths | permit_background_check_removed | NA | NA | NA | NA | 26 | 0 | True | no_source_verified_comparison_group | exploratory_sparse_comparison_do_not_interpret_as_mechanism |
| Total Firearm Deaths | misdemeanor_screen_removed | 1.047 | 0.487 | 0.700 | 0.487 | 12 | 14 | False | adequate_source_verified_comparison_group | exploratory_policy_feature_heterogeneity |

## Robustness Summary

The state-trend specification attenuates several suicide estimates, so the strongest responsible claim remains associational. Firearm homicide remains unstable and statistically weak across the Phase 1 checks.

| outcome_label | baseline_coef | baseline_p | twfe_specs_p05 | leave_one_min_coef | leave_one_max_coef | observed_exceeds_placebo_p95 | interpretation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.391 | <0.001 | 5 | 1.265 | 1.481 | True | stable_positive |
| Non-Firearm Suicide | 0.415 | 0.003 | 5 | 0.371 | 0.472 | True | stable_positive |
| Total Suicide | 1.805 | <0.001 | 6 | 1.656 | 1.954 | True | stable_positive |
| Firearm Homicide | -0.234 | 0.489 | 0 | -0.399 | -0.049 | False | sensitivity_required |
| Total Firearm Deaths | 1.271 | 0.008 | 4 | 1.058 | 1.532 | True | stable_positive |

## Arkansas Treatment-Year Sensitivity

The Arkansas sensitivity check keeps Arkansas excluded in the primary model and recodes it as 2021 and 2023 in alternate runs. 5 of 5 outcomes retain the same sign across both Arkansas codings, and 4 retain p < 0.05 across both codings.

| outcome_label | primary_coef | arkansas_2021_coef | arkansas_2021_delta | arkansas_2023_coef | arkansas_2023_delta | sign_retained | p05_retained |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Firearm Suicide | 1.391 | 1.361 | -0.030 | 1.379 | -0.012 | True | True |
| Non-Firearm Suicide | 0.415 | 0.416 | 0.002 | 0.406 | -0.008 | True | True |
| Total Suicide | 1.805 | 1.777 | -0.028 | 1.785 | -0.020 | True | True |
| Firearm Homicide | -0.234 | -0.205 | 0.028 | -0.250 | -0.016 | True | False |
| Total Firearm Deaths | 1.271 | 1.262 | -0.009 | 1.240 | -0.032 | True | True |

## Interpretation Boundary

Phase 1 strengthens the repository by making treatment coding auditable and by adding sensitivity checks that target staggered timing and robustness concerns. Phase 2B adds recent within-panel adopters to the analytic treatment map and documents Vermont and Arkansas as non-clean adoption cases. Phase 2C keeps Arkansas out of the primary clean-adoption map and reports 2021 and 2023 Arkansas treatment-year sensitivities. The non-adopter audit pass verifies that the remaining untreated states do not have a statewide permitless concealed-carry adoption through the panel window, and the mechanism audit resolves clean-adopter coding for the main permit-screening fields. Phase 3A adds external firearm-law controls to test whether the main association survives adjustment for other state gun laws. Phase 3B adds health-access and overdose controls to test whether the suicide signal survives selected non-firearm confounders. Phase 3B2 adds demographic, poverty, and mental-health-provider controls; the demographic-poverty results preserve the firearm-suicide signal, while the short HRSA mental-health window is too limited to serve as a full-panel replacement. The expanded evidence still does not establish causal proof.
