"""Terminal and Markdown report generation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def top_drivers(
    sensitivity: pd.DataFrame,
    target: str,
    limit: int = 5,
) -> list[str]:
    """Return the strongest sensitivity variables for a target."""
    if sensitivity.empty:
        return []
    subset = sensitivity[sensitivity["target"] == target]
    subset = subset.sort_values("absolute_rank", ascending=True)
    return subset.head(limit)["input_variable"].tolist()


def terminal_summary(
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    sims: int,
    scenario: str,
    target: str = "both",
) -> str:
    """Format a readable terminal report."""
    agi = summary[summary["target"] == "agi"].iloc[0]
    internal = summary[summary["target"] == "internal_asi"].iloc[0]
    public = summary[summary["target"] == "public_asi"].iloc[0]
    drivers = top_drivers(sensitivity, target="internal_asi", limit=5)
    driver_lines = "\n".join(f"  - {driver}" for driver in drivers)

    blocks = [
        "AGI and ASI Arrival Forecast",
        f"Scenario: {scenario}",
        f"Target view: {target}",
        f"Simulations: {sims:,}",
        "",
    ]
    if target in {"agi", "both"}:
        blocks.extend(
            [
                "AGI / Transformative General AI",
                f"  Median: {agi['median_month']}",
                f"  50% interval: {agi['interval_50']}",
                f"  90% interval: {agi['interval_90']}",
                "",
            ]
        )
    if target in {"asi", "both"}:
        blocks.extend(
            [
                "Internal ASI",
                f"  Median: {internal['median_month']}",
                f"  50% interval: {internal['interval_50']}",
                f"  90% interval: {internal['interval_90']}",
                "",
                "Public ASI",
                f"  Median: {public['median_month']}",
                f"  50% interval: {public['interval_50']}",
                f"  90% interval: {public['interval_90']}",
                "",
                "Main internal ASI drivers by absolute Spearman correlation",
                driver_lines,
            ]
        )
    return "\n".join(blocks).rstrip() + "\n"


def _driver_table(frame: pd.DataFrame) -> str:
    """Render a Markdown driver table."""
    if frame.empty:
        return "No driver rows available."
    lines = ["| Input variable | Spearman correlation | Interpretation |", "|---|---:|---|"]
    for _, row in frame.head(10).iterrows():
        lines.append(
            f"| `{row['input_variable']}` | "
            f"{row['spearman_correlation']:.3f} | "
            f"{row['interpretation']} |"
        )
    return "\n".join(lines)


def _stage_table(frame: pd.DataFrame | None) -> str:
    if frame is None or frame.empty:
        return "Stage timeline summary was not available."
    lines = [
        "| Stage | Median calendar month | 50% offset interval |",
        "|---|---:|---:|",
    ]
    for _, row in frame.iterrows():
        lines.append(
            f"| {row['display_name']} | {row['median_calendar_month']} | "
            f"{row['p25_month_offset']:.1f} to {row['p75_month_offset']:.1f} months |"
        )
    return "\n".join(lines)


def _metrics_table(frame: pd.DataFrame | None) -> str:
    if frame is None or frame.empty:
        return "Lag metrics were not available."
    lines = ["| Metric | Value |", "|---|---:|"]
    for _, row in frame.iterrows():
        lines.append(f"| `{row['metric']}` | {float(row['value']):.2f} |")
    return "\n".join(lines)


def _convergence_text(frame: pd.DataFrame | None) -> str:
    if frame is None or frame.empty:
        return "Batch-means convergence diagnostics were not available."
    row = frame.iloc[0]
    verdict = "passed" if bool(row["converged_under_one_month"]) else "did not pass"
    return (
        f"The run used {int(row['batches'])} batches. The inter-batch median "
        f"range was {float(row['batch_median_range_months']):.2f} months, so "
        f"the numerical convergence check {verdict} the under-one-month rule."
    )


def markdown_report(
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    sims: int,
    seed: int,
    scenario: str,
    stage_summary: pd.DataFrame | None = None,
    convergence: pd.DataFrame | None = None,
    metrics: pd.DataFrame | None = None,
) -> str:
    """Create the generated Markdown forecast report."""
    agi = summary[summary["target"] == "agi"].iloc[0]
    internal = summary[summary["target"] == "internal_asi"].iloc[0]
    public = summary[summary["target"] == "public_asi"].iloc[0]

    return f"""# AGI and ASI Arrival Forecast Report

Generated from scenario `{scenario}` with `{sims:,}` simulations and random seed `{seed}`.

This report is conditional on the editable inputs in `forecast_inputs/base_forecast_inputs.yaml`. It is not a claim that AGI or ASI will arrive in a specific month.

## What Was Forecast

The forecast estimates three month-level distributions:

- **AGI / transformative general AI**: broadly human-level or expert-level general cognitive capability.
- **Internal ASI**: capability-and-agency ASI inside a lab, company, government, or restricted deployment.
- **Public ASI**: comparable ASI capability becoming publicly visible or broadly accessible.

Most public evidence is about AGI, coding agents, compute, benchmarks, and AI R&D automation. ASI is further downstream. This repo therefore forecasts AGI first, then models the uncertain transition from AGI to ASI.

## AGI Forecast

- Median: **{agi['median_month']}**
- 50% interval: **{agi['interval_50']}**
- 90% interval: **{agi['interval_90']}**

## Internal ASI Forecast

- Median: **{internal['median_month']}**
- 50% interval: **{internal['interval_50']}**
- 90% interval: **{internal['interval_90']}**

## Public ASI Forecast

- Median: **{public['median_month']}**
- 50% interval: **{public['interval_50']}**
- 90% interval: **{public['interval_90']}**

## AGI-to-ASI Transition Metrics

{_metrics_table(metrics)}

## Stage-Gate Timeline

{_stage_table(stage_summary)}

## Forecast Drivers: AGI

{_driver_table(sensitivity[sensitivity["target"] == "agi"])}

## Forecast Drivers: Internal ASI

{_driver_table(sensitivity[sensitivity["target"] == "internal_asi"])}

## Forecast Drivers: Public ASI

{_driver_table(sensitivity[sensitivity["target"] == "public_asi"])}

## Forecast Drivers: AGI-to-ASI Lag

{_driver_table(sensitivity[sensitivity["target"] == "agi_to_asi_lag"])}

## Interpretation

The median is the 50/50 month: half of simulated futures arrive before it, and half arrive after it. The 50% interval contains the middle half of simulations. The 90% interval contains the central 90% of simulations.

More simulations reduce numerical noise. They do not make bad assumptions true.

## Convergence

{_convergence_text(convergence)}

## Limitations

- AGI and ASI are not the same target.
- Most existing evidence directly informs AGI or intermediate milestones, not ASI itself.
- The AGI-to-ASI transition is structurally uncertain and depends on AI R&D automation, superhuman AI researcher emergence, takeoff dynamics, infrastructure, and governance.
- Internal ASI and public ASI can diverge because deployment may be delayed.
- Spearman sensitivity is an association measure, not causal proof.
- Week-level precision is rejected; outputs are rounded to months.
"""


def write_markdown_report(
    summary: pd.DataFrame,
    sensitivity: pd.DataFrame,
    output_path: str | Path,
    sims: int,
    seed: int,
    scenario: str,
    stage_summary: pd.DataFrame | None = None,
    convergence: pd.DataFrame | None = None,
    metrics: pd.DataFrame | None = None,
) -> Path:
    """Write the generated forecast report to disk."""
    path = Path(output_path)
    path.write_text(
        markdown_report(
            summary,
            sensitivity,
            sims=sims,
            seed=seed,
            scenario=scenario,
            stage_summary=stage_summary,
            convergence=convergence,
            metrics=metrics,
        ),
        encoding="utf-8",
    )
    return path
