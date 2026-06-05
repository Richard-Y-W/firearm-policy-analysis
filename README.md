# Permitless Carry and Firearm Mortality

This repository contains the data-processing code, analysis scripts, outputs, and manuscript files for a state-level study of permitless concealed carry adoption and firearm mortality in the United States.

The project uses a 50-state annual panel from 1999 through 2024. The primary outcome is firearm suicide. Secondary outcomes include total suicide, non-firearm suicide, firearm homicide, and total firearm deaths. The analysis is observational: the estimates should be read as adjusted state-level associations, not as individual-level causal proof.

## Manuscript

The current manuscript files are in `manuscript/`:

- `manuscript/main.pdf`
- `manuscript/main.tex`
- `manuscript/supplementary.pdf`
- `manuscript/supplementary.tex`
- `manuscript/references.bib`
- `manuscript/figures/`
- `manuscript/tables/`

The manuscript reports a source-audited permitless-carry treatment map, fixed-effects panel estimates, staggered-adoption diagnostics, event-time checks, covariate sensitivity analyses, legal-coding edge cases, and exploratory heterogeneity analyses.

## Main Finding

Across the main state-year specifications, permitless carry adoption is most consistently associated with higher firearm suicide and total suicide rates. Firearm homicide does not show a comparable positive association in the available state-year data. The firearm-suicide result remains positive across several robustness checks, but it attenuates under state-specific linear trends and event-time diagnostics show pre-adoption signal. Those diagnostics are central to the interpretation: the paper presents an observational association with meaningful identification limits.

## Data Sources

| Domain | Source | Role |
| --- | --- | --- |
| Mortality | CDC WONDER Underlying Cause of Death | State-year outcome rates |
| Permitless carry timing | Source-audited legal coding | Treatment definition and adoption year |
| Firearm laws | Tufts State Firearm Law Database | External firearm-law sensitivity controls |
| Firearm ownership | RAND state-level firearm ownership estimates | Descriptive selection and heterogeneity |
| Labor market | Bureau of Labor Statistics LAUS | Unemployment control |
| Income | Bureau of Economic Analysis | Per-capita income control |
| Rurality | USDA Economic Research Service | Baseline structural measure |
| Politics | MIT Election Lab presidential returns | Descriptive selection measure |
| Health access | Census SAHIE | Recent-window sensitivity controls |
| Drug overdose | CDC overdose mortality data | Recent-window sensitivity controls |

The primary processed panel is `data/processed/analysis_panel_full_outcomes.csv`. The legal audit is `data/policy/permitless_carry_legal_audit.csv`. Additional source notes are in `docs/master_references.md` and `docs/legal_coding_appendix.md`.

## Empirical Design

The analysis combines several complementary specifications:

1. Two-way fixed-effects state-year regressions with state and year fixed effects, unemployment, per-capita income, and state-clustered standard errors.
2. Population-weighted fixed-effects models.
3. Pre-COVID and COVID-excluded samples.
4. External firearm-law covariate sensitivity models.
5. Non-firearm contextual covariate sensitivity models.
6. State-specific linear trend specifications.
7. Change-score comparisons across 2-, 3-, and 5-year windows.
8. Staggered-adoption diagnostics using cohort windows, not-yet-treated comparisons, and event-time checks.
9. Arkansas treatment-year recoding, leave-one-adopter-out checks, and placebo timing among never-treated states.
10. Exploratory heterogeneity by baseline gun ownership, rurality, and baseline firearm-suicide rate.

These specifications are intended to show where the association is stable and where it weakens. They do not eliminate the central concern that permitless carry adoption is politically and structurally selected.

## Key Outputs

Publication figures:

- `outputs/figures/publication/figure_01_outcome_trends_by_adoption.pdf`
- `outputs/figures/publication/figure_02_twfe_coefficient_forest.pdf`
- `outputs/figures/publication/figure_03_change_score_robustness.pdf`
- `outputs/figures/publication/figure_04_event_study_grid.pdf`
- `outputs/figures/publication/figure_05_heterogeneity_interactions.pdf`
- `outputs/figures/publication/figure_06_political_selection_scatter.pdf`

Main tables and reports:

- `outputs/tables/did/twfe_did_main_results.csv`
- `outputs/tables/modern_did/modern_did_summary.csv`
- `outputs/tables/robustness/robustness_summary.csv`
- `outputs/tables/robustness/arkansas_treatment_sensitivity_summary.csv`
- `outputs/tables/main/final_interpretation_report.md`

## Repository Structure

```text
data/
  raw/                         Public source files
  processed/                   Cleaned state-year panels
  policy/                      Source-audited permitless-carry legal coding

docs/                          Source notes and method documentation

manuscript/                    LaTeX manuscript, supplement, figures, and PDFs

outputs/
  figures/                     Generated figures
  tables/                      Model outputs and summary reports

src/
  analysis/                    Estimation, robustness, plotting, and reports
  data/                        Data cleaning and panel construction

tests/                         Unit and regression tests for core code paths
```

## Reproducibility

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Build the processed panel:

```bash
python -m src.data.process_firearm_law_controls
python -m src.data.process_nonfirearm_confounders
python -m src.data.build_master_analysis_panel
python -m src.data.extend_master_outcomes
```

Run the main analysis:

```bash
python -m src.analysis.run_all_analysis
```

Run the robustness and diagnostic scripts:

```bash
python -m src.analysis.policy_audit
python -m src.analysis.firearm_law_control_sensitivity
python -m src.analysis.nonfirearm_confounder_sensitivity
python -m src.analysis.modern_did
python -m src.analysis.robustness_checks
python -m src.analysis.arkansas_sensitivity
python -m src.analysis.phase1_publishability_report
```

Generate publication figures and the interpretation report:

```bash
python -m src.analysis.make_publication_figures
python -m src.analysis.interpret_results
```

Compile the manuscript from `manuscript/`:

```bash
latexmk -pdf main.tex
latexmk -pdf supplementary.tex
```

Run tests:

```bash
python -m pytest
```

## Limitations

- Adoption is not random. Adopting states differ from non-adopting states in baseline firearm suicide, gun ownership, rurality, and political context.
- State-level mortality models cannot identify individual firearm acquisition, storage, carrying behavior, or clinical mechanisms.
- Staggered adoption and heterogeneous treatment effects limit simple two-way fixed-effects interpretation.
- Event-time diagnostics show pre-adoption signal, so the estimates should not be presented as definitive causal effects.
- Firearm-homicide rates have missing or suppressed state-years concentrated in small-population states.
- Some contextual covariates are available only in shorter recent windows.
- Arkansas, Vermont, and Mississippi require special legal-coding treatment and are documented separately in the audit.

## Project Information

Authors: Byung Kim and Yucheng Wang
