from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "figures" / "publication"

OUTCOMES = {
    "firearm_suicide_rate_per_100k": "Firearm suicide",
    "nonfirearm_suicide_rate_per_100k": "Non-firearm suicide",
    "total_suicide_rate_per_100k": "Total suicide",
    "firearm_homicide_rate_per_100k": "Firearm homicide",
    "total_firearm_rate_per_100k": "Total firearm deaths",
}

EVENT_FILES = {
    "firearm_suicide_rate_per_100k": "event_study_firearm_suicide.csv",
    "nonfirearm_suicide_rate_per_100k": "event_study_nonfirearm_suicide.csv",
    "total_suicide_rate_per_100k": "event_study_total_suicide.csv",
    "firearm_homicide_rate_per_100k": "event_study_firearm_homicide.csv",
    "total_firearm_rate_per_100k": "event_study_total_firearm.csv",
}

STATE_ABBR = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
}


def configure_style():
    sns.set_theme(
        context="paper",
        style="whitegrid",
        font="DejaVu Sans",
        rc={
            "axes.edgecolor": "#3d3d3d",
            "axes.labelcolor": "#202020",
            "axes.titlesize": 9.5,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "legend.title_fontsize": 7.5,
            "figure.dpi": 150,
            "savefig.dpi": 450,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        },
    )
    plt.rcParams["axes.titleweight"] = "bold"


def savefig(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def add_panel_label(ax, label):
    ax.text(
        -0.08,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=9.5,
        fontweight="bold",
        va="bottom",
        ha="right",
    )


def load_panel():
    df = pd.read_csv(PANEL_FILE)
    df["Adoption group"] = np.where(df["ever_adopter"] == 1, "Adopting states", "Never-adopting states")
    return df


def load_state_baselines(df):
    rows = []
    for state, g in df.groupby("State"):
        g = g.sort_values("Year")
        permitless_year = g["permitless_year"].dropna()
        permitless_year = permitless_year.iloc[0] if not permitless_year.empty else np.nan

        if pd.notna(permitless_year):
            baseline = g.loc[g["Year"] < permitless_year, "firearm_suicide_rate_per_100k"].mean()
        else:
            baseline = g.loc[g["Year"] <= 2014, "firearm_suicide_rate_per_100k"].mean()

        rep = g.loc[g["Year"] == 2012, "rep_vote_share_2party"].dropna()
        if rep.empty:
            rep = g["rep_vote_share_2party"].dropna()

        gun = g["gun_ownership"].dropna()
        rows.append(
            {
                "State": state,
                "abbr": STATE_ABBR.get(state, state),
                "ever_adopter": int(g["ever_adopter"].max()),
                "Adoption group": "Adopting states" if int(g["ever_adopter"].max()) == 1 else "Never-adopting states",
                "permitless_year": permitless_year,
                "baseline_firearm_suicide": baseline,
                "rep_vote_share_baseline": rep.iloc[0] if not rep.empty else np.nan,
                "gun_ownership_baseline": gun.iloc[0] if not gun.empty else np.nan,
                "rurality": g["share_nonmetro_counties_2013"].dropna().iloc[0]
                if not g["share_nonmetro_counties_2013"].dropna().empty
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def format_axis(ax):
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.grid(axis="x", color="#f0f0f0", linewidth=0.5)
    sns.despine(ax=ax, trim=True)


def fig_outcome_trends(df):
    long = df.melt(
        id_vars=["State", "Year", "Adoption group"],
        value_vars=["firearm_suicide_rate_per_100k", "firearm_homicide_rate_per_100k"],
        var_name="outcome",
        value_name="rate",
    )
    long["Outcome"] = long["outcome"].map(OUTCOMES)

    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4), sharex=True)
    palette = {"Adopting states": "#1b6ca8", "Never-adopting states": "#8f8f8f"}

    for label, ax in zip(["Firearm suicide", "Firearm homicide"], axes):
        d = long[long["Outcome"] == label]
        sns.lineplot(
            data=d,
            x="Year",
            y="rate",
            hue="Adoption group",
            estimator="mean",
            errorbar=("ci", 95),
            palette=palette,
            linewidth=2,
            ax=ax,
        )
        ax.set_title(label)
        ax.set_xlabel("Year")
        ax.set_ylabel("Rate per 100,000")
        ax.axvline(2016, color="#444444", linestyle="--", linewidth=1, alpha=0.65)
        ax.text(2016.3, ax.get_ylim()[1] * 0.94, "median adoption year", fontsize=7.5, color="#444444")
        format_axis(ax)

    handles, labels = axes[0].get_legend_handles_labels()
    for ax in axes:
        ax.legend_.remove()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False)
    fig.suptitle("Mortality trends by permitless carry adoption status", y=1.02, fontsize=10.5, fontweight="bold")
    fig.subplots_adjust(bottom=0.22, wspace=0.28)
    savefig(fig, "figure_01_outcome_trends_by_adoption")


def fig_twfe_forest():
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    did = did.assign(
        ci_low=lambda x: x["coef_post_permitless"] - 1.96 * x["se_post_permitless"],
        ci_high=lambda x: x["coef_post_permitless"] + 1.96 * x["se_post_permitless"],
    ).sort_values("coef_post_permitless")

    fig, ax = plt.subplots(figsize=(6.6, 3.8))
    colors = np.where(did["p_post_permitless"] < 0.05, "#1b6ca8", "#9a9a9a")
    ax.hlines(did["outcome_label"], did["ci_low"], did["ci_high"], color=colors, linewidth=2.2)
    ax.scatter(did["coef_post_permitless"], did["outcome_label"], color=colors, s=52, zorder=3)
    ax.axvline(0, color="#202020", linewidth=1)
    ax.set_xlabel("Post-adoption coefficient, deaths per 100,000")
    ax.set_ylabel("")
    ax.set_title("TWFE estimates by mortality outcome")
    format_axis(ax)
    savefig(fig, "figure_02_twfe_coefficient_forest")


def fig_change_score_robustness():
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    order = ["Firearm Suicide", "Total Suicide", "Total Firearm Deaths", "Non-Firearm Suicide", "Firearm Homicide"]
    welch["outcome_label"] = pd.Categorical(welch["outcome_label"], categories=order, ordered=True)

    fig, ax = plt.subplots(figsize=(7.4, 4.1))
    sns.pointplot(
        data=welch.sort_values("outcome_label"),
        x="difference",
        y="outcome_label",
        hue="window",
        palette=["#2f7ebc", "#57a773", "#d08c2e"],
        dodge=0.42,
        linestyles="",
        markers=["o", "s", "D"],
        errorbar=None,
        ax=ax,
    )
    ax.axvline(0, color="#202020", linewidth=1)
    ax.set_xlabel("Adopter minus never-adopter change score, deaths per 100,000")
    ax.set_ylabel("")
    ax.set_title("Change-score robustness across pre/post windows")
    ax.legend(title="Window", frameon=False, loc="lower right")
    format_axis(ax)
    savefig(fig, "figure_03_change_score_robustness")


def fig_event_study_grid():
    frames = []
    for outcome, fname in EVENT_FILES.items():
        d = pd.read_csv(TABLES / "event_study" / fname)
        d["Outcome"] = OUTCOMES[outcome]
        frames.append(d)
    event = pd.concat(frames, ignore_index=True)

    order = ["Firearm suicide", "Total suicide", "Total firearm deaths", "Non-firearm suicide", "Firearm homicide"]
    fig, axes = plt.subplots(2, 3, figsize=(10.2, 6.0), sharex=True)
    axes = axes.ravel()

    for i, outcome in enumerate(order):
        ax = axes[i]
        d = event[event["Outcome"] == outcome]
        ax.fill_between(d["event_time"], d["ci_low"], d["ci_high"], color="#a7c7e7", alpha=0.55, linewidth=0)
        ax.plot(d["event_time"], d["coef"], color="#1b6ca8", marker="o", linewidth=1.8, markersize=4)
        ax.axhline(0, color="#202020", linewidth=0.9)
        ax.axvline(-1, color="#666666", linestyle="--", linewidth=0.9)
        ax.set_title(outcome)
        ax.set_xlabel("Years relative to adoption")
        ax.set_ylabel("Estimate")
        add_panel_label(ax, chr(65 + i))
        format_axis(ax)

    axes[-1].axis("off")
    fig.suptitle("Event-study estimates relative to permitless carry adoption", y=1.01, fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "figure_04_event_study_grid")


def fig_heterogeneity_forest():
    hetero = pd.read_csv(TABLES / "heterogeneity" / "heterogeneity_did_results.csv")
    dim_labels = {
        "high_gun_ownership": "High gun ownership",
        "high_rurality": "High rurality",
        "high_baseline_firearm_suicide": "High baseline firearm suicide",
    }
    hetero["Dimension"] = hetero["heterogeneity_dimension"].map(dim_labels)
    hetero["ci_low"] = hetero["interaction_coef"] - 1.96 * hetero["interaction_se"]
    hetero["ci_high"] = hetero["interaction_coef"] + 1.96 * hetero["interaction_se"]

    outcomes = ["Firearm Suicide", "Total Suicide", "Total Firearm Deaths", "Non-Firearm Suicide", "Firearm Homicide"]
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 4.1), sharey=True)
    palette = {"p<0.05": "#1b6ca8", "n.s.": "#9a9a9a"}

    for ax, dim in zip(axes, dim_labels.values()):
        d = hetero[hetero["Dimension"] == dim].copy()
        d["outcome_label"] = pd.Categorical(d["outcome_label"], categories=outcomes, ordered=True)
        d = d.sort_values("outcome_label")
        sig = np.where(d["interaction_p"] < 0.05, "p<0.05", "n.s.")
        colors = [palette[x] for x in sig]
        ax.hlines(d["outcome_label"], d["ci_low"], d["ci_high"], color=colors, linewidth=2.1)
        ax.scatter(d["interaction_coef"], d["outcome_label"], color=colors, s=46, zorder=3)
        ax.axvline(0, color="#202020", linewidth=1)
        ax.set_title(dim)
        ax.set_xlabel("Interaction coefficient")
        ax.set_ylabel("")
        format_axis(ax)

    fig.suptitle("Heterogeneity in post-adoption associations", y=1.02, fontsize=10.5, fontweight="bold")
    fig.tight_layout()
    savefig(fig, "figure_05_heterogeneity_interactions")


def fig_political_selection(state_level):
    d = state_level.dropna(subset=["baseline_firearm_suicide", "rep_vote_share_baseline", "gun_ownership_baseline"]).copy()
    fig, ax = plt.subplots(figsize=(6.7, 4.7))
    palette = {"Adopting states": "#1b6ca8", "Never-adopting states": "#8f8f8f"}
    sns.scatterplot(
        data=d,
        x="baseline_firearm_suicide",
        y="rep_vote_share_baseline",
        hue="Adoption group",
        size="gun_ownership_baseline",
        sizes=(55, 260),
        alpha=0.82,
        edgecolor="white",
        linewidth=0.6,
        palette=palette,
        legend=False,
        ax=ax,
    )

    for _, row in d.iterrows():
        if row["baseline_firearm_suicide"] >= d["baseline_firearm_suicide"].quantile(0.88) or row["rep_vote_share_baseline"] >= d[
            "rep_vote_share_baseline"
        ].quantile(0.88):
            ax.text(row["baseline_firearm_suicide"] + 0.05, row["rep_vote_share_baseline"] + 0.003, row["abbr"], fontsize=7)

    ax.set_xlabel("Baseline firearm suicide rate per 100,000")
    ax.set_ylabel("Republican two-party vote share")
    ax.set_title("Policy adoption is patterned by baseline risk and politics")
    handles = [
        Line2D([0], [0], marker="o", color="w", label="Adopting states", markerfacecolor=palette["Adopting states"], markersize=7),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Never-adopting states",
            markerfacecolor=palette["Never-adopting states"],
            markersize=7,
        ),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper left", title="Adoption group")
    ax.text(
        0.02,
        0.03,
        "Point size reflects baseline household firearm ownership",
        transform=ax.transAxes,
        fontsize=7,
        color="#555555",
    )
    format_axis(ax)
    savefig(fig, "figure_06_political_selection_scatter")


def main():
    configure_style()
    df = load_panel()
    state_level = load_state_baselines(df)

    fig_outcome_trends(df)
    fig_twfe_forest()
    fig_change_score_robustness()
    fig_event_study_grid()
    fig_heterogeneity_forest()
    fig_political_selection(state_level)

    print(f"Saved publication figures to: {OUT}")


if __name__ == "__main__":
    main()
