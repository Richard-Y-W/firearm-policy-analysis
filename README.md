# Permitless Carry Policy Analysis (WRHC 2026)

This repository analyzes whether adoption of permitless carry firearm laws is associated with changes in firearm mortality rates across U.S. states.

The project constructs a state-year panel dataset for 1999-2024 and evaluates post-adoption mortality patterns using multiple empirical strategies:

- Change-score comparisons
- Two-way fixed effects difference-in-differences
- Event-study analysis
- Heterogeneity analysis
- Political-selection analysis

The goal is not to establish causal proof, but to provide transparent empirical comparisons using publicly available data.

## Research Question

After a state adopts permitless carry laws, do firearm mortality rates change differently than in states that do not adopt the policy?

The analysis examines:

- Firearm suicide
- Firearm homicide
- Total firearm deaths
- Total suicide
- Non-firearm suicide

## Data Sources

The project integrates multiple public datasets into a unified state-year panel.

### Mortality Data

CDC WONDER - Underlying Cause of Death

Outcomes are derived from ICD-10 mortality codes and converted to rates per 100,000 residents:

- Firearm suicide
- Firearm homicide
- Total firearm deaths
- Total suicide
- Non-firearm suicide

Coverage: 1999-2024.

### Covariates

- RAND State-Level Household Firearm Ownership Database: estimated household firearm ownership share and baseline firearm ownership.
- Bureau of Labor Statistics LAUS: state unemployment rate.
- Bureau of Economic Analysis: state per-capita personal income.
- USDA Economic Research Service: Rural-Urban Continuum Codes, mean rurality, and share of non-metro counties.
- MIT Election Lab U.S. Presidential Elections: Republican two-party vote share and baseline political environment.

Permitless carry adoption years were coded manually based on the current panel definition. Phase 1 adds `data/policy/permitless_carry_legal_audit.csv` so the legal coding can be audited state by state. The table is currently a scaffold marked `needs_source`; it does not yet constitute a completed legal-source appendix.

## Panel Dataset

Final dataset structure:

- State x year panel
- 1999-2024
- 50 U.S. states

Core variables:

- `firearm_suicide_rate_per_100k`
- `firearm_homicide_rate_per_100k`
- `total_firearm_rate_per_100k`
- `total_suicide_rate_per_100k`
- `nonfirearm_suicide_rate_per_100k`

Controls:

- `unemployment_rate`
- `income_pc`
- `gun_ownership`
- `rurality`

Policy variables:

- `permitless_year`
- `post_permitless`
- `years_since_permitless`

## Empirical Methods

### Change-Score Design

For each state:

`A = mean(post-adoption rate) - mean(pre-adoption rate)`

Change scores are compared between adopting states and non-adopting states using Welch two-sample t-tests.

Robustness windows:

- 2-year pre vs. 2-year post
- 3-year pre vs. 3-year post
- 5-year pre vs. 5-year post

### Difference-in-Differences

Panel regressions estimate:

```text
Outcome_st =
    beta * PostPermitless_st
    + state fixed effects
    + year fixed effects
    + unemployment
    + income
    + error
```

Standard errors are clustered at the state level.

### Event Study

Event-time models estimate dynamic effects relative to the year of policy adoption. These figures support inspection of pre-policy trends and post-policy outcome evolution.

### Heterogeneity Analysis

The analysis tests whether policy associations differ across:

- Baseline firearm ownership
- Rurality
- Baseline firearm suicide rates

### Political Selection

The project examines whether policy adoption is systematically associated with political ideology, firearm prevalence, and structural suicide risk.

### Phase 1 Publishability Upgrade

The Phase 1 upgrade adds:

- Policy-audit scaffolding for permitless carry coding.
- Cohort-based staggered-adoption sensitivity estimates.
- Never-treated-control event-time sensitivity estimates.
- Robustness checks excluding COVID-era years, restricting to pre-2020 years, population weighting, state-specific linear trends, leave-one-adopter-out influence, and placebo timing among never-treated states.

These checks strengthen transparency but do not convert the project into causal proof. The state-trend specification attenuates several suicide estimates, and several event-study specifications show pre-adoption signals, so the responsible interpretation remains associational.

## Results

### Change-Score Results

| Outcome | Window | Difference | p-value |
| --- | --- | ---: | ---: |
| Firearm homicide | 2y | 0.150 | 0.389 |
| Firearm homicide | 3y | 0.243 | 0.216 |
| Firearm homicide | 5y | 0.221 | 0.370 |
| Firearm suicide | 2y | 0.720 | 0.000553 |
| Firearm suicide | 3y | 0.653 | 0.000445 |
| Firearm suicide | 5y | 0.731 | 0.000001 |
| Non-firearm suicide | 2y | 0.223 | 0.283 |
| Non-firearm suicide | 3y | 0.149 | 0.380 |
| Non-firearm suicide | 5y | 0.029 | 0.873 |
| Total firearm deaths | 2y | 0.777 | 0.009 |
| Total firearm deaths | 3y | 0.869 | 0.003 |
| Total firearm deaths | 5y | 0.962 | 0.003 |
| Total suicide | 2y | 0.943 | 0.001 |
| Total suicide | 3y | 0.802 | 0.000222 |
| Total suicide | 5y | 0.760 | 0.002 |

The strongest change-score signals appear in firearm suicide, total suicide, and total firearm deaths. Firearm homicide shows no statistically significant change across any robustness window.

### Phase 1 Sensitivity Summary

The main TWFE estimates remain positive for firearm suicide, total suicide, non-firearm suicide, and total firearm deaths, while firearm homicide remains statistically weak. Cohort ATT estimates are positive for suicide-related outcomes and total firearm deaths. Robustness checks show stable positive signs for firearm suicide and total suicide across leave-one-adopter-out checks, but state-specific linear trends attenuate several suicide estimates. The Phase 1 report is available at `outputs/tables/main/phase1_publishability_report.md`.

## Figures

### Publication Figures

The publication figure set is available in `outputs/figures/publication` as both PNG and PDF files.

![Publication trends](outputs/figures/publication/figure_01_outcome_trends_by_adoption.png)

![TWFE coefficient forest](outputs/figures/publication/figure_02_twfe_coefficient_forest.png)

![Change-score robustness](outputs/figures/publication/figure_03_change_score_robustness.png)

![Event-study grid](outputs/figures/publication/figure_04_event_study_grid.png)

![Heterogeneity interactions](outputs/figures/publication/figure_05_heterogeneity_interactions.png)

![Political selection scatter](outputs/figures/publication/figure_06_political_selection_scatter.png)

### Event Studies

![Event study homicide](outputs/figures/event_study/event_study_firearm_homicide.png)

![Event study firearm suicide](outputs/figures/event_study/event_study_firearm_suicide.png)

![Event study non-firearm suicide](outputs/figures/event_study/event_study_nonfirearm_suicide.png)

![Event study total firearm](outputs/figures/event_study/event_study_total_firearm.png)

![Event study total suicide](outputs/figures/event_study/event_study_total_suicide.png)

### Heterogeneity

![Heterogeneity firearm suicide](outputs/figures/heterogeneity/high_vs_low_baseline_firearm_suicide.png)

![Heterogeneity gun ownership](outputs/figures/heterogeneity/high_vs_low_gun_ownership.png)

![Heterogeneity rurality](outputs/figures/heterogeneity/high_vs_low_rurality.png)

### Political Selection

![Political selection scatter](outputs/figures/main/political_selection_scatter.png)

## Overall Interpretation

Across multiple empirical strategies, states adopting permitless carry laws tend to experience larger increases in firearm suicide rates relative to non-adopting states. No statistically significant association is detected between permitless carry adoption and firearm homicide rates.

Panel regressions also indicate increases in total suicide rates, suggesting that observed changes may reflect broader suicide trends rather than firearm-specific mechanisms alone. Associations appear stronger in states with higher baseline firearm suicide rates, higher firearm ownership, and greater rurality.

These findings should be interpreted cautiously due to the observational design and potential policy selection effects. Further research using individual-level data or alternative identification strategies would be necessary to establish causal mechanisms.

## Limitations

- The study uses quasi-experimental comparisons and cannot establish causal effects.
- States adopting permitless carry differ structurally and politically from non-adopting states.
- State-level analysis cannot identify individual-level behavioral mechanisms.
- Two-way fixed effects models may have limitations under staggered policy timing; Phase 1 adds sensitivity checks but does not eliminate all identification concerns.
- The legal audit table is currently a scaffold. All states remain marked `needs_source` until bill text, effective dates, concealed/open-carry scope, age thresholds, and permit-screening changes are verified.
- Gun ownership data are available through 2016 in the current processed panel and are carried forward afterward.
- Some event-study outputs contain statistically significant pre-adoption coefficients, so the results should be framed as associations.

## Repository Structure

```text
src/
    data/
        build_master_analysis_panel.py
        extend_master_outcomes.py
        process_unemployment.py
        process_income.py
        process_gun_ownership.py
        process_rurality.py
        process_politics.py

    analysis/
        run_all_analysis.py
        interpret_results.py
        policy_audit.py
        modern_did.py
        robustness_checks.py
        phase1_publishability_report.py

data/
    raw/
    processed/
    policy/

outputs/
    figures/
    tables/
```

## Reproducing the Analysis

Build the panel dataset:

```bash
python3 src/data/build_master_analysis_panel.py
python3 src/data/extend_master_outcomes.py
```

Run the full empirical analysis:

```bash
python3 src/analysis/run_all_analysis.py
```

Generate the interpretation report:

```bash
python3 src/analysis/interpret_results.py
```

Generate the publication figures:

```bash
python3 src/analysis/make_publication_figures.py
```

Run the Phase 1 publishability upgrade:

```bash
python3 src/analysis/policy_audit.py
python3 src/analysis/modern_did.py
python3 src/analysis/robustness_checks.py
python3 src/analysis/phase1_publishability_report.py
```

Outputs are written to `outputs/tables` and `outputs/figures`.

## Authors

Yucheng (Richard) Wang  
WRHC 2026 Research Project
