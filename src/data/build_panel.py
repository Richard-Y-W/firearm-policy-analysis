@"
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_CDC = ROOT / 'data' / 'raw' / 'cdc_wonder'
RAW_RAND = ROOT / 'data' / 'raw' / 'rand'
PROCESSED = ROOT / 'data' / 'processed'

PROCESSED.mkdir(parents=True, exist_ok=True)

def main():
    print('Put your CDC WONDER and RAND files into:')
    print(RAW_CDC)
    print(RAW_RAND)
    print('Then extend this script to clean and merge them.')

if __name__ == '__main__':
    main()
"@ | Set-Content src\data\build_panel.py