"""Small shared helpers for paths, YAML inputs, scenarios, and month math."""

from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml

from .schemas import validate_forecast_config


MONTH_PATTERN = re.compile(r"^\d{4}-\d{2}$")


def project_root() -> Path:
    """Return the repository root when running from the source tree."""
    return Path(__file__).resolve().parents[2]


def default_config_path() -> Path:
    """Default editable forecast inputs file used by the CLI."""
    return project_root() / "forecast_inputs" / "base_forecast_inputs.yaml"


def default_results_dir() -> Path:
    """Default generated results directory used by the CLI."""
    return project_root() / "results"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Read forecast inputs from YAML.

    The model intentionally keeps assumptions outside Python code so a reader
    can change the forecast without editing implementation details.
    """
    path = Path(config_path) if config_path else default_config_path()
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Config did not parse as a mapping: {path}")
    validated = validate_forecast_config(config)
    return validated.model_dump(exclude_none=True)


def dump_config(config: dict[str, Any]) -> str:
    """Render config for the `inputs` CLI command."""
    return yaml.safe_dump(config, sort_keys=False)


def _scale_parameter(
    config: dict[str, Any],
    section: str,
    key: str,
    factor: float,
    minimum: float | None = None,
) -> None:
    """Scale the relevant fields of a parameter distribution in-place."""
    distribution = config[section][key]

    def scaled(value: float) -> float:
        result = float(value) * factor
        if minimum is not None:
            result = max(result, minimum)
        return result

    for field in ("low", "mode", "high"):
        if field in distribution:
            distribution[field] = scaled(distribution[field])


def apply_scenario(config: dict[str, Any], scenario: str) -> dict[str, Any]:
    """Return a scenario-adjusted copy of the config.

    Scenarios are deliberately simple: they shift broad assumptions without
    changing the model structure. The base scenario leaves the file untouched.
    """
    adjusted = copy.deepcopy(config)

    if scenario == "base":
        return adjusted
    if scenario == "fast":
        _scale_parameter(adjusted, "agi_stage", "effective_compute_growth_x_per_year", 1.25, 1.01)
        _scale_parameter(adjusted, "agi_stage", "algorithmic_efficiency_x_per_year", 1.25, 1.01)
        _scale_parameter(adjusted, "agi_stage", "agent_time_horizon_doubling_months", 0.75, 0.5)
        _scale_parameter(adjusted, "agi_stage", "general_capability_lag_after_coding_months", 0.75, 0.0)
        _scale_parameter(adjusted, "agi_stage", "agi_integration_lag_months", 0.75, 0.0)
        _scale_parameter(adjusted, "asi_stage", "ai_rnd_automation_lag_after_agi_months", 0.75, 0.0)
        _scale_parameter(adjusted, "asi_stage", "superhuman_ai_researcher_lag_months", 0.75, 0.0)
        _scale_parameter(adjusted, "asi_stage", "takeoff_lag_months", 0.75, 0.0)
        _scale_parameter(adjusted, "deployment_stage", "governance_delay_months", 0.70, 0.0)
        return validate_forecast_config(adjusted).model_dump(exclude_none=True)
    if scenario == "slow":
        _scale_parameter(adjusted, "agi_stage", "effective_compute_growth_x_per_year", 0.80, 1.01)
        _scale_parameter(adjusted, "agi_stage", "algorithmic_efficiency_x_per_year", 0.75, 1.01)
        _scale_parameter(adjusted, "agi_stage", "agent_time_horizon_doubling_months", 1.35, 0.5)
        _scale_parameter(adjusted, "agi_stage", "general_capability_lag_after_coding_months", 1.35, 0.0)
        _scale_parameter(adjusted, "agi_stage", "agi_integration_lag_months", 1.35, 0.0)
        _scale_parameter(adjusted, "asi_stage", "ai_rnd_automation_lag_after_agi_months", 1.40, 0.0)
        _scale_parameter(adjusted, "asi_stage", "superhuman_ai_researcher_lag_months", 1.40, 0.0)
        _scale_parameter(adjusted, "asi_stage", "takeoff_lag_months", 1.40, 0.0)
        _scale_parameter(adjusted, "asi_stage", "infrastructure_friction_months", 1.25, 0.0)
        _scale_parameter(adjusted, "deployment_stage", "governance_delay_months", 1.50, 0.0)
        _scale_parameter(adjusted, "deployment_stage", "deployment_delay_internal_to_public_months", 1.25, 0.0)
        return validate_forecast_config(adjusted).model_dump(exclude_none=True)

    raise ValueError(f"Unknown scenario: {scenario}")


def month_to_index(month_label: str) -> int:
    """Convert YYYY-MM into a monotonic integer month index."""
    if not isinstance(month_label, str) or not MONTH_PATTERN.match(month_label):
        raise ValueError(f"Month must use YYYY-MM format, got: {month_label!r}")
    year_text, month_text = month_label.split("-")
    year = int(year_text)
    month = int(month_text)
    if month < 1 or month > 12:
        raise ValueError(f"Month number must be 01 through 12, got: {month_label!r}")
    return year * 12 + (month - 1)


def index_to_month(month_index: int) -> str:
    """Convert an integer month index back into YYYY-MM."""
    year = int(month_index) // 12
    month = int(month_index) % 12 + 1
    return f"{year:04d}-{month:02d}"


def ensure_output_dir(path: str | Path | None = None) -> Path:
    """Create and return the results directory."""
    results_dir = Path(path) if path else default_results_dir()
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


# Backwards-compatible internal name for older code and examples.
default_outputs_dir = default_results_dir
