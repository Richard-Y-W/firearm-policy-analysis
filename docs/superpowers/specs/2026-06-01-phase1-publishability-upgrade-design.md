# Phase 1 Publishability Upgrade Design

## Goal

Raise the project from a transparent first-pass analysis to a publishability-focused repository by fixing internal consistency, making the permitless-carry treatment auditable, adding modern staggered-adoption estimators, and running targeted robustness checks.

## Scope

Phase 1 stays inside the current data and codebase. It does not attempt a full external-data expansion for opioid mortality, mental-health access, demographics, or every firearm-law control. Those additions remain Phase 2 because they require separate source evaluation and harmonization.

Phase 1 includes:

- README and report corrections where committed tables disagree with narrative text.
- A legal audit table for permitless-carry policy coding.
- Modern staggered-adoption estimates for the existing mortality outcomes.
- Robustness checks for COVID-era sensitivity, population weighting, state trends, leave-one-state-out influence, and placebo timing.
- Output tables, figures, and a short publishability report that separates association, identification limits, and stronger evidence.

## Reader Uncertainty

The current repository can be criticized on five points:

1. README result values are stale relative to committed CSV outputs.
2. The policy treatment is manually coded without an auditable legal table.
3. Permitless concealed carry, permitless open carry, and broad constitutional-carry language are not separated.
4. Household gun ownership stops in 2016 and is carried forward.
5. Event-study estimates show nonzero pre-adoption coefficients, so causal language would overreach.

The upgrade should make those issues visible and testable rather than burying them.

## Data Design

Add `data/policy/permitless_carry_legal_audit.csv` with one row per state. Required fields:

- `State`
- `permitless_year_current`
- `bill_or_statute`
- `enactment_date`
- `effective_date`
- `permitless_concealed`
- `permitless_open`
- `constitutional_carry_label`
- `minimum_age`
- `training_requirement_removed`
- `background_check_permit_requirement_removed`
- `violent_misdemeanor_permit_screen_removed`
- `source_url`
- `coding_notes`
- `audit_status`

The Phase 1 table may start as an auditable scaffold populated from the existing policy year plus explicit `audit_status` values. Rows that are not legally verified must be marked `needs_source`, not silently treated as verified.

## Analysis Design

Keep the existing `run_all_analysis.py` as the first-pass replication layer. Add separate scripts rather than mixing new estimators into the original file.

Planned modules:

- `src/analysis/policy_audit.py`: validates the legal audit table against the panel and writes an audit summary.
- `src/analysis/modern_did.py`: computes cohort-specific and event-time estimates designed for staggered adoption.
- `src/analysis/robustness_checks.py`: runs prespecified robustness checks.
- `src/analysis/phase1_publishability_report.py`: consolidates original, modern, and robustness results into a concise Markdown report.

The modern estimator layer should prioritize transparent implementation over fragile dependencies. If a Python package for a named estimator is unavailable, implement a documented cohort-based estimator and Sun-Abraham-style event-time specification with never-treated controls.

## Robustness Design

Run the following checks for each outcome:

- Exclude COVID-era years 2020-2021.
- Exclude post-2019 years as a stricter pre-COVID design.
- Estimate population-weighted TWFE.
- Add state-specific linear trends.
- Leave one adopting state out at a time.
- Assign placebo adoption years to never-treated states and compare placebo estimates with observed estimates.

Each robustness output must include the outcome, specification name, coefficient or summary statistic, standard error where applicable, p-value where applicable, number of observations, and interpretation flag.

## Documentation Design

Update `README.md` after outputs are regenerated. The README should:

- Use results from committed CSV outputs.
- State that Phase 1 modern estimators are sensitivity analyses unless their assumptions are satisfied.
- Separate permitless concealed carry, open carry, and constitutional-carry terminology.
- Explicitly describe the 2016 gun-ownership carry-forward limitation.
- Treat nonzero pre-adoption coefficients as a reason for cautious associational language.

Add `docs/phase1_publishability_upgrade.md` to summarize what changed, how to reproduce the new outputs, and which Phase 2 data additions remain.

## Testing And Verification

Add lightweight tests for helper functions where behavior is deterministic:

- Policy audit table schema validation.
- Treatment-year consistency checks.
- Robustness-specification filters.
- Cohort/event-time construction.

Verification commands:

- `python -m pytest`
- `python src/analysis/policy_audit.py`
- `python src/analysis/modern_did.py`
- `python src/analysis/robustness_checks.py`
- `python src/analysis/phase1_publishability_report.py`

If repository dependencies are incomplete, document the exact missing dependency or data-file blocker and leave the code paths explicit.

## Non-Goals

Phase 1 does not:

- Claim causal proof.
- Build a full paper manuscript.
- Collect all external firearm-law controls.
- Replace the existing analysis pipeline.
- Hide unverified legal coding behind a completed-looking binary treatment.

## Expected Novelty After Phase 1

If implemented cleanly, the project should move from "updated first-pass state panel" to "transparent post-2019 permitless-carry mortality analysis with auditable treatment coding and modern staggered-adoption sensitivity checks." That is a publishability-oriented contribution, especially if the suicide findings persist under the new estimators and robustness checks.
