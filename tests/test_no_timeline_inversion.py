"""Timeline-ordering invariants for the v1.0 stage-gated model.

ANSWERS.txt modification #10: assert that across a large Monte Carlo run the
governance splits and phase-overlap compression never invert the timeline:

    public_ASI_month >= internal_ASI_month >= AGI_month >= current_date
"""

import numpy as np

from asi_forecast.helpers import load_config, month_to_index
from asi_forecast.monte_carlo import simulate_forecast


SAMPLES = 10_000


def test_no_timeline_inversion_across_10k_samples():
    config = load_config()
    simulations = simulate_forecast(config, sims=SAMPLES, seed=2027)

    agi = simulations["agi_month_index"].to_numpy()
    internal = simulations["internal_asi_month_index"].to_numpy()
    public = simulations["public_asi_month_index"].to_numpy()

    start_index = month_to_index(config["simulation"]["start_month"])

    assert (agi >= start_index).all(), "AGI must not precede the simulation start"
    assert (internal >= agi).all(), "internal ASI must not precede AGI"
    assert (public >= internal).all(), "public ASI must not precede internal ASI"


def test_lags_are_non_negative():
    config = load_config()
    simulations = simulate_forecast(config, sims=SAMPLES, seed=99)

    assert (simulations["agi_to_asi_lag_months"] >= 0).all()
    assert (simulations["internal_to_public_delay_months"] >= 0).all()
    assert (simulations["effective_agi_to_asi_lag_months"] >= 0).all()


def test_phase_overlap_compresses_the_raw_lag():
    config = load_config()
    simulations = simulate_forecast(config, sims=SAMPLES, seed=7)

    # Effective lag is the raw lag scaled by (1 - overlap) before the long tail,
    # so its mean must not exceed the raw sequential sum's mean.
    assert (
        simulations["effective_agi_to_asi_lag_months"].mean()
        < simulations["raw_agi_to_asi_lag_months"].mean()
    )
    overlap = simulations["phase_overlap_coefficient"].to_numpy()
    assert np.all((overlap >= 0.15) & (overlap <= 0.65))
