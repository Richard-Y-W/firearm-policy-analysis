from src.analysis.wrhc_change_score import ROOT, WrhcOutcomeConfig, run_wrhc_change_score_analysis


CONFIG = WrhcOutcomeConfig(
    data_file=ROOT / "data" / "processed" / "analysis_panel_total_firearm_deaths_1999_2024.csv",
    outcome_label="Total firearm deaths",
    event_figure="event_time_total_firearm_deaths.png",
    welch_output="welch_results_total_firearm_deaths.csv",
    state_score_output="state_level_A_3y_total_firearm_deaths.csv",
)


def main():
    results = run_wrhc_change_score_analysis(CONFIG)
    print(results)
    print("Saved analysis outputs.")


if __name__ == "__main__":
    main()
