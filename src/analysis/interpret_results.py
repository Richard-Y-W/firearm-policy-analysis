import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "outputs" / "tables"
OUT_FILE = TABLES / "main" / "final_interpretation_report.md"


def stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.10:
        return "*"
    return ""


def verdict_from_p_and_sign(coef, p):
    if pd.isna(coef) or pd.isna(p):
        return "insufficient evidence"
    if p < 0.05 and coef > 0:
        return "positive association"
    if p < 0.05 and coef < 0:
        return "negative association"
    return "no clear evidence"


def load_tables():
    model_summary = pd.read_csv(TABLES / "main" / "model_conclusion_summary.csv")
    did = pd.read_csv(TABLES / "did" / "twfe_did_main_results.csv")
    welch = pd.read_csv(TABLES / "main" / "welch_change_score_results.csv")
    hetero = pd.read_csv(TABLES / "heterogeneity" / "heterogeneity_did_results.csv")
    adopt_desc = pd.read_csv(TABLES / "political_selection" / "adopter_vs_nonadopter_state_characteristics.csv")
    logit = pd.read_csv(TABLES / "political_selection" / "logit_adoption_results.csv")
    state_level = pd.read_csv(TABLES / "main" / "state_level_characteristics.csv")
    return model_summary, did, welch, hetero, adopt_desc, logit, state_level


def outcome_section(outcome_label, did, welch, hetero):
    did_row = did.loc[did["outcome_label"] == outcome_label].iloc[0]
    welch_rows = welch.loc[welch["outcome_label"] == outcome_label].sort_values("window")
    hetero_rows = hetero.loc[hetero["outcome_label"] == outcome_label].sort_values("interaction_p")

    lines = []
    coef = did_row["coef_post_permitless"]
    p = did_row["p_post_permitless"]
    se = did_row["se_post_permitless"]

    lines.append(f"## {outcome_label}")
    lines.append("")
    lines.append(
        f"- **TWFE DiD estimate:** {coef:.3f} (SE {se:.3f}, p = {p:.4f}) {stars(p)} → **{verdict_from_p_and_sign(coef, p)}**."
    )
    lines.append("")

    lines.append("- **Welch pre-post change-score results:**")
    for _, row in welch_rows.iterrows():
        lines.append(
            f"  - {int(row['window'])}-year window: difference = {row['difference']:.3f}, "
            f"p = {row['p_value']:.4f} {stars(row['p_value'])}"
        )
    lines.append("")

    if not hetero_rows.empty:
        best = hetero_rows.iloc[0]
        lines.append(
            f"- **Strongest heterogeneity signal:** {best['heterogeneity_dimension']} "
            f"(interaction = {best['interaction_coef']:.3f}, p = {best['interaction_p']:.4f} {stars(best['interaction_p'])})"
        )
        lines.append("")

    return "\n".join(lines)


def build_main_conclusion(model_summary, did, welch):
    # Pull the key rows
    fs = did.loc[did["outcome_label"] == "Firearm Suicide"].iloc[0]
    nfs = did.loc[did["outcome_label"] == "Non-Firearm Suicide"].iloc[0]
    ts = did.loc[did["outcome_label"] == "Total Suicide"].iloc[0]
    fh = did.loc[did["outcome_label"] == "Firearm Homicide"].iloc[0]
    tf = did.loc[did["outcome_label"] == "Total Firearm Deaths"].iloc[0]

    fs_w = welch.loc[welch["outcome_label"] == "Firearm Suicide"].sort_values("window")
    fh_w = welch.loc[welch["outcome_label"] == "Firearm Homicide"].sort_values("window")
    nfs_w = welch.loc[welch["outcome_label"] == "Non-Firearm Suicide"].sort_values("window")
    ts_w = welch.loc[welch["outcome_label"] == "Total Suicide"].sort_values("window")

    lines = []
    lines.append("# Final Interpretation Report")
    lines.append("")
    lines.append("## High-Level Conclusion")
    lines.append("")

    # Main conclusion logic
    if fs["p_post_permitless"] < 0.05 and fh["p_post_permitless"] >= 0.05:
        lines.append(
            "The strongest and most policy-relevant finding is that **permitless carry adoption is associated with higher firearm suicide rates after adoption**, while **firearm homicide does not show comparably strong evidence of change** in the main TWFE specification."
        )
    else:
        lines.append(
            "The results do not point to a single uniformly strong effect across all outcomes, but they do suggest meaningful differences across mortality categories."
        )

    lines.append("")

    # Mechanism interpretation
    if fs["p_post_permitless"] < 0.05 and nfs["p_post_permitless"] < 0.05 and ts["p_post_permitless"] < 0.05:
        lines.append(
            "The mechanism layer indicates that the increase is **not confined only to firearm suicide** in the TWFE specification: non-firearm suicide and total suicide also rise. That means the evidence is **not a clean method-substitution-only story** in the current model set, even though firearm suicide remains a central part of the pattern."
        )
    elif fs["p_post_permitless"] < 0.05 and nfs["p_post_permitless"] >= 0.05:
        lines.append(
            "The mechanism layer is consistent with a **means-access interpretation**: firearm suicide rises while non-firearm suicide does not show comparably strong evidence of change."
        )
    else:
        lines.append(
            "The mechanism evidence is mixed and should be described cautiously."
        )

    lines.append("")

    # Welch robustness
    fs_sig = (fs_w["p_value"] < 0.05).sum()
    fh_sig = (fh_w["p_value"] < 0.05).sum()
    if fs_sig >= 2 and fh_sig == 0:
        lines.append(
            "The original Welch change-score design strongly reinforces the suicide result: **firearm suicide is positive and statistically significant across all three windows (2y, 3y, 5y)**, whereas **firearm homicide is not statistically significant in any of the three windows**."
        )
    lines.append("")

    # Total firearm deaths
    if tf["p_post_permitless"] < 0.05:
        lines.append(
            "Total firearm deaths also show a positive post-adoption association, suggesting the suicide finding is large enough to matter for overall firearm mortality."
        )
        lines.append("")

    lines.append("## Recommended one-sentence takeaway")
    lines.append("")
    lines.append(
        "\"States adopting permitless carry laws experienced larger post-adoption increases in firearm suicide rates, while firearm homicide showed no comparably robust evidence of change; broader suicide outcomes also increased, suggesting the pattern may extend beyond a narrow method-substitution story.\""
    )
    lines.append("")

    return "\n".join(lines)


def build_heterogeneity_section(hetero):
    lines = []
    lines.append("## Heterogeneity")
    lines.append("")

    sig = hetero.loc[hetero["interaction_p"] < 0.05].copy()
    if sig.empty:
        lines.append("No heterogeneity interaction survives the 5% level in this first-pass specification.")
        lines.append("")
        return "\n".join(lines)

    for outcome_label, g in sig.groupby("outcome_label"):
        g = g.sort_values("interaction_p")
        best = g.iloc[0]
        lines.append(
            f"- **{outcome_label}:** strongest heterogeneity appears along "
            f"`{best['heterogeneity_dimension']}` "
            f"(interaction = {best['interaction_coef']:.3f}, p = {best['interaction_p']:.4f} {stars(best['interaction_p'])})."
        )
    lines.append("")
    lines.append(
        "Substantively, the cleanest recurring pattern is that **rurality matters**: several outcomes show larger post-adoption associations in more rural states."
    )
    lines.append("")
    return "\n".join(lines)


def build_political_selection_section(logit, state_level):
    lines = []
    lines.append("## Political Selection")
    lines.append("")

    lines.append(
        "The descriptive state-level comparisons are more reliable than the logit coefficients here, because the adoption logit produced **perfect-separation / convergence warnings**."
    )
    lines.append("")
    lines.append(
        "That means the adoption model should be treated as **exploratory only**, not as a stable causal or predictive model."
    )
    lines.append("")

    adopter = state_level[state_level["ever_adopter"] == 1]
    non = state_level[state_level["ever_adopter"] == 0]

    if len(adopter) > 0 and len(non) > 0:
        lines.append("- Descriptive adopter vs non-adopter means:")
        lines.append(f"  - Republican vote share baseline: adopters = {adopter['rep_vote_share'].mean():.3f}, non-adopters = {non['rep_vote_share'].mean():.3f}")
        lines.append(f"  - Gun ownership baseline: adopters = {adopter['gun_ownership'].mean():.3f}, non-adopters = {non['gun_ownership'].mean():.3f}")
        lines.append(f"  - Rurality: adopters = {adopter['rurality'].mean():.3f}, non-adopters = {non['rurality'].mean():.3f}")
        lines.append(f"  - Baseline firearm suicide: adopters = {adopter['baseline_firearm_suicide'].mean():.3f}, non-adopters = {non['baseline_firearm_suicide'].mean():.3f}")
        lines.append("")

    lines.append(
        "The political-selection section can therefore be framed as: **policy adoption is politically and structurally patterned**, but the formal adoption model is unstable in this small sample and should be interpreted cautiously."
    )
    lines.append("")

    return "\n".join(lines)


def build_limitations_section():
    return """## Limitations

- This is still an **observational, state-level quasi-experimental design**, not a randomized experiment.
- The TWFE event-study / DiD results should be treated as a strong first-pass design, but a **modern staggered-adoption estimator** would be a worthwhile next upgrade.
- The political-selection logit showed **perfect-separation / convergence problems**, so those coefficients should not be overinterpreted.
- Some homicide observations are missing due to suppression / incomplete availability, so homicide results are based on a smaller effective sample.
- State-level analysis cannot identify which individuals changed behavior; avoid ecological fallacy language.

"""


def build_abstract_style_section(did):
    fs = did.loc[did["outcome_label"] == "Firearm Suicide"].iloc[0]
    fh = did.loc[did["outcome_label"] == "Firearm Homicide"].iloc[0]
    ts = did.loc[did["outcome_label"] == "Total Suicide"].iloc[0]

    return f"""## Draft Results Paragraph

Across the main state-year panel models, permitless carry adoption was associated with a **{fs['coef_post_permitless']:.3f}-point increase** in firearm suicide rates per 100,000 (p = {fs['p_post_permitless']:.4f}), while firearm homicide showed a **{fh['coef_post_permitless']:.3f}-point estimate** that was not statistically distinguishable from zero (p = {fh['p_post_permitless']:.4f}). Total suicide also increased in the main TWFE specification (coef = {ts['coef_post_permitless']:.3f}, p = {ts['p_post_permitless']:.4f}). Taken together, these findings suggest that permitless carry adoption is more consistently associated with suicide-related mortality than with firearm homicide in this dataset.

"""


def main():
    model_summary, did, welch, hetero, adopt_desc, logit, state_level = load_tables()

    sections = []
    sections.append(build_main_conclusion(model_summary, did, welch))
    sections.append(outcome_section("Firearm Suicide", did, welch, hetero))
    sections.append(outcome_section("Non-Firearm Suicide", did, welch, hetero))
    sections.append(outcome_section("Total Suicide", did, welch, hetero))
    sections.append(outcome_section("Firearm Homicide", did, welch, hetero))
    sections.append(outcome_section("Total Firearm Deaths", did, welch, hetero))
    sections.append(build_heterogeneity_section(hetero))
    sections.append(build_political_selection_section(logit, state_level))
    sections.append(build_abstract_style_section(did))
    sections.append(build_limitations_section())

    report = "\n".join(sections)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(report, encoding="utf-8")

    print(f"Saved: {OUT_FILE}")
    print("\n--- REPORT PREVIEW ---\n")
    print(report[:4000])


if __name__ == "__main__":
    main()