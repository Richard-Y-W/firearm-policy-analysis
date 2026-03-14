import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"

OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"

for sub in [
    OUT_TABLES / "main",
    OUT_TABLES / "mechanism",
    OUT_TABLES / "heterogeneity",
    OUT_TABLES / "political_selection",
    OUT_TABLES / "did",
    OUT_TABLES / "event_study",
    OUT_FIGS / "main",
    OUT_FIGS / "mechanism",
    OUT_FIGS / "heterogeneity",
    OUT_FIGS / "event_study",
]:
    sub.mkdir(parents=True, exist_ok=True)

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


def load_panel():
    df = pd.read_csv(DATA_FILE)
    df = df.sort_values(["State", "Year"]).reset_index(drop=True)

    # If duplicate columns were created earlier, coalesce them
    for base_col in [
        "gun_ownership_baseline",
        "mean_rucc_2013",
        "share_nonmetro_counties_2013",
        "baseline_firearm_suicide_rate",
        "rep_vote_share_baseline",
    ]:
        xcol = f"{base_col}_x"
        ycol = f"{base_col}_y"

        if xcol in df.columns and ycol in df.columns:
            df[base_col] = df[xcol].combine_first(df[ycol])
            df = df.drop(columns=[xcol, ycol])
        elif xcol in df.columns:
            df = df.rename(columns={xcol: base_col})
        elif ycol in df.columns:
            df = df.rename(columns={ycol: base_col})

    # state-level baseline metrics for heterogeneity / selection
    state_base = (
        df.groupby("State", as_index=False)
        .agg(
            ever_adopter=("ever_adopter", "max"),
            permitless_year=("permitless_year", "first"),
            gun_ownership_baseline=("gun_ownership", lambda x: x.dropna().iloc[0] if x.dropna().shape[0] else np.nan),
            mean_rucc_2013=("mean_rucc_2013", "first"),
            share_nonmetro_counties_2013=("share_nonmetro_counties_2013", "first"),
        )
    )

    # baseline firearm suicide rate: pre-policy mean if adopter, else full-sample pre-2015 mean
    baseline_rows = []
    for state, g in df.groupby("State"):
        permitless_year = g["permitless_year"].iloc[0]
        if pd.notna(permitless_year):
            baseline = g[g["Year"] < permitless_year]["firearm_suicide_rate_per_100k"].mean()
        else:
            baseline = g[g["Year"] <= 2014]["firearm_suicide_rate_per_100k"].mean()

        gv = g[["Year", "rep_vote_share_2party"]].dropna().drop_duplicates().sort_values("Year")
        rep_base = np.nan
        if not gv.empty:
            if 2012 in gv["Year"].values:
                rep_base = gv.loc[gv["Year"] == 2012, "rep_vote_share_2party"].iloc[0]
            else:
                rep_base = gv.iloc[-1]["rep_vote_share_2party"]

        baseline_rows.append({
            "State": state,
            "baseline_firearm_suicide_rate": baseline,
            "rep_vote_share_baseline": rep_base,
        })

    baseline_df = pd.DataFrame(baseline_rows)
    state_base = state_base.merge(baseline_df, on="State", how="left")

    # median splits
    for col in ["gun_ownership_baseline", "share_nonmetro_counties_2013", "baseline_firearm_suicide_rate"]:
        med = state_base[col].median()
        state_base[f"high_{col}"] = (state_base[col] >= med).astype(int)

    # Merge only columns that are NOT already in df
    merge_cols = [
        "State",
        "gun_ownership_baseline",
        "baseline_firearm_suicide_rate",
        "rep_vote_share_baseline",
        "high_gun_ownership_baseline",
        "high_share_nonmetro_counties_2013",
        "high_baseline_firearm_suicide_rate",
    ]

    df = df.merge(
        state_base[merge_cols],
        on="State",
        how="left"
    )

    return df, state_base


def make_descriptive_tables(df, state_base):
    state_level = (
        df.groupby("State", as_index=False)
        .agg(
            ever_adopter=("ever_adopter", "max"),
            permitless_year=("permitless_year", "first"),
            gun_ownership=("gun_ownership_baseline", "first"),
            rurality=("share_nonmetro_counties_2013", "first"),
            baseline_firearm_suicide=("baseline_firearm_suicide_rate", "first"),
            rep_vote_share=("rep_vote_share_baseline", "first"),
            income_pc=("income_pc", "mean"),
            unemployment_rate=("unemployment_rate", "mean"),
        )
    )

    # Save the raw state-level table
    state_level.to_csv(OUT_TABLES / "main" / "state_level_characteristics.csv", index=False)

    # Only summarize numeric columns
    numeric_cols = [
        "permitless_year",
        "gun_ownership",
        "rurality",
        "baseline_firearm_suicide",
        "rep_vote_share",
        "income_pc",
        "unemployment_rate",
    ]

    summary = (
        state_level.groupby("ever_adopter")[numeric_cols]
        .agg(["mean", "std", "median"])
    )
    summary.to_csv(OUT_TABLES / "main" / "state_baseline_summary_by_adopter.csv")

    print("Saved descriptive tables.")


def compute_change_score(g, outcome, anchor_year, window):
    pre = g[(g["Year"] >= anchor_year - window) & (g["Year"] <= anchor_year - 1)][outcome].mean()
    post = g[(g["Year"] >= anchor_year) & (g["Year"] <= anchor_year + window - 1)][outcome].mean()

    if pd.isna(pre) or pd.isna(post):
        return np.nan
    return post - pre


def run_welch_change_score_tests(df):
    """
    For adopters: actual adoption year.
    For never-adopters: pseudo-adoption windows averaged across all adopter cohort years.
    """
    adopter_years = sorted(df["permitless_year"].dropna().astype(int).unique().tolist())
    results = []

    adopter_states = df.loc[df["ever_adopter"] == 1, "State"].drop_duplicates().tolist()
    never_states = df.loc[df["ever_adopter"] == 0, "State"].drop_duplicates().tolist()

    for outcome in OUTCOMES:
        for window in [2, 3, 5]:
            adopter_scores = []
            for state in adopter_states:
                g = df[df["State"] == state].copy()
                anchor = int(g["permitless_year"].iloc[0])
                score = compute_change_score(g, outcome, anchor, window)
                if pd.notna(score):
                    adopter_scores.append(score)

            never_scores = []
            for state in never_states:
                g = df[df["State"] == state].copy()
                pseudo_scores = []
                for anchor in adopter_years:
                    score = compute_change_score(g, outcome, anchor, window)
                    if pd.notna(score):
                        pseudo_scores.append(score)
                if len(pseudo_scores) > 0:
                    never_scores.append(np.mean(pseudo_scores))

            if len(adopter_scores) >= 2 and len(never_scores) >= 2:
                tstat, pval = stats.ttest_ind(adopter_scores, never_scores, equal_var=False)
                results.append({
                    "outcome": outcome,
                    "outcome_label": OUTCOME_LABELS[outcome],
                    "window": window,
                    "n_adopter_states": len(adopter_scores),
                    "n_never_states": len(never_scores),
                    "mean_change_adopters": np.mean(adopter_scores),
                    "mean_change_never": np.mean(never_scores),
                    "difference": np.mean(adopter_scores) - np.mean(never_scores),
                    "welch_t": tstat,
                    "p_value": pval
                })

    out = pd.DataFrame(results).sort_values(["outcome", "window"])
    out.to_csv(OUT_TABLES / "main" / "welch_change_score_results.csv", index=False)
    print("Saved Welch change-score results.")


def run_twfe_did(df):
    rows = []

    for outcome in OUTCOMES:
        use_cols = [
            outcome, "post_permitless", "unemployment_rate", "income_pc", "State", "Year"
        ]
        d = df[use_cols].dropna().copy()

        formula = f"{outcome} ~ post_permitless + unemployment_rate + income_pc + C(State) + C(Year)"
        model = smf.ols(formula, data=d).fit(
            cov_type="cluster",
            cov_kwds={"groups": d["State"]}
        )

        rows.append({
            "outcome": outcome,
            "outcome_label": OUTCOME_LABELS[outcome],
            "coef_post_permitless": model.params.get("post_permitless", np.nan),
            "se_post_permitless": model.bse.get("post_permitless", np.nan),
            "p_post_permitless": model.pvalues.get("post_permitless", np.nan),
            "nobs": model.nobs,
            "r2": model.rsquared
        })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "did" / "twfe_did_main_results.csv", index=False)
    print("Saved TWFE DiD results.")


def event_study_design(df, outcome, min_k=-5, max_k=5):
    d = df.copy()

    d["rel_year"] = d["Year"] - d["permitless_year"]
    d["rel_year_capped"] = d["rel_year"].clip(min_k, max_k)

    event_cols = []
    event_name_map = {}

    for k in range(min_k, max_k + 1):
        if k == -1:
            continue  # omitted reference year

        if k < 0:
            col = f"event_m{abs(k)}"
        else:
            col = f"event_{k}"

        d[col] = ((d["ever_adopter"] == 1) & (d["rel_year_capped"] == k)).astype(int)
        event_cols.append(col)
        event_name_map[k] = col

    use_cols = [outcome, "unemployment_rate", "income_pc", "State", "Year"] + event_cols
    d = d[use_cols].dropna().copy()

    formula = (
        outcome
        + " ~ "
        + " + ".join(event_cols)
        + " + unemployment_rate + income_pc + C(State) + C(Year)"
    )

    model = smf.ols(formula, data=d).fit(
        cov_type="cluster",
        cov_kwds={"groups": d["State"]}
    )

    rows = []
    for k in range(min_k, max_k + 1):
        if k == -1:
            continue

        term = event_name_map[k]
        coef = model.params.get(term, np.nan)
        se = model.bse.get(term, np.nan)

        rows.append({
            "event_time": k,
            "coef": coef,
            "se": se,
            "p_value": model.pvalues.get(term, np.nan),
            "ci_low": coef - 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
            "ci_high": coef + 1.96 * se if pd.notna(coef) and pd.notna(se) else np.nan,
        })

    out = pd.DataFrame(rows).sort_values("event_time")
    return out


def save_event_study_outputs(df):
    for outcome in OUTCOMES:
        est = event_study_design(df, outcome)
        safe = outcome.replace("_rate_per_100k", "")
        est.to_csv(OUT_TABLES / "event_study" / f"event_study_{safe}.csv", index=False)

        plt.figure(figsize=(8, 5))
        plt.axhline(0, linewidth=1)
        plt.axvline(-1, linestyle="--", linewidth=1)
        plt.errorbar(est["event_time"], est["coef"],
                     yerr=1.96 * est["se"], fmt="o-", capsize=4)
        plt.title(f"Event Study: {OUTCOME_LABELS[outcome]}")
        plt.xlabel("Years Relative to Permitless Carry Adoption")
        plt.ylabel("Estimated Effect")
        plt.tight_layout()
        plt.savefig(OUT_FIGS / "event_study" / f"event_study_{safe}.png", dpi=200)
        plt.close()

    print("Saved event-study tables and figures.")


def run_heterogeneity_did(df):
    rows = []

    hetero_specs = {
        "high_gun_ownership": "high_gun_ownership_baseline",
        "high_rurality": "high_share_nonmetro_counties_2013",
        "high_baseline_firearm_suicide": "high_baseline_firearm_suicide_rate",
    }

    for outcome in OUTCOMES:
        for label, var in hetero_specs.items():
            use_cols = [
                outcome, "post_permitless", var, "unemployment_rate", "income_pc", "State", "Year"
            ]
            d = df[use_cols].dropna().copy()

            formula = (
                f"{outcome} ~ post_permitless + {var} + post_permitless:{var} "
                f"+ unemployment_rate + income_pc + C(State) + C(Year)"
            )
            model = smf.ols(formula, data=d).fit(
                cov_type="cluster",
                cov_kwds={"groups": d["State"]}
            )

            interaction_term = f"post_permitless:{var}"
            rows.append({
                "outcome": outcome,
                "outcome_label": OUTCOME_LABELS[outcome],
                "heterogeneity_dimension": label,
                "main_post_coef": model.params.get("post_permitless", np.nan),
                "interaction_coef": model.params.get(interaction_term, np.nan),
                "interaction_se": model.bse.get(interaction_term, np.nan),
                "interaction_p": model.pvalues.get(interaction_term, np.nan),
                "nobs": model.nobs
            })

    out = pd.DataFrame(rows)
    out.to_csv(OUT_TABLES / "heterogeneity" / "heterogeneity_did_results.csv", index=False)
    print("Saved heterogeneity DiD results.")


def make_heterogeneity_plots(df):
    for var, label in [
        ("high_gun_ownership_baseline", "High vs Low Gun Ownership"),
        ("high_share_nonmetro_counties_2013", "High vs Low Rurality"),
        ("high_baseline_firearm_suicide_rate", "High vs Low Baseline Firearm Suicide"),
    ]:
        agg = (
            df.groupby([var, "Year"], as_index=False)["firearm_suicide_rate_per_100k"]
            .mean()
        )

        plt.figure(figsize=(8, 5))
        for grp, grp_df in agg.groupby(var):
            grp_name = "High" if grp == 1 else "Low"
            plt.plot(grp_df["Year"], grp_df["firearm_suicide_rate_per_100k"], label=grp_name)

        plt.title(f"Firearm Suicide by {label}")
        plt.xlabel("Year")
        plt.ylabel("Mean Firearm Suicide Rate per 100k")
        plt.legend()
        plt.tight_layout()
        fname = label.lower().replace(" ", "_").replace("/", "_")
        plt.savefig(OUT_FIGS / "heterogeneity" / f"{fname}.png", dpi=200)
        plt.close()

    print("Saved heterogeneity plots.")


def run_political_selection(df):
    state_level = (
        df.groupby("State", as_index=False)
        .agg(
            ever_adopter=("ever_adopter", "max"),
            permitless_year=("permitless_year", "first"),
            rep_vote_share_baseline=("rep_vote_share_baseline", "first"),
            gun_ownership_baseline=("gun_ownership_baseline", "first"),
            rurality=("share_nonmetro_counties_2013", "first"),
            baseline_firearm_suicide=("baseline_firearm_suicide_rate", "first"),
            unemployment_rate=("unemployment_rate", "mean"),
            income_pc=("income_pc", "mean"),
        )
    )

    # Save full state-level file
    state_level.to_csv(
        OUT_TABLES / "political_selection" / "state_level_political_selection_inputs.csv",
        index=False
    )

    # Only summarize numeric columns
    numeric_cols = [
        "permitless_year",
        "rep_vote_share_baseline",
        "gun_ownership_baseline",
        "rurality",
        "baseline_firearm_suicide",
        "unemployment_rate",
        "income_pc",
    ]

    desc = (
        state_level.groupby("ever_adopter")[numeric_cols]
        .agg(["mean", "std", "median"])
    )
    desc.to_csv(
        OUT_TABLES / "political_selection" / "adopter_vs_nonadopter_state_characteristics.csv"
    )

    # Simple logit: who adopts?
    logit_df = state_level.dropna().copy()
    model = smf.logit(
        "ever_adopter ~ rep_vote_share_baseline + gun_ownership_baseline + rurality + baseline_firearm_suicide",
        data=logit_df
    ).fit(disp=False)

    rows = []
    for term in model.params.index:
        rows.append({
            "term": term,
            "coef": model.params[term],
            "se": model.bse[term],
            "p_value": model.pvalues[term],
            "odds_ratio": np.exp(model.params[term])
        })

    out = pd.DataFrame(rows)
    out.to_csv(
        OUT_TABLES / "political_selection" / "logit_adoption_results.csv",
        index=False
    )

    # Scatter plot
    plt.figure(figsize=(8, 5))
    plt.scatter(
        state_level["baseline_firearm_suicide"],
        state_level["rep_vote_share_baseline"],
        c=state_level["ever_adopter"]
    )
    plt.xlabel("Baseline Firearm Suicide Rate")
    plt.ylabel("Baseline Republican Two-Party Vote Share")
    plt.title("Political Selection and Baseline Risk")
    plt.tight_layout()
    plt.savefig(OUT_FIGS / "main" / "political_selection_scatter.png", dpi=200)
    plt.close()

    print("Saved political selection outputs.")


def build_conclusion_table():
    did = pd.read_csv(OUT_TABLES / "did" / "twfe_did_main_results.csv")
    welch = pd.read_csv(OUT_TABLES / "main" / "welch_change_score_results.csv")
    hetero = pd.read_csv(OUT_TABLES / "heterogeneity" / "heterogeneity_did_results.csv")

    summary_rows = []

    for outcome in did["outcome"].unique():
        did_row = did[did["outcome"] == outcome].iloc[0]
        welch_subset = welch[welch["outcome"] == outcome].sort_values("window")
        het_subset = hetero[hetero["outcome"] == outcome]

        best_het = None
        if not het_subset.empty:
            best_het = het_subset.loc[het_subset["interaction_p"].astype(float).idxmin(), "heterogeneity_dimension"]

        conclusion = "No clear evidence"
        if did_row["p_post_permitless"] < 0.05 and did_row["coef_post_permitless"] > 0:
            conclusion = "Positive post-adoption association"
        elif did_row["p_post_permitless"] < 0.05 and did_row["coef_post_permitless"] < 0:
            conclusion = "Negative post-adoption association"

        summary_rows.append({
            "outcome": outcome,
            "outcome_label": OUTCOME_LABELS[outcome],
            "did_coef": did_row["coef_post_permitless"],
            "did_p_value": did_row["p_post_permitless"],
            "welch_diff_2y": welch_subset.loc[welch_subset["window"] == 2, "difference"].iloc[0] if 2 in welch_subset["window"].values else np.nan,
            "welch_p_2y": welch_subset.loc[welch_subset["window"] == 2, "p_value"].iloc[0] if 2 in welch_subset["window"].values else np.nan,
            "welch_diff_3y": welch_subset.loc[welch_subset["window"] == 3, "difference"].iloc[0] if 3 in welch_subset["window"].values else np.nan,
            "welch_p_3y": welch_subset.loc[welch_subset["window"] == 3, "p_value"].iloc[0] if 3 in welch_subset["window"].values else np.nan,
            "welch_diff_5y": welch_subset.loc[welch_subset["window"] == 5, "difference"].iloc[0] if 5 in welch_subset["window"].values else np.nan,
            "welch_p_5y": welch_subset.loc[welch_subset["window"] == 5, "p_value"].iloc[0] if 5 in welch_subset["window"].values else np.nan,
            "strongest_heterogeneity_signal": best_het,
            "machine_summary": conclusion,
        })

    summary = pd.DataFrame(summary_rows)
    summary.to_csv(OUT_TABLES / "main" / "model_conclusion_summary.csv", index=False)
    print("Saved model conclusion summary.")


def main():
    df, state_base = load_panel()
    print("Loaded panel:", df.shape)

    make_descriptive_tables(df, state_base)
    run_welch_change_score_tests(df)
    run_twfe_did(df)
    save_event_study_outputs(df)
    run_heterogeneity_did(df)
    make_heterogeneity_plots(df)
    run_political_selection(df)
    build_conclusion_table()

    print("\nAll analyses complete.")
    print(f"Check outputs in:\n{OUT_TABLES}\n{OUT_FIGS}")


if __name__ == "__main__":
    main()