"""Today's AI-R&D automation fraction A_R&D(2026-10), by component.

A_supervised = sum_i w_i * a_i         (AI does the work with light steering)
A_autonomous = A_supervised * d        (d = autonomy discount)
Amdahl labour speed-up if automated work were free: 1 / (1 - A_supervised)

Components are NOT equally automatable; each a_i is sampled from its own
triangular (low, mode, high) and d from the autonomy-discount spec.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .sampling import inverse_cdf


def simulate_rnd_automation(config: dict, sims: int = 20000, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    block = config["rnd_automation_today"]
    supervised = np.zeros(sims)
    for _, row in block["components"].items():
        weight, low, mode, high = (float(v) for v in row)
        draws = inverse_cdf(
            {"dist": "triangular", "low": low, "mode": mode, "high": high},
            rng.random(sims),
        )
        supervised += weight * draws
    discount = inverse_cdf(block["autonomy_discount"], rng.random(sims))
    autonomous = supervised * discount
    return pd.DataFrame(
        {
            "a_rnd_supervised": supervised,
            "a_rnd_autonomous": autonomous,
            "amdahl_labour_speedup": 1.0 / (1.0 - supervised),
        }
    )


def rnd_automation_summary(config: dict) -> pd.DataFrame:
    sims = simulate_rnd_automation(config)
    rows = []
    for column in sims.columns:
        values = sims[column].to_numpy()
        rows.append(
            {
                "quantity": column,
                "p05": float(np.percentile(values, 5)),
                "p50": float(np.percentile(values, 50)),
                "p95": float(np.percentile(values, 95)),
            }
        )
    components = []
    for name, row in config["rnd_automation_today"]["components"].items():
        weight, low, mode, high = (float(v) for v in row)
        components.append(
            {
                "quantity": f"component:{name}",
                "p05": low,
                "p50": mode,
                "p95": high,
                "weight": weight,
            }
        )
    return pd.concat([pd.DataFrame(rows), pd.DataFrame(components)], ignore_index=True)
