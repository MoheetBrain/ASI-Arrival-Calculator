"""Phase overlap must compress only the cognitive lag, not physical buildout.

Deterministic worked example from the v0.4.0 spec:
    AGI = 100, AI R&D = 10, SAR = 10, takeoff = 10, infrastructure = 20, overlap = 0.5
    expected internal ASI = 100 + ((10+10+10) * 0.5) + 20 = 135   (NOT 125)
"""

import numpy as np

from asi_forecast.model import (
    effective_research_takeoff_lag_months,
    internal_asi_arrival_months,
    raw_research_takeoff_lag_months,
)


def test_infrastructure_friction_is_not_compressed():
    agi = np.array([100.0])
    ai_rnd = np.array([10.0])
    sar = np.array([10.0])
    takeoff = np.array([10.0])
    infrastructure = np.array([20.0])
    overlap = np.array([0.5])

    raw = raw_research_takeoff_lag_months(ai_rnd, sar, takeoff)
    effective = effective_research_takeoff_lag_months(raw, overlap)
    internal = internal_asi_arrival_months(agi, effective, infrastructure)

    assert raw[0] == 30.0
    assert effective[0] == 15.0
    assert internal[0] == 135.0, "infrastructure friction was wrongly compressed"
    assert internal[0] != 125.0
