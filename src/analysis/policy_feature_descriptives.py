from pathlib import Path

import pandas as pd

try:
    from src.analysis.mechanism_heterogeneity import MECHANISM_SPECS
    from src.analysis.phase1_utils import POLICY_AUDIT_FILE, ROOT, load_panel
except ModuleNotFoundError:
    from mechanism_heterogeneity import MECHANISM_SPECS
    from phase1_utils import POLICY_AUDIT_FILE, ROOT, load_panel


OUT_DIR = ROOT / "outputs" / "tables" / "mechanism"
BUNDLE_FILE = OUT_DIR / "policy_bundle_index_by_state.csv"
DISTRIBUTION_FILE = OUT_DIR / "policy_bundle_distribution.csv"
FEATURE_EVENT_FILE = OUT_DIR / "feature_stratified_event_means.csv"


def build_policy_bundle_table(audit: pd.DataFrame) -> pd.DataFrame:
    required = {"State", "audit_status"} | {
        spec["source_column"] for spec in MECHANISM_SPECS.values()
    }
    missing = sorted(required - set(audit.columns))
    if missing:
        raise ValueError(f"Policy audit missing feature columns: {missing}")

    source_verified = audit.loc[audit["audit_status"].astype(str).eq("source_verified")].copy()
    out = source_verified[["State"]].drop_duplicates("State").copy()
    for dimension, spec in MECHANISM_SPECS.items():
        values = source_verified.set_index("State")[spec["source_column"]].astype(str)
        out[dimension] = out["State"].map(values).isin(spec["positive_values"]).astype(int)
    out["policy_bundle_index"] = out[list(MECHANISM_SPECS)].sum(axis=1)
    return out.sort_values(["policy_bundle_index", "State"], ascending=[False, True]).reset_index(drop=True)


def build_policy_bundle_distribution(bundle: pd.DataFrame) -> pd.DataFrame:
    return (
        bundle.groupby("policy_bundle_index", as_index=False)
        .agg(n_states=("State", "nunique"), states=("State", lambda x: ";".join(sorted(x))))
        .sort_values("policy_bundle_index")
        .reset_index(drop=True)
    )


def build_feature_stratified_event_means(
    panel: pd.DataFrame,
    bundle: pd.DataFrame,
    *,
    outcome: str = "firearm_suicide_rate_per_100k",
    min_event_time: int = -5,
    max_event_time: int = 5,
) -> pd.DataFrame:
    required = {"State", "Year", "permitless_year", outcome}
    missing = sorted(required - set(panel.columns))
    if missing:
        raise ValueError(f"Panel missing feature event columns: {missing}")

    features = list(MECHANISM_SPECS) + ["policy_bundle_index"]
    data = panel.merge(bundle[["State"] + features], on="State", how="inner")
    data["event_time"] = data["Year"] - data["permitless_year"]
    data = data.loc[
        data["event_time"].between(min_event_time, max_event_time)
        & data[outcome].notna()
    ].copy()

    rows = []
    for feature in features:
        grouped = (
            data.groupby([feature, "event_time"], as_index=False)
            .agg(
                mean_outcome=(outcome, "mean"),
                n_states=("State", "nunique"),
                nobs=(outcome, "size"),
            )
            .rename(columns={feature: "feature_value"})
        )
        grouped["feature"] = feature
        grouped["outcome"] = outcome
        rows.append(grouped)
    if not rows:
        return pd.DataFrame(
            columns=["feature", "feature_value", "event_time", "mean_outcome", "n_states", "nobs", "outcome"]
        )
    return pd.concat(rows, ignore_index=True)[
        ["feature", "feature_value", "event_time", "mean_outcome", "n_states", "nobs", "outcome"]
    ].sort_values(["feature", "feature_value", "event_time"]).reset_index(drop=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = load_panel()
    audit = pd.read_csv(POLICY_AUDIT_FILE)
    bundle = build_policy_bundle_table(audit)
    distribution = build_policy_bundle_distribution(bundle)
    feature_event = build_feature_stratified_event_means(panel, bundle)
    bundle.to_csv(BUNDLE_FILE, index=False)
    distribution.to_csv(DISTRIBUTION_FILE, index=False)
    feature_event.to_csv(FEATURE_EVENT_FILE, index=False)
    print(f"Wrote: {BUNDLE_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {DISTRIBUTION_FILE.relative_to(Path.cwd())}")
    print(f"Wrote: {FEATURE_EVENT_FILE.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
