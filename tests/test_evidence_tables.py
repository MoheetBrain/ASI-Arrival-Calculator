from pathlib import Path

import pandas as pd


def test_evidence_tables_are_valid_csv():
    root = Path(__file__).resolve().parents[1]

    for path in sorted((root / "evidence_tables").glob("*.csv")):
        table = pd.read_csv(path)

        assert not table.empty, f"{path} should contain evidence rows"
