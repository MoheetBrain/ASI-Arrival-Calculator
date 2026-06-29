# Epoch AI

target_category:
  - intermediate
  - compute
primary_model_use:
  - agi_date

## What This Source Contributes

Epoch AI tracks AI compute, hardware, algorithmic progress, model scale, and cost trends. ASI Arrival Forecast uses it as the main source family for effective compute growth and algorithmic efficiency assumptions.

## Variables Informed

- `effective_compute_growth_x_per_year`
- `algorithmic_efficiency_x_per_year`

## How It Enters The Model

The simulation samples yearly effective compute growth and algorithmic efficiency growth. Their combined growth rate weakly adjusts the sampled agent task-horizon doubling time: faster combined progress shortens the time to cross the coding automation threshold, while slower combined progress lengthens it.

## Limitations

- Compute trends do not translate directly into autonomous agency.
- Hardware supply, inference cost, data limits, and bottlenecks can break simple extrapolations.
- The AGI-stage progress adjustment is deliberately simple and should be replaced with a better calibrated function.

## Placeholder Citation Links

- [Epoch AI](https://epoch.ai/)
- [Epoch AI research](https://epoch.ai/research)
