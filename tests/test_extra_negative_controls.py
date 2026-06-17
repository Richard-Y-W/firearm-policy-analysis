from pathlib import Path

import pandas as pd
import pytest

from src.analysis.extra_negative_controls import (
    EXTRA_NEGATIVE_CONTROL_EXPORTS,
    build_extra_negative_control_latex,
    build_extra_negative_control_panel,
)


def test_build_extra_negative_control_panel_requires_export_pairs(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="falls"):
        build_extra_negative_control_panel(raw_dir=tmp_path)


def test_build_extra_negative_control_panel_combines_available_placebo_exports(tmp_path: Path):
    for spec in EXTRA_NEGATIVE_CONTROL_EXPORTS.values():
        for filename in [spec["old"], spec["new"]]:
            pd.DataFrame(
                {
                    "State": ["A"],
                    "State Code": [1],
                    "Year": [2020 if "1999_2020" in filename else 2021],
                    "Deaths": [10],
                    "Population": [100000],
                }
            ).to_csv(tmp_path / filename, sep="\t", index=False)

    out = build_extra_negative_control_panel(raw_dir=tmp_path)

    assert {
        "falls_rate_per_100k",
        "non_transport_injury_excluding_falls_poisoning_rate_per_100k",
        "accidental_poisoning_rate_per_100k",
    }.issubset(out.columns)
    assert out["Year"].tolist() == [2020, 2021]


def test_build_extra_negative_control_latex_formats_placebo_rows():
    table = pd.DataFrame(
        {
            "outcome_label": [
                "Fall mortality",
                "Other non-transport injury excluding falls/poisoning",
                "Accidental poisoning mortality",
            ],
            "coef_post_permitless": [1.17755, -0.25, 2.25],
            "se_post_permitless": [0.91268, 1.1, 1.55],
            "p_post_permitless": [0.19698, 0.82, 0.145],
            "nobs": [1222, 1222, 1222],
        }
    )

    latex = build_extra_negative_control_latex(table)

    assert "\\label{tab:extra_negative_controls}" in latex
    assert "Fall mortality & 1.178 & 0.913 & 0.197 & 1222 \\\\" in latex
    assert "Other non-transport injury excluding falls/poisoning & -0.250 & 1.100 & 0.820 & 1222 \\\\" in latex
    assert "Accidental poisoning mortality & 2.250 & 1.550 & 0.145 & 1222 \\\\" in latex
