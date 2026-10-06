# Project Status

_Last updated: 2026-10-06 (v0.6.0 recalibration commit on branch `v0.6-recalibration`)._

## Project Objective

An auditable, causally grounded Monte Carlo forecast of when AGI, internal ASI and
public ASI arrive. Every live parameter traces to a classified source, and the
historical calibrations stay reproducible.

## Current Stage

v0.6.0: full recalibration on evidence to 2026-10-06. Experimental research model.
It is not a consensus forecast, not peer-reviewed, and not advice.

## Current Branch

`v0.6-recalibration`, branched from `main` at `a33ad3e` (v0.5.1, merged PR #1).

## Current System Architecture

```text
forecast_inputs/v0_6/inputs.yaml ──► v06/config.py (validate, scenario deep-merge, traceability)
                                       │
evidence_tables/v0_6_evidence_2026.csv ┘ (source_ids must resolve; tested)
                                       ▼
v06/engine.py
  sample_inputs: inverse-CDF + latent progress factor Z (Gaussian copula); regime ~ Bayesian posterior (v06/regimes.py)
  _agi_stage:    monthly horizon-doubling integration to AGI gate (+H2 mass, paradigm wall, pauses)
  _takeoff:      monthly AI-R&D feedback ODE from AGI to ASI capability gap (Amdahl f, r, p, compute cap, compute path)
  -> internal ASI (+training, demonstration, pause) -> public ASI (staged | secrecy)
v06/metrics.py, sensitivity.py (Spearman, tornado, ablations, alternate priors), backtest.py, report.py
cli.py: v0.6 default; v0.5.1 engine (monte_carlo.py, model.py) selected by --config base_forecast_inputs.yaml
```

## Capabilities Implemented

* Three targets (AGI, internal ASI, public ASI) and the AGI→ASI lag as a first-class
  output.
* Scenarios A (baseline posterior mixture), B (agi_era_fast) and C (bottlenecked).
* Four-regime takeoff mixture. Regime weights come from a prior plus 2026 evidence,
  with likelihoods averaged inside correlation groups.
* Explicit A_R&D(t). Today's level comes from a 14-component decomposition; after AGI
  it is modelled as an automation-fraction ODE.
* Emergent dynamics classes (subcritical, linear, superlinear, punctuated) and the
  loop gain at AGI.
* Sensitivity suite: Spearman drivers, factor tornado with common random numbers,
  13 ablations, 8 alternate priors, seed stability, batch convergence.
* Backtest of v0.5.1 against October 2026, and a within-engine attribution.
* CLI: `run`, `drivers`, `report` (full study and dashboard) and `inputs`, for both
  engines.

## Work Completed to Date

* v0.3–v0.5.1: stage-gated AGI→ASI model, structural constants exposed in YAML, an
  empirical recalibration, and a traceable evidence layer.
* v0.6.0 (this commit):
  * the audit;
  * an unchanged reproduction of v0.5.1;
  * a primary-source evidence sweep (39 sources);
  * the new engine;
  * recalibrated inputs;
  * 25 new tests;
  * the research note `research_note/2026_10_recalibration.md`;
  * archived outputs in `historical_runs/v0_6_0/`.

## Important Files and Artifacts

* `forecast_inputs/v0_6/inputs.yaml`: all v0.6 inputs and scenarios.
* `src/asi_forecast/v06/`: the engine and its analysis modules.
* `research_note/2026_10_recalibration.md`: the full A–R report, Q1–Q8 answers and
  the dashboard.
* `research_note/2026_10_model_audit.md`: the pre-change audit.
* `evidence_tables/v0_6_evidence_2026.csv`, `v0_6_parameter_sources.csv` (generated
  from the YAML; sync is tested).
* `evidence_notes/2026_leader_statements.md`, `2026_ai_rnd_automation.md`.
* `historical_runs/v0_5_1_unchanged/` and `historical_runs/v0_6_0/` (summary CSVs,
  charts, generated report).
* Historical v0.5.1 files, hash-pinned by tests: `forecast_inputs/base_forecast_inputs.yaml`,
  `author_prior_scenario.yaml`, `src/asi_forecast/{model,monte_carlo,uncertainty}.py`.

## Data Sources and Provenance

`evidence_tables/v0_6_evidence_2026.csv` has one row per source. Each row records the
claim, date, URL, evidence type, the proposition it supports, scope, uncertainty,
correlation group, the variable it affects, and its verification status. Primary
sources include METR, the Anthropic system cards and RSI essay, the OpenAI research
post and the GPT-6 Astra system card, Epoch AI, Forethought, AI Futures, EO 14409 and
arXiv 2609.25050.

Some rows were verified only from search-index excerpts or secondary reports:
* the Princeton shadow evaluation (via MIT Technology Review);
* the Huang quote;
* the Metaculus snapshot;
* the Mythos 5.1 card text;
* AlphaEvolve (pre-cutoff knowledge, not re-fetched).

Earlier AI-generated notes (ANSWERS.txt, GEMENI_01.txt, asi.txt, perplexity.txt) were
used as leads only.

## Decisions and Rationale

* **Historical model preserved.** v0.6 is a new engine and YAML, not an edit of v0.5.1.
* **Lags are emergent.** Lag times come from feedback dynamics (Jones/Davidson
  semi-endogenous form with an Amdahl automation fraction), not from fixed delays.
* **Compute cap placement.** The compute-bottleneck cap applies to the
  progress-rate speed-up, matching the semantics in Epoch and Forethought.
* **Regime consistency.** Recursive-regime parameters must produce superlinear
  dynamics (≥75% of un-paused draws); this is tested.
* **Infrastructure friction removed.** The calendar compute path with a post-2028
  slowdown replaces it, because the old friction term double-counted the compute
  trend.
* **Explicit judgement inputs.** P(H2)=0.10 and P(paradigm wall)=0.10 are stated as
  judgement inputs rather than hidden in a late tail.
* **Classification excludes compute.** Dynamics are classified on the software
  (AI-R&D) rate, so exogenous compute growth does not dilute the loop signal.

## Verification and Test Results

All results below were actually executed on 2026-10-06:
* `pytest`: 62 passed (37 pre-existing and 25 new).
* `asi-forecast run --target both --sims 10000` and `--sims 100000`: medians are
  identical to the month (AGI 2029-01, internal ASI 2032-04).
* `asi-forecast drivers --sims 100000 --sensitivity-sims 40000`: completed.
* `asi-forecast report --sims 100000 --sensitivity-sims 40000 --results-dir historical_runs/v0_6_0`:
  completed.
* A 500,000-simulation run matched the 100,000-simulation quantiles.
* Three seeds gave identical medians.
* Batch-median ranges are ≤1 month.
* There are no censored draws, and no ordering violations in 100k draws (tested).

## Known Failures and Limitations

* **Unmeasurable dominant inputs.** The ASI capability gap (OOM) and the AGI
  threshold are judgement inputs, and they dominate together with the horizon trend.
* **Judgement likelihoods.** The regime likelihood ratios are judgements, not fitted
  likelihoods.
* **Narrow A_R&D interval.** The reported interval (0.28–0.40) is too narrow because
  component weights are fixed.
* **Saturating horizon metric.** METR's horizon metric is saturated above 16h, so the
  current-horizon input relies on extrapolation.
* **Simplified pauses and release.** Pauses are added to the final date rather than
  interrupting the dynamics, and deployment is a two-branch mixture.
* **No physical-world gate.** There is no robotics gate; wet-lab science is covered
  only by the demonstration lag.
* **Secondary sourcing.** Some evidence comes from secondary or search-excerpt sources
  (flagged per row).

## Risks and Technical Debt

* **Two engines coexist.** The v0.5 report and plot code (`write_report.py`,
  `charts.py`) is still used only by the historical engine.
* **Partial scenario fix.** The v0.5.1 `fast`/`slow` scenario-scaling bug is
  documented but deliberately not fixed, to preserve the historical model.
* **Uncapped inputs.** The `asi_gap_oom` and `agi_threshold_hours` distributions should
  be revisited when new measurements exist (for example METR's next suite, or lab
  AI-R&D acceleration metrics).

## Current Blockers

None for the code. The forecast is limited by evidence that does not exist yet,
chiefly any measured AI-attributable acceleration and longer-horizon task suites.

## Exact Next Actions

1. Review and merge PR `v0.6-recalibration` into `main`.
2. When METR publishes a new long-task suite, or a lab reports an AI-attributable
   slope change, update `current_horizon_hours`, `doubling_months` and
   `regime_evidence`, then rerun `asi-forecast report`.
3. Replace the judgement-based regime likelihood ratios with a fitted model of lab
   acceleration metrics once two or more frontier generations of AECI-style data are
   public.
4. Widen the A_R&D decomposition with uncertain component weights (for example a
   Dirichlet distribution).
