"""Output tables and CLI wiring for the v0.6 engine."""

import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from asi_forecast.helpers import month_to_index
from asi_forecast.v06 import load_v06_config, simulate_v06
from asi_forecast.v06 import metrics
from asi_forecast.v06.rnd_automation import simulate_rnd_automation


@pytest.fixture(scope="module")
def frame():
    return simulate_v06(load_v06_config(), sims=6000, seed=21)


def test_by_year_probabilities_are_monotone(frame):
    table = metrics.by_year_probabilities(frame)
    for column in table.columns[1:]:
        assert np.all(np.diff(table[column].to_numpy()) >= -1e-12)
    last = table.iloc[-1]
    assert last["P(agi by end of year)"] >= last["P(internal_asi by end of year)"] >= last["P(public_asi by end of year)"]


def test_quantiles_are_ordered(frame):
    table = metrics.arrival_quantiles(frame)
    for _, row in table.iterrows():
        idx = [month_to_index(row[f"p{q:02d}"]) for q in metrics.PERCENTILES]
        assert idx == sorted(idx)


def test_lag_probabilities_are_monotone(frame):
    lag = metrics.lag_statistics(frame).set_index("metric")["value"]
    probs = [lag[f"P(lag < {t} months)"] for t in metrics.LAG_THRESHOLDS_MONTHS]
    assert probs == sorted(probs)
    assert abs(lag["P(lag < 120 months)"] + lag["P(lag > 120 months)"] - 1.0) < 1e-3


def test_rnd_automation_is_a_bounded_fraction():
    sims = simulate_rnd_automation(load_v06_config(), sims=5000)
    assert sims["a_rnd_supervised"].between(0, 1).all()
    assert (sims["a_rnd_autonomous"] <= sims["a_rnd_supervised"]).all()


def test_cli_v06_run_and_report(tmp_path):
    run = subprocess.run(
        [sys.executable, "-m", "asi_forecast.cli", "run", "--sims", "2000", "--scenario", "bottlenecked", "--results-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    assert "engine v0.6" in run.stdout and "Scenario: bottlenecked" in run.stdout
    summary = pd.read_csv(tmp_path / "forecast_summary.csv")
    assert set(summary["target"]) == {"agi", "internal_asi", "public_asi"}

    report = subprocess.run(
        [sys.executable, "-m", "asi_forecast.cli", "report", "--sims", "1500", "--sensitivity-sims", "800", "--results-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    assert "ASI ARRIVAL FORECAST — OCTOBER 2026" in report.stdout
    text = (tmp_path / "latest_forecast_report.md").read_text()
    for heading in ("Takeoff-regime posterior", "Backtest of v0.5.1", "factor tornado", "Alternate-prior checks"):
        assert heading in text


def test_cli_historical_engine_still_selectable(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "asi_forecast.cli", "run", "--config", "forecast_inputs/base_forecast_inputs.yaml", "--sims", "500", "--results-dir", str(tmp_path)],
        check=True, capture_output=True, text=True,
    )
    assert "Scenario: base" in result.stdout
