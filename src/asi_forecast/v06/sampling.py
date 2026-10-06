"""Inverse-CDF samplers with a shared latent factor (Gaussian copula).

Every v0.6 parameter is drawn as ``x = F^{-1}(u)`` where
``u = Phi(loading * Z + sqrt(1 - loading^2) * eps)``. ``Z`` is one latent
"progress-speed" factor per simulated world. This is how correlated evidence is
handled: reasoning, coding, task-horizon, compute and AI-R&D signals share a
common cause, so their parameters co-move instead of being treated as
independent likelihood multipliers.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.special import expit, logit
from scipy.stats import norm


Z95 = 1.6448536269514722


def correlated_uniform(
    rng: np.random.Generator, latent: np.ndarray, loading: float
) -> np.ndarray:
    """Uniforms whose normal scores load ``loading`` on the latent factor."""
    loading = float(loading)
    eps = rng.standard_normal(latent.shape[0])
    score = loading * latent + math.sqrt(max(1.0 - loading * loading, 0.0)) * eps
    return np.clip(norm.cdf(score), 1e-12, 1.0 - 1e-12)


def inverse_cdf(spec: dict, u: np.ndarray) -> np.ndarray:
    """Map uniforms to parameter values for one distribution spec."""
    dist = spec["dist"]
    if dist == "fixed":
        values = np.full(u.shape[0], float(spec["value"]))
    elif dist == "uniform":
        low, high = float(spec["low"]), float(spec["high"])
        values = low + (high - low) * u
    elif dist == "triangular":
        low, mode, high = float(spec["low"]), float(spec["mode"]), float(spec["high"])
        if high == low:
            values = np.full(u.shape[0], low)
        else:
            cut = (mode - low) / (high - low)
            left = low + np.sqrt(u * (high - low) * (mode - low))
            right = high - np.sqrt((1.0 - u) * (high - low) * (high - mode))
            values = np.where(u < cut, left, right)
    elif dist == "lognormal":
        median, p95 = float(spec["median"]), float(spec["p95"])
        sigma = math.log(p95 / median) / Z95
        values = median * np.exp(sigma * norm.ppf(u))
    elif dist == "logitnormal":
        median, p95 = float(spec["median"]), float(spec["p95"])
        sigma = (logit(p95) - logit(median)) / Z95
        values = expit(logit(median) + sigma * norm.ppf(u))
    else:  # pragma: no cover - guarded by config validation
        raise ValueError(f"unsupported dist {dist!r}")
    clip = spec.get("clip")
    if clip is not None:
        values = np.clip(values, float(clip[0]), float(clip[1]))
    return values


def sample(
    spec: dict,
    rng: np.random.Generator,
    latent: np.ndarray,
    loading: float | None = None,
) -> np.ndarray:
    """Sample one parameter, using its own latent_loading unless overridden."""
    if loading is None:
        loading = float(spec.get("latent_loading", 0.0))
    if spec["dist"] == "fixed":
        return np.full(latent.shape[0], float(spec["value"]))
    return inverse_cdf(spec, correlated_uniform(rng, latent, loading))


def spec_median(spec: dict) -> float:
    """Deterministic median of a spec (used by ablations)."""
    return float(inverse_cdf(spec, np.array([0.5]))[0])
