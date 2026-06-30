"""Uncertainty samplers used by ASI Arrival Forecast."""

from __future__ import annotations

from typing import Mapping

import numpy as np


# ANSWERS.txt "Long-Tail Problem": Biological Anchors fit gives sigma ~= 0.8332
# for the lognormal late tail (10th pct at t=11y, median at t=32y from 2020).
LONG_TAIL_SIGMA = 0.8332


def triangular_sample(
    rng: np.random.Generator,
    params: Mapping[str, float],
    size: int,
    name: str = "distribution",
) -> np.ndarray:
    """Sample from a triangular distribution.

    A triangular distribution is easy to audit: a low bound, a most likely
    value, and a high bound. It is not a claim that reality is triangular.
    """
    low = float(params["low"])
    mode = float(params["mode"])
    high = float(params["high"])

    if size < 0:
        raise ValueError("size must be non-negative")
    if low > mode or mode > high:
        raise ValueError(
            f"{name} must satisfy low <= mode <= high; got {low}, {mode}, {high}"
        )
    if low == high:
        return np.full(size, low, dtype=float)

    return rng.triangular(left=low, mode=mode, right=high, size=size)


def _clip_to_bounds(samples: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    """Clip sampled values to explicit audited bounds."""
    return np.clip(samples, bounds[0], bounds[1])


def sample_parameter(
    rng: np.random.Generator,
    spec: Mapping[str, float | str | list],
    size: int,
    name: str = "parameter",
) -> np.ndarray:
    """Sample one validated triangular forecast input distribution."""
    if spec.get("distribution") != "triangular":
        raise ValueError(f"{name} uses unsupported distribution: {spec.get('distribution')}")
    return triangular_sample(rng, spec, size=size, name=name)


def apply_long_tail_mixture(
    base_values_months: np.ndarray,
    rng: np.random.Generator,
    late_tail_weight: float,
    floor_offset_months: float,
    median_offset_months: float,
    sigma: float = LONG_TAIL_SIGMA,
) -> np.ndarray:
    """Route ``late_tail_weight`` of samples into a shifted lognormal late tail.

    Implements the mixture from ANSWERS.txt: with probability ``late_tail_weight``
    a sample is redrawn from ``floor_offset_months + Lognormal(median, sigma)``.
    The redrawn value only ever pushes a sample *later* (``maximum`` with the base
    draw), which both models systemic-bottleneck stalls and guarantees the
    downstream timeline ordering (public >= internal >= AGI) is preserved.

    All quantities are in months. For a date the ``floor_offset_months`` is the
    offset of ``late_tail_start_year`` from the simulation start; for a duration
    (the AGI-to-ASI lag) the floor is 0.
    """
    values = np.asarray(base_values_months, dtype=float).copy()
    if late_tail_weight <= 0.0:
        return values

    size = values.shape[0]
    late_mask = rng.random(size) < late_tail_weight
    if not late_mask.any():
        return values

    lognormal_draw = rng.lognormal(
        mean=np.log(median_offset_months),
        sigma=sigma,
        size=size,
    )
    late_values = floor_offset_months + lognormal_draw
    values[late_mask] = np.maximum(values[late_mask], late_values[late_mask])
    return values
