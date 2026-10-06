"""Write v0.6 result files, charts and the Markdown report/dashboard."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from ..helpers import month_to_index  # noqa: E402
from . import metrics  # noqa: E402
from .backtest import attribution_table, backtest_table  # noqa: E402
from .config import apply_v06_scenario, scenario_names  # noqa: E402
from .engine import simulate_v06  # noqa: E402
from .regimes import regime_posterior, regime_update_table  # noqa: E402
from .rnd_automation import rnd_automation_summary  # noqa: E402
from .sensitivity import (  # noqa: E402
    ABLATIONS,
    ALTERNATE_PRIORS,
    factor_tornado,
    run_variants,
    spearman_drivers,
)

SCENARIO_LABELS = {
    "baseline": "A — evidence-weighted baseline (preferred: posterior regime mixture)",
    "agi_era_fast": "B — AGI-era / fast takeoff (conditional)",
    "bottlenecked": "C — bottlenecked (conditional)",
}


def _md(frame: pd.DataFrame, floatfmt: str = ".3f") -> str:
    return frame.to_markdown(index=False, floatfmt=floatfmt)


def _months_to_label(start_month: str, offset: float) -> str:
    from ..helpers import index_to_month

    return index_to_month(month_to_index(start_month) + int(np.ceil(offset - 1e-9)))


def run_scenario(base_config: dict, scenario: str, sims: int, seed: int) -> tuple[dict, pd.DataFrame]:
    config = apply_v06_scenario(base_config, scenario)
    return config, simulate_v06(config, sims, seed)


def write_run_outputs(frame: pd.DataFrame, config: dict, results_dir: Path, prefix: str = "") -> dict:
    """Standard per-run CSVs. Returns the summary tables."""
    results_dir.mkdir(parents=True, exist_ok=True)
    horizon = config["simulation"]["horizon_month"]
    tables = {
        "quantiles": metrics.arrival_quantiles(frame, horizon),
        "lag": metrics.lag_statistics(frame),
        "by_year": metrics.by_year_probabilities(frame),
        "regimes": metrics.regime_table(frame),
        "dynamics": metrics.dynamics_table(frame),
        "convergence": metrics.convergence_check(frame, int(config["simulation"]["convergence_batches"])),
    }
    for name, table in tables.items():
        table.to_csv(results_dir / f"{prefix}{name}.csv", index=False)
    return tables


def plot_arrivals(frames: dict[str, pd.DataFrame], config: dict, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
    start = month_to_index(config["simulation"]["start_month"])
    for ax, (target, idx_col) in zip(
        axes,
        [("AGI", "agi_month_index"), ("Internal ASI", "internal_asi_month_index"), ("Public ASI", "public_asi_month_index")],
    ):
        for name, frame in frames.items():
            years = 2026 + (np.sort(frame[idx_col].to_numpy()) - (start - 9)) / 12.0
            ax.plot(years, np.linspace(0, 1, len(years)), label=SCENARIO_LABELS.get(name, name).split(" (")[0])
        ax.set_title(f"{target}: cumulative probability")
        ax.set_xlim(2026, 2050)
        ax.grid(alpha=0.3)
        ax.set_xlabel("year")
    axes[0].set_ylabel("P(arrived by year)")
    axes[0].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_lag(frame: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6))
    lag_years = frame["agi_to_asi_lag_months"] / 12.0
    bins = np.linspace(0, 12, 73)
    axes[0].hist(lag_years.clip(upper=12), bins=bins, color="#4c72b0", alpha=0.85)
    axes[0].axvline(lag_years.median(), color="black", ls="--", label=f"median {lag_years.median():.1f}y")
    axes[0].set_title("AGI -> internal ASI lag (baseline, all regimes)")
    axes[0].set_xlabel("years (clipped at 12)")
    axes[0].legend()
    for regime in ["bottlenecked", "moderate", "fast", "recursive"]:
        sub = np.sort(frame.loc[frame["regime"] == regime, "agi_to_asi_lag_months"].to_numpy() / 12.0)
        if len(sub):
            axes[1].plot(sub, np.linspace(0, 1, len(sub)), label=f"{regime} ({len(sub) / len(frame):.0%})")
    allv = np.sort(lag_years.to_numpy())
    axes[1].plot(allv, np.linspace(0, 1, len(allv)), color="black", lw=2, label="mixture")
    axes[1].set_xlim(0, 12)
    axes[1].set_title("Lag CDF by takeoff regime")
    axes[1].set_xlabel("years")
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def plot_tornado(tornado: pd.DataFrame, path: Path) -> None:
    base = tornado.attrs.get("baseline", {}).get("internal_median_months")
    frame = tornado.sort_values("swing:internal_median_months")
    fig, ax = plt.subplots(figsize=(10, 0.45 * len(frame) + 1.5))
    y = np.arange(len(frame))
    lo = frame["fast:internal_median_months"].to_numpy() / 12.0
    hi = frame["slow:internal_median_months"].to_numpy() / 12.0
    ax.barh(y, hi - lo, left=lo, color="#dd8452")
    if base is not None:
        ax.axvline(base / 12.0, color="black", ls="--", label="baseline median")
    ax.margins(x=0.05)
    ax.set_yticks(y)
    ax.set_yticklabels(frame["factor"], fontsize=8)
    ax.set_xlabel("internal-ASI median, years after 2026-10 (fast quantile .. slow quantile)")
    ax.set_title("What drives internal ASI (factor pinned at p10 / p90)")
    ax.legend()
    ax.grid(alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)


def _dashboard(head: dict, driver: str, too_early: str, too_late: str) -> str:
    p = head["p_internal_by"]
    return f"""```text
========================================
ASI ARRIVAL FORECAST — OCTOBER 2026
========================================

Probability operational AGI already exists:
{100 * head['p_agi_already']:.0f} %

AGI median:
{head['agi_median']}

AGI central 80% interval:
{head['agi_80'][0]} → {head['agi_80'][1]}

Internal ASI median:
{head['internal_median']}

Internal ASI central 80% interval:
{head['internal_80'][0]} → {head['internal_80'][1]}

Public ASI median:
{head['public_median']}

Public ASI central 80% interval:
{head['public_80'][0]} → {head['public_80'][1]}

Conditional median AGI → internal ASI lag:
{head['median_lag_months']:.0f} months ({head['median_lag_months'] / 12:.1f} years)

P(AGI→ASI lag < 1 year):
{100 * head['p_lag_lt_12']:.0f} %

P(AGI→ASI lag < 2 years):
{100 * head['p_lag_lt_24']:.0f} %

P(internal ASI by 2028):
{100 * p[2028]:.0f} %

P(internal ASI by 2030):
{100 * p[2030]:.0f} %

P(internal ASI by 2032):
{100 * p[2032]:.0f} %

P(internal ASI by 2035):
{100 * p[2035]:.0f} %

Most important forecast driver:
{driver}

Strongest reason forecast could be too early:
{too_early}

Strongest reason forecast could be too late:
{too_late}
========================================
```"""


def full_study(
    base_config: dict,
    results_dir: str | Path,
    sims: int,
    seed: int,
    sensitivity_sims: int,
    backtest_sims: int = 20000,
) -> dict:
    """Run scenarios A/B/C, sensitivity, backtest; write CSVs, charts and report."""
    out = Path(results_dir)
    out.mkdir(parents=True, exist_ok=True)
    frames: dict[str, pd.DataFrame] = {}
    tables: dict[str, dict] = {}
    configs: dict[str, dict] = {}
    for scenario in scenario_names(base_config):
        configs[scenario], frames[scenario] = run_scenario(base_config, scenario, sims, seed)
        tables[scenario] = write_run_outputs(frames[scenario], configs[scenario], out, prefix=f"{scenario}__")

    base_cfg, base = configs["baseline"], frames["baseline"]
    drivers = spearman_drivers(base)
    drivers.to_csv(out / "baseline__spearman_drivers.csv", index=False)
    tornado = factor_tornado(base_cfg, sensitivity_sims, seed)
    tornado.to_csv(out / "baseline__factor_tornado.csv", index=False)
    ablations = run_variants(base_cfg, ABLATIONS, sensitivity_sims, seed)
    ablations.to_csv(out / "baseline__ablations.csv", index=False)
    alt_priors = run_variants(base_cfg, ALTERNATE_PRIORS, sensitivity_sims, seed)
    alt_priors.to_csv(out / "baseline__alternate_priors.csv", index=False)
    regime_update = regime_update_table(base_cfg["takeoff"])
    regime_update.to_csv(out / "regime_posterior_update.csv", index=False)
    rnd = rnd_automation_summary(base_cfg)
    rnd.to_csv(out / "rnd_automation_today.csv", index=False)
    backtest = backtest_table(backtest_sims)
    backtest.to_csv(out / "backtest_v0_5_1.csv", index=False)
    attribution = attribution_table(base_cfg, sensitivity_sims, seed)
    attribution.to_csv(out / "attribution_vs_v0_5_1.csv", index=False)

    # Seed stability (deterministic seeds, independent streams).
    stab_rows = []
    for s in (seed, seed + 1, seed + 2):
        f = simulate_v06(base_cfg, sims, s)
        stab_rows.append(
            {
                "seed": s,
                "agi_p50": metrics.month_quantile(f["agi_month_index"].to_numpy(), 50),
                "internal_p50": metrics.month_quantile(f["internal_asi_month_index"].to_numpy(), 50),
                "internal_p90": metrics.month_quantile(f["internal_asi_month_index"].to_numpy(), 90),
                "public_p50": metrics.month_quantile(f["public_asi_month_index"].to_numpy(), 50),
                "lag_median_months": float(f["agi_to_asi_lag_months"].median()),
                "P(internal<=2030)": float(np.mean(f["internal_asi_month_index"] <= month_to_index("2030-12"))),
            }
        )
    stability = pd.DataFrame(stab_rows)
    stability.to_csv(out / "baseline__seed_stability.csv", index=False)

    plot_arrivals(frames, base_cfg, out / "arrival_cdfs_by_scenario.png")
    plot_lag(base, out / "agi_to_asi_lag_by_regime.png")
    plot_tornado(tornado, out / "factor_tornado_internal_asi.png")

    head = metrics.headline(base, base_cfg)
    top = tornado.iloc[0]
    lag_top = tornado.sort_values("swing:lag_median_months", ascending=False).iloc[0]
    driver = (
        f"Internal ASI date: {top['factor']} (internal-ASI median swings "
        f"{top['swing:internal_median_months'] / 12:.1f} y between its p10 and p90). "
        f"AGI->ASI lag: {lag_top['factor']} (lag median swings "
        f"{lag_top['swing:lag_median_months'] / 12:.1f} y)."
    )
    too_early = (
        "No AI-attributable acceleration is visible yet (Anthropic: Mythos 5 is a level shift, not a "
        "slope change); open-ended research judgement still fails; the METR horizon is a saturating "
        "SWE benchmark, so the AGI gate could be much further than 2-3 horizon doublings."
    )
    too_late = (
        "Horizons doubling every ~3-4 months plus 52-70x superhuman bounded R&D optimisation and "
        "3.1 agent-workdays per human workday could close the research-taste gap within one model "
        "generation, collapsing both the AGI gate and the AGI->ASI lag (recursive regime)."
    )
    dashboard = _dashboard(head, driver, too_early, too_late)
    (out / "dashboard.md").write_text(dashboard + "\n", encoding="utf-8")

    report = _report_markdown(
        sims, seed, sensitivity_sims, base_cfg, tables, drivers, tornado, ablations, alt_priors,
        regime_update, rnd, backtest, stability, dashboard, attribution,
    )
    (out / "latest_forecast_report.md").write_text(report, encoding="utf-8")
    # Compatibility summary file used by older tooling/tests.
    tables["baseline"]["quantiles"].to_csv(out / "forecast_summary.csv", index=False)
    return {"frames": frames, "tables": tables, "headline": head, "tornado": tornado, "dashboard": dashboard}


def _report_markdown(
    sims, seed, sensitivity_sims, cfg, tables, drivers, tornado, ablations, alt_priors,
    regime_update, rnd, backtest, stability, dashboard, attribution,
) -> str:
    posterior = regime_posterior(cfg["takeoff"])
    parts = [
        "# ASI Arrival Forecast v0.6.0 — generated report",
        "",
        f"Evidence cut-off 2026-10-06. Start month {cfg['simulation']['start_month']}. "
        f"{sims:,} simulations per scenario (seed {seed}); sensitivity runs use {sensitivity_sims:,}.",
        "Generated by `asi-forecast report`. Narrative interpretation: "
        "`research_note/2026_10_recalibration.md`.",
        "",
        "## Dashboard (scenario A)",
        dashboard,
        "",
        "## Takeoff-regime posterior",
        _md(pd.DataFrame([posterior])),
        "",
        "Bayesian update (likelihood ratios averaged within correlation groups):",
        _md(regime_update),
        "",
    ]
    for scenario, label in SCENARIO_LABELS.items():
        t = tables[scenario]
        parts += [
            f"## {label}",
            "",
            "### Arrival quantiles",
            _md(t["quantiles"]),
            "",
            "### AGI -> internal ASI lag (conditional on AGI)",
            _md(t["lag"]),
            "",
            "### Cumulative probability by year",
            _md(t["by_year"]),
            "",
            "### By takeoff regime",
            _md(t["regimes"]),
            "",
            "### Emergent dynamics class (AI-R&D loop)",
            _md(t["dynamics"]),
            "",
        ]
    parts += [
        "## AI-R&D automation today (A_R&D, 2026-10)",
        _md(rnd),
        "",
        "## Sensitivity: factor tornado (common random numbers)",
        _md(tornado[["factor", "swing:agi_median_months", "swing:lag_median_months", "swing:internal_median_months", "swing:public_median_months", "fast:internal_median_months", "slow:internal_median_months"]]),
        "",
        "## Sensitivity: top Spearman drivers per target",
    ]
    for target in ("agi", "agi_to_asi_lag", "internal_asi", "public_asi"):
        parts += [f"### {target}", _md(drivers[drivers["target"] == target].head(8)), ""]
    parts += [
        "## Leave-one-factor-out ablations",
        _md(ablations),
        "",
        "## Alternate-prior checks",
        _md(alt_priors),
        "",
        "## Monte Carlo stability (three seeds)",
        _md(stability),
        "",
        "## Convergence (batch ranges, scenario A)",
        _md(tables["baseline"]["convergence"]),
        "",
        "## Backtest of v0.5.1 against October 2026",
        _md(backtest),
        "",
        "## Attribution: cumulatively re-imposing v0.5.1 AGI-stage assumptions inside the v0.6 engine",
        _md(attribution),
        "",
    ]
    return "\n".join(parts)
