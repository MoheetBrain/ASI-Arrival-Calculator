"""Uncertainty samplers used by ASI Arrival Forecast."""

from __future__ import annotations

from typing import Mapping

import numpy as np


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
