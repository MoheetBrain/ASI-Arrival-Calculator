# v0.5.1 Model Audit (written before any v0.6 change)

Audited commit: `a33ad3e` (main, v0.5.1). Audit date: 2026-10-06.
Unchanged-model outputs are archived in `historical_runs/v0_5_1_unchanged/`
(100,000 sims, seed 42). Those numbers are reproduced below.

```text
CURRENT MODEL
-------------
AGI definition:
  "Perform or automate a very wide range of economically valuable cognitive
  tasks at approximately top-human or expert-human level" (agi_definition.yaml).
  Not operationalised: no threshold metric is attached to it. Operationally, AGI
  in the code is just "a sampled task-horizon gate plus sampled lags".

ASI definition:
  "Outperform top human teams across most important cognitive work, including AI
  research, SWE, science, maths, cyber, strategy, long-horizon autonomy."
  Also not operationalised; internal ASI = AGI + sum of sampled lags.

AGI causal variables:
  effective_compute_growth (lognormal 3.0-4.5x/yr), algorithmic_efficiency
  (lognormal 2.2-5.0x/yr), METR doubling time (tri 4/7/14 mo), current horizon
  (tri 2/8/40 h), coding threshold (tri 160/320/1000 human-h), general-capability
  lag (gamma 1-12 mo), integration lag (tri 0/6/18), compute-governance friction
  (tri 0/3/12).

AGI -> ASI variables:
  AI R&D automation lag (lognormal 0-8 mo), superhuman-AI-researcher lag
  (gamma 1-12), takeoff lag (lognormal 2-24), phase overlap (beta 0.30-0.85,
  multiplies the sum of those three by 1-overlap), infrastructure friction
  (lognormal 12-60, NOT compressed).

Current equations:
  d_adj   = d_METR * (log2(3.4*3.0) / log2(C*A))^0.5
  coding  = d_adj * log2(threshold / H0)
  longhz  = d_adj * log2(168 / H0)
  general = coding + gen_lag
  AGI     = max(coding, longhz, general) + integ_lag + compute_gov
            then with p=0.15: AGI = max(AGI, 2040 + LN(median 12y, sigma 0.76))
  iASI    = AGI + (rnd + sar + takeoff)*(1-overlap) + infra
  pASI    = iASI + deployment_delay + secrecy_delay

Current distributions: see forecast_inputs/base_forecast_inputs.yaml.
Current dependencies: Iman-Conover rank correlation on (compute, algo, doubling)
  only. Everything else independent, including all post-AGI lags.
Current scenario assumptions: single base scenario; `fast`/`slow` scale low/mode/
  high fields only (they do NOT move mean/std, so lognormal/gamma/beta params
  are unaffected by the scenario scaling - a latent bug).

Parameters supported by direct empirical evidence:
  METR doubling time & current horizon; compute growth; algorithmic efficiency;
  grid-interconnection lead times (for infra friction).
Parameters based on expert forecasts:
  long-tail sigma (ESPAI/XPT fit), bio-anchor median year (Cotra 2052),
  phase overlap (Davidson FTM output).
Parameters based on author judgement:
  coding threshold hours, general-capability lag, integration lag, dampening
  exponent 0.5, long-horizon 168h gate, all governance delays, secrecy delay.
Parameters explicitly aggressive / stress-test:
  ai_rnd lag (stress_test), SAR lag (stress_test), takeoff lag (aggressive),
  general-capability lag (aggressive).

Largest drivers of the existing forecast:
  AGI: METR doubling time (rho ~ dominant), then compute/algo via the adjusted
  doubling, then current horizon. Internal ASI: doubling time, then
  infrastructure friction (83% of the median AGI->ASI lag).

Largest apparent weaknesses:
  1. The AGI->ASI lag has a HARD 12-month floor: P(lag<12mo)=0.000 by
     construction (infra lognormal low=12, added uncompressed). The README calls
     this a "fast-takeoff regime", but 83% of the median lag is a post-AGI
     datacentre build that is assumed to START only after AGI. Infrastructure
     is in fact being built continuously pre-AGI; this is mis-specified.
  2. The max-gate is degenerate: `general` = coding + lag >= coding always, and
     the 168h long-horizon gate is always below the 320h coding gate, so the
     binding gate is "general" in 100% of draws. The long-horizon gate is dead.
  3. Long-tail mixture creates an artefact: AGI CDF is flat at 0.851 from 2035
     to 2040, then resumes. 15% of mass is teleported to >=2040 regardless of
     the rest of the model; the late tail is not causally linked to anything.
  4. No feedback: AI-R&D automation cannot affect anything pre-AGI, and post-
     AGI lags are independent fixed delays, not capability-dependent. There is
     no takeoff regime variable and no way to represent a self-limiting vs
     superlinear loop.
  5. P(AGI <= 2028) = 0.6% and P(AGI already exists) = 0 by construction:
     the start month (2026-06) is a hard floor and additive lags (integration
     0-18 + compute-gov 0-12 + general 1-12) put a ~1.5-year minimum on top of
     the coding gate.
  6. Doubling-time prior (mode 7 mo) uses the 2019-2024 long-run rate while
     the source row itself notes 2024-2025 models give ~3.5-4 mo.
  7. `fast`/`slow` scenarios do not scale mean/std of non-triangular inputs.
  8. Internal ASI ignores everything except a sum of lags - no multidomain
     criterion (maths, science, cyber) is represented.

Potential double-counting:
  - compute_governance_friction and agi_integration_lag are added on top of a
    trend extrapolation (METR) that already embeds historical integration and
    permitting frictions.
  - infrastructure_friction double-counts the compute trend: compute growth
    already reflects datacentre buildout; adding a fresh 12-60 mo build after
    AGI assumes no pre-built capacity exists.
  - compute/algo enter both through the doubling rescale (exponent 0.5) AND via
    the -0.70/-0.55 rank correlations with the doubling time itself.

Missing 2026 evidence (as of the v0.5.1 tables, last dated 2026-06-29):
  - Any METR measurement after Feb 2026; any 2026 H2 frontier model.
  - Any direct AI-R&D-automation measurement (lab surveys, RE-Bench-style
    results, AlphaEvolve-style closed-loop results, lab "automated researcher"
    goals and whether they were met).
  - Leader statements are placeholders (no quotes, no dates).
  - Prediction-market / Metaculus values are undated placeholders.
  - Counter-evidence (uplift RCTs, reliability/messy-task gaps) is absent.
```

## Unchanged-model reproduction (seed 42, 100,000 sims)

| Target | p5 | p10 | p25 | p50 | p75 | p90 | p95 |
|---|---|---|---|---|---|---|---|
| AGI | 2029-08 | 2029-12 | 2030-08 | 2031-07 | 2032-12 | 2048-10 | 2056-11 |
| Internal ASI | 2031-12 | 2032-05 | 2033-03 | 2034-05 | 2036-02 | 2051-07 | 2059-08 |
| Public ASI | 2033-05 | 2033-10 | 2034-09 | 2035-11 | 2037-08 | 2053-01 | 2061-03 |

AGI->internal-ASI lag: mean 33.5 mo, median 30.9 mo; P(<3 mo)=P(<6)=P(<12)=0.000,
P(<24)=0.172, P(<60)=0.961, P(>120)=0.000.

Cumulative P(by end of year):

| Year | AGI | Internal ASI | Public ASI |
|---|---|---|---|
| 2026 | 0.000 | 0.000 | 0.000 |
| 2027 | 0.000 | 0.000 | 0.000 |
| 2028 | 0.006 | 0.000 | 0.000 |
| 2029 | 0.104 | 0.000 | 0.000 |
| 2030 | 0.359 | 0.003 | 0.000 |
| 2031 | 0.608 | 0.050 | 0.002 |
| 2032 | 0.756 | 0.204 | 0.025 |
| 2033 | 0.822 | 0.423 | 0.128 |
| 2034 | 0.844 | 0.616 | 0.317 |
| 2035 | 0.850 | 0.742 | 0.525 |
| 2036 | 0.851 | 0.808 | 0.682 |
| 2040 | 0.851 | 0.851 | 0.848 |
| 2045 | 0.877 | 0.857 | 0.852 |
| 2050 | 0.917 | 0.895 | 0.883 |
