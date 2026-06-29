"""Analysis utilities for forecast outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .helpers import index_to_month


PERCENTILES = [5, 10, 25, 50, 75, 90, 95]


def percentile_month(values: np.ndarray, percentile: int) -> tuple[int, str]:
    """Return rounded month index and display label for a percentile."""
    month_index = int(round(float(np.percentile(values, percentile))))
    return month_index, index_to_month(month_index)


def summarize_arrivals(simulations: pd.DataFrame) -> pd.DataFrame:
    """Build a compact summary table for AGI, internal ASI, and public ASI."""
    rows = []
    targets = [
        ("agi", "agi_month_index"),
        ("internal_asi", "internal_asi_month_index"),
        ("public_asi", "public_asi_month_index"),
    ]

    for target_name, column in targets:
        values = simulations[column].to_numpy()
        row: dict[str, str | int] = {"target": target_name}
        for percentile in PERCENTILES:
            month_index, month_label = percentile_month(values, percentile)
            key = f"p{percentile:02d}"
            row[f"{key}_index"] = month_index
            row[f"{key}_month"] = month_label
        row["median_month"] = row["p50_month"]
        row["interval_50"] = f"{row['p25_month']} to {row['p75_month']}"
        row["interval_90"] = f"{row['p05_month']} to {row['p95_month']}"
        rows.append(row)

    return pd.DataFrame(rows)


def summarize_stage_timeline(simulations: pd.DataFrame) -> pd.DataFrame:
    """Summarize median stage-gate completion months."""
    stage_columns = [
        ("coding_automation", "Strong coding automation"),
        ("long_horizon_agent", "Long-horizon agent reliability"),
        ("general_capability", "Broad general capability"),
        ("agi_arrival", "AGI"),
        ("internal_asi_arrival", "Internal ASI"),
        ("public_asi_arrival", "Public ASI"),
    ]
    rows = []
    for column_prefix, display_name in stage_columns:
        values = simulations[f"{column_prefix}_months"].to_numpy()
        if column_prefix == "agi_arrival":
            calendar_column = "agi_month"
        elif column_prefix == "internal_asi_arrival":
            calendar_column = "internal_asi_month"
        elif column_prefix == "public_asi_arrival":
            calendar_column = "public_asi_month"
        else:
            calendar_column = None
        rows.append(
            {
                "stage": column_prefix,
                "display_name": display_name,
                "median_month_offset": float(np.median(values)),
                "p25_month_offset": float(np.percentile(values, 25)),
                "p75_month_offset": float(np.percentile(values, 75)),
                "median_calendar_month": (
                    simulations[calendar_column].iloc[int(np.argsort(values)[len(values) // 2])]
                    if calendar_column
                    else index_to_month(
                        int(round(np.median(simulations["agi_month_index"] - simulations["agi_arrival_months"] + values)))
                    )
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_lag_metrics(simulations: pd.DataFrame) -> pd.DataFrame:
    """Summarize lag metrics that are not arrival-date targets."""
    metrics = [
        (
            "median_agi_to_internal_asi_lag_months",
            float(np.median(simulations["agi_to_asi_lag_months"])),
        ),
        (
            "median_agi_to_internal_asi_lag_years",
            float(np.median(simulations["agi_to_asi_lag_months"]) / 12.0),
        ),
        (
            "median_internal_to_public_delay_months",
            float(np.median(simulations["internal_to_public_delay_months"])),
        ),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value"])


def batch_means_convergence(
    simulations: pd.DataFrame,
    batches: int = 10,
    target_col: str = "internal_asi_month_index",
) -> pd.DataFrame:
    """Run batch-means convergence on median arrival month.

    A run is treated as converged when the inter-batch median range is below
    one month. This is a numerical-noise check, not a proof that assumptions
    are correct.
    """
    if batches < 2:
        raise ValueError("batches must be at least 2")

    chunks = np.array_split(simulations[target_col].to_numpy(), batches)
    medians = [float(np.median(chunk)) for chunk in chunks if len(chunk) > 0]
    overall = float(np.median(simulations[target_col].to_numpy()))
    median_range = max(medians) - min(medians)

    return pd.DataFrame(
        {
            "target": [target_col],
            "batches": [len(medians)],
            "overall_median_month": [index_to_month(int(round(overall)))],
            "batch_median_range_months": [median_range],
            "converged_under_one_month": [median_range < 1.0],
        }
    )


def optional_sobol_placeholder() -> pd.DataFrame:
    """Return Sobol integration status.

    SALib is intentionally optional because it is not always available in a
    minimal local environment. When installed, this module is where true Sobol
    analysis should be wired in against a Saltelli sample design. Spearman
    drivers remain the default no-extra-dependency sensitivity output.
    """
    try:
        import SALib  # noqa: F401
    except ModuleNotFoundError:
        return pd.DataFrame(
            [
                {
                    "method": "sobol_total_order",
                    "status": "not_run",
                    "reason": "SALib is not installed; Spearman drivers were generated instead.",
                }
            ]
        )
    return pd.DataFrame(
        [
            {
                "method": "sobol_total_order",
                "status": "available_not_run",
                "reason": "SALib is installed, but v0.3 keeps Sobol as an explicit future Saltelli-design step.",
            }
        ]
    )
