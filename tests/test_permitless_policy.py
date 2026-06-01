from src.data.permitless_policy import (
    BASELINE_PERMITLESS_STATES,
    PERMITLESS_ADOPTION,
    REVIEWED_AMBIGUOUS_STATES,
)


def test_phase2b_recent_adopters_are_in_within_panel_policy_map():
    assert PERMITLESS_ADOPTION["Nebraska"] == 2023
    assert PERMITLESS_ADOPTION["Louisiana"] == 2024
    assert PERMITLESS_ADOPTION["South Carolina"] == 2024


def test_baseline_and_ambiguous_states_are_not_within_panel_adoptions():
    assert "Vermont" not in PERMITLESS_ADOPTION
    assert "Vermont" in BASELINE_PERMITLESS_STATES
    assert "Arkansas" not in PERMITLESS_ADOPTION
    assert "Arkansas" in REVIEWED_AMBIGUOUS_STATES
