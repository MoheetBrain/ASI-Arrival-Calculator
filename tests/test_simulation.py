import subprocess
import sys

import pandas as pd

from asi_forecast.analyze import summarize_arrivals
from asi_forecast.helpers import index_to_month, load_config, month_to_index
from asi_forecast.monte_carlo import simulate_forecast


def test_simulation_returns_requested_number_of_samples():
    config = load_config()
    simulations = simulate_forecast(config, sims=250, seed=7)

    assert len(simulations) == 250
    assert {"agi_month", "internal_asi_month", "public_asi_month"}.issubset(
        simulations.columns
    )


def test_percentiles_are_ordered():
    config = load_config()
    simulations = simulate_forecast(config, sims=500, seed=9)
    summary = summarize_arrivals(simulations)

    assert set(summary["target"]) == {"agi", "internal_asi", "public_asi"}
    for _, row in summary.iterrows():
        assert row["p05_index"] <= row["p10_index"]
        assert row["p10_index"] <= row["p25_index"]
        assert row["p25_index"] <= row["p50_index"]
        assert row["p50_index"] <= row["p75_index"]
        assert row["p75_index"] <= row["p90_index"]
        assert row["p90_index"] <= row["p95_index"]


def test_dates_are_parseable_round_trip():
    month = "2029-07"
    index = month_to_index(month)

    assert index_to_month(index) == month


def test_simulation_month_labels_are_parseable():
    config = load_config()
    simulations = simulate_forecast(config, sims=50, seed=11)

    for label in simulations["agi_month"].head(10):
        assert index_to_month(month_to_index(label)) == label


def test_asi_dates_are_never_before_agi():
    config = load_config()
    simulations = simulate_forecast(config, sims=500, seed=12)

    assert (simulations["internal_asi_month_index"] >= simulations["agi_month_index"]).all()
    assert (
        simulations["public_asi_month_index"]
        >= simulations["internal_asi_month_index"]
    ).all()
    assert (simulations["agi_to_asi_lag_months"] >= 0).all()


def test_cli_target_both_writes_summary(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "asi_forecast.cli",
            "run",
            "--target",
            "both",
            "--sims",
            "250",
            "--results-dir",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "AGI / Transformative General AI" in result.stdout
    summary = pd.read_csv(tmp_path / "forecast_summary.csv")
    assert {"agi", "internal_asi", "public_asi"}.issubset(set(summary["target"]))


def test_cli_explain_targets_works():
    result = subprocess.run(
        [sys.executable, "-m", "asi_forecast.cli", "explain-targets"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "AGI and ASI are separated" in result.stdout
    assert "AGI -> AI R&D automation" in result.stdout
