# Implementation Report: AGI-to-ASI Split

## Summary

I refactored the repository from a direct ASI forecast into a stage-gated AGI-to-ASI forecasting pipeline. The model now forecasts AGI first, then models the uncertain transition from AGI to internal ASI, and finally models public deployment delay.

The core conceptual correction is:

```text
AGI evidence -> AGI forecast
AGI + AI R&D automation + takeoff dynamics -> ASI forecast
```

## What Changed

### Forecast Inputs

Implemented in `forecast_inputs/`:

- `base_forecast_inputs.yaml`: empirical base case with separate `agi_stage`, `asi_stage`, and `deployment_stage` sections.
- `author_prior_scenario.yaml`: separate July 2029 ASI author-prior scenario, not blended into the base case.
- `agi_definition.yaml`: machine-readable AGI definition.
- `asi_definition.yaml`: machine-readable capability-and-agency ASI definition.
- `milestone_definitions.yaml`: definitions for coding automation, long-horizon agents, AGI, AI R&D automation, superhuman AI researcher, internal ASI, and public ASI.
- `capability_ladder.yaml`: qualitative 7-checkpoint ladder for interpreting memory, formal verification, agency, infrastructure, synthetic-data, AI R&D, and takeoff evidence.

### Evidence Tables

Implemented in `evidence_tables/`:

- `agi_evidence.csv`: AGI, weak AGI, TAI, general AI, and human-level AI evidence.
- `asi_evidence.csv`: ASI, superhuman AI researcher, recursive self-improvement, and intelligence explosion evidence.
- `intermediate_milestones.csv`: coding automation, agent horizons, compute growth, algorithmic efficiency, AI R&D automation, deployment, and governance inputs.
- Existing tables were retained and aligned with the new split.

### Evidence Notes

Updated files in `evidence_notes/` with metadata:

- `target_category`
- `primary_model_use`

This makes it clear whether each source informs AGI timing, the AGI-to-ASI lag, AI R&D automation, takeoff, deployment delay, or comparison-only context.

### Model Code

Implemented in `src/asi_forecast/`:

- `model.py`: stage-gated AGI-to-ASI equations.
- `monte_carlo.py`: vectorized simulation returning AGI, internal ASI, public ASI, AGI-to-ASI lag, and sampled inputs.
- `schemas.py`: Pydantic validation for the input YAML.
- `drivers.py`: separate Spearman driver tables for AGI, internal ASI, public ASI, and AGI-to-ASI lag.
- `analyze.py`: summary percentiles, lag metrics, stage summaries, and convergence checks.
- `charts.py`: three-distribution arrival chart plus AGI-to-ASI lag chart.
- `cli.py`: `--target agi|asi|both`, `explain-targets`, and updated result files.

### Outputs

Generated outputs now include:

- `forecast_summary.csv`
- `forecast_metrics.csv`
- `latest_forecast_report.md`
- `simulated_agi_arrival_months.csv`
- `simulated_internal_asi_arrival_months.csv`
- `simulated_public_asi_arrival_months.csv`
- `simulated_agi_to_asi_lags.csv`
- `arrival_probability_distribution.png`
- `agi_to_asi_lag_distribution.png`
- `forecast_drivers.csv`
- `what_drives_the_forecast.png`

## How The Model Works

For each simulated future:

1. Sample AGI-stage inputs.
2. Estimate strong coding automation timing.
3. Estimate long-horizon agent reliability timing.
4. Estimate broad general capability timing.
5. Set AGI to the latest required AGI milestone plus AGI integration lag.
6. Add AI R&D automation lag after AGI.
7. Add superhuman AI researcher lag.
8. Add takeoff lag.
9. Add infrastructure and governance friction.
10. Produce internal ASI.
11. Add public deployment delay.
12. Produce public ASI.

## Validation

Tests now check:

- AGI date exists.
- Internal ASI date exists.
- Public ASI date exists.
- Internal ASI is always at or after AGI.
- Public ASI is always at or after internal ASI.
- AGI-to-ASI lag is never negative.
- CLI `--target both` works.
- CLI `explain-targets` works.
- `forecast_summary.csv` contains AGI, internal ASI, and public ASI.

## Important Assumptions Requiring Review

- Current agent task horizon.
- Coding automation threshold in human-hours.
- General capability lag after coding automation.
- AI R&D automation lag after AGI.
- Superhuman AI researcher lag.
- Takeoff lag.
- Governance and public deployment delays.

These assumptions are visible in `forecast_inputs/base_forecast_inputs.yaml` and should be reviewed before public promotion.
