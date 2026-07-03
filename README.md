# The “Exam Deadline” Hypothesis: A Structural Monte Carlo Forecast of AGI and ASI Arrival

## Abstract

This project presents an open-source structural Monte Carlo forecast of Artificial General Intelligence (AGI) and Artificial Superintelligence (ASI) arrival. The aim is not to claim certainty about a single date, but to replace vague timeline claims with an auditable probabilistic model whose assumptions, equations, and outputs can be inspected and challenged.

The current v0.5.0 model forecasts AGI first, then models the uncertain transition from AGI to internal capability-and-agency ASI, and finally from internal ASI to public visibility or deployment. Under the current recalibrated parameter set, the model gives a median AGI arrival of **July 2031**, a median internal ASI arrival of **May 2034**, and a median public ASI visibility/deployment date of **November 2035**. The median AGI-to-internal-ASI transition is approximately **2.6 years**.

The forecast should be interpreted as a conditional result of the model assumptions, not as a definitive prediction. The repository is designed for adversarial review: all key assumptions are exposed, the code is reproducible, and the model can be rerun or modified by critics.

GitHub repository / working branch:
https://github.com/MoheetBrain/ASI-Arrival-Calculator/pull/1

---

## 1. Motivation

A persistent weakness in AI safety, governance, and public discussion is the reliance on vague timeline claims such as “AGI in 5–20 years” or “superintelligence before the end of the decade.” Such claims are difficult to audit because they often hide the underlying causal structure.

The “Exam Deadline” hypothesis starts from a simple idea: if the arrival of AGI or ASI is decision-relevant, then vague forecasts are not enough. Policy, safety, infrastructure, and alignment planning require more precise probabilistic timelines, even if the precision must be framed honestly.

This project therefore asks:

> Given explicit assumptions about compute growth, algorithmic efficiency, agent reliability, AI R&D automation, takeoff dynamics, infrastructure friction, and governance delay, what month-level probability distribution follows for AGI and ASI arrival?

The central contribution is not the exact date. The contribution is the auditable forecasting engine.

---

## 2. Definitions

### Artificial General Intelligence

In this project, AGI means an AI system that can perform or automate a very wide range of economically valuable cognitive tasks at approximately expert-human or top-human level. This includes software engineering, analysis, research assistance, planning, computer use, and general problem-solving across novel domains.

### Capability-and-agency ASI

Capability-and-agency ASI means an AI system or AI-agent system that can outperform top human teams across most important cognitive work, including AI research, software engineering, scientific discovery, mathematics, cybersecurity, strategy, and long-horizon autonomous tasks. It must also generalise to novel tasks and pursue objectives using planning, memory, tool use, self-correction, and coordination.

This definition does not require proof of consciousness, emotion, or subjective experience. Those questions are important, but they are not used as the primary forecast target because they are not currently measurable in a way that would make the model auditable.

---

## 3. Forecast outputs

The current v0.5.0 recalibrated model gives the following median forecasts:

| Forecast target                    |   Median date |
| ---------------------------------- | ------------: |
| AGI arrival                        |     July 2031 |
| Internal capability-and-agency ASI |      May 2034 |
| Public ASI visibility/deployment   | November 2035 |
| AGI → internal ASI lag             |    ~2.6 years |
| Probability AGI arrives after 2060 |         ~3.8% |

These dates are month-level medians. A median forecast means that, under the current model assumptions, half of simulated futures arrive before that month and half arrive after it.

The model does not claim that AGI or ASI will definitely arrive in those months.

---

## 4. Method summary

The model uses a structural Monte Carlo pipeline rather than a trained AI model. This is deliberate. There is no historical dataset of previous ASI arrivals, so training a black-box machine learning model to predict ASI arrival directly would be methodologically weak.

Instead, the model uses a manually specified causal structure with uncertain parameters. It samples many possible futures from probability distributions over those parameters, then reports the resulting distribution over arrival months.

The model separates the forecast into stages:

1. Strong coding automation
2. Long-horizon agent reliability
3. Broad AGI capability
4. AI R&D automation
5. Superhuman AI researcher capability
6. Accelerated / recursive AI progress
7. Internal capability-and-agency ASI
8. Public ASI visibility/deployment

The core structure is:

AGI arrives when the model crosses the strongest bottleneck among coding automation, long-horizon agency, and general capability.

Internal ASI arrives after AGI plus the compressed AGI-to-ASI transition, with physical infrastructure friction added separately.

Public ASI arrives after internal ASI plus deployment governance and secrecy/visibility delay.

---

## 5. Core equations

The current model uses the following simplified structure:

```text
AGI_month =
  max(
    coding_automation_month,
    long_horizon_agent_month,
    general_capability_month
  )
  + agi_integration_lag
  + compute_governance_friction
```

```text
raw_research_takeoff_lag =
  ai_rnd_automation_lag
  + superhuman_ai_researcher_lag
  + takeoff_lag
```

```text
effective_research_takeoff_lag =
  raw_research_takeoff_lag × (1 - phase_overlap_coefficient)
```

```text
internal_ASI_month =
  AGI_month
  + effective_research_takeoff_lag
  + infrastructure_friction
```

```text
public_ASI_month =
  internal_ASI_month
  + deployment_governance_delay
  + secrecy_visibility_delay
```

The model explicitly separates physical infrastructure friction from software/R&D phase overlap. This matters because software research stages may overlap, but data centres, power constraints, hardware procurement, and deployment infrastructure cannot simply be compressed away by faster research loops.

---

## 6. Monte Carlo design

The model uses Monte Carlo simulation to generate many possible futures. Each run samples values for uncertain variables such as compute growth, algorithmic efficiency, agent task-horizon growth, AI R&D automation lag, takeoff lag, infrastructure friction, governance delay, and visibility delay.

The current implementation includes:

* lognormal, gamma, beta, and triangular distributions
* bounded support for sampled variables
* Iman-Conover rank-correlation induction to preserve non-normal marginals while introducing dependency between macro variables
* an AGI-date long-tail mixture to avoid assigning zero probability to very late arrival
* deterministic tests checking timeline ordering, including public ASI ≥ internal ASI ≥ AGI

The v0.5.0 branch reports 33 passing tests. These tests verify software consistency and invariants, not scientific truth.

---

## 7. Why AGI and ASI are separated

The model deliberately forecasts AGI and ASI separately.

Most available evidence is about AGI, AI agents, coding benchmarks, compute scaling, benchmark progress, or AI R&D automation. Much less evidence directly measures ASI. Treating AGI evidence as direct ASI evidence would overclaim.

The model therefore uses the following structure:

```text
AGI
  → AI R&D automation
  → superhuman AI researcher
  → accelerated / recursive AI progress
  → internal ASI
  → public ASI
```

This distinction is central to the project. AGI is not assumed to equal ASI. The AGI-to-ASI lag is explicitly modelled as an uncertain distribution.

---

## 8. Current interpretation of the result

The current output says:

> Under the v0.5.0 recalibrated assumptions, the model’s median forecast is AGI in July 2031, internal ASI in May 2034, and public ASI visibility/deployment in November 2035.

The most important interpretation is not merely the date. The important result is that the model implies a compressed AGI-to-ASI transition under an aggressive AI R&D automation regime.

The current median AGI-to-internal-ASI lag is approximately 2.6 years. This is much shorter than a slow-takeoff view, but it remains conditional on the model’s assumptions about AI R&D automation, phase overlap, task-horizon progress, and takeoff dynamics.

---

## 9. Important limitations

This model is not a peer-reviewed consensus forecast.

The current model should be read as an auditable experimental prototype. Its key limitations are:

1. Some parameters remain evidence-light or judgement-based.
2. The evidence tables require further calibration and citation hardening.
3. The phase-overlap coefficient is highly influential.
4. The task-horizon / compute / algorithmic-efficiency relationship is difficult to decompose cleanly.
5. Coding automation is still represented structurally rather than through a fully calibrated benchmark-to-time model.
6. Monthly precision should not be mistaken for certainty. Month-level output is used because the model operates over month-indexed distributions, not because the exact month is known.
7. The model has not yet been fully backtested against historical AI capability milestones.
8. Passing software tests does not prove that the scientific assumptions are true.

The safest interpretation is:

> This is an auditable structural scaffold showing how a compute/METR-style short-timeline worldview propagates into AGI and ASI arrival distributions under explicit assumptions.

---

## 10. What changed in v0.5.0

The v0.5.0 recalibration materially changed the forecast.

Compared with the previous version:

| Target        | Earlier version | v0.5.0 recalibrated |
| ------------- | --------------: | ------------------: |
| AGI           |      March 2032 |           July 2031 |
| Internal ASI  |   December 2036 |            May 2034 |
| Public ASI    |     August 2038 |       November 2035 |
| AGI → ASI lag |      ~4.5 years |          ~2.6 years |
| P(AGI > 2060) |           ~4.1% |               ~3.8% |

The pull-forward is mainly caused by shorter cognitive lags for AI R&D automation, superhuman AI researcher capability, and takeoff, combined with a higher phase-overlap coefficient. Infrastructure friction increased, but the cognitive-lag compression dominated the physical-friction increase.

This is a major model sensitivity and should be treated as an object of criticism rather than hidden.

---

## 11. Reproducibility

The code is open-source and intended to be run locally. The model is designed so that critics can:

* inspect the YAML assumptions
* change parameter distributions
* rerun the Monte Carlo engine
* compare fast/base/slow scenarios
* inspect forecast drivers
* audit the equations
* challenge the evidence tables
* submit pull requests or critiques

GitHub:
https://github.com/MoheetBrain/ASI-Arrival-Calculator/pull/1

The current v0.5.0 branch was committed as:

```text
commit: 01a4b4a
branch: v0.5-empirical-recalibration
tests: 33 passing
```

---

## 12. Safe public claim

The strongest honest claim is:

> This repository presents an auditable structural Monte Carlo model for forecasting AGI and ASI arrival months. Under the current v0.5.0 recalibrated assumptions, the model’s median forecast is AGI in July 2031, internal capability-and-agency ASI in May 2034, and public ASI visibility/deployment in November 2035. These dates are conditional outputs of the model, not claims of certainty.

Unsafe claim:

> AGI will happen in July 2031 and ASI will happen in November 2035.

That is not what the model proves.

---

## 13. Conclusion

The “Exam Deadline” hypothesis argues that AI timeline forecasting should move from vague verbal estimates to auditable probabilistic models. This project implements that idea as a public structural Monte Carlo forecasting engine.

The current model forecasts AGI in July 2031, internal ASI in May 2034, and public ASI in November 2035 under the v0.5.0 recalibrated assumptions. These outputs should be treated as conditional and criticisable. The project is designed to invite adversarial review, not to close the debate.

The next scientific step is to harden the evidence tables, calibrate the most sensitive variables, and compare the model against external forecasts from Metaculus, AI Impacts, Epoch-style analyses, and other timeline models.
