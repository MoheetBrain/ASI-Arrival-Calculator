"""Stage-gated AGI-to-ASI structural equations (v0.4.0 calibration-prep).

All structural constants are now passed in explicitly (sourced from YAML by
``monte_carlo.py``) rather than hardcoded here, so every number that influences
the forecast is auditable in ``forecast_inputs/base_forecast_inputs.yaml``.

Key behaviours:

1. Double-count fix: the compute/algo rescaling of the empirical METR doubling is
   dampened by a sub-linear exponent (the empirical doubling already embeds those
   drivers). The exponent and the baseline rates are YAML inputs.
2. AGI is a max-gate over its prerequisites (not a sum), plus the integration lag
   and the internal compute-governance friction.
3. Phase overlap compresses ONLY the research/takeoff cognitive lags. Physical
   infrastructure friction is added uncompressed (it cannot be assumed to
   parallelise away).
4. Governance is split: compute-governance friction is internal (folded into AGI),
   while deployment + secrecy delays apply only to the public date.
"""

from __future__ import annotations

import numpy as np


def progress_adjusted_doubling_months(
    agent_time_horizon_doubling_months: np.ndarray,
    effective_compute_growth_x_per_year: np.ndarray,
    algorithmic_efficiency_x_per_year: np.ndarray,
    baseline_effective_compute_x_per_year: float,
    baseline_algorithmic_efficiency_x_per_year: float,
    dampening_exponent: float,
) -> np.ndarray:
    """Adjust task-horizon doubling time by *dampened* compute/algo progress.

    The speedup ratio (base_log / sampled_log) is raised to ``dampening_exponent``
    (sub-linear, e.g. 0.5) so that faster-than-baseline progress shortens the
    doubling time only partially, avoiding the double-count of drivers already
    baked into the empirical METR doubling. Baselines and exponent come from YAML.

    ⚠️ SEMANTICS WARNING (do not blindly paste asi.txt Q1's value): here
    ``exponent = 0`` means NO compute/algo rescale (full exclusion of the
    double-count, i.e. asi.txt's "Formulation A"), and ``exponent = 1`` means the
    FULL rescale (maximum double-count). asi.txt Q1 uses the opposite convention
    ("1.0 = complete exclusion"), so setting this to 1.0 would MAXIMISE the
    double-count. Rewiring to a true downstream (Formulation A) architecture is a
    deferred structural change; until then this stays at the conservative 0.5.
    """
    combined_progress = effective_compute_growth_x_per_year * algorithmic_efficiency_x_per_year
    base_combined_progress = (
        baseline_effective_compute_x_per_year * baseline_algorithmic_efficiency_x_per_year
    )
    base_log_progress = np.log2(base_combined_progress)
    sampled_log_progress = np.maximum(np.log2(np.maximum(combined_progress, 1.0001)), 0.01)
    speedup_ratio = base_log_progress / sampled_log_progress
    return agent_time_horizon_doubling_months * speedup_ratio ** dampening_exponent


def coding_automation_months(
    current_agent_task_horizon_hours: np.ndarray,
    coding_automation_threshold_human_hours: np.ndarray,
    adjusted_doubling_months: np.ndarray,
) -> np.ndarray:
    """Estimate when strong coding automation threshold is crossed."""
    ratio = coding_automation_threshold_human_hours / np.maximum(
        current_agent_task_horizon_hours,
        0.001,
    )
    return adjusted_doubling_months * np.maximum(np.log2(ratio), 0.0)


def long_horizon_agent_months(
    current_agent_task_horizon_hours: np.ndarray,
    adjusted_doubling_months: np.ndarray,
    task_horizon_threshold_hours: float,
) -> np.ndarray:
    """Estimate when the long-horizon task threshold (e.g. one week) is reached.

    ``task_horizon_threshold_hours`` is a YAML input (no longer a hardcoded 168).
    """
    ratio = task_horizon_threshold_hours / np.maximum(
        current_agent_task_horizon_hours,
        0.001,
    )
    return adjusted_doubling_months * np.maximum(np.log2(ratio), 0.0)


def agi_arrival_months(
    coding_automation: np.ndarray,
    long_horizon_agent: np.ndarray,
    general_capability_lag_after_coding_months: np.ndarray,
    agi_integration_lag_months: np.ndarray,
    compute_governance_friction_months: np.ndarray,
) -> np.ndarray:
    """AGI is the MAX of its prerequisites, not their sum.

    AGI requires coding automation, long-horizon agency, and broad generality to
    mature simultaneously, so the arrival date is the latest (max) prerequisite
    plus the integration lag and the internal compute-governance friction
    (gigawatt data-centre permitting etc.), which is an internal-capability delay.
    """
    general_capability = coding_automation + general_capability_lag_after_coding_months
    return (
        np.maximum.reduce([coding_automation, long_horizon_agent, general_capability])
        + agi_integration_lag_months
        + compute_governance_friction_months
    )


def raw_research_takeoff_lag_months(
    ai_rnd_automation_lag_after_agi_months: np.ndarray,
    superhuman_ai_researcher_lag_months: np.ndarray,
    takeoff_lag_months: np.ndarray,
) -> np.ndarray:
    """Naive sequential sum of the post-AGI COGNITIVE transition lags.

    Infrastructure friction is intentionally excluded here: only software / R&D
    stages are candidates for parallel overlap.
    """
    return (
        ai_rnd_automation_lag_after_agi_months
        + superhuman_ai_researcher_lag_months
        + takeoff_lag_months
    )


def effective_research_takeoff_lag_months(
    raw_research_takeoff_lag_months: np.ndarray,
    phase_overlap_coefficient: np.ndarray,
) -> np.ndarray:
    """Compress the cognitive research/takeoff lag for parallel/overlapping stages."""
    return raw_research_takeoff_lag_months * (1.0 - phase_overlap_coefficient)


def internal_asi_arrival_months(
    agi_months: np.ndarray,
    effective_research_takeoff_lag_months: np.ndarray,
    infrastructure_friction_months: np.ndarray,
) -> np.ndarray:
    """Internal ASI = AGI + compressed cognitive lag + UNCOMPRESSED infra friction.

    Software/R&D stages may overlap and are compressed by the phase-overlap
    coefficient upstream. Physical data-centre buildout, power, and hardware
    procurement (``infrastructure_friction_months``) cannot be assumed to overlap
    away, so it is added at full size here.

    Governance is intentionally absent: safety/export frameworks do not slow a
    lab's secret internal achievement. Internal compute-governance friction is
    already folded into AGI.
    """
    return (
        agi_months
        + effective_research_takeoff_lag_months
        + infrastructure_friction_months
    )


def public_asi_arrival_months(
    internal_asi_months: np.ndarray,
    deployment_governance_delay_months: np.ndarray,
    secrecy_visibility_delay_months: np.ndarray,
) -> np.ndarray:
    """Public ASI = internal ASI + deployment review + secrecy/visibility delay."""
    return (
        internal_asi_months
        + deployment_governance_delay_months
        + secrecy_visibility_delay_months
    )
