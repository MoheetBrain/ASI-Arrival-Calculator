"""Vectorized Monte Carlo simulation for the AGI-to-ASI forecast."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .helpers import index_to_month, month_to_index
from .model import (
    agi_arrival_months,
    coding_automation_months,
    internal_asi_arrival_months,
    long_horizon_agent_months,
    progress_adjusted_doubling_months,
    public_asi_arrival_months,
)
from .uncertainty import sample_parameter


def _sample_named(
    config: dict,
    section: str,
    rng: np.random.Generator,
    key: str,
    sims: int,
) -> np.ndarray:
    """Sample one named triangular forecast input from a config section."""
    return sample_parameter(rng, config[section][key], sims, name=key)


def _month_labels(month_indices: np.ndarray) -> list[str]:
    """Convert numeric month indices into YYYY-MM labels."""
    return [index_to_month(month_index) for month_index in month_indices]


def simulate_forecast(
    config: dict,
    sims: int | None = None,
    seed: int | None = None,
) -> pd.DataFrame:
    """Run the AGI-to-ASI Monte Carlo simulation."""
    simulation_config = config["simulation"]
    sims = int(sims or simulation_config["default_sims"])
    seed = int(seed if seed is not None else simulation_config["random_seed"])
    if sims <= 0:
        raise ValueError("sims must be positive")

    rng = np.random.default_rng(seed)

    effective_compute = _sample_named(
        config, "agi_stage", rng, "effective_compute_growth_x_per_year", sims
    )
    algorithmic_efficiency = _sample_named(
        config, "agi_stage", rng, "algorithmic_efficiency_x_per_year", sims
    )
    horizon_doubling = _sample_named(
        config, "agi_stage", rng, "agent_time_horizon_doubling_months", sims
    )
    current_horizon = _sample_named(
        config, "agi_stage", rng, "current_agent_task_horizon_hours", sims
    )
    coding_threshold = _sample_named(
        config, "agi_stage", rng, "coding_automation_threshold_human_hours", sims
    )
    general_capability_lag = _sample_named(
        config, "agi_stage", rng, "general_capability_lag_after_coding_months", sims
    )
    agi_integration_lag = _sample_named(
        config, "agi_stage", rng, "agi_integration_lag_months", sims
    )

    ai_rnd_lag = _sample_named(
        config, "asi_stage", rng, "ai_rnd_automation_lag_after_agi_months", sims
    )
    sar_lag = _sample_named(
        config, "asi_stage", rng, "superhuman_ai_researcher_lag_months", sims
    )
    takeoff_lag = _sample_named(config, "asi_stage", rng, "takeoff_lag_months", sims)
    infrastructure_friction = _sample_named(
        config, "asi_stage", rng, "infrastructure_friction_months", sims
    )
    governance_delay = _sample_named(
        config, "deployment_stage", rng, "governance_delay_months", sims
    )
    deployment_delay = _sample_named(
        config,
        "deployment_stage",
        rng,
        "deployment_delay_internal_to_public_months",
        sims,
    )

    adjusted_doubling = progress_adjusted_doubling_months(
        horizon_doubling,
        effective_compute,
        algorithmic_efficiency,
    )
    coding_months = coding_automation_months(
        current_horizon,
        coding_threshold,
        adjusted_doubling,
    )
    long_horizon_months = long_horizon_agent_months(current_horizon, adjusted_doubling)
    general_capability_months = coding_months + general_capability_lag
    agi_month_offsets = agi_arrival_months(
        coding_months,
        long_horizon_months,
        general_capability_lag,
        agi_integration_lag,
    )
    internal_asi_offsets = internal_asi_arrival_months(
        agi_month_offsets,
        ai_rnd_lag,
        sar_lag,
        takeoff_lag,
        infrastructure_friction,
        governance_delay,
    )
    public_asi_offsets = public_asi_arrival_months(internal_asi_offsets, deployment_delay)
    agi_to_asi_lag = internal_asi_offsets - agi_month_offsets

    start_index = month_to_index(simulation_config["start_month"])
    agi_month_index = start_index + np.ceil(agi_month_offsets).astype(int)
    internal_asi_month_index = start_index + np.ceil(internal_asi_offsets).astype(int)
    public_asi_month_index = start_index + np.ceil(public_asi_offsets).astype(int)

    frame = pd.DataFrame(
        {
            "sim_id": np.arange(1, sims + 1),
            "effective_compute_growth_x_per_year": effective_compute,
            "algorithmic_efficiency_x_per_year": algorithmic_efficiency,
            "agent_time_horizon_doubling_months": horizon_doubling,
            "current_agent_task_horizon_hours": current_horizon,
            "coding_automation_threshold_human_hours": coding_threshold,
            "general_capability_lag_after_coding_months": general_capability_lag,
            "agi_integration_lag_months": agi_integration_lag,
            "ai_rnd_automation_lag_after_agi_months": ai_rnd_lag,
            "superhuman_ai_researcher_lag_months": sar_lag,
            "takeoff_lag_months": takeoff_lag,
            "infrastructure_friction_months": infrastructure_friction,
            "governance_delay_months": governance_delay,
            "deployment_delay_internal_to_public_months": deployment_delay,
            "adjusted_agent_time_horizon_doubling_months": adjusted_doubling,
            "coding_automation_months": coding_months,
            "long_horizon_agent_months": long_horizon_months,
            "general_capability_months": general_capability_months,
            "agi_arrival_months": agi_month_offsets,
            "internal_asi_arrival_months": internal_asi_offsets,
            "public_asi_arrival_months": public_asi_offsets,
            "agi_to_asi_lag_months": agi_to_asi_lag,
            "internal_to_public_delay_months": deployment_delay,
            "agi_month_index": agi_month_index,
            "internal_asi_month_index": internal_asi_month_index,
            "public_asi_month_index": public_asi_month_index,
        }
    )
    frame["agi_month"] = _month_labels(frame["agi_month_index"].to_numpy())
    frame["internal_asi_month"] = _month_labels(
        frame["internal_asi_month_index"].to_numpy()
    )
    frame["public_asi_month"] = _month_labels(frame["public_asi_month_index"].to_numpy())

    # Compatibility aliases for older code/tests.
    frame["internal_month_index"] = frame["internal_asi_month_index"]
    frame["public_month_index"] = frame["public_asi_month_index"]
    frame["internal_month"] = frame["internal_asi_month"]
    frame["public_month"] = frame["public_asi_month"]
    return frame
