import numpy as np
import pytest

from asi_forecast.uncertainty import triangular_sample


def test_triangular_sampler_returns_requested_length():
    rng = np.random.default_rng(123)
    samples = triangular_sample(
        rng,
        {"low": 1, "mode": 2, "high": 5},
        size=250,
        name="test_distribution",
    )

    assert len(samples) == 250
    assert samples.min() >= 1
    assert samples.max() <= 5


def test_triangular_sampler_rejects_invalid_order():
    rng = np.random.default_rng(123)

    with pytest.raises(ValueError):
        triangular_sample(
            rng,
            {"low": 5, "mode": 2, "high": 1},
            size=10,
            name="bad_distribution",
        )
