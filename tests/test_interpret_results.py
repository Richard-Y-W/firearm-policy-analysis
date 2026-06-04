from src.analysis.interpret_results import build_limitations_section


def test_limitations_reference_completed_modern_staggered_checks():
    text = build_limitations_section()

    assert "modern staggered-adoption checks" in text
    assert "would be a worthwhile next upgrade" not in text
