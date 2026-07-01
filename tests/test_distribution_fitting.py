"""The non-triangular samplers must reproduce their target moments and bounds."""

import numpy as np
import pytest

from asi_forecast.uncertainty import sample_distribution


def _spec(distribution, low, mode, high, mean=None, std=None):
    spec = {"distribution": distribution, "low": low, "mode": mode, "high": high}
    if mean is not None:
        spec["mean"] = mean
    if std is not None:
        spec["std"] = std
    return spec


@pytest.mark.parametrize(
    "distribution, low, mode, high, mean, std",
    [
        ("lognormal", 12.0, 24.0, 60.0, 28.0, 12.0),   # infra friction (Q12)
        ("lognormal", 3.0, 3.8, 4.5, 3.77, 0.39),      # compute (Q2)
        ("gamma", 1.0, 3.0, 12.0, 4.1, 2.8),           # superhuman lag (Q9)
        ("gamma", 3.0, 9.0, 24.0, 11.0, 6.0),          # secrecy (Q14)
    ],
)
def test_moment_fit_is_close(distribution, low, mode, high, mean, std):
    rng = np.random.default_rng(0)
    draws = sample_distribution(
        rng, _spec(distribution, low, mode, high, mean, std), size=200_000
    )
    # Clipping to [low, high] pulls the moments slightly; allow a tolerance band.
    assert abs(draws.mean() - mean) < 0.15 * mean
    assert draws.min() >= low
    assert draws.max() <= high


def test_beta_respects_support_and_shape():
    rng = np.random.default_rng(1)
    draws = sample_distribution(
        rng, _spec("beta", 0.30, 0.65, 0.85, 0.61, 0.15), size=200_000
    )
    assert draws.min() >= 0.30
    assert draws.max() <= 0.85
    assert abs(draws.mean() - 0.61) < 0.03


def test_triangular_fallback_without_moments():
    rng = np.random.default_rng(2)
    draws = sample_distribution(rng, _spec("gamma", 1.0, 4.0, 12.0), size=50_000)
    # No mean/std supplied -> triangular-derived moments; still bounded.
    assert draws.min() >= 1.0
    assert draws.max() <= 12.0


def test_infeasible_beta_moments_raise():
    rng = np.random.default_rng(3)
    with pytest.raises(ValueError):
        # variance too large for the support -> infeasible beta.
        sample_distribution(
            rng, _spec("beta", 0.0, 0.5, 1.0, 0.5, 0.9), size=100
        )


def test_unsupported_distribution_raises():
    rng = np.random.default_rng(4)
    with pytest.raises(ValueError):
        sample_distribution(rng, _spec("cauchy", 1.0, 2.0, 3.0), size=10)
