from src.analysis.additional_data_availability import audit_additional_data_sources


def test_audit_additional_data_sources_reports_missing_inputs(tmp_path):
    out = audit_additional_data_sources(root=tmp_path)

    assert set(out["analysis"]) == {
        "negative_control_mortality",
        "nics_handgun_proxy",
        "sex_age_stratification",
    }
    assert set(out["availability_status"]) == {"missing_required_local_data"}


def test_audit_additional_data_sources_reports_refresh_step_when_data_exist(tmp_path):
    processed = tmp_path / "data" / "processed"
    processed.mkdir(parents=True)
    panel = processed / "analysis_panel_negative_control_mortality_1999_2024.csv"
    panel.write_text("State,Year\nAlabama,2024\n")

    out = audit_additional_data_sources(root=tmp_path)
    row = out[out["analysis"].eq("negative_control_mortality")].iloc[0]

    assert row["availability_status"] == "local_data_detected"
    assert "additional_mortality_checks" in row["next_step"]
    assert "Export the six files" not in row["next_step"]
