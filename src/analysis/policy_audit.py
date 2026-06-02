from pathlib import Path

import pandas as pd

try:
    from src.analysis.phase1_utils import (
        POLICY_AUDIT_COLUMNS,
        POLICY_AUDIT_MECHANISM_FIELDS,
        POLICY_AUDIT_FILE,
        ROOT,
        load_panel,
        validate_policy_audit_mechanism_rows,
        validate_policy_audit_verified_rows,
        validate_policy_audit_schema,
        validate_policy_year_consistency,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        POLICY_AUDIT_COLUMNS,
        POLICY_AUDIT_MECHANISM_FIELDS,
        POLICY_AUDIT_FILE,
        ROOT,
        load_panel,
        validate_policy_audit_mechanism_rows,
        validate_policy_audit_verified_rows,
        validate_policy_audit_schema,
        validate_policy_year_consistency,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "policy_audit"
SUMMARY_FILE = OUT_DIR / "policy_audit_summary.csv"
STATUS_FILE = OUT_DIR / "policy_audit_status_counts.csv"
MECHANISM_FILE = OUT_DIR / "policy_mechanism_summary.csv"


def build_policy_audit_scaffold(panel: pd.DataFrame) -> pd.DataFrame:
    states = (
        panel[["State", "permitless_year"]]
        .drop_duplicates("State")
        .sort_values("State")
        .reset_index(drop=True)
    )
    rows = []
    for _, row in states.iterrows():
        permitless_year = row["permitless_year"]
        has_year = pd.notna(permitless_year)
        entry = {col: "" for col in POLICY_AUDIT_COLUMNS}
        entry["State"] = row["State"]
        entry["permitless_year_current"] = int(permitless_year) if has_year else ""
        entry["coding_notes"] = (
            "Scaffold generated from current panel permitless_year; legal source audit pending."
            if has_year
            else "No permitless adoption year in current panel; legal source audit pending."
        )
        entry["audit_status"] = "needs_source"
        rows.append(entry)
    return pd.DataFrame(rows, columns=POLICY_AUDIT_COLUMNS)


def load_or_create_policy_audit(panel: pd.DataFrame) -> pd.DataFrame:
    POLICY_AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if POLICY_AUDIT_FILE.exists():
        audit = pd.read_csv(POLICY_AUDIT_FILE, keep_default_na=False)
    else:
        audit = build_policy_audit_scaffold(panel)
        audit.to_csv(POLICY_AUDIT_FILE, index=False)
    audit = validate_policy_audit_schema(audit)
    audit = validate_policy_audit_verified_rows(audit)
    audit = validate_policy_audit_mechanism_rows(audit)
    audit.to_csv(POLICY_AUDIT_FILE, index=False)
    return audit


def build_policy_mechanism_summary(audit: pd.DataFrame) -> pd.DataFrame:
    clean_adopters = audit.loc[
        audit["audit_status"].astype(str).str.strip().eq("source_verified")
    ]
    rows = []
    for field in POLICY_AUDIT_MECHANISM_FIELDS:
        counts = clean_adopters[field].astype(str).str.strip().value_counts(sort=False)
        for value, count in counts.items():
            rows.append(
                {
                    "mechanism_field": field,
                    "mechanism_value": value,
                    "state_count": int(count),
                }
            )
    return pd.DataFrame(
        rows,
        columns=["mechanism_field", "mechanism_value", "state_count"],
    )


def write_policy_audit_outputs(panel: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel_states = panel[["State", "permitless_year"]].drop_duplicates("State")
    summary = validate_policy_year_consistency(panel_states, audit)
    summary.to_csv(SUMMARY_FILE, index=False)

    status_counts = (
        audit["audit_status"]
        .value_counts(dropna=False)
        .rename_axis("audit_status")
        .reset_index(name="state_count")
    )
    status_counts.to_csv(STATUS_FILE, index=False)

    mechanism_summary = build_policy_mechanism_summary(audit)
    mechanism_summary.to_csv(MECHANISM_FILE, index=False)
    return summary


def main():
    panel = load_panel()
    audit = load_or_create_policy_audit(panel)
    summary = write_policy_audit_outputs(panel, audit)
    mismatch_count = int(summary["year_mismatch"].sum())
    print(f"Policy audit rows: {len(audit)}")
    print(f"Year mismatches: {mismatch_count}")
    print(f"Wrote: {POLICY_AUDIT_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {SUMMARY_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {MECHANISM_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
