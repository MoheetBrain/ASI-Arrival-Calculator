"""Stage-gated AGI-to-ASI structural equations."""

from __future__ import annotations

import numpy as np


LONG_HORIZON_AGENT_THRESHOLD_HOURS = 168.0


def progress_adjusted_doubling_months(
    agent_time_horizon_doubling_months: np.ndarray,
    effective_compute_growth_x_per_year: np.ndarray,
    algorithmic_efficiency_x_per_year: np.ndarray,
) -> np.ndarray:
    """Adjust task-horizon doubling time by compute and algorithmic progress."""
    combined_progress = effective_compute_growth_x_per_year * algorithmic_efficiency_x_per_year
    base_combined_progress = 3.4 * 3.0
    base_log_progress = np.log2(base_combined_progress)
    sampled_log_progress = np.maximum(np.log2(np.maximum(combined_progress, 1.0001)), 0.01)
    return agent_time_horizon_doubling_months * (base_log_progress / sampled_log_progress)


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
) -> np.ndarray:
    """Estimate when one-week autonomous task reliability is reached."""
    ratio = LONG_HORIZON_AGENT_THRESHOLD_HOURS / np.maximum(
        current_agent_task_horizon_hours,
        0.001,
    )
    return adjusted_doubling_months * np.maximum(np.log2(ratio), 0.0)


def agi_arrival_months(
    coding_automation: np.ndarray,
    long_horizon_agent: np.ndarray,
    general_capability_lag_after_coding_months: np.ndarray,
    agi_integration_lag_months: np.ndarray,
) -> np.ndarray:
    """AGI occurs after coding, long-horizon agency, and broad generality."""
    general_capability = coding_automation + general_capability_lag_after_coding_months
    return (
        np.maximum.reduce([coding_automation, long_horizon_agent, general_capability])
        + agi_integration_lag_months
    )


def internal_asi_arrival_months(
    agi_months: np.ndarray,
    ai_rnd_automation_lag_after_agi_months: np.ndarray,
    superhuman_ai_researcher_lag_months: np.ndarray,
    takeoff_lag_months: np.ndarray,
    infrastructure_friction_months: np.ndarray,
    governance_delay_months: np.ndarray,
) -> np.ndarray:
    """Internal ASI is downstream of AGI, AI R&D automation, SAR, and takeoff."""
    return (
        agi_months
        + ai_rnd_automation_lag_after_agi_months
        + superhuman_ai_researcher_lag_months
        + takeoff_lag_months
        + infrastructure_friction_months
        + governance_delay_months
    )


def public_asi_arrival_months(
    internal_asi_months: np.ndarray,
    deployment_delay_internal_to_public_months: np.ndarray,
) -> np.ndarray:
    """Public ASI is internal ASI plus public deployment delay."""
    return internal_asi_months + deployment_delay_internal_to_public_months
