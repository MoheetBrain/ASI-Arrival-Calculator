"""Uncertainty samplers used by ASI Arrival Forecast.

v0.5 calibration adds three distribution families beyond triangular so the model
can ingest the empirically recalibrated inputs (ANSWERS.txt / asi.txt):

- ``lognormal`` and ``gamma`` are location-SHIFTED to ``low`` and fitted by
  method-of-moments from ``mean`` + ``std`` (falling back to triangular-derived
  moments), then clipped to ``[low, high]`` as explicit audited bounds. Shifting
  avoids a probability pile-up at the low bound.
- ``beta`` is fitted on the support ``[low, high]`` by method-of-moments.

Every family therefore respects the audited ``low``/``high`` bounds, which keeps
the downstream timeline-ordering invariant intact (all lags stay >= 0).
"""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np


SUPPORTED_DISTRIBUTIONS = ("triangular", "lognormal", "gamma", "beta")


def _validate_bounds(low: float, mode: float, high: float, name: str) -> None:
    if low > mode or mode > high:
        raise ValueError(
            f"{name} must satisfy low <= mode <= high; got {low}, {mode}, {high}"
        )


def _triangular_moments(low: float, mode: float, high: float) -> tuple[float, float]:
    """Analytic mean and std of a triangular distribution (moment fallback)."""
    mean = (low + mode + high) / 3.0
    variance = (
        low * low + mode * mode + high * high
        - low * mode - low * high - mode * high
    ) / 18.0
    return mean, math.sqrt(max(variance, 0.0))


def _resolve_moments(spec: Mapping[str, float], low: float, mode: float, high: float) -> tuple[float, float]:
    mean = spec.get("mean")
    std = spec.get("std")
    if mean is None or std is None:
        return _triangular_moments(low, mode, high)
    return float(mean), float(std)


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
    _validate_bounds(low, mode, high, name)
    if low == high:
        return np.full(size, low, dtype=float)

    return rng.triangular(left=low, mode=mode, right=high, size=size)


def _clip_to_bounds(samples: np.ndarray, bounds: tuple[float, float]) -> np.ndarray:
    """Clip sampled values to explicit audited bounds."""
    return np.clip(samples, bounds[0], bounds[1])


def _lognormal_sample(rng, low, high, mean, std, size, name):
    shifted_mean = mean - low
    if shifted_mean <= 0:
        raise ValueError(f"{name}: lognormal requires mean > low")
    sigma_sq = math.log(1.0 + (std / shifted_mean) ** 2)
    mu = math.log(shifted_mean) - sigma_sq / 2.0
    draws = low + rng.lognormal(mean=mu, sigma=math.sqrt(sigma_sq), size=size)
    return _clip_to_bounds(draws, (low, high))


def _gamma_sample(rng, low, high, mean, std, size, name):
    shifted_mean = mean - low
    if shifted_mean <= 0 or std <= 0:
        raise ValueError(f"{name}: gamma requires mean > low and std > 0")
    shape = (shifted_mean / std) ** 2
    scale = std * std / shifted_mean
    draws = low + rng.gamma(shape=shape, scale=scale, size=size)
    return _clip_to_bounds(draws, (low, high))


def _beta_sample(rng, low, high, mean, std, size, name):
    span = high - low
    if span <= 0:
        raise ValueError(f"{name}: beta requires high > low")
    m = (mean - low) / span
    v = (std / span) ** 2
    if not (0.0 < m < 1.0) or v <= 0 or v >= m * (1.0 - m):
        raise ValueError(
            f"{name}: beta moments infeasible (m={m:.3f}, v={v:.4f}); "
            "need 0<m<1 and var < m(1-m)"
        )
    common = m * (1.0 - m) / v - 1.0
    alpha = m * common
    beta = (1.0 - m) * common
    return low + span * rng.beta(alpha, beta, size=size)


def sample_distribution(
    rng: np.random.Generator,
    spec: Mapping[str, float | str],
    size: int,
    name: str = "parameter",
) -> np.ndarray:
    """Sample one validated forecast input, dispatching on ``distribution``.

    Defaults to triangular when ``distribution`` is absent (e.g. governance
    vectors that were not recalibrated to a new family).
    """
    distribution = spec.get("distribution", "triangular")
    if distribution not in SUPPORTED_DISTRIBUTIONS:
        raise ValueError(f"{name} uses unsupported distribution: {distribution}")

    low = float(spec["low"])
    mode = float(spec["mode"])
    high = float(spec["high"])
    _validate_bounds(low, mode, high, name)

    if distribution == "triangular":
        return triangular_sample(rng, spec, size=size, name=name)

    mean, std = _resolve_moments(spec, low, mode, high)
    if distribution == "lognormal":
        return _lognormal_sample(rng, low, high, mean, std, size, name)
    if distribution == "gamma":
        return _gamma_sample(rng, low, high, mean, std, size, name)
    return _beta_sample(rng, low, high, mean, std, size, name)


def sample_parameter(
    rng: np.random.Generator,
    spec: Mapping[str, float | str | list],
    size: int,
    name: str = "parameter",
) -> np.ndarray:
    """Sample one validated forecast input distribution (any supported family)."""
    return sample_distribution(rng, spec, size=size, name=name)


def apply_long_tail_mixture(
    base_values_months: np.ndarray,
    rng: np.random.Generator,
    late_tail_weight: float,
    floor_offset_months: float,
    median_offset_months: float,
    sigma: float,
) -> np.ndarray:
    """Route ``late_tail_weight`` of samples into a shifted lognormal late tail.

    With probability ``late_tail_weight`` a sample is redrawn from
    ``floor_offset_months + Lognormal(median, sigma)``. The redrawn value only ever
    pushes a sample *later* (``maximum`` with the base draw), which models
    systemic-bottleneck stalls and guarantees the downstream timeline ordering
    (public >= internal >= AGI) is preserved. ``sigma`` is supplied by the caller
    from YAML (``long_tail_calibration.sigma``); there is no hidden default.

    CALIBRATION WARNING: The long-tail mixture is designed to prevent a hard upper
    wall. It may shift the median slightly because late-tail samples are applied
    with a max() operation. This is intentional but is treated as a calibration
    risk until externally validated. (asi.txt Q13 proposes replacing this mixture
    with a direct lognormal on the base AGI metric; deferred because it would
    abandon the structural-gate AGI and threatens the timeline-ordering invariant.)

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
