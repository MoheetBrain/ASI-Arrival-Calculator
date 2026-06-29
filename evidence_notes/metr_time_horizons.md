# METR Time Horizons

target_category:
  - intermediate
primary_model_use:
  - agi_date
  - ai_rnd_automation

## What This Source Contributes

METR evaluates frontier AI systems on increasingly long autonomous tasks. ASI Arrival Forecast uses this source family for current agent task horizons and possible time-horizon doubling rates.

## Variables Informed

- `current_agent_task_horizon_hours`
- `agent_time_horizon_doubling_months`

## How It Enters The Model

The model samples a current reliable autonomous task horizon and a doubling time. It then estimates when the sampled horizon crosses a coding automation threshold measured in human-hours.

## Limitations

- Benchmarks can be gamed or become stale.
- Task horizon depends heavily on scaffolding, tools, supervision, and failure tolerance.
- Coding automation may arrive before or after generalized long-horizon agency.

## Placeholder Citation Links

- [METR](https://metr.org/)
- [METR research](https://metr.org/research/)
