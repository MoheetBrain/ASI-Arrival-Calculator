"""Bayesian update of the takeoff-regime weights.

P(regime | E) ∝ P(regime) * prod_g exp( mean_{e in g} log LR_e(regime) )

Evidence items in the same correlation group are AVERAGED in log space (they
are treated as one observation of a shared latent fact), and groups are then
multiplied. This is the explicit anti-double-counting rule for correlated
signals such as "no slope change", "judgement lagging" and "bounded R&D tasks
improving fast", which all come from the same lab-internal measurements.
"""

from __future__ import annotations

import math
from collections import defaultdict

import pandas as pd


def regime_posterior(takeoff: dict) -> dict[str, float]:
    """Return posterior regime weights (or the scenario override when present)."""
    regimes = list(takeoff["regimes"])
    override = takeoff.get("regime_weights_override")
    if override:
        return {r: float(override[r]) for r in regimes}
    prior = {r: float(takeoff["regime_prior"]["weights"][r]) for r in regimes}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in takeoff.get("regime_evidence", []):
        grouped[item["correlation_group"]].append(item)
    log_post = {r: math.log(prior[r]) for r in regimes}
    for items in grouped.values():
        for r in regimes:
            log_post[r] += sum(math.log(float(i["likelihood"][r])) for i in items) / len(items)
    peak = max(log_post.values())
    unnorm = {r: math.exp(v - peak) for r, v in log_post.items()}
    total = sum(unnorm.values())
    return {r: unnorm[r] / total for r in regimes}


def regime_update_table(takeoff: dict) -> pd.DataFrame:
    """Audit table: prior, each group's averaged likelihood ratio, posterior."""
    regimes = list(takeoff["regimes"])
    prior = {r: float(takeoff["regime_prior"]["weights"][r]) for r in regimes}
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in takeoff.get("regime_evidence", []):
        grouped[item["correlation_group"]].append(item)
    rows = [{"step": "prior", **prior}]
    for group, items in grouped.items():
        row = {"step": f"group:{group} (n={len(items)}, averaged)"}
        for r in regimes:
            row[r] = math.exp(
                sum(math.log(float(i["likelihood"][r])) for i in items) / len(items)
            )
        rows.append(row)
    posterior = regime_posterior({**takeoff, "regime_weights_override": None})
    rows.append({"step": "posterior", **posterior})
    return pd.DataFrame(rows)
