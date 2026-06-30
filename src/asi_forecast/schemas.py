"""Pydantic schemas for AGI-to-ASI forecast input validation (v1.0).

The v1.0 schema reflects the structural fixes in ANSWERS.txt:

- A ``phase_overlap_coefficient`` for the AGI-to-ASI transition.
- A ``long_tail_adjustment`` lognormal mixture to remove hard upper-bound walls.
- The generic ``governance_delay`` is removed and replaced by three targeted
  governance vectors with explicit ``applies_to`` semantics.
- A ``correlation_matrix`` that couples the macro drivers (effective compute,
  algorithmic efficiency, agent task-horizon doubling).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


DistributionName = Literal["triangular"]
EvidenceCategory = Literal[
    "agi", "asi", "intermediate", "governance", "compute", "outside_forecast"
]


class TriangularParameter(BaseModel):
    """One editable triangular forecast input."""

    model_config = ConfigDict(extra="forbid")

    distribution: DistributionName
    low: float
    mode: float
    high: float
    unit: str
    evidence_category: EvidenceCategory | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_ordering(self) -> "TriangularParameter":
        if self.low > self.mode or self.mode > self.high:
            raise ValueError("triangular parameters require low <= mode <= high")
        return self


class GovernanceParameter(BaseModel):
    """A targeted governance delay vector.

    Unlike the deleted generic ``governance_delay_months``, each vector records
    *where* it applies (``applies_to``) so the engine can place it on the correct
    timeline: internal capability vs public deployment vs public visibility.
    """

    model_config = ConfigDict(extra="forbid")

    applies_to: Literal[
        "internal_agi_and_internal_asi",
        "public_asi_only",
        "public_visibility_only",
    ]
    low: float
    mode: float
    high: float
    unit: str = "months"
    evidence: str | None = None

    @model_validator(mode="after")
    def validate_ordering(self) -> "GovernanceParameter":
        if self.low > self.mode or self.mode > self.high:
            raise ValueError("governance parameters require low <= mode <= high")
        return self


class GovernanceSpec(BaseModel):
    """The three targeted governance vectors that replace the generic delay."""

    model_config = ConfigDict(extra="forbid")

    compute_governance_friction_months: GovernanceParameter
    deployment_governance_delay_months: GovernanceParameter
    secrecy_visibility_delay_months: GovernanceParameter


class LongTailSpec(BaseModel):
    """Lognormal mixture that restores fat-tail probability mass.

    ANSWERS.txt "Long-Tail Problem": triangular-only inputs impose an artificial
    0% probability wall past their high bound. A mixture routes ``late_tail_weight``
    of the mass into a shifted lognormal so late-century arrivals remain possible.
    """

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    distribution_type: Literal["mixture"] = "mixture"
    base_model_weight: float = Field(ge=0.0, le=1.0)
    late_tail_weight: float = Field(ge=0.0, le=1.0)
    late_tail_distribution: Literal["shifted_lognormal"] = "shifted_lognormal"
    late_tail_start_year: int = Field(ge=2020)
    description: str | None = None

    @model_validator(mode="after")
    def validate_weights(self) -> "LongTailSpec":
        total = self.base_model_weight + self.late_tail_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                "base_model_weight + late_tail_weight must sum to 1.0; "
                f"got {total}"
            )
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
    """Strict top-level AGI-to-ASI forecast input file (v1.0)."""

    model_config = ConfigDict(extra="forbid")

    simulation: SimulationSpec
    author_prior: AuthorPriorSpec
    agi_stage: dict[str, TriangularParameter]
    asi_stage: dict[str, TriangularParameter]
    phase_overlap_coefficient: TriangularParameter
    long_tail_adjustment: LongTailSpec
    governance: GovernanceSpec
    correlation_matrix: dict[str, dict[str, float]] | None = None

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

    @field_validator("correlation_matrix")
    @classmethod
    def validate_correlations(
        cls,
        matrix: dict[str, dict[str, float]] | None,
    ) -> dict[str, dict[str, float]] | None:
        if matrix is None:
            return matrix
        for source, targets in matrix.items():
            for target, value in targets.items():
                if not -1.0 <= float(value) <= 1.0:
                    raise ValueError(
                        f"correlation {source}->{target} must be in [-1, 1]; "
                        f"got {value}"
                    )
        return matrix


def validate_forecast_config(raw_config: dict) -> ForecastConfig:
    """Validate and return a typed forecast config."""
    return ForecastConfig.model_validate(raw_config)
