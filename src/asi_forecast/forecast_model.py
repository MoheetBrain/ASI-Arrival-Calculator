"""Forecast model constants and column names.

Keeping these labels in one file makes generated CSVs easier to compare
across versions.
"""

from __future__ import annotations


SAMPLED_INPUT_COLUMNS = [
    "effective_compute_growth_x_per_year",
    "algorithmic_efficiency_x_per_year",
    "agent_time_horizon_doubling_months",
    "current_agent_task_horizon_hours",
    "coding_automation_threshold_human_hours",
    "general_capability_lag_after_coding_months",
    "agi_integration_lag_months",
    "ai_rnd_automation_lag_after_agi_months",
    "superhuman_ai_researcher_lag_months",
    "takeoff_lag_months",
    "infrastructure_friction_months",
    "phase_overlap_coefficient",
    "compute_governance_friction_months",
    "deployment_governance_delay_months",
    "secrecy_visibility_delay_months",
]


DERIVED_COLUMNS = [
    "adjusted_agent_time_horizon_doubling_months",
    "coding_automation_months",
    "long_horizon_agent_months",
    "general_capability_months",
    "agi_arrival_months",
    "raw_agi_to_asi_lag_months",
    "effective_agi_to_asi_lag_months",
    "internal_asi_arrival_months",
    "public_asi_arrival_months",
    "agi_to_asi_lag_months",
]
