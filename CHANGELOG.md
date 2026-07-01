# Changelog

## 0.5.1
- Added `evidence_tables/v0_5_parameter_sources.csv`: every live engine parameter
  now traces to a source_id, URL, quote, and regime tag (METR, Epoch, Davidson FTM,
  Anthropic, Sakana, ESPAI, Cotra) from asi.txt + perplexity.txt research.
- Honest regime tagging: the post-AGI cognitive lags are marked `stress_test` /
  `aggressive`, NOT baseline — the model runs in a fast-takeoff regime.
- Added external calibration (ESPAI 2047, Cotra 2052) to README + report; the model
  is ~16y earlier than ESPAI HLMI, a property of the aggressive priors.
- Enforcement test `test_parameter_traceability.py` blocks unsourced parameters.
- NOTE: the values are now *traceable and regime-labelled*, but NOT a consensus
  forecast. Still not preprint-ready as a prediction.

## 0.5.0
Empirical recalibration from the asi.txt evidence audit (14-variable Q1-Q14).

- Added lognormal, gamma, and beta distribution families to the sampler
  (method-of-moments fitting from mean/std, location-shifted, clipped to bounds).
- Recalibrated inputs: compute/algo -> lognormal, cognitive lags -> gamma/lognormal
  (much smaller), infrastructure friction 6->24mo (lognormal), phase overlap -> beta
  (0.65), secrecy -> gamma, correlations 0.50->0.35 and -0.60->-0.70, long-tail
  sigma 0.8332->0.76.
- Iman-Conover verified to survive the non-normal marginals (targets still met,
  marginals preserved).
- Retired the unsourced 60-month cognitive-lag long-tail (double-counted the
  physical stall now carried by the infrastructure_friction lognormal); long tail
  now applies to the AGI date only.
- Defused asi.txt landmines: kept dampening exponent at 0.5 (its formula semantics
  are inverted vs asi.txt Q1), kept the hours-based coding gate, kept structural
  AGI + mixture. Formulation-A rewiring, SWE-bench-Pro gate, direct-lognormal AGI,
  and the evidence-table rebuild remain deferred.
- Forecast shifted earlier: AGI ~2031-07, internal ASI ~2034-05, public ASI
  ~2035-11 (cognitive-lag recalibration dominates the infra-friction increase).
- Still an experimental calibration prototype; NOT preprint-ready.

## 0.4.0
0.4.0 exposes hidden structural constants in YAML and fixes AGI-to-ASI overlap handling.

- Moved hidden Python constants into `forecast_inputs/base_forecast_inputs.yaml`:
  task-horizon double-count dampening exponent, long-horizon threshold hours,
  long-tail sigma, bio-anchor median year, AGI-to-ASI lag late-tail median,
  and the compute/algorithmic-efficiency baseline rates. Each carries an explicit
  `confidence` and `evidence_status`.
- Phase overlap no longer compresses `infrastructure_friction_months`. Only the
  research/takeoff cognitive lags overlap; physical buildout is added uncompressed.
- Long-tail mixture median-shift behaviour is now documented as a calibration risk.
- This is a calibration-prep prototype, NOT a preprint-grade or publication-ready model.

## 0.3.0
Stage-gated AGI-to-ASI Monte Carlo with triangular inputs (initial public structure).
