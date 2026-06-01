# Phase 1 Publishability Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Phase 1 credibility and novelty upgrades described in `docs/superpowers/specs/2026-06-01-phase1-publishability-upgrade-design.md`.

**Architecture:** Keep the original `src/analysis/run_all_analysis.py` pipeline intact and add a separate Phase 1 analysis layer. Shared deterministic helpers live in `src/analysis/phase1_utils.py`, command-line scripts write versioned outputs under `outputs/tables`, and tests validate schema, filtering, cohort construction, and estimator behavior.

**Tech Stack:** Python 3, pandas, numpy, statsmodels, scipy, pytest, Markdown/CSV outputs.

---

## File Structure

- Create `src/analysis/phase1_utils.py`: shared constants, outcome list, path helpers, policy-audit validation, filter builders, regression helpers, and cohort/event-time helper functions.
- Create `src/analysis/policy_audit.py`: generates and validates `data/policy/permitless_carry_legal_audit.csv`; writes `outputs/tables/policy_audit/policy_audit_summary.csv`.
- Create `src/analysis/modern_did.py`: writes transparent staggered-adoption sensitivity outputs to `outputs/tables/modern_did/`.
- Create `src/analysis/robustness_checks.py`: writes robustness outputs to `outputs/tables/robustness/`.
- Create `src/analysis/phase1_publishability_report.py`: writes `outputs/tables/main/phase1_publishability_report.md`.
- Create `tests/test_phase1_utils.py`: deterministic tests for schema validation, treatment consistency, robustness filters, and cohort/event-time construction.
- Create `docs/phase1_publishability_upgrade.md`: human-readable reproduction and interpretation note.
- Modify `README.md`: correct stale results and add Phase 1 outputs/limitations.
- Modify `requirements.txt`: add `pytest` if missing.

---

### Task 1: Add Shared Phase 1 Helpers And Tests

**Files:**
- Create: `src/analysis/phase1_utils.py`
- Create: `tests/test_phase1_utils.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Add failing tests for schema, filters, and event-time construction**

Create `tests/test_phase1_utils.py` with tests that import functions not yet implemented:

```python
import pandas as pd
import pytest

from src.analysis.phase1_utils import (
    POLICY_AUDIT_COLUMNS,
    add_event_time_columns,
    build_robustness_sample,
    validate_policy_audit_schema,
)


def test_validate_policy_audit_schema_rejects_missing_columns():
    table = pd.DataFrame({"State": ["A"], "permitless_year_current": [2020]})

    with pytest.raises(ValueError, match="missing required columns"):
        validate_policy_audit_schema(table)


def test_validate_policy_audit_schema_accepts_required_columns():
    table = pd.DataFrame([{col: "" for col in POLICY_AUDIT_COLUMNS}])
    table.loc[0, "State"] = "A"
    table.loc[0, "permitless_year_current"] = 2020
    table.loc[0, "audit_status"] = "needs_source"

    validated = validate_policy_audit_schema(table)

    assert list(validated.columns) == POLICY_AUDIT_COLUMNS


def test_build_robustness_sample_excludes_covid_years():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "A", "A"],
            "Year": [2019, 2020, 2021, 2022],
            "y": [1, 2, 3, 4],
        }
    )

    filtered = build_robustness_sample(panel, "exclude_covid")

    assert filtered["Year"].tolist() == [2019, 2022]


def test_build_robustness_sample_excludes_post_2019():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "A"],
            "Year": [2018, 2019, 2020],
            "y": [1, 2, 3],
        }
    )

    filtered = build_robustness_sample(panel, "pre_covid_only")

    assert filtered["Year"].tolist() == [2018, 2019]


def test_add_event_time_columns_marks_never_treated_as_missing():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B"],
            "Year": [2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, pd.NA, pd.NA],
        }
    )

    out = add_event_time_columns(panel)

    assert out.loc[out["State"] == "A", "event_time"].tolist() == [-1, 0]
    assert out.loc[out["State"] == "B", "event_time"].isna().all()
```

- [ ] **Step 2: Run tests and verify they fail because the module is missing**

Run: `python3 -m pytest tests/test_phase1_utils.py -q`

Expected: FAIL with `ModuleNotFoundError: No module named 'src.analysis.phase1_utils'`.

- [ ] **Step 3: Add minimal helper implementation**

Create `src/analysis/phase1_utils.py` with:

```python
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
POLICY_AUDIT_FILE = ROOT / "data" / "policy" / "permitless_carry_legal_audit.csv"

OUTCOMES = [
    "firearm_suicide_rate_per_100k",
    "nonfirearm_suicide_rate_per_100k",
    "total_suicide_rate_per_100k",
    "firearm_homicide_rate_per_100k",
    "total_firearm_rate_per_100k",
]

OUTCOME_LABELS = {
    "firearm_suicide_rate_per_100k": "Firearm Suicide",
    "nonfirearm_suicide_rate_per_100k": "Non-Firearm Suicide",
    "total_suicide_rate_per_100k": "Total Suicide",
    "firearm_homicide_rate_per_100k": "Firearm Homicide",
    "total_firearm_rate_per_100k": "Total Firearm Deaths",
}

POLICY_AUDIT_COLUMNS = [
    "State",
    "permitless_year_current",
    "bill_or_statute",
    "enactment_date",
    "effective_date",
    "permitless_concealed",
    "permitless_open",
    "constitutional_carry_label",
    "minimum_age",
    "training_requirement_removed",
    "background_check_permit_requirement_removed",
    "violent_misdemeanor_permit_screen_removed",
    "source_url",
    "coding_notes",
    "audit_status",
]


def load_panel() -> pd.DataFrame:
    return pd.read_csv(PANEL_FILE).sort_values(["State", "Year"]).reset_index(drop=True)


def validate_policy_audit_schema(table: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in POLICY_AUDIT_COLUMNS if col not in table.columns]
    if missing:
        raise ValueError(f"Policy audit table missing required columns: {missing}")
    return table[POLICY_AUDIT_COLUMNS].copy()


def build_robustness_sample(panel: pd.DataFrame, specification: str) -> pd.DataFrame:
    if specification == "baseline":
        return panel.copy()
    if specification == "exclude_covid":
        return panel.loc[~panel["Year"].isin([2020, 2021])].copy()
    if specification == "pre_covid_only":
        return panel.loc[panel["Year"] <= 2019].copy()
    raise ValueError(f"Unknown robustness specification: {specification}")


def add_event_time_columns(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    out["event_time"] = out["Year"] - out["permitless_year"]
    out.loc[out["permitless_year"].isna(), "event_time"] = np.nan
    out["cohort"] = out["permitless_year"]
    return out


def fit_twfe(
    data: pd.DataFrame,
    outcome: str,
    *,
    weights: str | None = None,
    state_trends: bool = False,
):
    terms = ["post_permitless", "unemployment_rate", "income_pc", "C(State)", "C(Year)"]
    d = data[[outcome, "post_permitless", "unemployment_rate", "income_pc", "State", "Year"] + ([weights] if weights else [])].dropna().copy()
    if state_trends:
        d["centered_year"] = d["Year"] - d["Year"].min()
        terms.append("C(State):centered_year")
    formula = f"{outcome} ~ {' + '.join(terms)}"
    if weights:
        return smf.wls(formula, data=d, weights=d[weights]).fit(cov_type="cluster", cov_kwds={"groups": d["State"]})
    return smf.ols(formula, data=d).fit(cov_type="cluster", cov_kwds={"groups": d["State"]})
```

- [ ] **Step 4: Add pytest to requirements if missing**

Append `pytest` to `requirements.txt` only if no existing line equals `pytest`.

- [ ] **Step 5: Run tests and verify helper tests pass**

Run: `python3 -m pytest tests/test_phase1_utils.py -q`

Expected: PASS.

- [ ] **Step 6: Commit**

Run:

```bash
git add requirements.txt src/analysis/phase1_utils.py tests/test_phase1_utils.py
git commit -m "test: add phase 1 analysis helpers"
```

---

### Task 2: Add Policy Audit Scaffold

**Files:**
- Create: `src/analysis/policy_audit.py`
- Create: `data/policy/permitless_carry_legal_audit.csv`
- Create output: `outputs/tables/policy_audit/policy_audit_summary.csv`
- Modify: `tests/test_phase1_utils.py`

- [ ] **Step 1: Add test for treatment-year consistency**

Extend `tests/test_phase1_utils.py`:

```python
from src.analysis.phase1_utils import validate_policy_year_consistency


def test_validate_policy_year_consistency_counts_mismatches():
    panel_states = pd.DataFrame(
        {
            "State": ["A", "B"],
            "permitless_year": [2020.0, pd.NA],
        }
    )
    audit = pd.DataFrame(
        {
            "State": ["A", "B"],
            "permitless_year_current": [2021.0, pd.NA],
        }
    )

    summary = validate_policy_year_consistency(panel_states, audit)

    assert summary["year_mismatch"].sum() == 1
```

- [ ] **Step 2: Run test and verify it fails because the function is missing**

Run: `python3 -m pytest tests/test_phase1_utils.py::test_validate_policy_year_consistency_counts_mismatches -q`

Expected: FAIL with import error for `validate_policy_year_consistency`.

- [ ] **Step 3: Implement consistency helper**

Add to `src/analysis/phase1_utils.py`:

```python
def validate_policy_year_consistency(panel_states: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    panel_years = panel_states[["State", "permitless_year"]].drop_duplicates("State").copy()
    merged = panel_years.merge(
        audit[["State", "permitless_year_current", "audit_status"]],
        on="State",
        how="outer",
    )
    panel = pd.to_numeric(merged["permitless_year"], errors="coerce")
    audit_year = pd.to_numeric(merged["permitless_year_current"], errors="coerce")
    merged["year_mismatch"] = ~(
        (panel.isna() & audit_year.isna()) | (panel.fillna(-1).astype(float) == audit_year.fillna(-1).astype(float))
    )
    return merged
```

- [ ] **Step 4: Run targeted test and verify it passes**

Run: `python3 -m pytest tests/test_phase1_utils.py::test_validate_policy_year_consistency_counts_mismatches -q`

Expected: PASS.

- [ ] **Step 5: Create policy audit script**

Create `src/analysis/policy_audit.py` that:

- loads `analysis_panel_full_outcomes.csv`,
- creates one row per state if the audit CSV is missing,
- fills `permitless_year_current` from the panel,
- writes all unknown legal fields as empty strings,
- marks `audit_status` as `needs_source`,
- validates schema,
- writes mismatch summary to `outputs/tables/policy_audit/policy_audit_summary.csv`.

- [ ] **Step 6: Run policy audit script**

Run: `python3 src/analysis/policy_audit.py`

Expected: creates/validates the audit table and writes a summary CSV with 50 states.

- [ ] **Step 7: Run all helper tests**

Run: `python3 -m pytest tests/test_phase1_utils.py -q`

Expected: PASS.

- [ ] **Step 8: Commit**

Run:

```bash
git add src/analysis/phase1_utils.py src/analysis/policy_audit.py tests/test_phase1_utils.py data/policy/permitless_carry_legal_audit.csv outputs/tables/policy_audit/policy_audit_summary.csv
git commit -m "feat: add auditable policy coding scaffold"
```

---

### Task 3: Add Modern Staggered-Adoption Sensitivity Outputs

**Files:**
- Create: `src/analysis/modern_did.py`
- Create outputs under: `outputs/tables/modern_did/`
- Modify: `tests/test_phase1_utils.py`

- [ ] **Step 1: Add test for cohort comparison rows**

Extend tests:

```python
from src.analysis.phase1_utils import build_cohort_att_table


def test_build_cohort_att_table_returns_cohort_window_rows():
    panel = pd.DataFrame(
        {
            "State": ["A", "A", "B", "B", "C", "C"],
            "Year": [2019, 2020, 2019, 2020, 2019, 2020],
            "permitless_year": [2020, 2020, pd.NA, pd.NA, pd.NA, pd.NA],
            "ever_adopter": [1, 1, 0, 0, 0, 0],
            "outcome": [2.0, 5.0, 1.0, 2.0, 1.0, 3.0],
        }
    )

    out = build_cohort_att_table(panel, "outcome", windows=(1,))

    assert out.loc[0, "cohort"] == 2020
    assert out.loc[0, "window"] == 1
    assert out.loc[0, "att"] == 1.5
```

- [ ] **Step 2: Run test and verify it fails because the function is missing**

Run: `python3 -m pytest tests/test_phase1_utils.py::test_build_cohort_att_table_returns_cohort_window_rows -q`

Expected: FAIL with import error for `build_cohort_att_table`.

- [ ] **Step 3: Implement cohort ATT helper**

Add to `src/analysis/phase1_utils.py`:

```python
def build_cohort_att_table(panel: pd.DataFrame, outcome: str, windows=(2, 3, 5)) -> pd.DataFrame:
    rows = []
    cohorts = sorted(panel["permitless_year"].dropna().astype(int).unique())
    for cohort in cohorts:
        treated_states = panel.loc[panel["permitless_year"] == cohort, "State"].drop_duplicates()
        controls = panel.loc[panel["permitless_year"].isna(), "State"].drop_duplicates()
        for window in windows:
            pre_years = list(range(cohort - window, cohort))
            post_years = list(range(cohort, cohort + window))
            treated = panel.loc[panel["State"].isin(treated_states)]
            control = panel.loc[panel["State"].isin(controls)]
            t_pre = treated.loc[treated["Year"].isin(pre_years), outcome].mean()
            t_post = treated.loc[treated["Year"].isin(post_years), outcome].mean()
            c_pre = control.loc[control["Year"].isin(pre_years), outcome].mean()
            c_post = control.loc[control["Year"].isin(post_years), outcome].mean()
            if pd.notna(t_pre) and pd.notna(t_post) and pd.notna(c_pre) and pd.notna(c_post):
                rows.append(
                    {
                        "outcome": outcome,
                        "cohort": cohort,
                        "window": window,
                        "n_treated_states": int(len(treated_states)),
                        "n_control_states": int(len(controls)),
                        "treated_change": t_post - t_pre,
                        "control_change": c_post - c_pre,
                        "att": (t_post - t_pre) - (c_post - c_pre),
                    }
                )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Add modern DiD script**

Create `src/analysis/modern_did.py` to:

- call `build_cohort_att_table` for each outcome,
- write `cohort_att_by_outcome.csv`,
- estimate a Sun-Abraham-style event specification with cohort-by-event dummies against never-treated controls where feasible,
- write `event_time_never_control_estimates.csv`,
- summarize pretrend flags in `modern_did_summary.csv`.

- [ ] **Step 5: Run tests and script**

Run:

```bash
python3 -m pytest tests/test_phase1_utils.py -q
python3 src/analysis/modern_did.py
```

Expected: tests pass and outputs are written under `outputs/tables/modern_did/`.

- [ ] **Step 6: Commit**

Run:

```bash
git add src/analysis/phase1_utils.py src/analysis/modern_did.py tests/test_phase1_utils.py outputs/tables/modern_did
git commit -m "feat: add modern staggered adoption sensitivity outputs"
```

---

### Task 4: Add Robustness Checks

**Files:**
- Create: `src/analysis/robustness_checks.py`
- Create outputs under: `outputs/tables/robustness/`

- [ ] **Step 1: Add robustness script**

Create `src/analysis/robustness_checks.py` to run:

- baseline TWFE,
- exclude 2020-2021,
- pre-2020 only,
- population-weighted TWFE,
- state-specific linear trends,
- leave-one-adopting-state-out TWFE,
- placebo-adoption distribution for never-treated states.

- [ ] **Step 2: Run tests**

Run: `python3 -m pytest tests/test_phase1_utils.py -q`

Expected: PASS.

- [ ] **Step 3: Run robustness script**

Run: `python3 src/analysis/robustness_checks.py`

Expected: writes `twfe_robustness_results.csv`, `leave_one_state_out.csv`, `placebo_never_treated.csv`, and `robustness_summary.csv`.

- [ ] **Step 4: Commit**

Run:

```bash
git add src/analysis/robustness_checks.py outputs/tables/robustness
git commit -m "feat: add phase 1 robustness checks"
```

---

### Task 5: Add Phase 1 Report And Documentation

**Files:**
- Create: `src/analysis/phase1_publishability_report.py`
- Create: `docs/phase1_publishability_upgrade.md`
- Create output: `outputs/tables/main/phase1_publishability_report.md`
- Modify: `README.md`

- [ ] **Step 1: Add report script**

Create `src/analysis/phase1_publishability_report.py` to read:

- `outputs/tables/did/twfe_did_main_results.csv`,
- `outputs/tables/main/welch_change_score_results.csv`,
- `outputs/tables/policy_audit/policy_audit_summary.csv`,
- `outputs/tables/modern_did/modern_did_summary.csv`,
- `outputs/tables/robustness/robustness_summary.csv`.

Write a Markdown report that names:

- what was corrected,
- what remains associational,
- which outcomes persist across sensitivity checks,
- whether the legal audit table is source-verified or still `needs_source`.

- [ ] **Step 2: Run report script**

Run: `python3 src/analysis/phase1_publishability_report.py`

Expected: writes `outputs/tables/main/phase1_publishability_report.md`.

- [ ] **Step 3: Add docs note**

Create `docs/phase1_publishability_upgrade.md` with reproduction commands:

```bash
python3 src/analysis/policy_audit.py
python3 src/analysis/modern_did.py
python3 src/analysis/robustness_checks.py
python3 src/analysis/phase1_publishability_report.py
```

Also list Phase 2 remaining work: external firearm-law controls, opioid mortality, mental-health access, demographics, and legal-source verification.

- [ ] **Step 4: Update README**

Update `README.md` to:

- correct stale change-score p-values using `outputs/tables/main/welch_change_score_results.csv`,
- add Phase 1 outputs,
- state the treatment audit is a scaffold unless `audit_status` is source verified,
- state gun ownership is carried forward after 2016,
- state nonzero pre-adoption coefficients keep claims associational.

- [ ] **Step 5: Run scripts**

Run:

```bash
python3 src/analysis/policy_audit.py
python3 src/analysis/modern_did.py
python3 src/analysis/robustness_checks.py
python3 src/analysis/phase1_publishability_report.py
```

Expected: all scripts exit 0.

- [ ] **Step 6: Commit**

Run:

```bash
git add README.md docs/phase1_publishability_upgrade.md src/analysis/phase1_publishability_report.py outputs/tables/main/phase1_publishability_report.md
git commit -m "docs: add phase 1 publishability report"
```

---

### Task 6: Final Verification

**Files:**
- Verify all changed files.

- [ ] **Step 1: Run full verification**

Run:

```bash
python3 -m pytest
python3 src/analysis/policy_audit.py
python3 src/analysis/modern_did.py
python3 src/analysis/robustness_checks.py
python3 src/analysis/phase1_publishability_report.py
git status --short
```

Expected: pytest passes, all scripts exit 0, and git status only shows intentional regenerated output changes if scripts rewrote existing files.

- [ ] **Step 2: Review diff**

Run:

```bash
git diff --stat HEAD
git diff -- README.md docs/phase1_publishability_upgrade.md outputs/tables/main/phase1_publishability_report.md
```

Expected: diff reflects Phase 1 scope only.

- [ ] **Step 3: Commit any final regenerated outputs**

Run:

```bash
git add README.md docs src data/policy outputs/tables requirements.txt tests
git commit -m "chore: verify phase 1 publishability upgrade"
```

Only run this commit if there are remaining intentional tracked changes after Tasks 1-5.

---

## Self-Review Notes

- Spec coverage: each Phase 1 requirement maps to a task.
- Placeholder scan: the plan contains no unresolved marker language.
- Type consistency: helper names used in tests match helper names introduced in tasks.
- Scope check: Phase 2 external covariates are explicitly excluded.
