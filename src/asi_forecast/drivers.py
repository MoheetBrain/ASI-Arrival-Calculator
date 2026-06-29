"""Forecast driver analysis for the AGI-to-ASI pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from .forecast_model import SAMPLED_INPUT_COLUMNS


def _interpret_correlation(correlation: float, variable: str, target_name: str) -> str:
    """Return a plain-English driver interpretation."""
    if np.isnan(correlation):
        return "No variation in this input for this run."
    direction = "later" if correlation > 0 else "earlier"
    return f"Higher `{variable}` is associated with {direction} {target_name} in this simulation."


def spearman_sensitivity(
    simulations: pd.DataFrame,
    target_col: str,
    target_name: str,
) -> pd.DataFrame:
    """Compute Spearman rank correlations for sampled inputs."""
    rows: list[dict[str, float | int | str]] = []
    target = simulations[target_col].to_numpy()

    for column in SAMPLED_INPUT_COLUMNS:
        if column not in simulations.columns:
            continue
        values = simulations[column].to_numpy()
        if np.nanstd(values) == 0:
            correlation = np.nan
        else:
            correlation = float(spearmanr(values, target, nan_policy="omit").statistic)
        rows.append(
            {
                "target": target_name,
                "input_variable": column,
                "spearman_correlation": correlation,
                "abs_correlation": abs(correlation) if not np.isnan(correlation) else np.nan,
                "interpretation": _interpret_correlation(correlation, column, target_name),
            }
        )

    result_frame = pd.DataFrame(rows).sort_values(
        "abs_correlation",
        ascending=False,
        na_position="last",
    )
    result_frame["absolute_rank"] = range(1, len(result_frame) + 1)
    return result_frame[
        [
            "target",
            "input_variable",
            "spearman_correlation",
            "absolute_rank",
            "interpretation",
        ]
    ].reset_index(drop=True)


def combined_sensitivity(simulations: pd.DataFrame) -> pd.DataFrame:
    """Return driver tables for AGI, internal ASI, public ASI, and lag."""
    targets = [
        ("agi", "agi_month_index"),
        ("internal_asi", "internal_asi_month_index"),
        ("public_asi", "public_asi_month_index"),
        ("agi_to_asi_lag", "agi_to_asi_lag_months"),
    ]
    return pd.concat(
        [
            spearman_sensitivity(simulations, target_col=column, target_name=name)
            for name, column in targets
        ],
        ignore_index=True,
    )
