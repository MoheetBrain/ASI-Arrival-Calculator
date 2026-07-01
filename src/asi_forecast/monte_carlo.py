"""Vectorized Monte Carlo simulation for the AGI-to-ASI forecast (v0.4.0).

All structural constants are read from YAML (no hidden Python defaults): the
double-count dampening exponent, the long-horizon threshold hours, the baseline
progress rates, and the long-tail sigma / bio-anchor median year / lag tail median.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .helpers import index_to_month, month_to_index
from .iman_conover import build_correlation_matrix, induce_rank_correlation
from .model import (
    agi_arrival_months,
    coding_automation_months,
    effective_research_takeoff_lag_months,
    internal_asi_arrival_months,
    long_horizon_agent_months,
    progress_adjusted_doubling_months,
    public_asi_arrival_months,
    raw_research_takeoff_lag_months,
)
from .uncertainty import apply_long_tail_mixture, sample_parameter


# Macro drivers whose joint draw is corrected by the correlation matrix.
CORRELATED_DRIVERS = [
    "effective_compute_growth_x_per_year",
    "algorithmic_efficiency_x_per_year",
    "agent_time_horizon_doubling_months",
]


def _sample_named(
    config: dict,
    section: str,
    rng: np.random.Generator,
    key: str,
    sims: int,
) -> np.ndarray:
    """Sample one named triangular forecast input from a config section."""
    return sample_parameter(rng, config[section][key], sims, name=key)


def _sample_governance(
    config: dict,
    rng: np.random.Generator,
    key: str,
    sims: int,
) -> np.ndarray:
    """Sample one targeted governance vector (dispatches on its distribution)."""
    return sample_parameter(rng, config["governance"][key], sims, name=key)


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

    # --- Structural constants from YAML (no hidden defaults) -------------------
    structural = config["structural_adjustments"]
    baselines = config["baseline_progress_rates"]
    long_tail_cal = config["long_tail_calibration"]
    dampening_exponent = float(
        structural["task_horizon_double_count_dampening_exponent"]["value"]
    )
    task_horizon_threshold_hours = float(
        structural["task_horizon_threshold_hours"]["value"]
    )
    baseline_compute = float(
        baselines["effective_compute_growth_baseline_x_per_year"]["value"]
    )
    baseline_algo = float(
        baselines["algorithmic_efficiency_baseline_x_per_year"]["value"]
    )
    long_tail_sigma = float(long_tail_cal["sigma"]["value"])
    bio_anchor_median_year = int(long_tail_cal["bio_anchor_median_year"]["value"])
    # lag_late_tail_median_months is retained in YAML for provenance/rollback but is
    # NOT applied in v0.5: the recalibrated cognitive lags are small, so a 60-month
    # cognitive-lag tail double-counts the physical stall now carried by the
    # infrastructure_friction lognormal (asi.txt Q12/Q13). Long tail -> AGI date only.

    rng = np.random.default_rng(seed)

    # --- Macro drivers, sampled then coupled via Iman-Conover -----------------
    effective_compute = _sample_named(
        config, "agi_stage", rng, "effective_compute_growth_x_per_year", sims
    )
    algorithmic_efficiency = _sample_named(
        config, "agi_stage", rng, "algorithmic_efficiency_x_per_year", sims
    )
    horizon_doubling = _sample_named(
        config, "agi_stage", rng, "agent_time_horizon_doubling_months", sims
    )

    correlation_spec = config.get("correlation_matrix")
    if correlation_spec:
        target = build_correlation_matrix(CORRELATED_DRIVERS, correlation_spec)
        stacked = np.column_stack(
            [effective_compute, algorithmic_efficiency, horizon_doubling]
        )
        stacked = induce_rank_correlation(stacked, target, rng)
        effective_compute, algorithmic_efficiency, horizon_doubling = stacked.T

    # --- Remaining AGI-stage inputs -------------------------------------------
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

    # --- Post-AGI transition lags ---------------------------------------------
    # Cognitive R&D/takeoff lags (compressible by phase overlap).
    ai_rnd_lag = _sample_named(
        config, "asi_stage", rng, "ai_rnd_automation_lag_after_agi_months", sims
    )
    sar_lag = _sample_named(
        config, "asi_stage", rng, "superhuman_ai_researcher_lag_months", sims
    )
    takeoff_lag = _sample_named(config, "asi_stage", rng, "takeoff_lag_months", sims)
    # Physical buildout lag (NOT compressible by phase overlap).
    infrastructure_friction = _sample_named(
        config, "asi_stage", rng, "infrastructure_friction_months", sims
    )
    phase_overlap = sample_parameter(
        rng, config["phase_overlap_coefficient"], sims, name="phase_overlap_coefficient"
    )

    # --- Targeted governance vectors ------------------------------------------
    compute_gov_friction = _sample_governance(
        config, rng, "compute_governance_friction_months", sims
    )
    deployment_gov_delay = _sample_governance(
        config, rng, "deployment_governance_delay_months", sims
    )
    secrecy_visibility_delay = _sample_governance(
        config, rng, "secrecy_visibility_delay_months", sims
    )

    # --- Structural equations -------------------------------------------------
    adjusted_doubling = progress_adjusted_doubling_months(
        horizon_doubling,
        effective_compute,
        algorithmic_efficiency,
        baseline_compute,
        baseline_algo,
        dampening_exponent,
    )
    coding_months = coding_automation_months(
        current_horizon,
        coding_threshold,
        adjusted_doubling,
    )
    long_horizon_months = long_horizon_agent_months(
        current_horizon,
        adjusted_doubling,
        task_horizon_threshold_hours,
    )
    general_capability_months = coding_months + general_capability_lag
    agi_month_offsets = agi_arrival_months(
        coding_months,
        long_horizon_months,
        general_capability_lag,
        agi_integration_lag,
        compute_gov_friction,
    )

    # Phase overlap compresses only the cognitive research/takeoff lag.
    raw_research_takeoff = raw_research_takeoff_lag_months(
        ai_rnd_lag,
        sar_lag,
        takeoff_lag,
    )
    effective_research_takeoff = effective_research_takeoff_lag_months(
        raw_research_takeoff,
        phase_overlap,
    )

    # --- Long-tail mixture (separate tails for AGI date and the cognitive lag) -
    start_index = month_to_index(simulation_config["start_month"])
    long_tail = config.get("long_tail_adjustment", {})
    if long_tail.get("enabled"):
        late_weight = float(long_tail["late_tail_weight"])
        late_start_year = int(long_tail["late_tail_start_year"])
        late_start_offset = month_to_index(f"{late_start_year:04d}-01") - start_index
        agi_median_offset = max(
            (bio_anchor_median_year - late_start_year) * 12.0, 12.0
        )
        # Long tail applies to the AGI date only (asi.txt Q13). It propagates to
        # internal/public ASI additively; the physical-stall tail on the ASI side
        # is carried by the infrastructure_friction lognormal, not a second tail.
        agi_month_offsets = apply_long_tail_mixture(
            agi_month_offsets,
            rng,
            late_tail_weight=late_weight,
            floor_offset_months=float(late_start_offset),
            median_offset_months=agi_median_offset,
            sigma=long_tail_sigma,
        )

    # Infrastructure friction is added UNCOMPRESSED (physical, does not overlap).
    internal_asi_offsets = internal_asi_arrival_months(
        agi_month_offsets,
        effective_research_takeoff,
        infrastructure_friction,
    )
    public_asi_offsets = public_asi_arrival_months(
        internal_asi_offsets,
        deployment_gov_delay,
        secrecy_visibility_delay,
    )

    raw_total_lag = raw_research_takeoff + infrastructure_friction
    effective_total_lag = effective_research_takeoff + infrastructure_friction
    agi_to_asi_lag = internal_asi_offsets - agi_month_offsets
    internal_to_public_delay = deployment_gov_delay + secrecy_visibility_delay

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
            "phase_overlap_coefficient": phase_overlap,
            "compute_governance_friction_months": compute_gov_friction,
            "deployment_governance_delay_months": deployment_gov_delay,
            "secrecy_visibility_delay_months": secrecy_visibility_delay,
            "adjusted_agent_time_horizon_doubling_months": adjusted_doubling,
            "coding_automation_months": coding_months,
            "long_horizon_agent_months": long_horizon_months,
            "general_capability_months": general_capability_months,
            "agi_arrival_months": agi_month_offsets,
            "raw_research_takeoff_lag_months": raw_research_takeoff,
            "effective_research_takeoff_lag_months": effective_research_takeoff,
            "raw_agi_to_asi_lag_months": raw_total_lag,
            "effective_agi_to_asi_lag_months": effective_total_lag,
            "internal_asi_arrival_months": internal_asi_offsets,
            "public_asi_arrival_months": public_asi_offsets,
            "agi_to_asi_lag_months": agi_to_asi_lag,
            "internal_to_public_delay_months": internal_to_public_delay,
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
