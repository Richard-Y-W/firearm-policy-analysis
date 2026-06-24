# Permitless Carry Analysis Status

Last updated: 2026-06-17.

## Current State

- Manuscript source files in `manuscript/` include the negative-control, NICS, covariate-balanced TWFE, stacked DiD, sex/age, and firearm-specific suicide-minus-nonfirearm checks.
- `manuscript/main.pdf` and `manuscript/supplementary.pdf` should be regenerated after any `.tex` or table update.
- The main robustness table now includes the firearm-specific suicide-minus-nonfirearm estimate: 0.976 deaths per 100,000, `p<0.001`.
- The NICS table now decomposes handgun, permit, permit-recheck, and combined handgun-or-permit checks and reports a COVID-excluded sample. The combined handgun-or-permit row shows no net increase in either sample.
- The political common-support audit is saved at `outputs/tables/political_selection/common_support_overlap.csv`; using the repository's 2012 vote-share baseline, 21 of 26 adopters sit above the verified non-adopter range for Republican two-party vote share. A 1999-2014 mean gives 20 of 26, so the qualitative non-overlap claim is not sensitive to this definition.
- Wild-cluster bootstrap inference is reproducible via `src/analysis/wild_cluster_bootstrap.py` and saved at `outputs/tables/robustness/wild_cluster_bootstrap_results.csv`.
- Fall, other non-transport injury excluding falls/poisoning, and accidental-poisoning exports are saved in `data/raw/cdc_wonder/`; the processed panel and estimates are saved at `data/processed/analysis_panel_extra_negative_control_mortality_1999_2024.csv` and `outputs/tables/negative_controls/extra_negative_control_twfe_results.csv`.

## Reproduction Commands

```bash
python3 -m src.data.process_nics
python3 -m src.analysis.firearm_specific_suicide
python3 -m src.analysis.nics_mechanism
python3 -m src.analysis.political_common_support
python3 -m src.analysis.wild_cluster_bootstrap
python3 -m src.analysis.extra_negative_controls
python3 -m src.analysis.main_robustness_table
python3 -m pytest
```

Compile from `manuscript/`:

```bash
latexmk -pdf main.tex
latexmk -pdf supplementary.tex
```

## Open Items

- Total firearm deaths remain a secondary outcome-family check, not a stable headline row: baseline 1.271 (`p=0.008`) attenuates to 0.070 (`p=0.806`) with state trends and 0.141 (`p=0.851`) under covariate balancing.
- Authorship is listed as equal contribution by Wang and Kim. Confirm that this matches the intended contribution statement before submission.
