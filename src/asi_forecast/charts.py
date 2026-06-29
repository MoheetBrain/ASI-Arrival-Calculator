"""Matplotlib charts for AGI and ASI Arrival Forecast results."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_CACHE_ROOT = Path(tempfile.gettempdir()) / "asi-forecast-mpl-cache"
(_CACHE_ROOT / "matplotlib").mkdir(parents=True, exist_ok=True)
(_CACHE_ROOT / "xdg").mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("XDG_CACHE_HOME", str(_CACHE_ROOT / "xdg"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .helpers import index_to_month

try:
    import seaborn as sns

    sns.set_theme(style="whitegrid")
except Exception:
    sns = None


def plot_arrival_distribution(simulations: pd.DataFrame, output_path: str | Path) -> Path:
    """Plot AGI, internal ASI, and public ASI arrival month distributions."""
    path = Path(output_path)
    agi = simulations["agi_month_index"]
    internal = simulations["internal_asi_month_index"]
    public = simulations["public_asi_month_index"]
    minimum = int(min(agi.min(), internal.min(), public.min()))
    maximum = int(max(agi.max(), internal.max(), public.max()))
    bins = range(minimum, maximum + 2)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.hist(agi, bins=bins, alpha=0.58, label="AGI")
    ax.hist(internal, bins=bins, alpha=0.52, label="Internal ASI")
    ax.hist(public, bins=bins, alpha=0.46, label="Public ASI")
    ax.set_title("AGI and ASI arrival month distribution")
    ax.set_xlabel("Calendar month")
    ax.set_ylabel("Simulated futures")
    ax.legend()

    tick_step = max(6, (maximum - minimum) // 10)
    ticks = list(range(minimum, maximum + 1, tick_step))
    ax.set_xticks(ticks)
    ax.set_xticklabels([index_to_month(tick) for tick in ticks], rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_lag_distribution(simulations: pd.DataFrame, output_path: str | Path) -> Path:
    """Plot the AGI-to-internal-ASI lag distribution."""
    path = Path(output_path)
    lag_months = simulations["agi_to_asi_lag_months"]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.hist(lag_months, bins=40, alpha=0.75)
    ax.set_title("AGI-to-internal-ASI lag distribution")
    ax.set_xlabel("Lag after AGI, in months")
    ax.set_ylabel("Simulated futures")
    secondary = ax.secondary_xaxis(
        "top",
        functions=(lambda months: months / 12.0, lambda years: years * 12.0),
    )
    secondary.set_xlabel("Lag after AGI, in years")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path


def plot_sensitivity(sensitivity: pd.DataFrame, output_path: str | Path) -> Path:
    """Plot top internal ASI driver correlations."""
    path = Path(output_path)
    top = (
        sensitivity[sensitivity["target"] == "internal_asi"]
        .sort_values("absolute_rank", ascending=True)
        .head(10)
        .copy()
    )
    top = top.sort_values("spearman_correlation")

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.barh(top["input_variable"], top["spearman_correlation"])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("Internal ASI sensitivity")
    ax.set_xlabel("Spearman rank correlation with arrival month")
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return path
