"""Iman-Conover rank-correlation induction.

ANSWERS.txt "Variable-Correlation Problem": sampling inherently correlated
macro drivers independently pairs impossible worlds (e.g. explosive compute with
stagnant algorithms). The Iman-Conover method reorders already-sampled marginals
to match a target Spearman rank-correlation matrix *without* distorting those
marginals (each column keeps its exact triangular shape).

This module also provides the simpler v0.2 scenario-scalar fallback described in
the report, for environments where the full method is undesirable.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def build_correlation_matrix(
    columns: list[str],
    correlation_spec: dict[str, dict[str, float]] | None,
) -> np.ndarray:
    """Assemble a symmetric correlation matrix for ``columns`` from a sparse spec.

    The spec only needs the upper triangle (``a: {b: rho}``); the lower triangle
    and unit diagonal are filled automatically.
    """
    size = len(columns)
    matrix = np.eye(size)
    if not correlation_spec:
        return matrix

    index = {name: position for position, name in enumerate(columns)}
    for source, targets in correlation_spec.items():
        if source not in index:
            continue
        for target, value in targets.items():
            if target not in index:
                continue
            i, j = index[source], index[target]
            matrix[i, j] = matrix[j, i] = float(value)
    return matrix


def _nearest_positive_definite(matrix: np.ndarray, epsilon: float = 1e-10) -> np.ndarray:
    """Clip eigenvalues so a (possibly indefinite) correlation matrix is PD."""
    symmetric = (matrix + matrix.T) / 2.0
    eigenvalues, eigenvectors = np.linalg.eigh(symmetric)
    eigenvalues = np.clip(eigenvalues, epsilon, None)
    rebuilt = eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T
    # Renormalise to a correlation matrix (unit diagonal).
    diagonal = np.sqrt(np.diag(rebuilt))
    rebuilt = rebuilt / np.outer(diagonal, diagonal)
    return (rebuilt + rebuilt.T) / 2.0


def induce_rank_correlation(
    samples: np.ndarray,
    target_correlation: np.ndarray,
    rng: np.random.Generator,
) -> np.ndarray:
    """Reorder ``samples`` columns to match ``target_correlation`` (Spearman).

    Parameters
    ----------
    samples:
        Array of shape ``(n, k)`` whose columns are independent marginal draws.
    target_correlation:
        ``(k, k)`` symmetric target rank-correlation matrix.

    Returns
    -------
    np.ndarray
        A copy of ``samples`` with rows permuted per column so that the induced
        rank correlation approximates the target. Marginal values are preserved.
    """
    n, k = samples.shape
    if k == 1 or n < 2:
        return samples.copy()

    # 1. Van der Waerden scores, one independently-permuted column per variable.
    van_der_waerden = norm.ppf(np.arange(1, n + 1) / (n + 1))
    score_matrix = np.empty((n, k))
    for column in range(k):
        score_matrix[:, column] = rng.permutation(van_der_waerden)

    # 2. Remove the incidental correlation in the score matrix.
    score_correlation = np.corrcoef(score_matrix, rowvar=False)
    try:
        score_cholesky = np.linalg.cholesky(score_correlation)
    except np.linalg.LinAlgError:
        score_cholesky = np.linalg.cholesky(_nearest_positive_definite(score_correlation))

    # 3. Impose the target correlation in normal-score space.
    try:
        target_cholesky = np.linalg.cholesky(target_correlation)
    except np.linalg.LinAlgError:
        target_cholesky = np.linalg.cholesky(_nearest_positive_definite(target_correlation))

    correlated_scores = score_matrix @ np.linalg.inv(score_cholesky).T @ target_cholesky.T

    # 4. Reorder each marginal to follow the rank pattern of the correlated scores.
    correlated = np.empty_like(samples)
    for column in range(k):
        target_ranks = np.argsort(np.argsort(correlated_scores[:, column]))
        sorted_marginal = np.sort(samples[:, column])
        correlated[:, column] = sorted_marginal[target_ranks]
    return correlated


def scenario_scalar_shift(
    rng: np.random.Generator,
    sims: int,
    strength: float = 1.0,
) -> np.ndarray:
    """v0.2 fallback: a shared macro investment factor in [0, 1].

    Callers can use this single shared factor to nudge the modes of correlated
    inputs in the same direction, a coarse stand-in for the full method.
    """
    factor = rng.uniform(0.0, 1.0, size=sims)
    return 0.5 + strength * (factor - 0.5)
