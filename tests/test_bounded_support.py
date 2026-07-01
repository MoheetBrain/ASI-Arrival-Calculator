"""Unbounded families (lognormal/gamma) must not leak absurd arrival months.

Because every input is clipped to its audited [low, high], no simulated arrival
should land implausibly far in the future even in a large run.
"""

from asi_forecast.helpers import load_config, month_to_index
from asi_forecast.monte_carlo import simulate_forecast


def test_all_inputs_within_audited_bounds():
    config = load_config()
    sims = simulate_forecast(config, sims=50_000, seed=42)

    stages = {**config["agi_stage"], **config["asi_stage"]}
    stages["phase_overlap_coefficient"] = config["phase_overlap_coefficient"]
    for name, spec in stages.items():
        if name not in sims.columns:
            continue
        values = sims[name].to_numpy()
        assert values.min() >= spec["low"] - 1e-9, f"{name} below low bound"
        assert values.max() <= spec["high"] + 1e-9, f"{name} above high bound"


def test_no_absurd_arrival_months():
    config = load_config()
    sims = simulate_forecast(config, sims=50_000, seed=42)
    start_index = month_to_index(config["simulation"]["start_month"])
    # Even the fattest tail should not exceed ~year 2200 (index sanity ceiling).
    ceiling = month_to_index("2200-01")
    for col in ("agi_month_index", "internal_asi_month_index", "public_asi_month_index"):
        assert sims[col].min() >= start_index
        assert sims[col].max() <= ceiling, f"{col} produced an absurd month"
