"""Pydantic schemas for AGI-to-ASI forecast input validation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DistributionName = Literal["triangular"]
EvidenceCategory = Literal["agi", "asi", "intermediate", "governance", "compute", "outside_forecast"]


class TriangularParameter(BaseModel):
    """One editable triangular forecast input."""

    model_config = ConfigDict(extra="forbid")

    distribution: DistributionName
    low: float
    mode: float
    high: float
    unit: str
    evidence_category: EvidenceCategory | None = None

    @model_validator(mode="after")
    def validate_ordering(self) -> "TriangularParameter":
        if self.low > self.mode or self.mode > self.high:
            raise ValueError("triangular parameters require low <= mode <= high")
        return self


class SimulationSpec(BaseModel):
    """Simulation control parameters."""

    model_config = ConfigDict(extra="forbid")

    start_month: str
    default_sims: int = Field(gt=0)
    random_seed: int
    convergence_batches: int = Field(default=10, ge=2)


class AuthorPriorSpec(BaseModel):
    """Documented author prior, not blended into the empirical base by default."""

    model_config = ConfigDict(extra="forbid")

    agi_median_month: str | None = None
    asi_median_month: str | None = None
    weight: float = Field(ge=0.0, le=1.0)
    note: str


class ForecastConfig(BaseModel):
    """Strict top-level AGI-to-ASI forecast input file."""

    model_config = ConfigDict(extra="forbid")

    simulation: SimulationSpec
    author_prior: AuthorPriorSpec
    agi_stage: dict[str, TriangularParameter]
    asi_stage: dict[str, TriangularParameter]
    deployment_stage: dict[str, TriangularParameter]

    @field_validator("agi_stage")
    @classmethod
    def require_agi_keys(
        cls,
        stage: dict[str, TriangularParameter],
    ) -> dict[str, TriangularParameter]:
        required = {
            "effective_compute_growth_x_per_year",
            "algorithmic_efficiency_x_per_year",
            "agent_time_horizon_doubling_months",
            "current_agent_task_horizon_hours",
            "coding_automation_threshold_human_hours",
            "general_capability_lag_after_coding_months",
            "agi_integration_lag_months",
        }
        missing = required - set(stage)
        if missing:
            raise ValueError(f"agi_stage missing required keys: {sorted(missing)}")
        return stage

    @field_validator("asi_stage")
    @classmethod
    def require_asi_keys(
        cls,
        stage: dict[str, TriangularParameter],
    ) -> dict[str, TriangularParameter]:
        required = {
            "ai_rnd_automation_lag_after_agi_months",
            "superhuman_ai_researcher_lag_months",
            "takeoff_lag_months",
            "infrastructure_friction_months",
        }
        missing = required - set(stage)
        if missing:
            raise ValueError(f"asi_stage missing required keys: {sorted(missing)}")
        return stage

    @field_validator("deployment_stage")
    @classmethod
    def require_deployment_keys(
        cls,
        stage: dict[str, TriangularParameter],
    ) -> dict[str, TriangularParameter]:
        required = {
            "governance_delay_months",
            "deployment_delay_internal_to_public_months",
        }
        missing = required - set(stage)
        if missing:
            raise ValueError(f"deployment_stage missing required keys: {sorted(missing)}")
        return stage


def validate_forecast_config(raw_config: dict) -> ForecastConfig:
    """Validate and return a typed forecast config."""
    return ForecastConfig.model_validate(raw_config)
