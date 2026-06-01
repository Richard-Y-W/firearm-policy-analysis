from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "analysis_panel.csv"


def main():
    if not PANEL.exists():
        print("Missing analysis_panel.csv in data/processed/")
        return

    df = pd.read_csv(PANEL)
    print(df.head())
    print(df.columns.tolist())


if __name__ == "__main__":
    main()
