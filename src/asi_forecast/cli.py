"""Command-line interface for ASI Arrival Forecast."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from . import __version__
from .analyze import (
    batch_means_convergence,
    summarize_arrivals,
    summarize_lag_metrics,
    summarize_stage_timeline,
)
from .drivers import combined_sensitivity
from .helpers import (
    apply_scenario,
    default_results_dir,
    dump_config,
    ensure_output_dir,
    load_config,
    project_root,
)
from .monte_carlo import simulate_forecast
from .write_report import terminal_summary, write_markdown_report


SUMMARY_FILE = "forecast_summary.csv"
METRICS_FILE = "forecast_metrics.csv"
AGI_ARRIVALS_FILE = "simulated_agi_arrival_months.csv"
INTERNAL_ARRIVALS_FILE = "simulated_internal_asi_arrival_months.csv"
PUBLIC_ARRIVALS_FILE = "simulated_public_asi_arrival_months.csv"
AGI_TO_ASI_LAGS_FILE = "simulated_agi_to_asi_lags.csv"
DRIVERS_FILE = "forecast_drivers.csv"
REPORT_FILE = "latest_forecast_report.md"
ARRIVAL_CHART_FILE = "arrival_probability_distribution.png"
LAG_CHART_FILE = "agi_to_asi_lag_distribution.png"
DRIVERS_CHART_FILE = "what_drives_the_forecast.png"
STAGE_TIMELINE_FILE = "stage_gate_timeline_summary.csv"
CONVERGENCE_FILE = "convergence_diagnostics.csv"

GENERATED_RESULT_FILES = [
    "simulated_internal_arrival_months.csv",
    "simulated_public_arrival_months.csv",
    "sobol_status.csv",
    SUMMARY_FILE,
    METRICS_FILE,
    AGI_ARRIVALS_FILE,
    INTERNAL_ARRIVALS_FILE,
    PUBLIC_ARRIVALS_FILE,
    AGI_TO_ASI_LAGS_FILE,
    DRIVERS_FILE,
    REPORT_FILE,
    ARRIVAL_CHART_FILE,
    LAG_CHART_FILE,
    DRIVERS_CHART_FILE,
    STAGE_TIMELINE_FILE,
    CONVERGENCE_FILE,
]


EXPLAIN_TEXT = """ASI Arrival Forecast samples many possible futures from explicit assumptions.

It does not predict the future as a certainty. It asks: if these inputs were a
reasonable description of uncertainty, what distribution of AGI and ASI arrival
months would they imply?

The model separates:
- AGI: broadly human-level or expert-level general capability.
- Internal ASI: capability exists inside a lab, company, government, or restricted deployment.
- Public ASI: comparable capability becomes publicly visible or broadly accessible.

The median is the 50/50 month: half the simulated futures arrive before it,
and half arrive after it. The 50% interval is the middle half of simulations.
The 90% interval is the central 90% of simulations.

More simulations reduce numerical noise. They do not make bad assumptions true.
Edit forecast_inputs/base_forecast_inputs.yaml to inspect or change the assumptions.
"""


EXPLAIN_TARGETS_TEXT = """AGI and ASI are separated in this repo.

AGI means broadly human-level or expert-level general capability across many
economically valuable cognitive tasks: software engineering, analysis, research
assistance, planning, computer use, and general problem-solving across novel
domains.

Capability-and-agency ASI means substantially beyond top human teams across
important cognitive work, especially AI R&D, software engineering, scientific
discovery, mathematics, cybersecurity, strategy, and long-horizon autonomous
tasks.

Most public evidence is about AGI, coding agents, compute, benchmarks, and AI
R&D automation. That evidence cannot honestly be treated as direct ASI evidence.
ASI is further downstream.

The model therefore forecasts AGI first, then models the uncertain transition:

AGI -> AI R&D automation -> superhuman AI researcher -> accelerated progress
-> internal ASI -> public ASI.
"""


def _load_run_config(args: argparse.Namespace) -> tuple[dict, int, int]:
    """Load inputs, apply scenario, and resolve simulation count plus seed."""
    base_config = load_config(args.config)
    config = apply_scenario(base_config, args.scenario)
    simulation_config = config["simulation"]
    sims = int(args.sims or simulation_config["default_sims"])
    seed = int(args.seed if args.seed is not None else simulation_config["random_seed"])
    return config, sims, seed


def _results_dir_from_args(args: argparse.Namespace) -> Path:
    """Return the requested results directory."""
    return ensure_output_dir(args.results_dir)


def run_pipeline(
    config: dict,
    sims: int,
    seed: int,
    scenario: str,
    results_dir: str | Path | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run simulation, write all standard results, and return data frames."""
    from .charts import plot_arrival_distribution, plot_lag_distribution, plot_sensitivity

    results_path = ensure_output_dir(results_dir)
    simulations = simulate_forecast(config, sims=sims, seed=seed)
    summary = summarize_arrivals(simulations)
    summary["sims"] = sims
    summary["seed"] = seed
    summary["scenario"] = scenario
    driver_table = combined_sensitivity(simulations)
    stage_summary = summarize_stage_timeline(simulations)
    metrics = summarize_lag_metrics(simulations)
    convergence = batch_means_convergence(
        simulations,
        batches=int(config["simulation"].get("convergence_batches", 10)),
    )

    summary.to_csv(results_path / SUMMARY_FILE, index=False)
    metrics.to_csv(results_path / METRICS_FILE, index=False)
    simulations[["sim_id", "agi_month_index", "agi_month"]].to_csv(
        results_path / AGI_ARRIVALS_FILE,
        index=False,
    )
    simulations[["sim_id", "internal_asi_month_index", "internal_asi_month"]].to_csv(
        results_path / INTERNAL_ARRIVALS_FILE,
        index=False,
    )
    simulations[["sim_id", "public_asi_month_index", "public_asi_month"]].to_csv(
        results_path / PUBLIC_ARRIVALS_FILE,
        index=False,
    )
    simulations[["sim_id", "agi_to_asi_lag_months"]].to_csv(
        results_path / AGI_TO_ASI_LAGS_FILE,
        index=False,
    )
    driver_table.to_csv(results_path / DRIVERS_FILE, index=False)
    stage_summary.to_csv(results_path / STAGE_TIMELINE_FILE, index=False)
    convergence.to_csv(results_path / CONVERGENCE_FILE, index=False)
    write_markdown_report(
        summary,
        driver_table,
        results_path / REPORT_FILE,
        sims=sims,
        seed=seed,
        scenario=scenario,
        stage_summary=stage_summary,
        convergence=convergence,
        metrics=metrics,
    )
    plot_arrival_distribution(simulations, results_path / ARRIVAL_CHART_FILE)
    plot_lag_distribution(simulations, results_path / LAG_CHART_FILE)
    plot_sensitivity(driver_table, results_path / DRIVERS_CHART_FILE)

    return simulations, summary, driver_table


def command_run(args: argparse.Namespace) -> int:
    """Handle `run`."""
    config, sims, seed = _load_run_config(args)
    _, summary, driver_table = run_pipeline(
        config,
        sims=sims,
        seed=seed,
        scenario=args.scenario,
        results_dir=args.results_dir,
    )
    print(
        terminal_summary(
            summary,
            driver_table,
            sims=sims,
            scenario=args.scenario,
            target=args.target,
        )
    )
    print(f"Saved results to: {Path(args.results_dir or default_results_dir())}")
    return 0


def command_explain(_: argparse.Namespace) -> int:
    """Handle `explain`."""
    print(EXPLAIN_TEXT)
    return 0


def command_explain_targets(_: argparse.Namespace) -> int:
    """Handle `explain-targets`."""
    print(EXPLAIN_TARGETS_TEXT)
    return 0


def command_inputs(args: argparse.Namespace) -> int:
    """Handle `inputs` and the old `assumptions` alias."""
    config = load_config(args.config)
    print(dump_config(config))
    return 0


def command_evidence(_: argparse.Namespace) -> int:
    """Handle `evidence` and the old `sources` alias."""
    root = project_root()
    notes_dir = root / "evidence_notes"
    tables_dir = root / "evidence_tables"

    print("ASI Arrival Forecast evidence notes\n")
    for path in sorted(notes_dir.glob("*.md")):
        print(f"- {path.relative_to(root)}")

    print("\nEvidence tables")
    for path in sorted(tables_dir.glob("*.csv")):
        print(f"- {path.relative_to(root)}")
    return 0


def _print_top_drivers(driver_table: pd.DataFrame) -> None:
    """Print top forecast drivers for every target."""
    for target in ("agi", "internal_asi", "public_asi", "agi_to_asi_lag"):
        top = driver_table[driver_table["target"] == target].head(8)
        print(f"Top {target} forecast drivers\n")
        print(top[["input_variable", "spearman_correlation", "absolute_rank"]].to_string(index=False))
        print()


def command_drivers(args: argparse.Namespace) -> int:
    """Handle `drivers` and the old `sensitivity` alias."""
    results_dir = _results_dir_from_args(args)
    drivers_path = results_dir / DRIVERS_FILE

    if drivers_path.exists() and not args.rerun:
        driver_table = pd.read_csv(drivers_path)
    else:
        config, sims, seed = _load_run_config(args)
        _, _, driver_table = run_pipeline(
            config,
            sims=sims,
            seed=seed,
            scenario=args.scenario,
            results_dir=results_dir,
        )

    _print_top_drivers(driver_table)
    print(f"\nSaved drivers to: {drivers_path}")
    return 0


def command_report(args: argparse.Namespace) -> int:
    """Handle `report`.

    If existing summary and driver CSVs are present, regenerate the Markdown
    report from them. Otherwise run the pipeline first.
    """
    results_dir = _results_dir_from_args(args)
    summary_path = results_dir / SUMMARY_FILE
    drivers_path = results_dir / DRIVERS_FILE
    stage_path = results_dir / STAGE_TIMELINE_FILE
    convergence_path = results_dir / CONVERGENCE_FILE
    metrics_path = results_dir / METRICS_FILE
    config, sims, seed = _load_run_config(args)
    scenario = args.scenario

    if summary_path.exists() and drivers_path.exists():
        summary = pd.read_csv(summary_path)
        driver_table = pd.read_csv(drivers_path)
        stage_summary = pd.read_csv(stage_path) if stage_path.exists() else None
        convergence = pd.read_csv(convergence_path) if convergence_path.exists() else None
        metrics = pd.read_csv(metrics_path) if metrics_path.exists() else None
        if "sims" in summary.columns:
            sims = int(summary["sims"].iloc[0])
        if "seed" in summary.columns:
            seed = int(summary["seed"].iloc[0])
        if "scenario" in summary.columns:
            scenario = str(summary["scenario"].iloc[0])
    else:
        _, summary, driver_table = run_pipeline(
            config,
            sims=sims,
            seed=seed,
            scenario=scenario,
            results_dir=results_dir,
        )
        stage_summary = pd.read_csv(stage_path) if stage_path.exists() else None
        convergence = pd.read_csv(convergence_path) if convergence_path.exists() else None
        metrics = pd.read_csv(metrics_path) if metrics_path.exists() else None

    report_path = write_markdown_report(
        summary,
        driver_table,
        results_dir / REPORT_FILE,
        sims=sims,
        seed=seed,
        scenario=scenario,
        stage_summary=stage_summary,
        convergence=convergence,
        metrics=metrics,
    )
    print(f"Saved report to: {report_path}")
    return 0


def command_clean_results(args: argparse.Namespace) -> int:
    """Remove known generated result files and keep results/.gitkeep."""
    results_dir = _results_dir_from_args(args)
    keep_file = results_dir / ".gitkeep"
    keep_file.touch(exist_ok=True)
    removed: list[Path] = []

    for filename in GENERATED_RESULT_FILES:
        path = results_dir / filename
        if path.exists() and path.is_file():
            path.unlink()
            removed.append(path)

    if removed:
        print("Removed generated result files:")
        for path in removed:
            print(f"- {path}")
    else:
        print("No generated result files found.")
    print(f"Kept: {keep_file}")
    return 0


def add_common_run_arguments(parser: argparse.ArgumentParser) -> None:
    """Arguments shared by commands that may run the model."""
    parser.add_argument("--sims", type=int, default=None, help="Number of simulations.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed.")
    parser.add_argument(
        "--target",
        choices=["agi", "asi", "both"],
        default="both",
        help="Which forecast target view to print. The simulation still computes all targets.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help=(
            "Path to forecast inputs YAML. Defaults to "
            "forecast_inputs/base_forecast_inputs.yaml."
        ),
    )
    parser.add_argument(
        "--scenario",
        choices=["base", "fast", "slow"],
        default="base",
        help="Scenario adjustment to apply.",
    )
    parser.add_argument(
        "--results-dir",
        "--output-dir",
        dest="results_dir",
        default=None,
        help="Directory for generated results. Defaults to results/.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the argparse parser."""
    parser = argparse.ArgumentParser(
        prog="asi-forecast",
        description=(
            "Public Monte Carlo forecast for capability-and-agency artificial "
            "superintelligence arrival months."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ASI Arrival Forecast {__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the Monte Carlo forecast.")
    add_common_run_arguments(run_parser)
    run_parser.set_defaults(func=command_run)

    explain_parser = subparsers.add_parser(
        "explain",
        help="Explain the model in everyday language.",
    )
    explain_parser.set_defaults(func=command_explain)

    explain_targets_parser = subparsers.add_parser(
        "explain-targets",
        help="Explain AGI, ASI, and why the model separates them.",
    )
    explain_targets_parser.set_defaults(func=command_explain_targets)

    inputs_parser = subparsers.add_parser(
        "inputs",
        aliases=["assumptions"],
        help="Print the editable forecast inputs YAML.",
    )
    inputs_parser.add_argument("--config", default=None)
    inputs_parser.set_defaults(func=command_inputs)

    evidence_parser = subparsers.add_parser(
        "evidence",
        aliases=["sources"],
        help="List evidence notes and evidence tables.",
    )
    evidence_parser.set_defaults(func=command_evidence)

    drivers_parser = subparsers.add_parser(
        "drivers",
        aliases=["sensitivity"],
        help="Show which assumptions drive the result.",
    )
    add_common_run_arguments(drivers_parser)
    drivers_parser.add_argument(
        "--rerun",
        action="store_true",
        help="Rerun the forecast before showing drivers.",
    )
    drivers_parser.set_defaults(func=command_drivers)

    report_parser = subparsers.add_parser(
        "report",
        help="Regenerate the latest Markdown report.",
    )
    add_common_run_arguments(report_parser)
    report_parser.set_defaults(func=command_report)

    clean_parser = subparsers.add_parser(
        "clean-results",
        help="Remove generated result files while keeping results/.gitkeep.",
    )
    clean_parser.add_argument(
        "--results-dir",
        "--output-dir",
        dest="results_dir",
        default=None,
        help="Directory containing generated results. Defaults to results/.",
    )
    clean_parser.set_defaults(func=command_clean_results)

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
