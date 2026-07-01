"""The v0.4.0 structural YAML sections must exist and validate strictly."""

import copy

import pytest

from asi_forecast.helpers import load_config
from asi_forecast.schemas import validate_forecast_config


def test_sections_exist_with_confidence_and_evidence():
    cfg = load_config()
    for section in (
        "structural_adjustments",
        "long_tail_calibration",
        "baseline_progress_rates",
    ):
        assert section in cfg, f"missing YAML section: {section}"

    exp = cfg["structural_adjustments"]["task_horizon_double_count_dampening_exponent"]
    assert exp["value"] == 0.5
    assert exp["confidence"]
    assert exp["evidence_status"]

    lag = cfg["long_tail_calibration"]["lag_late_tail_median_months"]
    assert lag["value"] == 60
    assert lag["confidence"]
    assert lag["evidence_status"]


def test_dampening_exponent_bounds_enforced():
    cfg = load_config()
    bad = copy.deepcopy(cfg)
    bad["structural_adjustments"]["task_horizon_double_count_dampening_exponent"]["value"] = 1.5
    with pytest.raises(Exception):
        validate_forecast_config(bad)

    bad2 = copy.deepcopy(cfg)
    bad2["structural_adjustments"]["task_horizon_double_count_dampening_exponent"]["value"] = 0.0
    with pytest.raises(Exception):
        validate_forecast_config(bad2)


def test_positive_and_non_negative_constraints():
    cfg = load_config()
    bad = copy.deepcopy(cfg)
    bad["baseline_progress_rates"]["effective_compute_growth_baseline_x_per_year"]["value"] = 0.0
    with pytest.raises(Exception):
        validate_forecast_config(bad)

    bad2 = copy.deepcopy(cfg)
    bad2["long_tail_calibration"]["lag_late_tail_median_months"]["value"] = -1.0
    with pytest.raises(Exception):
        validate_forecast_config(bad2)


def test_required_metadata_fields_enforced():
    cfg = load_config()
    bad = copy.deepcopy(cfg)
    del bad["structural_adjustments"]["task_horizon_threshold_hours"]["confidence"]
    with pytest.raises(Exception):
        validate_forecast_config(bad)

    bad2 = copy.deepcopy(cfg)
    del bad2["long_tail_calibration"]["sigma"]["evidence_status"]
    with pytest.raises(Exception):
        validate_forecast_config(bad2)
