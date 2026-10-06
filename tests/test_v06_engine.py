"""Invariants and mechanism checks for the v0.6 engine."""

import copy

import numpy as np
import pytest

from asi_forecast.helpers import month_to_index
from asi_forecast.v06 import load_v06_config, simulate_v06
from asi_forecast.v06.config import apply_v06_scenario
from asi_forecast.v06.regimes import regime_posterior

SIMS = 20_000


@pytest.fixture(scope="module")
def config():
    return load_v06_config()


@pytest.fixture(scope="module")
def frame(config):
    return simulate_v06(config, sims=SIMS, seed=11)


def test_timeline_ordering_and_non_negative_lags(frame, config):
    start = month_to_index(config["simulation"]["start_month"])
    assert (frame["agi_month_index"] >= start).all()
    assert (frame["internal_asi_month_index"] >= frame["agi_month_index"]).all()
    assert (frame["public_asi_month_index"] >= frame["internal_asi_month_index"]).all()
    assert (frame["agi_to_asi_lag_months"] >= 0).all()
    assert (frame["public_delay_months"] >= 0).all()
    assert (frame["agi_months"] >= 0).all()


def test_all_inputs_finite(frame):
    numeric = frame.select_dtypes(include=[np.number])
    assert np.isfinite(numeric.drop(columns=["accel_ratio", "software_rate_at_asi_oom_per_year", "progress_rate_at_asi_oom_per_year", "automation_fraction_at_asi", "research_speedup_at_asi"]).to_numpy()).all()


def test_seeded_runs_are_deterministic(config):
    a = simulate_v06(config, sims=3000, seed=5)
    b = simulate_v06(config, sims=3000, seed=5)
    assert (a["internal_asi_months"].to_numpy() == b["internal_asi_months"].to_numpy()).all()


def test_monte_carlo_medians_are_stable_across_seeds(config):
    a = simulate_v06(config, sims=SIMS, seed=101)
    b = simulate_v06(config, sims=SIMS, seed=202)
    for column in ("agi_months", "internal_asi_months", "agi_to_asi_lag_months"):
        assert abs(a[column].median() - b[column].median()) < 2.5, column


def test_h2_mass_appears_at_start_month(frame, config):
    start = month_to_index(config["simulation"]["start_month"])
    p_h2 = config["agi_status"]["p_already_agi"]["value"]
    share = np.mean(frame["agi_month_index"] == start)
    assert share >= p_h2 - 0.01


def test_no_hard_lag_floor(frame):
    """v0.5.1 had P(lag < 12 months) = 0 by construction; v0.6 must not."""
    assert np.mean(frame["agi_to_asi_lag_months"] < 12) > 0.0


def test_regime_definitions_are_self_consistent(frame):
    unpaused = frame[frame["post_agi_pause_months"] == 0]
    rec = unpaused[unpaused["regime"] == "recursive"]
    assert np.mean(rec["dynamics_class"] == "SUPERLINEAR") >= 0.75
    assert frame.loc[frame["regime"] == "recursive", "loop_gain_log10_per_oom"].median() > 0
    assert frame.loc[frame["regime"] == "bottlenecked", "loop_gain_log10_per_oom"].median() < 0
    medians = frame.groupby("regime")["agi_to_asi_lag_months"].median()
    assert medians["recursive"] < medians["fast"] < medians["moderate"] < medians["bottlenecked"]


def test_regime_shares_match_posterior(frame, config):
    posterior = regime_posterior(config["takeoff"])
    shares = frame["regime"].value_counts(normalize=True)
    for regime, weight in posterior.items():
        assert abs(shares.get(regime, 0.0) - weight) < 0.015


def test_correlated_evidence_is_not_double_counted(config):
    takeoff = copy.deepcopy(config["takeoff"])
    before = regime_posterior(takeoff)
    duplicate = copy.deepcopy(takeoff["regime_evidence"][0])
    duplicate["id"] = "duplicate_of_first"
    takeoff["regime_evidence"].append(duplicate)
    after = regime_posterior(takeoff)
    # Duplicating an item inside a correlation group re-weights the group average
    # but must not multiply its likelihood a second time.
    naive = {r: before[r] * float(duplicate["likelihood"][r]) for r in before}
    total = sum(naive.values())
    naive = {r: v / total for r, v in naive.items()}
    shift_after = sum(abs(after[r] - before[r]) for r in before)
    shift_naive = sum(abs(naive[r] - before[r]) for r in before)
    assert shift_after < shift_naive
    assert abs(sum(after.values()) - 1.0) < 1e-12


def test_scenarios_are_ordered(config):
    medians = {}
    for scenario in ("agi_era_fast", "baseline", "bottlenecked"):
        cfg = apply_v06_scenario(config, scenario)
        medians[scenario] = simulate_v06(cfg, sims=8000, seed=3)["internal_asi_months"].median()
    assert medians["agi_era_fast"] < medians["baseline"] < medians["bottlenecked"]


def test_compute_slowdown_delays_agi(config):
    fast = simulate_v06(config, sims=8000, seed=4, fixed={"compute_late_multiplier": 1.0})
    slow = simulate_v06(config, sims=8000, seed=4, fixed={"compute_late_multiplier": 0.35})
    assert slow["agi_months"].median() > fast["agi_months"].median()


def test_fixed_quantile_uses_common_random_numbers(config):
    early = simulate_v06(config, sims=8000, seed=9, fixed_quantile={"doubling_months": 0.1})
    late = simulate_v06(config, sims=8000, seed=9, fixed_quantile={"doubling_months": 0.9})
    assert early["agi_months"].median() < late["agi_months"].median()
    # Everything not overridden is identical draw-for-draw.
    assert (early["asi_gap_oom"].to_numpy() == late["asi_gap_oom"].to_numpy()).all()


def test_unknown_scenario_rejected(config):
    with pytest.raises(ValueError):
        apply_v06_scenario(config, "nonexistent")
