# AI Impacts Survey

target_category:
  - agi
  - outside_forecast
primary_model_use:
  - agi_date
  - comparison_only

## What This Source Contributes

AI Impacts surveys collect expert judgments about high-level machine intelligence and related AI timelines. ASI Arrival Forecast uses this source family as an external sanity check rather than a direct mechanistic driver.

## Variables Informed

- External timeline comparison rows in `evidence_tables/outside_forecasts.csv`
- Optional future priors

## How It Enters The Model

The base model does not force expert survey medians into the simulation. Instead, survey-based estimates can be added as prior distributions or comparison baselines.

## Limitations

- Definitions vary across surveys and respondents.
- Expert elicitation can be unstable and sensitive to framing.
- HLAI, AGI, and capability-and-agency ASI are not identical concepts.

## Placeholder Citation Links

- [AI Impacts timeline surveys](https://wiki.aiimpacts.org/doku.php?id=ai_timelines:predictions_of_human-level_ai_timelines:ai_timeline_surveys)
