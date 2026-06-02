import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


ROOT = Path(__file__).resolve().parents[2]
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_FIGS = ROOT / "outputs" / "figures"

BLUE = "#1F5A85"
GRAY = "#6F7378"
LIGHT_GRAY = "#E9ECEF"
DARK = "#202124"

WINDOW_SETTINGS = [
    (2, 2, 2021, "2y_pre_vs_2y_post"),
    (3, 3, 2020, "3y_pre_vs_3y_post"),
    (5, 5, 2018, "5y_pre_vs_5y_post"),
]


@dataclass(frozen=True)
class WrhcOutcomeConfig:
    data_file: Path
    outcome_label: str
    event_figure: str
    welch_output: str
    state_score_output: str


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


def compute_change_score(df, state, treatment_year, pre_k=3, post_k=3):
    pre_years = list(range(treatment_year - pre_k, treatment_year))
    post_years = list(range(treatment_year + 1, treatment_year + post_k + 1))

    state_rows = df[df["State"] == state]
    pre = state_rows[state_rows["Year"].isin(pre_years)]["rate_per_100k"]
    post = state_rows[state_rows["Year"].isin(post_years)]["rate_per_100k"]

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
        (vx**2) / ((nx**2) * (nx - 1)) + (vy**2) / ((ny**2) * (ny - 1))
    )
    p = 2 * stats.t.sf(abs(t), dfree)
    margin = stats.t.ppf(0.975, dfree) * se

    return {
        "n_adopters": nx,
        "n_controls": ny,
        "mean_A_adopters": mx,
        "mean_A_controls": my,
        "diff": mx - my,
        "t": t,
        "df": dfree,
        "p": p,
        "ci_low": (mx - my) - margin,
        "ci_high": (mx - my) + margin,
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
    for state, treatment_year in adopt_map.items():
        if treatment_year > latest_treatment_year:
            continue
        score = compute_change_score(df, state, treatment_year, pre_k, post_k)
        if not np.isnan(score):
            adopters.append((state, treatment_year, score))
    adopters_df = pd.DataFrame(adopters, columns=["State", "EffectiveYear", "A"])

    never_adopters = sorted(set(df["State"].unique()) - set(adopt_map))
    controls = []
    for state in never_adopters:
        vals = []
        for _, row in adopters_df.iterrows():
            score = compute_change_score(
                df,
                state,
                int(row["EffectiveYear"]),
                pre_k,
                post_k,
            )
            if not np.isnan(score):
                vals.append(score)
        if len(vals) == len(adopters_df) and vals:
            controls.append((state, float(np.mean(vals))))
    controls_df = pd.DataFrame(controls, columns=["State", "A"])
    return adopters_df, controls_df


def make_event_plot(df, adopters, controls, config: WrhcOutcomeConfig):
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

    for state, treatment_year in adopter_year_map.items():
        for k in k_range:
            if k == 0:
                continue
            rate = get_rate(state, treatment_year + k)
            if not np.isnan(rate):
                adopter_points.append((k, rate))

    for treatment_year in adopter_years:
        for state in control_states:
            for k in k_range:
                if k == 0:
                    continue
                rate = get_rate(state, treatment_year + k)
                if not np.isnan(rate):
                    control_points.append((k, rate))

    adopter_mean = pd.DataFrame(adopter_points, columns=["event_time", "rate"]).groupby(
        "event_time", as_index=False
    )["rate"].mean()
    control_mean = pd.DataFrame(control_points, columns=["event_time", "rate"]).groupby(
        "event_time", as_index=False
    )["rate"].mean()

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
    ax.set_ylabel(f"{config.outcome_label} per 100,000")
    ax.set_title(f"{config.outcome_label} around adoption", loc="left")

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
    fig.savefig(OUT_FIGS / config.event_figure, dpi=500, bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def run_wrhc_change_score_analysis(config: WrhcOutcomeConfig) -> pd.DataFrame:
    configure_plot_style()
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    OUT_FIGS.mkdir(parents=True, exist_ok=True)

    if not config.data_file.exists():
        raise FileNotFoundError(f"Missing analysis panel: {config.data_file}")

    df = pd.read_csv(config.data_file)
    results = []
    state_scores = None

    for pre_k, post_k, latest_t, label in WINDOW_SETTINGS:
        adopters, controls = build_change_scores(df, pre_k, post_k, latest_t)
        res = welch_ttest(adopters["A"], controls["A"])
        res["window"] = label
        results.append(res)

        if label == "3y_pre_vs_3y_post":
            make_event_plot(df, adopters, controls, config)
            adopters = adopters.copy()
            controls = controls.copy()
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
        [
            "window",
            "n_adopters",
            "n_controls",
            "mean_A_adopters",
            "mean_A_controls",
            "diff",
            "t",
            "df",
            "p",
            "ci_low",
            "ci_high",
        ]
    ]
    results_df.to_csv(OUT_TABLES / config.welch_output, index=False)

    if state_scores is not None:
        state_scores.to_csv(OUT_TABLES / config.state_score_output, index=False)

    return results_df
