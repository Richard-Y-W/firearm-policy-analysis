from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "figures" / "publication"

BLUE = "#1F5A85"
TEAL = "#2F8F83"
GOLD = "#C4862C"
RED = "#A6463D"
GRAY = "#737373"
LIGHT_GRAY = "#E9ECEF"
DARK = "#202124"

OUTCOMES = {
    "firearm_suicide_rate_per_100k": "Firearm Suicide",
    "nonfirearm_suicide_rate_per_100k": "Non-Firearm Suicide",
    "total_suicide_rate_per_100k": "Total Suicide",
    "firearm_homicide_rate_per_100k": "Firearm Homicide",
    "total_firearm_rate_per_100k": "Total Firearm Deaths",
}

OUTCOME_ORDER = [
    "Firearm Suicide",
    "Total Suicide",
    "Total Firearm Deaths",
    "Non-Firearm Suicide",
    "Firearm Homicide",
]

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
        style="white",
        font="DejaVu Sans",
        rc={
            "axes.edgecolor": "#B9B9B9",
            "axes.labelcolor": DARK,
            "axes.labelsize": 9.5,
            "axes.titlesize": 10.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
            "legend.title_fontsize": 8.5,
            "figure.dpi": 160,
            "savefig.dpi": 500,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        },
    )
    plt.rcParams.update(
        {
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )


def savefig(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)


def load_panel():
    df = pd.read_csv(PANEL_FILE)
    df["Adoption group"] = np.where(df["ever_adopter"] == 1, "Adopting states", "Never-adopting states")
    return df


def load_state_baselines(df):
    rows = []
    for state, g in df.groupby("State"):
        g = g.sort_values("Year")
        permitless_years = g["permitless_year"].dropna()
        permitless_year = permitless_years.iloc[0] if not permitless_years.empty else np.nan
        if pd.notna(permitless_year):
            baseline = g.loc[g["Year"] < permitless_year, "firearm_suicide_rate_per_100k"].mean()
        else:
            baseline = g.loc[g["Year"] <= 2014, "firearm_suicide_rate_per_100k"].mean()
        rep = g.loc[g["Year"] == 2012, "rep_vote_share_2party"].dropna()
        if rep.empty:
            rep = g["rep_vote_share_2party"].dropna()
        gun = g["gun_ownership"].dropna()
        rural = g["share_nonmetro_counties_2013"].dropna()
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
                "rurality": rural.iloc[0] if not rural.empty else np.nan,
            }
        )
    return pd.DataFrame(rows)


def style_axis(ax, xgrid=False):
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.8)
    if xgrid:
        ax.grid(axis="x", color="#F2F3F4", linewidth=0.6)
    ax.tick_params(length=0, pad=3)
    ax.spines["left"].set_color("#C9C9C9")
    ax.spines["bottom"].set_color("#C9C9C9")


def panel_label(ax, label):
    ax.text(
        -0.02,
        1.05,
        label,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=10,
        fontweight="bold",
        color=DARK,
    )


def title_and_note(fig, title, note, y_title=0.985, y_note=0.022):
    fig.suptitle(title, x=0.01, y=y_title, ha="left", fontsize=13.5, fontweight="bold", color=DARK)
    fig.text(0.01, y_note, note, ha="left", va="bottom", fontsize=8.2, color="#555555")


def fig_outcome_trends(df):
    outcomes = [
        ("firearm_suicide_rate_per_100k", "Firearm Suicide"),
        ("total_suicide_rate_per_100k", "Total Suicide"),
        ("total_firearm_rate_per_100k", "Total Firearm Deaths"),
        ("firearm_homicide_rate_per_100k", "Firearm Homicide"),
    ]
    annual = (
        df.melt(
            id_vars=["State", "Year", "Adoption group"],
            value_vars=[x[0] for x in outcomes],
            var_name="outcome",
            value_name="rate",
        )
        .assign(Outcome=lambda x: x["outcome"].map(OUTCOMES))
        .groupby(["Year", "Adoption group", "Outcome"], as_index=False)["rate"]
        .mean()
    )

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.5), sharex=True)
    axes = axes.ravel()
    palette = {"Adopting states": BLUE, "Never-adopting states": GRAY}

    for ax, (_, label), letter in zip(axes, outcomes, "ABCD"):
        d = annual[annual["Outcome"] == label]
        for group, color, width in [("Adopting states", BLUE, 2.7), ("Never-adopting states", GRAY, 2.2)]:
            g = d[d["Adoption group"] == group].sort_values("Year")
            ax.plot(g["Year"], g["rate"], color=color, linewidth=width)
            ax.scatter(g["Year"].iloc[-1], g["rate"].iloc[-1], s=22, color=color, zorder=3)
            ax.text(
                g["Year"].iloc[-1] + 0.25,
                g["rate"].iloc[-1],
                f"{g['rate'].iloc[-1]:.1f}",
                color=color,
                fontsize=8,
                va="center",
                fontweight="bold",
            )
        ax.set_title(label, loc="left")
        ax.set_xlim(1999, 2025.2)
        ax.set_xlabel("")
        ax.set_ylabel("Deaths per 100,000")
        panel_label(ax, letter)
        style_axis(ax)

    handles = [
        Line2D([0], [0], color=BLUE, linewidth=2.7, label="Adopting states"),
        Line2D([0], [0], color=GRAY, linewidth=2.2, label="Never-adopting states"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.52, 0.93), ncol=2, frameon=False)
    title_and_note(
        fig,
        "Outcome trends by permitless carry adoption status",
        "Annual state means, 1999-2024. Groups are defined by whether a state ever adopts permitless carry during the panel.",
        y_title=0.995,
        y_note=0.01,
    )
    fig.tight_layout(rect=[0, 0.045, 1, 0.91])
    savefig(fig, "figure_01_outcome_trends_by_adoption")


def fig_twfe_forest():
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    did = did.assign(
        ci_low=lambda x: x["coef_post_permitless"] - 1.96 * x["se_post_permitless"],
        ci_high=lambda x: x["coef_post_permitless"] + 1.96 * x["se_post_permitless"],
    )
    did["outcome_label"] = pd.Categorical(did["outcome_label"], categories=OUTCOME_ORDER[::-1], ordered=True)
    did = did.sort_values("outcome_label")

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    colors = np.where(did["p_post_permitless"] < 0.05, BLUE, GRAY)
    y = np.arange(len(did))
    ax.axvspan(-0.25, 0.25, color="#F5F5F5", zorder=0)
    ax.hlines(y, did["ci_low"], did["ci_high"], color=colors, linewidth=2.6)
    ax.scatter(did["coef_post_permitless"], y, color=colors, s=70, zorder=3, edgecolor="white", linewidth=0.7)
    ax.axvline(0, color=DARK, linewidth=1)
    for yi, row in zip(y, did.itertuples()):
        ax.text(
            row.ci_high + 0.06,
            yi,
            f"{row.coef_post_permitless:+.2f} (p={row.p_post_permitless:.3f})",
            va="center",
            fontsize=8.3,
            color="#4A4A4A",
        )
    ax.set_yticks(y)
    ax.set_yticklabels(did["outcome_label"])
    ax.set_xlabel("Post-adoption coefficient, deaths per 100,000")
    ax.set_ylabel("")
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Adjusted difference-in-differences estimates",
        "Two-way fixed effects models include state and year fixed effects plus unemployment and income controls; intervals are +/- 1.96 SE.",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.92])
    savefig(fig, "figure_02_twfe_coefficient_forest")


def fig_change_score_robustness():
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    welch["outcome_label"] = pd.Categorical(welch["outcome_label"], categories=OUTCOME_ORDER[::-1], ordered=True)
    welch["window_label"] = welch["window"].astype(int).astype(str) + "-year"
    welch = welch.sort_values(["outcome_label", "window"])

    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    windows = list(welch["window_label"].drop_duplicates())
    offsets = np.linspace(-0.22, 0.22, len(windows))
    colors = dict(zip(windows, [BLUE, TEAL, GOLD]))
    base_y = {label: i for i, label in enumerate(welch["outcome_label"].cat.categories)}

    for offset, window in zip(offsets, windows):
        d = welch[welch["window_label"] == window]
        yy = [base_y[x] + offset for x in d["outcome_label"]]
        ax.scatter(d["difference"], yy, s=58, color=colors[window], label=window, edgecolor="white", linewidth=0.6, zorder=3)
        for x, yval, p in zip(d["difference"], yy, d["p_value"]):
            if p < 0.05:
                ax.text(x + 0.05, yval, "*", va="center", ha="left", color=colors[window], fontsize=12, fontweight="bold")

    ax.axvline(0, color=DARK, linewidth=1)
    ax.set_yticks(range(len(base_y)))
    ax.set_yticklabels(list(base_y.keys()))
    ax.set_xlabel("Adopter minus never-adopter change score, deaths per 100,000")
    ax.set_ylabel("")
    ax.legend(title="Pre/post window", frameon=False, loc="lower right")
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Change-score comparisons across robustness windows",
        "Positive values indicate larger pre/post increases in adopting states. Asterisks denote Welch-test p<0.05.",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.92])
    savefig(fig, "figure_03_change_score_robustness")


def fig_event_study_grid():
    frames = []
    for outcome, fname in EVENT_FILES.items():
        d = pd.read_csv(TABLES / "event_study" / fname)
        d["Outcome"] = OUTCOMES[outcome]
        frames.append(d)
    event = pd.concat(frames, ignore_index=True)

    fig, axes = plt.subplots(2, 3, figsize=(10.4, 6.3), sharex=True)
    axes = axes.ravel()
    for ax, outcome, letter in zip(axes, OUTCOME_ORDER, "ABCDE"):
        d = event[event["Outcome"] == outcome].sort_values("event_time")
        ax.fill_between(d["event_time"], d["ci_low"], d["ci_high"], color="#C8D8E8", alpha=0.8, linewidth=0)
        ax.plot(d["event_time"], d["coef"], color=BLUE, marker="o", linewidth=2, markersize=4.5)
        ax.axhline(0, color=DARK, linewidth=0.9)
        ax.axvline(-1, color="#777777", linestyle="--", linewidth=0.9)
        ax.set_title(outcome, loc="left")
        ax.set_xlabel("Years relative to adoption")
        ax.set_ylabel("Estimate")
        panel_label(ax, letter)
        style_axis(ax, xgrid=True)
    axes[-1].axis("off")
    axes[-1].text(
        0.02,
        0.9,
        "\n".join(textwrap.wrap("Reference period is the year immediately before adoption. Shaded bands show 95% confidence intervals.", 34)),
        transform=axes[-1].transAxes,
        ha="left",
        va="top",
        fontsize=9,
        color="#555555",
    )
    title_and_note(
        fig,
        "Event-study estimates around adoption",
        "Dynamic coefficients are plotted relative to the year before permitless carry adoption.",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.92])
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
    hetero["outcome_label"] = pd.Categorical(hetero["outcome_label"], categories=OUTCOME_ORDER[::-1], ordered=True)

    fig, axes = plt.subplots(1, 3, figsize=(10.8, 4.7), sharey=True)
    for ax, dim, letter in zip(axes, dim_labels.values(), "ABC"):
        d = hetero[hetero["Dimension"] == dim].sort_values("outcome_label")
        y = np.arange(len(d))
        colors = np.where(d["interaction_p"] < 0.05, BLUE, GRAY)
        ax.hlines(y, d["ci_low"], d["ci_high"], color=colors, linewidth=2.3)
        ax.scatter(d["interaction_coef"], y, color=colors, s=58, zorder=3, edgecolor="white", linewidth=0.6)
        ax.axvline(0, color=DARK, linewidth=1)
        ax.set_yticks(y)
        ax.set_yticklabels(d["outcome_label"])
        ax.set_title(dim, loc="left")
        ax.set_xlabel("Interaction coefficient")
        panel_label(ax, letter)
        style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Heterogeneity in post-adoption associations",
        "Interaction terms estimate whether post-adoption associations are larger in states above the median on each baseline dimension.",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.91])
    savefig(fig, "figure_05_heterogeneity_interactions")


def fig_political_selection(state_level):
    d = state_level.dropna(subset=["baseline_firearm_suicide", "rep_vote_share_baseline", "gun_ownership_baseline"]).copy()
    fig, ax = plt.subplots(figsize=(7.4, 5.4))
    palette = {"Adopting states": BLUE, "Never-adopting states": GRAY}
    sns.scatterplot(
        data=d,
        x="baseline_firearm_suicide",
        y="rep_vote_share_baseline",
        hue="Adoption group",
        size="gun_ownership_baseline",
        sizes=(55, 290),
        alpha=0.88,
        edgecolor="white",
        linewidth=0.75,
        palette=palette,
        legend=False,
        ax=ax,
    )
    sns.regplot(
        data=d,
        x="baseline_firearm_suicide",
        y="rep_vote_share_baseline",
        scatter=False,
        color="#444444",
        line_kws={"linewidth": 1.2, "linestyle": "--", "alpha": 0.7},
        ci=None,
        ax=ax,
    )
    label_mask = (
        (d["baseline_firearm_suicide"] >= d["baseline_firearm_suicide"].quantile(0.86))
        | (d["rep_vote_share_baseline"] >= d["rep_vote_share_baseline"].quantile(0.86))
        | (d["rep_vote_share_baseline"] <= d["rep_vote_share_baseline"].quantile(0.12))
    )
    for _, row in d[label_mask].iterrows():
        ax.text(row["baseline_firearm_suicide"] + 0.05, row["rep_vote_share_baseline"] + 0.002, row["abbr"], fontsize=7.5)

    ax.set_xlabel("Baseline firearm suicide rate per 100,000")
    ax.set_ylabel("Baseline Republican two-party vote share")
    handles = [
        Line2D([0], [0], marker="o", color="w", label="Adopting states", markerfacecolor=BLUE, markersize=7.5),
        Line2D([0], [0], marker="o", color="w", label="Never-adopting states", markerfacecolor=GRAY, markersize=7.5),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper left", title="Adoption group")
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Policy adoption is patterned by baseline risk and politics",
        "Point size is proportional to baseline household firearm ownership. State-level baseline measures describe selection, not treatment effects.",
    )
    fig.tight_layout(rect=[0, 0.07, 1, 0.91])
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
