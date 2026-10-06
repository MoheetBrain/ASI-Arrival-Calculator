"""v0.6 auditability contract and protection of the historical v0.5.1 calibration."""

import hashlib
from pathlib import Path

import pandas as pd

from asi_forecast.helpers import index_to_month, load_config, month_to_index
from asi_forecast.monte_carlo import simulate_forecast
from asi_forecast.v06 import load_v06_config
from asi_forecast.v06.config import all_source_ids, traceability_problems

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence_tables" / "v0_6_evidence_2026.csv"
EVIDENCE_TYPES = {
    "EMPIRICAL CAPABILITY RESULT",
    "EMPIRICAL INFRASTRUCTURE RESULT",
    "ACADEMIC ANALYSIS",
    "EXPERT FORECAST",
    "FRONTIER-LAB LEADER FORECAST",
    "STRATEGIC / MARKETING STATEMENT",
    "THEORETICAL ARGUMENT",
    "AUTHOR PRIOR",
}

# SHA-256 of the v0.5.1 files at commit a33ad3e. The historical calibration must
# never be edited in place; v0.6 lives in forecast_inputs/v0_6/ and src/.../v06/.
HISTORICAL_HASHES = {
    "forecast_inputs/base_forecast_inputs.yaml": "fa59265dbe816cc89922b13abaaa7821c92a623aafab22c336879ea7fbc9494c",
    "forecast_inputs/author_prior_scenario.yaml": "61bd532f1af0776e53e625ebd1fdbe5c82630f0a6f65ea0cfac3c2b106b2643c",
    "src/asi_forecast/model.py": "4feee6a162290460a895d2e485c4600c441f27142f97afca1a9e425529040053",
    "src/asi_forecast/monte_carlo.py": "fdb5baba873e083354f6f671b9a0a6f9d33e4239c44263b06d14eeaa28136425",
    "src/asi_forecast/uncertainty.py": "bf8ccfa41d800ed4457e4c854ab3a5f69372085200c549c298f92fc0eddb1299",
}


def test_every_parameter_is_traceable():
    problems = traceability_problems(load_v06_config())
    assert not problems, problems


def test_every_source_id_resolves_to_the_evidence_table():
    table = pd.read_csv(EVIDENCE)
    known = set(table["source_id"])
    missing = sorted(all_source_ids(load_v06_config()) - known)
    assert not missing, f"unknown source ids: {missing}"


def test_evidence_rows_are_complete_and_classified():
    table = pd.read_csv(EVIDENCE)
    assert table["source_id"].is_unique
    for column in table.columns:
        assert table[column].notna().all(), f"empty values in {column}"
    assert set(table["evidence_type"]) <= EVIDENCE_TYPES
    assert table["source_url"].str.startswith("http").all()


def test_historical_v051_files_are_unchanged():
    for rel, expected in HISTORICAL_HASHES.items():
        digest = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        assert digest == expected, f"{rel} was modified; historical calibration must be preserved"


def test_historical_v051_forecast_reproduces():
    """The unchanged v0.5.1 engine still produces its published medians."""
    config = load_config(ROOT / "forecast_inputs" / "base_forecast_inputs.yaml")
    frame = simulate_forecast(config, sims=100_000, seed=42)

    def median_month(column):
        values = frame[column].to_numpy()
        import numpy as np

        return index_to_month(int(round(float(np.percentile(values, 50)))))

    assert median_month("agi_month_index") == "2031-07"
    assert median_month("internal_asi_month_index") == "2034-05"
    assert median_month("public_asi_month_index") == "2035-11"
    assert month_to_index("2031-07") < month_to_index("2034-05")


def test_parameter_source_table_matches_yaml():
    """evidence_tables/v0_6_parameter_sources.csv must be regenerated when inputs change."""
    from asi_forecast.v06.config import parameter_table

    expected = parameter_table(load_v06_config()).astype(str)
    on_disk = pd.read_csv(ROOT / "evidence_tables" / "v0_6_parameter_sources.csv", keep_default_na=False).astype(str)
    assert list(expected["parameter"]) == list(on_disk["parameter"])
    assert list(expected["distribution"]) == list(on_disk["distribution"])
