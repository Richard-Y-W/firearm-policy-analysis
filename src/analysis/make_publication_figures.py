from pathlib import Path
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analysis.phase1_utils import apply_clean_primary_sample
except ModuleNotFoundError:
    from phase1_utils import apply_clean_primary_sample


ROOT = Path(__file__).resolve().parents[2]
PANEL_FILE = ROOT / "data" / "processed" / "analysis_panel_full_outcomes.csv"
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "figures" / "publication"

BLUE = "#2F77B4"
ORANGE = "#DF8F2D"
RED = "#C44E52"
GRAY = "#5F5F5F"
LIGHT_GRAY = "#E7E7E7"
DARK = "#111111"
MUTED_TEAL = "#3A8F8A"
MUTED_PURPLE = "#7B6FAF"
MUTED_GOLD = "#C49A34"
MUTED_ROSE = "#B85C70"
RAW_POINT = "#B9B9B9"

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

OUTCOME_COLORS = {
    "Firearm Suicide": BLUE,
    "Total Suicide": MUTED_TEAL,
    "Total Firearm Deaths": MUTED_PURPLE,
    "Non-Firearm Suicide": MUTED_GOLD,
    "Firearm Homicide": MUTED_ROSE,
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
        style="white",
        font="Arial",
        rc={
            "axes.edgecolor": DARK,
            "axes.labelcolor": DARK,
            "axes.labelsize": 9.5,
            "axes.titlesize": 10.2,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "legend.fontsize": 8.5,
            "legend.title_fontsize": 8.5,
            "figure.dpi": 180,
            "savefig.dpi": 600,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "lines.solid_capstyle": "round",
            "patch.linewidth": 0.4,
        },
    )
    plt.rcParams.update(
        {
            "axes.titleweight": "bold",
            "axes.linewidth": 0.9,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "legend.frameon": False,
        }
    )


def savefig(fig, stem):
    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{stem}.{ext}", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def load_panel():
    df = pd.read_csv(PANEL_FILE)
    df = apply_clean_primary_sample(df)
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
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.7, alpha=0.78)
    if xgrid:
        ax.grid(axis="x", color=LIGHT_GRAY, linewidth=0.55, alpha=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(length=3.0, width=0.9, color=DARK, labelcolor=DARK, pad=2.8)
    ax.spines["left"].set_color(DARK)
    ax.spines["bottom"].set_color(DARK)


def panel_label(ax, label):
    ax.text(
        -0.055,
        1.045,
        label,
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.2,
        fontweight="bold",
        color=DARK,
    )


def title_and_note(fig, title, note, y_title=0.95, y_note=0.015):
    fig.suptitle(title, x=0.01, y=y_title, ha="left", fontsize=10.6, fontweight="bold", color=DARK)
    fig.text(0.01, y_note, note, ha="left", va="bottom", fontsize=7.2, color="#4B4B4B")


def p_text(p):
    return "p<0.001" if p < 0.001 else f"p={p:.3f}"


def adopter_state_changes(df, outcomes):
    rows = []
    adopters = df[df["ever_adopter"] == 1].dropna(subset=["permitless_year"])
    for (state, permitless_year), g in adopters.groupby(["State", "permitless_year"]):
        pre = g[g["Year"] < permitless_year]
        post = g[g["Year"] >= permitless_year]
        if pre.empty or post.empty:
            continue
        for outcome in outcomes:
            rows.append(
                {
                    "State": state,
                    "outcome": outcome,
                    "Outcome": OUTCOMES[outcome],
                    "change": post[outcome].mean() - pre[outcome].mean(),
                }
            )
    return pd.DataFrame(rows)


def event_state_context(df, outcome, window=(-5, 5)):
    treated = df[df["ever_adopter"] == 1].dropna(subset=["permitless_year"]).copy()
    treated["event_time"] = (treated["Year"] - treated["permitless_year"]).astype(int)
    treated = treated[treated["event_time"].between(window[0], window[1])]
    baselines = (
        treated[treated["event_time"] == -1]
        .set_index("State")[outcome]
        .rename("reference_rate")
    )
    treated = treated.join(baselines, on="State")
    treated = treated.dropna(subset=["reference_rate", outcome])
    treated["relative_rate"] = treated[outcome] - treated["reference_rate"]
    return treated[treated["event_time"] != -1]


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

    fig, axes = plt.subplots(2, 2, figsize=(7.6, 5.35), sharex=True)
    axes = axes.ravel()

    for ax, (_, label), letter in zip(axes, outcomes, "ABCD"):
        d = annual[annual["Outcome"] == label]
        line_specs = [
            ("Adopting states", BLUE, 2.25, "-"),
            ("Never-adopting states", ORANGE, 2.0, (0, (3, 2))),
        ]
        for group, color, width, linestyle in line_specs:
            g = d[d["Adoption group"] == group].sort_values("Year")
            ax.plot(g["Year"], g["rate"], color=color, linewidth=width, linestyle=linestyle)
            ax.scatter(g["Year"].iloc[-1], g["rate"].iloc[-1], s=24, color=color, zorder=3, edgecolor="white", linewidth=0.55)
            ax.text(
                g["Year"].iloc[-1] + 0.25,
                g["rate"].iloc[-1],
                f"{g['rate'].iloc[-1]:.1f}",
                color=color,
                fontsize=8.0,
                va="center",
                fontweight="semibold",
            )
        ax.set_title(f"{letter}. {label}", loc="left")
        ax.set_xlim(1999, 2025.4)
        ax.set_xticks([2000, 2005, 2010, 2015, 2020, 2024])
        ax.set_xlabel("")
        ax.set_ylabel("Deaths per 100,000" if letter in "AC" else "")
        style_axis(ax)

    handles = [
        Line2D([0], [0], color=BLUE, linewidth=2.9, label="Adopting states"),
        Line2D([0], [0], color=ORANGE, linewidth=2.5, linestyle=(0, (3, 2)), label="Never-adopting states"),
    ]
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.56, 0.955), ncol=2, frameon=False)
    title_and_note(
        fig,
        "Outcome trends by permitless carry adoption status",
        "Annual state means, 1999-2024. Groups are defined by whether a state ever adopts permitless carry during the panel.",
        y_title=0.995,
        y_note=0.01,
    )
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.12, top=0.84, wspace=0.18, hspace=0.38)
    savefig(fig, "figure_01_outcome_trends_by_adoption")


def fig_twfe_forest(df):
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    did = did.assign(
        ci_low=lambda x: x["coef_post_permitless"] - 1.96 * x["se_post_permitless"],
        ci_high=lambda x: x["coef_post_permitless"] + 1.96 * x["se_post_permitless"],
    )
    did["outcome_label"] = pd.Categorical(did["outcome_label"], categories=OUTCOME_ORDER[::-1], ordered=True)
    did = did.sort_values("outcome_label")

    fig, ax = plt.subplots(figsize=(6.7, 3.65))
    colors = did["outcome_label"].map(OUTCOME_COLORS).to_numpy()
    y = np.arange(len(did))
    raw = adopter_state_changes(df, list(OUTCOMES.keys()))
    raw["outcome_label"] = pd.Categorical(raw["Outcome"], categories=OUTCOME_ORDER[::-1], ordered=True)
    base_y = {label: i for i, label in enumerate(did["outcome_label"])}
    rng = np.random.default_rng(1934)
    for label, g in raw.dropna(subset=["outcome_label"]).groupby("outcome_label", observed=False):
        if label not in base_y:
            continue
        jitter = rng.uniform(-0.13, 0.13, len(g))
        ax.scatter(
            g["change"],
            np.full(len(g), base_y[label]) + jitter,
            s=12,
            color=RAW_POINT,
            alpha=0.36,
            linewidth=0,
            zorder=1,
        )
    ax.axvspan(-0.25, 0.25, color="#F2F2F2", zorder=0)
    ax.hlines(y, did["ci_low"], did["ci_high"], color=colors, linewidth=2.45, zorder=2)
    ax.scatter(did["coef_post_permitless"], y, color=colors, s=62, zorder=3, edgecolor="white", linewidth=0.8)
    ax.axvline(0, color=DARK, linewidth=1.0)
    for yi, row in zip(y, did.itertuples()):
        ax.text(
            row.ci_high + 0.07,
            yi,
            f"{row.coef_post_permitless:+.2f} ({p_text(row.p_post_permitless)})",
            va="center",
            fontsize=7.5,
            color="#333333",
        )
    ax.set_yticks(y)
    ax.set_yticklabels(did["outcome_label"])
    ax.set_xlabel("Post-adoption coefficient, deaths per 100,000")
    ax.set_ylabel("")
    ax.set_xlim(min(did["ci_low"].min() - 0.15, -0.8), did["ci_high"].max() + 0.7)
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Adjusted difference-in-differences estimates",
        "Colored estimates are adjusted TWFE coefficients with +/- 1.96 SE intervals; pale points show unadjusted adopter-state pre/post changes.",
    )
    fig.subplots_adjust(left=0.22, right=0.985, bottom=0.20, top=0.84)
    savefig(fig, "figure_02_twfe_coefficient_forest")


def fig_change_score_robustness():
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    welch["outcome_label"] = pd.Categorical(welch["outcome_label"], categories=OUTCOME_ORDER[::-1], ordered=True)
    welch["window_label"] = welch["window"].astype(int).astype(str) + "-year"
    welch = welch.sort_values(["outcome_label", "window"])

    fig, ax = plt.subplots(figsize=(6.9, 3.95))
    windows = list(welch["window_label"].drop_duplicates())
    offsets = np.linspace(-0.22, 0.22, len(windows))
    colors = dict(zip(windows, [BLUE, ORANGE, RED]))
    base_y = {label: i for i, label in enumerate(welch["outcome_label"].cat.categories)}

    for offset, window in zip(offsets, windows):
        d = welch[welch["window_label"] == window]
        yy = [base_y[x] + offset for x in d["outcome_label"]]
        ax.scatter(d["difference"], yy, s=48, color=colors[window], label=window, edgecolor="white", linewidth=0.7, zorder=3)
        for x, yval, p in zip(d["difference"], yy, d["p_value"]):
            if p < 0.05:
                ax.text(x + 0.028, yval, "*", va="center", ha="left", color=colors[window], fontsize=10.5, fontweight="bold")

    ax.axvline(0, color=DARK, linewidth=1.0)
    ax.set_yticks(range(len(base_y)))
    ax.set_yticklabels(list(base_y.keys()))
    ax.set_xlabel("Adopter minus never-adopter change score, deaths per 100,000")
    ax.set_ylabel("")
    ax.legend(title="Pre/post window", frameon=False, loc="lower right", handletextpad=0.5)
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Change-score comparisons across robustness windows",
        "Positive values indicate larger pre/post increases in adopting states. Asterisks denote Welch-test p<0.05.",
    )
    fig.subplots_adjust(left=0.24, right=0.985, bottom=0.20, top=0.84)
    savefig(fig, "figure_03_change_score_robustness")


def fig_event_study_grid(df):
    frames = []
    for outcome, fname in EVENT_FILES.items():
        d = pd.read_csv(TABLES / "event_study" / fname)
        d["outcome"] = outcome
        d["Outcome"] = OUTCOMES[outcome]
        frames.append(d)
    event = pd.concat(frames, ignore_index=True)

    fig, axes = plt.subplots(2, 3, figsize=(7.6, 4.9), sharex=True)
    axes = axes.ravel()
    for ax, outcome, letter in zip(axes, OUTCOME_ORDER, "ABCDE"):
        d = event[event["Outcome"] == outcome].sort_values("event_time")
        outcome_key = d["outcome"].iloc[0]
        color = OUTCOME_COLORS[outcome]
        raw = event_state_context(df, outcome_key)
        rng = np.random.default_rng(sum(ord(ch) for ch in outcome))
        ax.scatter(
            raw["event_time"] + rng.uniform(-0.08, 0.08, len(raw)),
            raw["relative_rate"],
            s=9,
            color=RAW_POINT,
            alpha=0.28,
            linewidth=0,
            zorder=1,
        )
        ax.errorbar(
            d["event_time"],
            d["coef"],
            yerr=[d["coef"] - d["ci_low"], d["ci_high"] - d["coef"]],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=1.45,
            capsize=3.2,
            capthick=1.25,
            markersize=4.2,
            markeredgecolor="white",
            markeredgewidth=0.55,
            zorder=3,
        )
        ax.plot(d["event_time"], d["coef"], color=color, linewidth=1.25, alpha=0.85, zorder=2)
        ax.axhline(0, color=DARK, linewidth=0.9)
        ax.axvline(-1, color="#8A8A8A", linestyle=(0, (3, 2)), linewidth=0.85)
        ax.set_title(f"{letter}. {outcome}", loc="left")
        ax.set_xticks([-5, -3, -1, 1, 3, 5])
        ax.set_xlabel("Years relative to adoption")
        ax.set_ylabel("Estimate" if letter in "AD" else "")
        style_axis(ax, xgrid=True)
    axes[-1].axis("off")
    axes[-1].text(
        0.02,
        0.82,
        "\n".join(
            textwrap.wrap(
                "Reference period: year immediately before adoption. Whiskers show 95% confidence intervals; pale points show treated state-year deviations from that state's reference year.",
                32,
            )
        ),
        transform=axes[-1].transAxes,
        ha="left",
        va="top",
        fontsize=7.8,
        color="#4B4B4B",
    )
    title_and_note(
        fig,
        "Event-study estimates around adoption",
        "Dynamic coefficients are plotted relative to the year before permitless carry adoption; background points show the underlying treated-state event-time data.",
    )
    fig.subplots_adjust(left=0.075, right=0.985, bottom=0.14, top=0.84, wspace=0.28, hspace=0.48)
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

    fig, axes = plt.subplots(1, 3, figsize=(7.85, 3.9), sharey=True)
    for ax, dim, letter in zip(axes, dim_labels.values(), "ABC"):
        d = hetero[hetero["Dimension"] == dim].sort_values("outcome_label")
        y = np.arange(len(d))
        colors = d["outcome_label"].map(OUTCOME_COLORS).to_numpy()
        ax.hlines(y, d["ci_low"], d["ci_high"], color=colors, linewidth=2.25, alpha=0.92)
        for yi, row, color in zip(y, d.itertuples(), colors):
            marker = "D" if row.interaction_p < 0.05 else "o"
            ax.scatter(
                row.interaction_coef,
                yi,
                color=color,
                marker=marker,
                s=54,
                zorder=3,
                edgecolor="white",
                linewidth=0.75,
            )
        ax.axvline(0, color=DARK, linewidth=1.0)
        ax.set_yticks(y)
        ax.set_yticklabels(d["outcome_label"])
        ax.set_title(f"{letter}. {dim}", loc="left")
        ax.set_xlabel("Interaction coefficient")
        style_axis(ax, xgrid=True)
        ax.margins(x=0.08)
    title_and_note(
        fig,
        "Heterogeneity in post-adoption associations",
        "Interaction terms estimate whether associations are larger in states above each baseline median; diamonds mark p<0.05.",
    )
    fig.subplots_adjust(left=0.20, right=0.985, bottom=0.20, top=0.82, wspace=0.20)
    savefig(fig, "figure_05_heterogeneity_interactions")


def fig_political_selection(state_level):
    d = state_level.dropna(subset=["baseline_firearm_suicide", "rep_vote_share_baseline", "gun_ownership_baseline"]).copy()
    fig, ax = plt.subplots(figsize=(6.95, 4.75))
    palette = {"Adopting states": BLUE, "Never-adopting states": ORANGE}
    sns.scatterplot(
        data=d,
        x="baseline_firearm_suicide",
        y="rep_vote_share_baseline",
        hue="Adoption group",
        size="gun_ownership_baseline",
        sizes=(34, 155),
        alpha=0.86,
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
        color="#595959",
        line_kws={"linewidth": 1.25, "linestyle": (0, (3, 2)), "alpha": 0.8},
        ci=None,
        ax=ax,
    )
    labels = {
        "Utah": (0.07, 0.006),
        "Wyoming": (0.07, 0.006),
        "Montana": (0.07, 0.006),
        "Hawaii": (0.07, 0.004),
        "New York": (0.06, 0.004),
        "Vermont": (0.06, -0.002),
        "California": (0.06, 0.004),
        "Maryland": (0.06, 0.004),
        "Nevada": (0.06, 0.004),
        "New Mexico": (0.06, 0.004),
    }
    for _, row in d[d["State"].isin(labels)].iterrows():
        dx, dy = labels[row["State"]]
        ax.text(
            row["baseline_firearm_suicide"] + dx,
            row["rep_vote_share_baseline"] + dy,
            row["abbr"],
            fontsize=7.0,
            color=DARK,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.82, "pad": 0.35},
        )

    ax.set_xlabel("Baseline firearm suicide rate per 100,000")
    ax.set_ylabel("Baseline Republican two-party vote share")
    handles = [
        Line2D([0], [0], marker="o", color="w", label="Adopting states", markerfacecolor=BLUE, markeredgecolor="white", markersize=6.4),
        Line2D([0], [0], marker="o", color="w", label="Never-adopting states", markerfacecolor=ORANGE, markeredgecolor="white", markersize=6.4),
    ]
    ax.legend(handles=handles, frameon=False, loc="upper left", title="Adoption group")
    style_axis(ax, xgrid=True)
    title_and_note(
        fig,
        "Policy adoption is patterned by baseline risk and politics",
        "Point size is proportional to baseline household firearm ownership. State-level baseline measures describe selection, not treatment effects.",
    )
    fig.subplots_adjust(left=0.12, right=0.985, bottom=0.20, top=0.84)
    savefig(fig, "figure_06_political_selection_scatter")


def main():
    configure_style()
    df = load_panel()
    state_level = load_state_baselines(df)
    fig_outcome_trends(df)
    fig_twfe_forest(df)
    fig_change_score_robustness()
    fig_event_study_grid(df)
    fig_heterogeneity_forest()
    fig_political_selection(state_level)
    print(f"Saved publication figures to: {OUT}")


if __name__ == "__main__":
    main()
