"""Summary statistics for v0.6 simulations (quantiles, lags, by-year CDFs)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..helpers import index_to_month, month_to_index

PERCENTILES = [5, 10, 25, 50, 75, 90, 95]
YEARS = [2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2040, 2045, 2050]
LAG_THRESHOLDS_MONTHS = [3, 6, 12, 24, 60, 120]
TARGETS = [
    ("agi", "agi_month_index", "agi_months"),
    ("internal_asi", "internal_asi_month_index", "internal_asi_months"),
    ("public_asi", "public_asi_month_index", "public_asi_months"),
]


def month_quantile(indices: np.ndarray, q: float) -> str:
    """Quantile of an integer month index, reported as the month it falls in."""
    return index_to_month(int(np.ceil(np.percentile(indices, q) - 1e-9)))


def arrival_quantiles(frame: pd.DataFrame, horizon_month: str | None = None) -> pd.DataFrame:
    rows = []
    horizon_idx = month_to_index(horizon_month) if horizon_month else None
    for name, idx_col, _ in TARGETS:
        values = frame[idx_col].to_numpy()
        row = {"target": name}
        for q in PERCENTILES:
            label = month_quantile(values, q)
            if horizon_idx is not None and month_to_index(label) >= horizon_idx:
                label = f">={horizon_month}"
            row[f"p{q:02d}"] = label
        row["central_80"] = f"{row['p10']} -> {row['p90']}"
        rows.append(row)
    return pd.DataFrame(rows)


def lag_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    """AGI -> internal ASI lag, conditional on AGI being reached (pre-horizon)."""
    reached = ~frame["agi_censored"].to_numpy()
    lag = frame.loc[reached, "agi_to_asi_lag_months"].to_numpy()
    rows = [
        ("conditioning", "AGI reached before simulation horizon"),
        ("n_conditioned", int(reached.sum())),
        ("mean_lag_months", float(lag.mean())),
        ("median_lag_months", float(np.median(lag))),
    ]
    for q in PERCENTILES:
        rows.append((f"p{q:02d}_lag_months", float(np.percentile(lag, q))))
    for t in LAG_THRESHOLDS_MONTHS:
        rows.append((f"P(lag < {t} months)", float(np.mean(lag < t))))
    rows.append(("P(lag > 120 months)", float(np.mean(lag > 120))))
    return pd.DataFrame(rows, columns=["metric", "value"])


def by_year_probabilities(frame: pd.DataFrame, years: list[int] | None = None) -> pd.DataFrame:
    years = years or YEARS
    rows = []
    for year in years:
        cutoff = month_to_index(f"{year:04d}-12")
        row = {"year": year}
        for name, idx_col, _ in TARGETS:
            row[f"P({name} by end of year)"] = float(np.mean(frame[idx_col].to_numpy() <= cutoff))
        rows.append(row)
    return pd.DataFrame(rows)


def regime_table(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for regime, group in frame.groupby("regime", sort=False):
        lag = group["agi_to_asi_lag_months"].to_numpy()
        rows.append(
            {
                "regime": regime,
                "share": len(group) / len(frame),
                "lag_p10": float(np.percentile(lag, 10)),
                "lag_p50": float(np.median(lag)),
                "lag_p90": float(np.percentile(lag, 90)),
                "P(lag<12m)": float(np.mean(lag < 12)),
                "loop_gain_median": float(group["loop_gain_log10_per_oom"].median()),
                "research_speedup_at_asi_median": float(group["research_speedup_at_asi"].median()),
                "share_superlinear": float(np.mean(group["dynamics_class"] == "SUPERLINEAR")),
                "share_subcritical": float(np.mean(group["dynamics_class"] == "SUBCRITICAL")),
            }
        )
    order = {"bottlenecked": 0, "moderate": 1, "fast": 2, "recursive": 3}
    return pd.DataFrame(rows).sort_values("regime", key=lambda s: s.map(order)).reset_index(drop=True)


def dynamics_table(frame: pd.DataFrame) -> pd.DataFrame:
    counts = frame["dynamics_class"].value_counts(normalize=True)
    return counts.rename_axis("dynamics_class").reset_index(name="share")


def headline(frame: pd.DataFrame, config: dict) -> dict:
    """Numbers used by the dashboard."""
    horizon = config["simulation"]["horizon_month"]
    q = arrival_quantiles(frame, horizon).set_index("target")
    lags = lag_statistics(frame).set_index("metric")["value"]
    years = by_year_probabilities(frame, [2026, 2028, 2030, 2032, 2035]).set_index("year")
    start_idx = month_to_index(config["simulation"]["start_month"])
    return {
        "p_agi_already": float(np.mean(frame["agi_month_index"].to_numpy() <= start_idx)),
        "agi_median": q.loc["agi", "p50"],
        "agi_80": (q.loc["agi", "p10"], q.loc["agi", "p90"]),
        "internal_median": q.loc["internal_asi", "p50"],
        "internal_80": (q.loc["internal_asi", "p10"], q.loc["internal_asi", "p90"]),
        "public_median": q.loc["public_asi", "p50"],
        "public_80": (q.loc["public_asi", "p10"], q.loc["public_asi", "p90"]),
        "median_lag_months": float(lags["median_lag_months"]),
        "p_lag_lt_12": float(lags["P(lag < 12 months)"]),
        "p_lag_lt_24": float(lags["P(lag < 24 months)"]),
        "p_internal_by": {y: float(years.loc[y, "P(internal_asi by end of year)"]) for y in (2028, 2030, 2032, 2035)},
    }


def convergence_check(frame: pd.DataFrame, batches: int = 10) -> pd.DataFrame:
    rows = []
    for name, idx_col, _ in TARGETS:
        chunks = np.array_split(frame[idx_col].to_numpy(), batches)
        medians = [float(np.median(c)) for c in chunks]
        p90s = [float(np.percentile(c, 90)) for c in chunks]
        rows.append(
            {
                "target": name,
                "batches": batches,
                "median_range_months": max(medians) - min(medians),
                "p90_range_months": max(p90s) - min(p90s),
            }
        )
    lag = np.array_split(frame["agi_to_asi_lag_months"].to_numpy(), batches)
    lag_medians = [float(np.median(c)) for c in lag]
    rows.append(
        {
            "target": "agi_to_asi_lag",
            "batches": batches,
            "median_range_months": max(lag_medians) - min(lag_medians),
            "p90_range_months": float(np.ptp([np.percentile(c, 90) for c in lag])),
        }
    )
    return pd.DataFrame(rows)
