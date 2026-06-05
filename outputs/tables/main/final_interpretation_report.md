# Final Interpretation Report

## High-Level Conclusion

The strongest and most policy-relevant finding is that **permitless carry adoption is associated with higher firearm suicide rates after adoption**, while **firearm homicide does not show comparably strong evidence of change** in the main TWFE specification.

The mechanism layer indicates that the increase is **not confined only to firearm suicide** in the TWFE specification: non-firearm suicide and total suicide also rise. That means the evidence is **not a clean method-substitution-only story** in the current model set, even though firearm suicide remains a central part of the pattern.

The original Welch change-score design reinforces the suicide result: **firearm suicide is positive and statistically significant across all three windows (2y, 3y, 5y)**, whereas **firearm homicide is not statistically significant in any of the three windows**.

Total firearm deaths also show a positive post-adoption association, suggesting the suicide finding is large enough to matter for overall firearm mortality.

## Recommended One-Sentence Takeaway

"States adopting permitless carry laws experienced larger post-adoption increases in firearm suicide rates, while firearm homicide showed no comparably robust evidence of change; broader suicide outcomes also increased, suggesting the pattern may extend beyond a narrow method-substitution story."

## Firearm Suicide

- **TWFE DiD estimate:** 1.391 (SE 0.222, p = 0.0000) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.658, p = 0.0015 ***
  - 3-year window: difference = 0.634, p = 0.0006 ***
  - 5-year window: difference = 0.699, p = 0.0000 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 0.988, p = 0.0001 ***)

## Non-Firearm Suicide

- **TWFE DiD estimate:** 0.415 (SE 0.139, p = 0.0029) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.214, p = 0.2787 
  - 3-year window: difference = 0.134, p = 0.4192 
  - 5-year window: difference = 0.047, p = 0.7922 

- **Strongest heterogeneity signal:** high_rurality (interaction = 0.745, p = 0.0000 ***)

## Total Suicide

- **TWFE DiD estimate:** 1.805 (SE 0.294, p = 0.0000) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.872, p = 0.0029 ***
  - 3-year window: difference = 0.767, p = 0.0009 ***
  - 5-year window: difference = 0.746, p = 0.0038 ***

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.733, p = 0.0000 ***)

## Firearm Homicide

- **TWFE DiD estimate:** -0.234 (SE 0.338, p = 0.4889)  -> **no clear evidence**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = -0.034, p = 0.8812 
  - 3-year window: difference = 0.024, p = 0.9281 
  - 5-year window: difference = 0.035, p = 0.8989 

- **Strongest heterogeneity signal:** high_baseline_firearm_suicide (interaction = 0.048, p = 0.8945 )

## Total Firearm Deaths

- **TWFE DiD estimate:** 1.271 (SE 0.482, p = 0.0083) *** -> **positive association**.

- **Welch pre-post change-score results:**
  - 2-year window: difference = 0.537, p = 0.1456 
  - 3-year window: difference = 0.617, p = 0.1131 
  - 5-year window: difference = 0.718, p = 0.0636 *

- **Strongest heterogeneity signal:** high_rurality (interaction = 1.140, p = 0.1915 )

## Heterogeneity

- **Firearm Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 0.988, p = 0.0001 ***).
- **Non-Firearm Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 0.745, p = 0.0000 ***).
- **Total Suicide:** strongest heterogeneity appears along `high_rurality` (interaction = 1.733, p = 0.0000 ***).

Substantively, the cleanest recurring pattern is that **rurality matters**: several outcomes show larger post-adoption associations in more rural states.

## Political Selection

The descriptive state-level comparisons are more reliable than the logit coefficients here, because the adoption logit produced **perfect-separation / convergence warnings**.

That means the adoption model should be treated as **exploratory only**, not as a stable causal or predictive model.

- Descriptive adopter vs non-adopter means:
  - Republican vote share baseline: adopters = 0.579, non-adopters = 0.421
  - Gun ownership baseline: adopters = 0.476, non-adopters = 0.322
  - Rurality: adopters = 0.679, non-adopters = 0.433
  - Baseline firearm suicide: adopters = 8.849, non-adopters = 5.435

The political-selection section can therefore be framed as: **policy adoption is politically and structurally patterned**, but the formal adoption model is unstable in this small sample and should be interpreted cautiously.

## Results Summary

Across the main state-year panel models, permitless carry adoption was associated with a **1.391-point increase** in firearm suicide rates per 100,000 (p = 0.0000), while firearm homicide showed a **-0.234-point estimate** that was not statistically distinguishable from zero (p = 0.4889). Total suicide also increased in the main TWFE specification (coef = 1.805, p = 0.0000). Taken together, these findings suggest that permitless carry adoption is more consistently associated with suicide-related mortality than with firearm homicide in this dataset.


## Limitations

- This is still an **observational, state-level quasi-experimental design**, not a randomized experiment.
- The modern staggered-adoption checks reduce reliance on plain TWFE, but several pre-adoption signals remain, so the estimates should still be framed as associational sensitivity evidence.
- Policy-feature heterogeneity is exploratory because some mechanism-specific adopter groups are small or lack a source-verified comparison group.
- The political-selection logit showed **perfect-separation / convergence problems**, so those coefficients should not be overinterpreted.
- Some homicide observations are missing due to suppression / incomplete availability, so homicide results are based on a smaller effective sample.
- State-level analysis cannot identify which individuals changed behavior; avoid ecological fallacy language.

