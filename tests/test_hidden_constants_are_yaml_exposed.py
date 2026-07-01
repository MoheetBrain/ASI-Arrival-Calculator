"""Model-critical constants must live in YAML, not hardcoded in Python.

Two checks:
1. The old module-level magic constants are gone.
2. There is no silent fallback: removing a structural YAML section makes the
   simulation fail loudly rather than quietly using a hidden default.
"""

import copy

import pytest

import asi_forecast.model as model_module
import asi_forecast.monte_carlo as monte_carlo_module
import asi_forecast.uncertainty as uncertainty_module
from asi_forecast.helpers import load_config
from asi_forecast.monte_carlo import simulate_forecast


def test_module_level_magic_constants_removed():
    for name in (
        "LONG_HORIZON_AGENT_THRESHOLD_HOURS",
        "BASE_EFFECTIVE_COMPUTE_X_PER_YEAR",
        "BASE_ALGORITHMIC_EFFICIENCY_X_PER_YEAR",
        "COMPUTE_PROGRESS_DAMPENING_EXPONENT",
    ):
        assert not hasattr(model_module, name), f"{name} still hardcoded in model.py"

    for name in ("BIO_ANCHOR_MEDIAN_YEAR", "LAG_LATE_TAIL_MEDIAN_MONTHS"):
        assert not hasattr(monte_carlo_module, name), f"{name} still hardcoded in monte_carlo.py"

    assert not hasattr(uncertainty_module, "LONG_TAIL_SIGMA"), "LONG_TAIL_SIGMA still hardcoded"


@pytest.mark.parametrize(
    "section",
    ["structural_adjustments", "baseline_progress_rates", "long_tail_calibration"],
)
def test_no_silent_fallback_when_section_missing(section):
    cfg = load_config()
    broken = copy.deepcopy(cfg)
    del broken[section]
    with pytest.raises(KeyError):
        simulate_forecast(broken, sims=16, seed=1)
