# Final Interpretation Report

## High-Level Conclusion

The strongest and most policy-relevant finding is that **permitless carry adoption is associated with higher firearm suicide rates after adoption**, while **firearm homicide does not show comparably strong evidence of change** in the main TWFE specification.

The mechanism layer indicates that the increase is **not confined only to firearm suicide** in the TWFE specification: non-firearm suicide and total suicide also rise. That means the evidence is **not a clean method-substitution-only story** in the current model set, even though firearm suicide remains a central part of the pattern.

The original Welch change-score design reinforces the suicide result: **firearm suicide is positive and statistically significant across all three windows (2y, 3y, 5y)**, whereas **firearm homicide is not statistically significant in any of the three windows**.

Total firearm deaths also show a positive post-adoption association, suggesting the suicide finding is large enough to matter for overall firearm mortality.

## Recommended One-Sentence Takeaway

"States adopting permitless carry laws experienced larger post-adoption increases in firearm suicide rates, while firearm homicide showed no comparably robust evidence of change; broader suicide outcomes also increased, suggesting the pattern may extend beyond a narrow method-substitution story."

## Firearm Suicide

- **TWFE DiD estimate:** 1.263 (SE 0.227, p = 0.0000) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.641, p = 0.0013 ***
  - 3-year window: difference = 0.603, p = 0.0008 ***
  - 5-year window: difference = 0.674, p = 0.0000 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 0.870, p = 0.0025 ***)

## Non-Firearm Suicide

- **TWFE DiD estimate:** 0.312 (SE 0.146, p = 0.0322) ** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.219, p = 0.2499
  - 3-year window: difference = 0.151, p = 0.3427
  - 5-year window: difference = 0.033, p = 0.8472

- **Strongest heterogeneity signal:** high_gun_ownership (interaction = 0.549, p = 0.0012 ***)

## Total Suicide

- **TWFE DiD estimate:** 1.576 (SE 0.316, p = 0.0000) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.860, p = 0.0023 ***
  - 3-year window: difference = 0.754, p = 0.0007 ***
  - 5-year window: difference = 0.707, p = 0.0041 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.325, p = 0.0024 ***)

## Firearm Homicide

- **TWFE DiD estimate:** -0.072 (SE 0.368, p = 0.8455)  -> **no clear evidence**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.016, p = 0.9442
  - 3-year window: difference = 0.081, p = 0.7567
  - 5-year window: difference = 0.112, p = 0.6859

- **Strongest heterogeneity signal:** high_baseline_firearm_suicide (interaction = 0.648, p = 0.2183 )

## Total Firearm Deaths

- **TWFE DiD estimate:** 1.341 (SE 0.471, p = 0.0044) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.561, p = 0.1166
  - 3-year window: difference = 0.645, p = 0.0878 *
  - 5-year window: difference = 0.779, p = 0.0424 **

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.630, p = 0.0256 **)

## Heterogeneity

- **Firearm Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 0.870, p = 0.0025 ***).
- **Non-Firearm Suicide:** strongest heterogeneity appears along `high_gun_ownership` (interaction = 0.549, p = 0.0012 ***).
- **Total Firearm Deaths:** strongest heterogeneity appears along `high_rurality` (interaction = 1.630, p = 0.0256 **).
- **Total Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 1.325, p = 0.0024 ***).

Substantively, the cleanest recurring pattern is that **rurality matters**: several outcomes show larger post-adoption associations in more rural states.

## Political Selection

The descriptive state-level comparisons are more reliable than the logit coefficients here, because the adoption logit produced **perfect-separation / convergence warnings**.

That means the adoption model should be treated as **exploratory only**, not as a stable causal or predictive model.

- Descriptive adopter vs non-adopter means:
  - Republican vote share baseline: adopters = 0.579, non-adopters = 0.425
  - Gun ownership baseline: adopters = 0.479, non-adopters = 0.342
  - Rurality: adopters = 0.683, non-adopters = 0.461
  - Baseline firearm suicide: adopters = 8.847, non-adopters = 5.734

The political-selection section can therefore be framed as: **policy adoption is politically and structurally patterned**, but the formal adoption model is unstable in this small sample and should be interpreted cautiously.

## Draft Results Paragraph

Across the main state-year panel models, permitless carry adoption was associated with a **1.263-point increase** in firearm suicide rates per 100,000 (p = 0.0000), while firearm homicide showed a **-0.072-point estimate** that was not statistically distinguishable from zero (p = 0.8455). Total suicide also increased in the main TWFE specification (coef = 1.576, p = 0.0000). Taken together, these findings suggest that permitless carry adoption is more consistently associated with suicide-related mortality than with firearm homicide in this dataset.


## Limitations

- This is still an **observational, state-level quasi-experimental design**, not a randomized experiment.
- The modern staggered-adoption checks reduce reliance on plain TWFE, but several pre-adoption signals remain, so the estimates should still be framed as associational sensitivity evidence.
- Policy-feature heterogeneity is exploratory because some mechanism-specific adopter groups are small or lack a source-verified comparison group.
- The political-selection logit showed **perfect-separation / convergence problems**, so those coefficients should not be overinterpreted.
- Some homicide observations are missing due to suppression / incomplete availability, so homicide results are based on a smaller effective sample.
- State-level analysis cannot identify which individuals changed behavior; avoid ecological fallacy language.
