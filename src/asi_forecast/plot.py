"""Compatibility plotting module.

The project keeps Matplotlib as the guaranteed backend. If seaborn is
available, charts.py applies its style; otherwise plots still render.
"""

from .charts import plot_arrival_distribution, plot_lag_distribution, plot_sensitivity

__all__ = ["plot_arrival_distribution", "plot_lag_distribution", "plot_sensitivity"]
