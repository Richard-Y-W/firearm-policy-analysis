import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "analysis_panel_firearm_suicide_deaths_1999_2024.csv"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"

OUT_TABLES.mkdir(parents=True, exist_ok=True)
OUT_FIGS.mkdir(parents=True, exist_ok=True)

BLUE = "#1F5A85"
GRAY = "#6F7378"
LIGHT_GRAY = "#E9ECEF"
DARK = "#202124"
OUTCOME_LABEL = "Firearm suicide deaths"
EVENT_FIGURE = "event_time_firearm_suicide_deaths.png"


def configure_plot_style():
    plt.rcParams.update(
        {
            "axes.edgecolor": "#C9C9C9",
            "axes.labelcolor": DARK,
            "axes.labelsize": 10,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.titlesize": 12,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
            "font.family": "DejaVu Sans",
            "legend.fontsize": 9,
            "savefig.facecolor": "white",
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
        }
    )


def compute_A(df, state, t, pre_k=3, post_k=3):
    pre_years = list(range(t - pre_k, t))
    post_years = list(range(t + 1, t + post_k + 1))

    s = df[df["State"] == state]
    pre = s[s["Year"].isin(pre_years)]["rate_per_100k"]
    post = s[s["Year"].isin(post_years)]["rate_per_100k"]

    if len(pre) != pre_k or len(post) != post_k:
        return np.nan

    return float(post.mean() - pre.mean())

def welch_ttest(x, y):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)

    nx, ny = len(x), len(y)
    mx, my = x.mean(), y.mean()
    vx, vy = x.var(ddof=1), y.var(ddof=1)

    se = math.sqrt(vx / nx + vy / ny)
    t = (mx - my) / se
    dfree = (vx / nx + vy / ny) ** 2 / (
        (vx ** 2) / ((nx ** 2) * (nx - 1)) + (vy ** 2) / ((ny ** 2) * (ny - 1))
    )
    p = 2 * stats.t.sf(abs(t), dfree)
    ci_low = (mx - my) - stats.t.ppf(0.975, dfree) * se
    ci_high = (mx - my) + stats.t.ppf(0.975, dfree) * se

    return {
        "n_adopters": nx,
        "n_controls": ny,
        "mean_A_adopters": mx,
        "mean_A_controls": my,
        "diff": mx - my,
        "t": t,
        "df": dfree,
        "p": p,
        "ci_low": ci_low,
        "ci_high": ci_high,
    }

def build_change_scores(df, pre_k, post_k, latest_treatment_year):
    adopt_map = (
        df[["State", "permitless_year"]]
        .dropna()
        .drop_duplicates()
        .set_index("State")["permitless_year"]
        .astype(int)
        .to_dict()
    )

    adopters = []
    for st, t in adopt_map.items():
        if t > latest_treatment_year:
            continue
        a = compute_A(df, st, t, pre_k=pre_k, post_k=post_k)
        if not np.isnan(a):
            adopters.append((st, t, a))

    adopters_df = pd.DataFrame(adopters, columns=["State", "EffectiveYear", "A"])

    all_states = sorted(df["State"].unique().tolist())
    never_adopters = [s for s in all_states if s not in adopt_map]

    controls = []
    for st in never_adopters:
        vals = []
        for _, row in adopters_df.iterrows():
            t = int(row["EffectiveYear"])
            a = compute_A(df, st, t, pre_k=pre_k, post_k=post_k)
            if not np.isnan(a):
                vals.append(a)
        if len(vals) == len(adopters_df) and len(vals) > 0:
            controls.append((st, float(np.mean(vals))))

    controls_df = pd.DataFrame(controls, columns=["State", "A"])
    return adopters_df, controls_df

def make_event_plot(df, adopters, controls):
    rate_lookup = df.set_index(["State", "Year"])["rate_per_100k"]
    adopter_year_map = dict(zip(adopters["State"], adopters["EffectiveYear"]))
    control_states = controls["State"].tolist()
    adopter_years = adopters["EffectiveYear"].astype(int).tolist()

    def get_rate(state, year):
        try:
            return float(rate_lookup.loc[(state, year)])
        except KeyError:
            return np.nan

    k_range = list(range(-6, 7))
    adopter_points = []
    control_points = []

    for st, t in adopter_year_map.items():
        for k in k_range:
            if k == 0:
                continue
            r = get_rate(st, t + k)
            if not np.isnan(r):
                adopter_points.append((k, r))

    for t in adopter_years:
        for st in control_states:
            for k in k_range:
                if k == 0:
                    continue
                r = get_rate(st, t + k)
                if not np.isnan(r):
                    control_points.append((k, r))

    adopter_df = pd.DataFrame(adopter_points, columns=["event_time", "rate"])
    control_df = pd.DataFrame(control_points, columns=["event_time", "rate"])

    adopter_mean = adopter_df.groupby("event_time", as_index=False)["rate"].mean()
    control_mean = control_df.groupby("event_time", as_index=False)["rate"].mean()

    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    ax.plot(
        adopter_mean["event_time"],
        adopter_mean["rate"],
        color=BLUE,
        linewidth=2.4,
        marker="o",
        markersize=5.5,
        label="Adopting states",
    )
    ax.plot(
        control_mean["event_time"],
        control_mean["rate"],
        color=GRAY,
        linewidth=2.2,
        marker="o",
        markersize=5.2,
        label="Never-adopting controls",
    )
    ax.axvline(0, color="#8A8A8A", linestyle="--", linewidth=1)
    ax.grid(axis="y", color=LIGHT_GRAY, linewidth=0.8)
    ax.tick_params(length=0, pad=3)
    ax.set_xticks(k_range)
    ax.set_xlabel("Years relative to permitless carry adoption")
    ax.set_ylabel(f"{OUTCOME_LABEL} per 100,000")
    ax.set_title(f"{OUTCOME_LABEL} around adoption", loc="left")

    for series, color, label in [
        (adopter_mean, BLUE, "Adopting states"),
        (control_mean, GRAY, "Never-adopting controls"),
    ]:
        last = series.sort_values("event_time").iloc[-1]
        ax.text(
            last["event_time"] + 0.18,
            last["rate"],
            label,
            color=color,
            fontsize=9,
            fontweight="bold",
            va="center",
        )

    fig.text(
        0.02,
        0.02,
        "Adoption year omitted; lines show annual group means.",
        fontsize=8.3,
        color="#555555",
        ha="left",
        va="bottom",
    )
    ax.set_xlim(min(k_range) - 0.4, max(k_range) + 1.9)
    fig.tight_layout(rect=[0, 0.055, 1, 1])
    fig.savefig(OUT_FIGS / EVENT_FIGURE, dpi=500, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)

def main():
    configure_plot_style()

    if not DATA.exists():
        raise FileNotFoundError(f"Missing analysis panel: {DATA}")

    df = pd.read_csv(DATA)

    results = []
    state_scores = None

    settings = [
        (2, 2, 2021, "2y_pre_vs_2y_post"),
        (3, 3, 2020, "3y_pre_vs_3y_post"),
        (5, 5, 2018, "5y_pre_vs_5y_post"),
    ]

    for pre_k, post_k, latest_t, label in settings:
        adopters, controls = build_change_scores(df, pre_k, post_k, latest_t)
        res = welch_ttest(adopters["A"], controls["A"])
        res["window"] = label
        results.append(res)

        if label == "3y_pre_vs_3y_post":
            make_event_plot(df, adopters, controls)
            adopters["group"] = "Adopter"
            controls["group"] = "Control"
            controls["EffectiveYear"] = np.nan
            state_scores = pd.concat(
                [
                    adopters[["State", "group", "EffectiveYear", "A"]],
                    controls[["State", "group", "EffectiveYear", "A"]],
                ],
                ignore_index=True,
            )

    results_df = pd.DataFrame(results)[
        ["window", "n_adopters", "n_controls", "mean_A_adopters", "mean_A_controls", "diff", "t", "df", "p", "ci_low", "ci_high"]
    ]
    results_df.to_csv(OUT_TABLES / "welch_results_firearm_suicide_deaths.csv", index=False)

    if state_scores is not None:
        state_scores.to_csv(OUT_TABLES / "state_level_A_3y_firearm_suicide_deaths.csv", index=False)

    print(results_df)
    print("Saved analysis outputs.")

if __name__ == "__main__":
    main()
