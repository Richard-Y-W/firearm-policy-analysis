import subprocess
import sys


def test_run_all_analysis_uses_headless_matplotlib_backend():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import src.analysis.run_all_analysis; import matplotlib; print(matplotlib.get_backend())",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip().lower() == "agg"
