"""Stage-gated AGI-to-ASI structural equations (v1.0).

This module implements the revised equations from ANSWERS.txt:

1. Double-count fix: the empirical METR doubling already embeds compute and
   algorithmic progress, so the compute/algo rescaling is dampened by a
   sub-linear exponent instead of applied at full strength.
2. AGI is a max-gate over its prerequisites (not a sum), plus the integration
   lag and the internal compute-governance friction.
3. The AGI-to-ASI lag is summed RAW and then compressed by
   (1 - phase_overlap_coefficient) to credit parallel/overlapping stages.
4. Governance is split: compute-governance friction is internal (folded into
   AGI), while deployment + secrecy delays apply only to the public date.
"""

from __future__ import annotations

import numpy as np


LONG_HORIZON_AGENT_THRESHOLD_HOURS = 168.0

# Baseline combined progress used to normalise the doubling-time rescale.
BASE_EFFECTIVE_COMPUTE_X_PER_YEAR = 3.4
BASE_ALGORITHMIC_EFFICIENCY_X_PER_YEAR = 3.0

# ANSWERS.txt "Double-Count Problem": multiplying the empirical doubling by the
# full compute*algo ratio double-counts the very drivers that produced it. We
# apply a sub-linear dampening exponent (effective_agent_progress =
# task_horizon_growth_rate ** 0.5) so compute/algo still informs the doubling
# but at reduced, non-double-counted strength.
COMPUTE_PROGRESS_DAMPENING_EXPONENT = 0.5


def progress_adjusted_doubling_months(
    agent_time_horizon_doubling_months: np.ndarray,
    effective_compute_growth_x_per_year: np.ndarray,
    algorithmic_efficiency_x_per_year: np.ndarray,
    dampening_exponent: float = COMPUTE_PROGRESS_DAMPENING_EXPONENT,
) -> np.ndarray:
    """Adjust task-horizon doubling time by *dampened* compute/algo progress.

    The speedup ratio (base_log / sampled_log) is raised to a sub-linear
    exponent so that faster-than-baseline progress shortens the doubling time
    only partially, avoiding the double-count of drivers already baked into the
    empirical METR doubling.
    """
    combined_progress = effective_compute_growth_x_per_year * algorithmic_efficiency_x_per_year
    base_combined_progress = (
        BASE_EFFECTIVE_COMPUTE_X_PER_YEAR * BASE_ALGORITHMIC_EFFICIENCY_X_PER_YEAR
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


def raw_agi_to_asi_lag_months(
    ai_rnd_automation_lag_after_agi_months: np.ndarray,
    superhuman_ai_researcher_lag_months: np.ndarray,
    takeoff_lag_months: np.ndarray,
    infrastructure_friction_months: np.ndarray,
) -> np.ndarray:
    """Naive sequential sum of the post-AGI intelligence-explosion lags."""
    return (
        ai_rnd_automation_lag_after_agi_months
        + superhuman_ai_researcher_lag_months
        + takeoff_lag_months
        + infrastructure_friction_months
    )


def effective_agi_to_asi_lag_months(
    raw_lag_months: np.ndarray,
    phase_overlap_coefficient: np.ndarray,
) -> np.ndarray:
    """Compress the raw lag for parallel/overlapping transition stages."""
    return raw_lag_months * (1.0 - phase_overlap_coefficient)


def internal_asi_arrival_months(
    agi_months: np.ndarray,
    effective_lag_months: np.ndarray,
) -> np.ndarray:
    """Internal ASI = AGI + the overlap-compressed transition lag.

    Governance is intentionally absent here: safety/export frameworks do not slow
    a lab's secret internal achievement (governance_delay_added_to_internal_asi
    = false). Internal compute-governance friction is already folded into AGI.
    """
    return agi_months + effective_lag_months


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
