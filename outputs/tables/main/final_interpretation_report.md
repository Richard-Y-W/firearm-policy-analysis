# Final Interpretation Report

## High-Level Conclusion

The strongest and most policy-relevant finding is that **permitless carry adoption is associated with higher firearm suicide rates after adoption**, while **firearm homicide does not show comparably strong evidence of change** in the main TWFE specification.

The mechanism layer indicates that the increase is **not confined only to firearm suicide** in the TWFE specification: non-firearm suicide and total suicide also rise. That means the evidence is **not a clean method-substitution-only story** in the current model set, even though firearm suicide remains a central part of the pattern.

The original Welch change-score design strongly reinforces the suicide result: **firearm suicide is positive and statistically significant across all three windows (2y, 3y, 5y)**, whereas **firearm homicide is not statistically significant in any of the three windows**.

Total firearm deaths also show a positive post-adoption association, suggesting the suicide finding is large enough to matter for overall firearm mortality.

## Recommended one-sentence takeaway

"States adopting permitless carry laws experienced larger post-adoption increases in firearm suicide rates, while firearm homicide showed no comparably robust evidence of change; broader suicide outcomes also increased, suggesting the pattern may extend beyond a narrow method-substitution story."

## Firearm Suicide

- **TWFE DiD estimate:** 1.277 (SE 0.230, p = 0.0000) *** → **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.720, p = 0.0006 ***
  - 3-year window: difference = 0.653, p = 0.0004 ***
  - 5-year window: difference = 0.731, p = 0.0000 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 0.863, p = 0.0032 ***)

## Non-Firearm Suicide

- **TWFE DiD estimate:** 0.313 (SE 0.145, p = 0.0306) ** → **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.223, p = 0.2833 
  - 3-year window: difference = 0.149, p = 0.3796 
  - 5-year window: difference = 0.029, p = 0.8732 

- **Strongest heterogeneity signal:** high_gun_ownership (interaction = 0.568, p = 0.0011 ***)

## Total Suicide

- **TWFE DiD estimate:** 1.589 (SE 0.319, p = 0.0000) *** → **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.943, p = 0.0011 ***
  - 3-year window: difference = 0.802, p = 0.0002 ***
  - 5-year window: difference = 0.760, p = 0.0020 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.353, p = 0.0025 ***)

## Firearm Homicide

- **TWFE DiD estimate:** -0.054 (SE 0.375, p = 0.8860)  → **no clear evidence**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.150, p = 0.3889 
  - 3-year window: difference = 0.243, p = 0.2157 
  - 5-year window: difference = 0.221, p = 0.3702 

- **Strongest heterogeneity signal:** high_baseline_firearm_suicide (interaction = 0.650, p = 0.2414 )

## Total Firearm Deaths

- **TWFE DiD estimate:** 1.376 (SE 0.472, p = 0.0036) *** → **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.777, p = 0.0091 ***
  - 3-year window: difference = 0.869, p = 0.0032 ***
  - 5-year window: difference = 0.962, p = 0.0034 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.659, p = 0.0291 **)

## Heterogeneity

- **Firearm Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 0.863, p = 0.0032 ***).
- **Non-Firearm Suicide:** strongest heterogeneity appears along `high_gun_ownership` (interaction = 0.568, p = 0.0011 ***).
- **Total Firearm Deaths:** strongest heterogeneity appears along `high_rurality` (interaction = 1.659, p = 0.0291 **).
- **Total Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 1.353, p = 0.0025 ***).

Substantively, the cleanest recurring pattern is that **rurality matters**: several outcomes show larger post-adoption associations in more rural states.

## Political Selection

The descriptive state-level comparisons are more reliable than the logit coefficients here, because the adoption logit produced **perfect-separation / convergence warnings**.

That means the adoption model should be treated as **exploratory only**, not as a stable causal or predictive model.

- Descriptive adopter vs non-adopter means:
  - Republican vote share baseline: adopters = 0.578, non-adopters = 0.444
  - Gun ownership baseline: adopters = 0.479, non-adopters = 0.357
  - Rurality: adopters = 0.695, non-adopters = 0.475
  - Baseline firearm suicide: adopters = 8.958, non-adopters = 5.917

The political-selection section can therefore be framed as: **policy adoption is politically and structurally patterned**, but the formal adoption model is unstable in this small sample and should be interpreted cautiously.

## Draft Results Paragraph

Across the main state-year panel models, permitless carry adoption was associated with a **1.277-point increase** in firearm suicide rates per 100,000 (p = 0.0000), while firearm homicide showed a **-0.054-point estimate** that was not statistically distinguishable from zero (p = 0.8860). Total suicide also increased in the main TWFE specification (coef = 1.589, p = 0.0000). Taken together, these findings suggest that permitless carry adoption is more consistently associated with suicide-related mortality than with firearm homicide in this dataset.


## Limitations

- This is still an **observational, state-level quasi-experimental design**, not a randomized experiment.
- The TWFE event-study / DiD results should be treated as a strong first-pass design, but a **modern staggered-adoption estimator** would be a worthwhile next upgrade.
- The political-selection logit showed **perfect-separation / convergence problems**, so those coefficients should not be overinterpreted.
- Some homicide observations are missing due to suppression / incomplete availability, so homicide results are based on a smaller effective sample.
- State-level analysis cannot identify which individuals changed behavior; avoid ecological fallacy language.

