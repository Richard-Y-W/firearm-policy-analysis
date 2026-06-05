from pathlib import Path

import numpy as np
import pandas as pd

try:
    from src.analysis.phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        POLICY_AUDIT_FILE,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )
except ModuleNotFoundError:
    from phase1_utils import (
        BASELINE_CONTROL_COLUMNS,
        OUTCOMES,
        OUTCOME_LABELS,
        POLICY_AUDIT_FILE,
        ROOT,
        fit_fixed_effect_regression,
        load_panel,
    )


OUT_DIR = ROOT / "outputs" / "tables" / "mechanism"
DETAIL_FILE = OUT_DIR / "mechanism_heterogeneity_results.csv"
MIN_MECHANISM_GROUP_STATES = 3

MECHANISM_SPECS = {
    "training_removed": {
        "source_column": "training_requirement_removed",
        "positive_values": {"yes"},
        "post_column": "post_training_removed",
    },
    "permit_background_check_removed": {
        "source_column": "background_check_permit_requirement_removed",
        "positive_values": {
            "yes",
            "carry_permit_screen_removed_purchase_permit_retained",
        },
        "post_column": "post_permit_background_check_removed",
    },
    "misdemeanor_screen_removed": {
        "source_column": "violent_misdemeanor_permit_screen_removed",
        "positive_values": {"permit_specific_misdemeanor_screen_removed"},
        "post_column": "post_misdemeanor_screen_removed",
    },
}


def add_mechanism_indicators(panel: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    required = {"State", "audit_status"} | {
        spec["source_column"] for spec in MECHANISM_SPECS.values()
    }
    missing = sorted(required - set(audit.columns))
    if missing:
        raise ValueError(f"Policy audit missing mechanism columns: {missing}")
    if "post_permitless" not in panel.columns:
        raise ValueError("Panel missing post_permitless column")

    source_verified = audit.loc[audit["audit_status"].astype(str).eq("source_verified")].copy()
    mechanism = source_verified[["State"]].drop_duplicates("State").copy()
    for dimension, spec in MECHANISM_SPECS.items():
        values = source_verified.set_index("State")[spec["source_column"]].astype(str)
        mechanism[dimension] = (
            mechanism["State"].map(values).isin(spec["positive_values"]).astype(int)
        )

    out = panel.merge(mechanism, on="State", how="left")
    for dimension, spec in MECHANISM_SPECS.items():
        out[dimension] = out[dimension].fillna(0).astype(int)
        out[spec["post_column"]] = out["post_permitless"].astype(int) * out[dimension]
    return out


def _source_verified_counts(audit: pd.DataFrame, dimension: str) -> tuple[int, int]:
    spec = MECHANISM_SPECS[dimension]
    source_verified = audit.loc[audit["audit_status"].astype(str).eq("source_verified")].copy()
    positive = source_verified[spec["source_column"]].astype(str).isin(
        spec["positive_values"]
    )
    return int(positive.sum()), int((~positive).sum())


def _empty_model_row(
    outcome: str,
    outcome_label: str,
    dimension: str,
    post_column: str,
    n_mechanism_states: int,
    n_other_states: int,
    warning: str,
) -> dict:
    return {
        "outcome": outcome,
        "outcome_label": outcome_label,
        "mechanism_dimension": dimension,
        "interaction_term": post_column,
        "main_post_coef": np.nan,
        "interaction_coef": np.nan,
        "interaction_se": np.nan,
        "interaction_p": np.nan,
        "nobs": np.nan,
        "n_mechanism_states": n_mechanism_states,
        "n_other_states": n_other_states,
        "sparse_comparison": True,
        "comparison_warning": warning,
        "interpretation_scope": "exploratory_sparse_comparison_do_not_interpret_as_mechanism",
    }


def run_mechanism_heterogeneity_models(
    panel: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    outcomes=None,
    outcome_labels=None,
) -> pd.DataFrame:
    outcomes = outcomes or OUTCOMES
    outcome_labels = outcome_labels or OUTCOME_LABELS
    source_verified_states = set(
        audit.loc[audit["audit_status"].astype(str).eq("source_verified"), "State"]
    )
    if "ever_adopter" in panel.columns:
        analytic_panel = panel.loc[
            panel["ever_adopter"].eq(0) | panel["State"].isin(source_verified_states)
        ].copy()
    else:
        analytic_panel = panel.copy()
    data = add_mechanism_indicators(analytic_panel, audit)
    rows = []

    for outcome in outcomes:
        for dimension, spec in MECHANISM_SPECS.items():
            post_column = spec["post_column"]
            n_mechanism_states, n_other_states = _source_verified_counts(audit, dimension)
            sparse = (
                n_mechanism_states < MIN_MECHANISM_GROUP_STATES
                or n_other_states < MIN_MECHANISM_GROUP_STATES
            )
            if n_mechanism_states == 0 or n_other_states == 0:
                rows.append(
                    _empty_model_row(
                        outcome,
                        outcome_labels.get(outcome, outcome),
                        dimension,
                        post_column,
                        n_mechanism_states,
                        n_other_states,
                        "no_source_verified_comparison_group",
                    )
                )
                continue

            result = fit_fixed_effect_regression(
                data,
                outcome,
                ["post_permitless", post_column],
                controls=BASELINE_CONTROL_COLUMNS,
            )
            rows.append(
                {
                    "outcome": outcome,
                    "outcome_label": outcome_labels.get(outcome, outcome),
                    "mechanism_dimension": dimension,
                    "interaction_term": post_column,
                    "main_post_coef": result.params.get("post_permitless", np.nan),
                    "interaction_coef": result.params.get(post_column, np.nan),
                    "interaction_se": result.bse.get(post_column, np.nan),
                    "interaction_p": result.pvalues.get(post_column, np.nan),
                    "nobs": result.nobs,
                    "n_mechanism_states": n_mechanism_states,
                    "n_other_states": n_other_states,
                    "sparse_comparison": sparse,
                    "comparison_warning": (
                        "small_source_verified_comparison_group"
                        if sparse
                        else "adequate_source_verified_comparison_group"
                    ),
                    "interpretation_scope": (
                        "exploratory_sparse_comparison_do_not_interpret_as_mechanism"
                        if sparse
                        else "exploratory_policy_feature_heterogeneity"
                    ),
                }
            )
    return pd.DataFrame(rows)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    audit = pd.read_csv(POLICY_AUDIT_FILE)
    detail = run_mechanism_heterogeneity_models(panel, audit)
    detail.to_csv(DETAIL_FILE, index=False)
    print(f"Wrote: {DETAIL_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
