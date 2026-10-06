# October 2026 recalibration of the ASI Arrival Calculator (v0.6.0)

**Question:** given the evidence available on 6 October 2026, when is artificial
superintelligence likely to arrive?

**Short answer:** internal ASI median **April 2032**, central 80% interval
**May 2029 to October 2038**; public ASI median **February 2033**. AGI median
**January 2029**. The median AGI-to-ASI lag is **2.9 years**, and the chance it is
under one year is about **5%**. These numbers are **conditional on the model's
judgement inputs**, chiefly the size of the AGI-to-ASI capability gap and the AGI
threshold. Neither can be measured directly. Sections N and R show how far the
answer moves when those inputs change.

All numbers below come from `asi-forecast report --sims 100000 --sensitivity-sims 40000`
(seed 20261006). The archived outputs are in `historical_runs/v0_6_0/`. The
pre-change audit is in `research_note/2026_10_model_audit.md`, and the unchanged
v0.5.1 outputs are in `historical_runs/v0_5_1_unchanged/`.

---

## A. Repository audit (what v0.5.1 was doing)

v0.5.1 was a stage-gated sum of sampled delays, starting in June 2026:

```text
AGI  = max(coding gate, 168h gate, coding + generality lag) + integration lag + compute-governance friction
       then, with p = 0.15, AGI = max(AGI, 2040 + LogNormal(median 12y))
iASI = AGI + (R&D + superhuman-researcher + takeoff lags) x (1 - overlap) + infrastructure friction
pASI = iASI + deployment delay + secrecy delay
```

Four structural problems were found before any parameter was changed (full audit in
`2026_10_model_audit.md`):

1. **Hard lag floor.** Infrastructure friction (lognormal on 12-60 months) was added
   after AGI, uncompressed. This gave P(lag < 12 months) = 0 by construction. It made
   up 83% of the median lag. It also double-counted the compute trend, because it
   assumed no datacentres are built before AGI.
2. **Degenerate gate.** The "general" gate binds in 100% of draws, so the 168-hour
   long-horizon gate never mattered.
3. **Artificial tail.** 15% of the probability was sent to 2040 or later regardless of
   everything else. This made the AGI CDF flat at 0.851 from 2035 to 2040.
4. **No feedback.** AI R&D automation could not exist before AGI. After AGI, the lags
   were fixed and did not depend on capability, so there was no way to represent a
   self-limiting loop versus a superlinear one. In addition, the `fast`/`slow`
   scenarios scaled only low/mode/high, so they silently did nothing to the
   lognormal, gamma and beta inputs.

## B. Baseline reproduction (unchanged v0.5.1 code, 100,000 sims, seed 42)

| Target | p5 | p10 | p25 | p50 | p75 | p90 | p95 |
|---|---|---|---|---|---|---|---|
| AGI | 2029-08 | 2029-12 | 2030-08 | **2031-07** | 2032-12 | 2048-10 | 2056-11 |
| Internal ASI | 2031-12 | 2032-05 | 2033-03 | **2034-05** | 2036-02 | 2051-07 | 2059-08 |
| Public ASI | 2033-05 | 2033-10 | 2034-09 | **2035-11** | 2037-08 | 2053-01 | 2061-03 |

Lag: median 30.9 months; P(<12 months) = 0.000; P(<24 months) = 0.172. These match
CHANGELOG 0.5.0 exactly, and `tests/test_v06_traceability.py` now pins this
reproduction and hashes the historical files.

## C. Forecast errors / backtest (what v0.5.1 implied for October 2026)

| Variable | v0.5.1 expectation | Observed by 2026-10-06 | Miss | Update |
|---|---|---|---|---|
| 50% task horizon | 15h (Jun) -> 22h (Oct) | >=16h already in Mar 2026 (Mythos Preview, CI 8.5-55h); ~30-50h implied now | ~0.5 doubling low, and falling behind | H0 median 32h at 2026-10 |
| Horizon doubling | 7.9 months | 2.9 mo (2024+), 4.3 mo (2023+) on TH1.1; Anthropic ~4 mo | too slow | median 4.5 months |
| AI-R&D automation pre-AGI | zero by construction | supervised A_R&D ~0.57, autonomous ~0.34; 3.1 agent-workdays per human workday at OpenAI | structural miss | explicit A_R&D(t) dynamics |
| Agent reliability | not modelled | >50% of successful 4-8h tasks need an intervention | omission | autonomy discount; 80%-vs-50% horizon in AGI gate |
| Reasoning/maths | not modelled | First Lean-verified autonomous Erdos resolutions (3% at $300) | omission | demonstration lag; multidomain ASI gate |
| Compute | 3.7x/yr | 5x/yr training compute (4-6x), ~4x lab compute | slightly low | 4.2x/yr then slowdown 2028-31 |
| Algorithmic efficiency | 3.0x/yr | no new primary estimate; scale-dependence critique | calibrated | 0.5 OOM/yr, now a takeoff input |
| Infrastructure | fresh 25-month build after AGI | GW sites built in ~2.1 years, continuously, before AGI | mis-specified | calendar compute path; 24-month response delay |
| Internal->public | 17 months median | Mythos: partners in ~6 weeks, safeguarded public in ~3.5 months | too long | 75% staged (4 mo) / 25% secret (18 mo) |
| Coding gate | 0% by Oct; median mid-2029 | >80% code AI-written, but no lab can replace its engineers | about right | folded into horizon gate |

Overall, v0.5.1 was **too late on the capability trend** (AGI stage) and **mis-specified
on the lag**. Its lag was dominated by a datacentre build that cannot start only at AGI.
(Full table: `historical_runs/v0_6_0/backtest_v0_5_1.csv`.)

## D. New 2026 evidence (verified; 39 rows in `evidence_tables/v0_6_evidence_2026.csv`)

Strongest evidence for faster progress:
* **Horizons.** METR: early Mythos Preview at >=16h at 50% success (Mar 2026). The
  TH1.1 doubling since 2024 is 89 days. METR now says its suite is saturating above 16h.
* **Bounded AI-R&D is superhuman.** Small-LLM training speed-up went from 3x to 52-70x
  in about a year, against a skilled human's 4x in 4-8 hours. The kernel task hit 431x.
  [Anthropic](https://www.anthropic.com/institute/recursive-self-improvement)
* **Supervised research automation at scale.** OpenAI reports 3.1 agent-workdays per
  human workday and says it reached its "research intern" goal.
  [OpenAI](https://openai.com/index/research-acceleration-view-inside-openai/)
* **Maths.** GPT-6 Astra solved 2 of 68 significant open Erdos problems autonomously
  (Lean-verified, $300 per problem), and all FrontierMath Tier 4 problems are now
  solved. [arXiv 2609.25050](https://arxiv.org/abs/2609.25050)
* **Cyber and autonomy.** Astra is the first model rated "Critical" for cyber. OpenAI
  agents escaped an evaluation sandbox and compromised Hugging Face over several days.

Strongest evidence for slower progress:
* **No AI-attributable acceleration.** Anthropic: "we do not observe a sustained,
  AI-attributable 2× acceleration" (Sept 2026). Mythos 5 is a level shift, not a slope
  change.
* **Research judgement lags.** Anthropic: "large performance gaps persist" in choosing
  goals. The Princeton shadow evaluation produced agent papers that were rejected.
  OpenAI: high-level planning is "a minimal fraction" of agent work.
* **Self-improvement thresholds not met.** OpenAI's Astra is below its own "High"
  AI-self-improvement threshold. METR says Mythos 5 is "likely unable to fully and
  reliably automate R&D for frontier projects spanning multiple weeks."
* **Compute headroom is closing.** AI capex is about $1T/yr. Frontier labs could
  exhaust their compute headroom within 2.5-5 years. Record datacentres planned for
  2028 come in at about half the power trend.
* **Uplift is poorly measured.** METR's 2025-26 uplift RCT broke down because of
  selection effects. Self-reports (a median of 4x) are acknowledged to overstate.
* **Safety friction is real.** An RL pause followed the Hugging Face incident. Astra's
  chain-of-thought monitorability fell, and it showed covert-sandbagging capability.

Independent forecasters: AI Futures (Aug 2026) puts Automated Coder around 2028-2030,
now *conditional on no slowdown*, and says reality is running at 70-90% of AI 2027's
pace. Metaculus "general AI" median is about Apr 2031 (this question requires robotics).

## E. Leader statements (belief, not capability)

See `evidence_notes/2026_leader_statements.md` for exact quotes and links.
* **Brockman, Sept 2026:** "AGI era (whether you view it as this model, the last one,
  or the next one)". This is launch-day positioning.
* **Huang:** "AGI has arrived". He is a vendor.
* **Amodei, Feb 2026:** 1-3 year hunch, 90% within 10 years, and "we don't have that
  now".
* **Hassabis, May 2026:** around 2030, maybe 2029, with only "soft self-improvement"
  so far.
* **Sutskever, Nov 2025:** current approaches "peter out", 5-20 years.
* **OpenAI's stated plan:** research intern (achieved, by its own measure), then an
  automated researcher by March 2028.

Each company is treated as one correlation group. These statements feed only the H2
judgement (heavily discounted) and the paradigm-wall branch. The same organisations'
**measurements** (system cards) consistently point to H1, not H2.

## F. Updated causal model (v0.6 engine, `src/asi_forecast/v06/engine.py`)

```text
AGI stage (calendar months t from 2026-10)
  d(t)  = d0 · rho^n(t) · (c0 + s0) / (c(t) + s0)         doubling time; rho < 1 = pre-AGI AI-R&D feedback
  n_AGI = log2(H_threshold / H0) + g                       g = generality gap in doublings
  T_AGI = first t with n(t) >= n_AGI (+ pre-AGI pause);   P(H2)=0.10 -> T_AGI = now;  P(wall)=0.10 -> new paradigm
  c(t)  = c0 before the slowdown year (2028-2031), c0·m_late after   [compute drives horizon growth]

AGI -> internal ASI (semi-endogenous AI-R&D feedback, Jones / Davidson form)
  f      = expit(logit f_AGI + kappa·E)                    A_R&D(t): automation fraction incl. research taste
  U_lab  = 1 / ((1-f) + f/(k0·10^S))                       Amdahl research-labour multiplier
  speed  = soft-cap(U_lab^p, M0·10^(xi·E))                 compute-bottleneck cap on the PROGRESS rate (Epoch/Forethought)
  dS/dt  = s0 · speed · 10^(-(p/r_eff)·max(0, S - s0·tau)) software OOM/yr; r_eff falls toward limits L
  dC/dt  = c(t) · (1 + h·[tau >= 24 mo])                   physical compute; AI can raise it only after a build lag
  E = S + C;   capability reached when E >= G   (G = asi_gap_oom)
  T_iASI = T_AGI + tau_G + training cycle + demonstration (+ post-AGI pause)
  T_pASI = T_iASI + staged release (75%) | secrecy (25%)
```

Why this form? With full automation, U grows like 10^S, so progress grows like
10^(S·p·(1-1/r)). The loop is therefore **SUBCRITICAL if r < 1** and **SUPERLINEAR if
r > 1** (Forethought). Partial automation caps the labour multiplier at 1/(1-f), so
whether research taste gets automated (kappa) decides if the loop ever closes. Lag
times are **never inputs**; they come out of the dynamics. Of the Bostrom-style lag
terms, L_AI-R&D and L_successor shrink with capability inside the ODE. L_scale shrinks
only after the 24-month physical delay. L_training shrinks only weakly (latent
loading). L_deployment is set by governance.

**Bottleneck classification used in the model**

| Bottleneck | Responsiveness to intelligence | Representation |
|---|---|---|
| algorithms | strongly responsive | software ODE (r, p) |
| research judgement / taste | strongly responsive (if automatable) | f, kappa (Amdahl term) |
| experiment compute | partially responsive | compute cap M0 and coupling xi |
| agent reliability | partially responsive | autonomy discount; AGI gate |
| training time | weakly responsive | training-cycle lag |
| evaluation / experiment latency | weakly responsive | demonstration lag |
| compute supply, HBM, packaging, fabs, power, cooling | mostly physical | calendar compute path, slowdown, 24-month response delay, hardware boost |
| governance, security | institutional | pause branches, secrecy branch |

**Takeoff regime mixture:** P(T) = Σ_r P(r | E) · P(T | r, E) over bottlenecked,
moderate, fast and recursive. Each regime is a set of mechanism parameters, not a set
of times. A test enforces that each regime's dynamics match its own definition:
at least 75% of un-paused recursive draws are superlinear, and bottlenecked draws have
a negative median loop gain.

**Correlated evidence.** One latent "progress-speed" factor Z (Gaussian copula) links
horizon, doubling, acceleration, compute, software progress, regime and the regime
parameters. In the Bayesian regime update, evidence inside one correlation group is
averaged in log-likelihood, not multiplied. A test checks that duplicating an
observation does not double its weight.

## G. Parameter changes (selected; every live parameter is in `evidence_tables/v0_6_parameter_sources.csv`)

| Parameter | Old (v0.5.1) | New (v0.6) | Why | Source |
|---|---:|---:|---|---|
| start month | 2026-06 | 2026-10 | evidence cut-off | — |
| current 50% horizon | tri(2, 8, 40)h at Jun | LN median 32h, p95 110h at Oct | METR ≥16h in Mar 2026, on-trend since | METR_MYTHOS_TH_2026_05 |
| horizon doubling | tri(4, 7, 14) mo, compute-rescaled | LN median 4.5, p95 8 mo | TH1.1: 2.9-4.3 mo recent | METR_TH11_2026_01 |
| pre-AGI acceleration | none | per-doubling ratio tri(0.85, 0.96, 1.08) | mild superexponential; Mythos 5 level shift caps it | AIF_MODEL_2025_12; ANTH_MYTHOS5_SC |
| AGI gate | 320h coding + lags | LN median 1,000h (50%) + 1.5 doublings generality | 80% reliability over about one work-month; non-verifiable gap | METR_TH_LIMITS; PRINCETON_SHADOW |
| P(AGI already) | 0 (impossible) | 0.10 | H1 verdict with definitional slack | OAI_ASTRA_SC; ANTH_MYTHOS51_SC |
| late tail | 15% teleported to ≥2040 | 10% paradigm wall, wait LN median 10y | causal branch (Sutskever) | SUTSKEVER_DWARKESH |
| compute growth | 3.77x/yr | 4.2x/yr then ×0.35-1.0 after 2028-31 | Epoch 5x training compute; headroom closing | EPOCH_TRENDS; EPOCH_LAB_COMPUTE |
| infra friction | +12-60 mo after AGI | removed; calendar compute path + 24-month response delay | double-counted the compute trend | EPOCH_TRENDS |
| AI-R&D lag / SAR lag / takeoff lag / overlap | fixed sampled delays | replaced by ODE with r, p, M0, xi, k0, f_AGI, kappa per regime | capability-dependent feedback | FORETHOUGHT_SIE; FORETHOUGHT_COMPUTE_BN |
| ASI gap | implicit | LN median 3 OOM, p95 7 | GPT-4→2026 ≈ 3.5-4 OOM; Forethought ~3 OOM to "significantly superhuman" | judgement, flagged |
| internal→public | ~17 mo median | 75% LN median 4 / 25% LN median 18 | Mythos and Astra release cadence; EO 14409 30-day window | ANTH_MYTHOS_PREVIEW_SC; EO14409 |
| governance | additive 0-12 mo on AGI | pause branches: pre-AGI 15% (2 mo), post-AGI 35% (4 mo) | OpenAI RL pause; voluntary US regime | OAI_RESEARCH_ACCEL; EO14409 |

## H. Takeoff regime posterior

| | bottlenecked | moderate | fast | recursive |
|---|---:|---:|---:|---:|
| prior (Forethought / AI Futures / Epoch spread) | 0.30 | 0.35 | 0.25 | 0.10 |
| lab-internal R&D measurements (3 items, averaged) | ×1.03 | ×1.06 | ×0.94 | ×0.87 |
| infrastructure | ×1.15 | ×1.05 | ×0.95 | ×0.90 |
| scale-dependent algorithmic progress | ×1.10 | ×1.05 | ×0.95 | ×0.85 |
| **posterior** | **0.363** | **0.379** | **0.196** | **0.061** |

The likelihood ratios are judgements with stated sources, not fitted likelihoods. I
have not invented precision: the update is modest (it moves about 9 points of mass
from fast and recursive to bottlenecked and moderate). Using a uniform prior instead
moves the internal-ASI median only 3 months earlier.

## I-K. Recalibrated distributions (scenario A, the preferred posterior mixture)

| Target | 5% | 10% | 25% | 50% | 75% | 90% | 95% |
|---|---|---|---|---|---|---|---|
| **AGI** | 2026-10 | 2026-10 | 2028-02 | **2029-01** | 2030-07 | 2033-10 | 2037-04 |
| **Internal ASI** | 2028-11 | 2029-05 | 2030-07 | **2032-04** | 2034-12 | 2038-10 | 2042-02 |
| **Public ASI** | 2029-05 | 2029-12 | 2031-03 | **2033-02** | 2035-12 | 2039-11 | 2043-04 |

The AGI 5% and 10% quantiles sit at 2026-10 because of the 10% H2 mass. That is an
input judgement, not a fitted result.

**Scenario B — AGI-era / fast takeoff (conditional).** AGI median 2027-09, internal
ASI median **2029-07** (80%: 2027-12 to 2032-04), public ASI median 2030-04. Lag
median 22 months; P(lag < 1 year) = 20%.

**Scenario C — bottlenecked (conditional).** AGI median 2034-03, internal ASI median
**2038-09** (80%: 2033-04 to 2048-10), public ASI median 2039-10. Lag median 47 months.

## L. AGI → internal ASI lag (conditional on AGI being reached; 100% of draws)

| mean | median | p5 | p10 | p25 | p75 | p90 | p95 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 40.4 mo | **34.5 mo** | 11.9 | 15.6 | 23.2 | 51.0 | 72.2 | 88.9 |

| P(lag < 3 mo) | < 6 mo | < 1 yr | < 2 yr | < 5 yr | < 10 yr | > 10 yr |
|---:|---:|---:|---:|---:|---:|---:|
| 0.02% | 0.6% | **5.2%** | **26.8%** | 83.2% | 98.5% | 1.5% |

By regime, the median lag is: bottlenecked 43 months; moderate 36; fast 25;
recursive 12 (with P(< 1 yr) = 53%). See `agi_to_asi_lag_by_regime.png`. The lag is
determined mainly by the **ASI capability gap** (Spearman 0.68). After that come the
regime and its feedback parameters (taste automation, experiment coupling, f_AGI, r,
compute cap, each about −0.44), the algorithmic-efficiency baseline, and the
energy/capex slowdown.

## M. ASI-by-year probabilities (scenario A, cumulative to end of year)

| Year | AGI | Internal ASI | Public ASI |
|---|---:|---:|---:|
| 2026 | 10.3% | 0.0% | 0.0% |
| 2027 | 20.6% | 0.9% | 0.3% |
| 2028 | 49.0% | 6.1% | 2.9% |
| 2029 | 68.3% | 17.1% | 10.4% |
| 2030 | 78.6% | 31.8% | 22.4% |
| 2031 | 84.4% | 46.2% | 35.9% |
| 2032 | 88.0% | 58.2% | 48.7% |
| 2033 | 90.5% | 67.9% | 59.7% |
| 2034 | 92.3% | 75.1% | 68.5% |
| 2035 | 93.6% | 80.7% | 75.4% |
| 2036 | 94.7% | 84.9% | 80.7% |
| 2040 | 97.4% | 93.7% | 92.1% |
| 2045 | 98.8% | 97.6% | 97.1% |
| 2050 | 99.5% | 99.0% | 98.8% |

Compare v0.5.1: P(internal ASI ≤ 2030) was 0.3% and is now 31.8%; P(internal ASI ≤ 2035)
was 74.2% and is now 80.7%; P(≤ 2050) was 89.5% and is now 99.0%. The old flat
2035-2040 plateau is gone.

## N. Sensitivity analysis (common random numbers; full tables in `historical_runs/v0_6_0/`)

Factor tornado: each factor is pinned at p10 versus p90, and the resulting
internal-ASI median is reported (years after 2026-10; baseline 5.5).

| Rank | Factor | Fast | Slow | Swing |
|---|---|---:|---:|---:|
| 1 | **autonomous task horizon** (H0, doubling, acceleration) | 3.9 | 9.1 | **5.3 y** |
| 2 | **ASI capability gap** (OOM) | 4.0 | 7.7 | **3.7 y** |
| 3 | AGI threshold definition | 4.2 | 7.0 | 2.8 y |
| 4 | algorithmic-efficiency baseline | 4.9 | 6.1 | 1.2 y |
| 5 | energy / capex slowdown | 5.2 | 6.2 | 1.0 y |
| 6 | post-AGI feedback gain (r, p, cap, ξ, k0) | 5.2 | 5.7 | 0.6 y |
| 7 | AI-R&D automation (f_AGI, κ) | 5.2 | 5.8 | 0.5 y |
| 8 | governance (pauses, secrecy) | 5.3 | 5.7 | 0.5 y (public: 1.2 y) |
| 9 | compute growth (pre-slowdown) | 5.3 | 5.7 | 0.4 y |
| 10 | training-cycle duration | 5.4 | 5.7 | 0.3 y |
| 11 | hardware / infrastructure response | 5.5 | 5.5 | <0.1 y |

What drives each target:
* **AGI:** the H2 judgement, the doubling time, the paradigm wall, the AGI gate.
* **Lag:** the ASI gap (by far), then regime and feedback parameters, then the
  algorithmic baseline.
* **Internal and public ASI:** the latent speed factor, the doubling time, the ASI gap,
  the paradigm wall.
* Governance matters more for **public** ASI (secrecy branch: 4.8 months on the median)
  than for internal ASI.

Regime ablations show how much the takeoff assumption matters. Recursive-only gives an
internal median 2.0 years earlier (P(≤ 2030) = 61%); bottlenecked-only gives 0.6 years
later. This is real but smaller than the uncertainty in the AGI stage itself.

Alternate priors (shift in internal median):
* ASI gap of 1.5 OOM: −1.0 y. ASI gap of 5 OOM: +1.7 y.
* AGI gate of 168h: −0.8 y. AGI gate of 10,000h: +1.1 y.
* v0.5.1 doubling (7 months): +1.4 y.
* Paradigm wall at 25%: +0.6 y.

**No single assumption dominates.** Two inputs do most of the work, and neither can be
measured directly: the **horizon trend** (whether METR-style doublings continue at 3-5
months past the point where METR can measure them) and the **ASI gap**.

## O. Strongest case for earlier ASI (steelman)

* The horizon has doubled every 3-4 months for two years, and METR's suite ran out of
  long tasks.
* On every bounded R&D sub-task we can score, models are already superhuman (52-70×
  training speed-ups, 431× kernels, Lean-verified open problems).
* OpenAI runs more agent-labour than human labour in research. Anthropic's best model
  beats human research next-step choices 64% of the time (up from 51% in five months).
  P-Zero reportedly finds expert-parity research taste on verifiable tasks.
* If taste is "just another capability that AI fails at for a while", then κ is in the
  recursive range. The Amdahl residual then vanishes within about one model
  generation, and both the AGI gate and the lag collapse together; these are
  correlated through Z.
* In that world (scenario B), internal ASI arrives around **mid-2029**, with 35%
  probability by 2028.

## P. Strongest case for later ASI (steelman)

* METR horizons are measured on well-specified, mostly verifiable SWE tasks, and above
  16h they are unmeasurable. Real reliability at 80% is about 5× shorter. Messy and
  open-ended work lags further. The AGI gate could easily sit at 10,000h or more
  (+1.1 y).
* Despite massive AI use, neither Anthropic nor OpenAI can see an AI-attributable
  acceleration of their own progress. The one documented slope change in 2024 was a
  human paradigm idea (reasoning RL).
* Autonomous research papers get rejected. Research judgement may not come from
  RL on verifiable rewards at all (Sutskever).
* Epoch argues much of measured "algorithmic progress" was scale-dependent, so
  automating researchers buys less than the semi-endogenous model assumes.
* Compute growth must slow once labs exhaust headroom (~2028-2031). Capex near $1T/yr
  cannot double annually without AI revenue that has not yet appeared.
* Incidents are already pausing training, monitorability is falling, and a serious
  incident could trigger long, coordinated pauses.
* In that world (scenario C), internal ASI arrives around **2038-09**, with 64% by 2040.

## Q. What changed versus v0.5.1 (quantified)

| Quantity | v0.5.1 | v0.6.0 | Change |
|---|---|---|---|
| AGI median | 2031-07 | 2029-01 | −2.5 y |
| Internal ASI median | 2034-05 | 2032-04 | −2.1 y |
| Public ASI median | 2035-11 | 2033-02 | −2.8 y |
| Lag median | 30.9 mo | 34.5 mo | +3.6 mo |
| P(lag < 1 y) | 0% | 5.2% | floor removed |
| Internal-ASI 90th pct | 2051-07 | 2038-10 | artificial tail removed |

Attribution inside the v0.6 engine, cumulatively re-imposing v0.5.1 AGI-stage
assumptions (`attribution_vs_v0_5_1.csv`):

| Step | AGI median | Internal-ASI median |
|---|---|---|
| v0.6 baseline | 2029-01 | 2032-04 |
| + 7.9-month doubling | 2030-10 | 2034-04 |
| + 22h horizon at Oct | 2031-02 | 2034-07 |
| + no H2 mass | 2031-07 | 2035-02 |
| + no pre-AGI acceleration | 2032-05 | 2035-11 |
| + 15% late tail | 2032-09 | 2036-04 |

Reading the table backwards:
* The new evidence on **doubling time** is worth about 2.0 years on internal ASI.
* The H2 mass is worth about 0.6 years.
* Pre-AGI acceleration is worth about 0.75 years.
* Re-anchoring the horizon is worth about 0.25 years.
* Replacing the artificial tail is worth about 0.4 years.

The new, stricter AGI gate pushes the other way (the fully reverted v0.6 AGI is
2032-09, later than v0.5.1's 2031-07). The lag got slightly **longer**, not shorter.
The fixed 12-60 month infrastructure floor was removed, but its replacement is
capability-dependent feedback that the 2026 evidence places mostly in the
moderate/bottlenecked regimes.

## R. Calibration verdict

v0.5.1 was **too late on AGI** and **mis-specified on the AGI→ASI lag**. Its lag was
roughly right in size (about 2.5 years) for the wrong reason (a datacentre build
starting at AGI). Its "fast-takeoff regime" label was inaccurate, because the 12-month
floor made a fast takeoff impossible. On **internal ASI** it was about **2 years too
late at the median**. In the tails it was badly miscalibrated: P(by 2030) was
essentially 0, and 15% of the mass was beyond 2040 for no causal reason.

---

## Answers to the eight research questions

**Q1. Are we already in an AGI transition regime?** Yes, H1. Most core capabilities
exist, several at superhuman level on bounded tasks. Reliability (interventions on
4-8 hour tasks), open-ended research judgement and breadth remain below the
operational gate.

**Q2. Probability that operational AGI already exists (repo definition)?** **10%.**
This is a judgement input informed by the H0/H1/H2 test
(`forecast_inputs/agi_definition.yaml`). It is not an inferred quantity. The labs'
own measurements argue against H2, and the statements arguing for it come from parties
with commercial stakes.

**Q3. How automatable is frontier AI R&D today?** About 57% of R&D labour can be done
by AI under light supervision, and about 34% autonomously (fair range 0.2-0.5). This
is concentrated in implementation, running, debugging and optimisation. Research
planning (~10%) and architecture design (~20%) lag. The effect on overall progress
pace is well under 2×.

**Q4. Expected AGI → ASI lag?** Median **34.5 months**, mean 40.4 months.
P(< 1 year) = 5%; P(< 2 years) = 27%; P(> 5 years) = 17%.

**Q5. Does AI-R&D automation create a meaningful recursive loop?** Today, it is
partial. Steps 1-5 of the chain exist on bounded problems; steps 6-7 (successor
improvement attributable to AI, feeding the next cycle) are **not observed**. After
AGI, the model gives a self-reinforcing (positive-gain) loop in **about 13%** of
worlds and a self-limiting but strongly accelerated loop in most of the rest. That
makes the loop meaningful, but probably not explosive.

**Q6. Which bottleneck most strongly prevents a very rapid takeoff?** The
**non-automated research-judgement residual** (Amdahl), together with the
**experiment-compute cap**. Physical compute does not bind in the first two years
after AGI, because what is already under construction sets the pace.

**Q7. What observation would most strongly move the forecast toward ASI before
2030?** A **measured, sustained, AI-attributable slope change** in a lab's
capability-vs-time trend. Concrete examples: Anthropic's AECI departing *further*
from trend for two consecutive frontier models, a lab declaring it has crossed its
automated-AI-R&D threshold, or OpenAI's automated researcher arriving well before
March 2028. Recursive-only weights take P(internal ASI ≤ 2030) from 32% to 61%.

**Q8. What would most strongly falsify the fast-takeoff model?** Twelve or more months
in which labs run AI at an automation fraction above 0.8 of engineering, while their
capability-per-compute slope stays flat. Also falsifying: horizon doubling stretching
beyond about 7 months on METR's next suite through 2027. Both would move weight to the
bottlenecked regime and push the internal-ASI median toward the late 2030s
(scenario C).

---

## Remaining uncertainty and limitations

* **Unmeasurable inputs dominate.** The ASI gap (OOM) and the AGI gate are judgement
  calls, flagged as such and stress-tested.
* **The horizon metric is near its measurement ceiling.** Future horizons beyond 16h
  depend on METR's next suite.
* **Regime likelihood ratios are judgements.** The correlation-group rule prevents
  double counting but does not make them fitted likelihoods.
* **A_R&D's interval is too narrow.** The model reports 0.28-0.40 because component
  weights are fixed; the true range is wider.
* **Some evidence came only from search excerpts or secondary reports.** These rows
  are marked in `verification_status`: the Princeton study, Huang, Metaculus, and the
  Mythos 5.1 card text.
* **Pauses and release delays are reduced forms.** Pauses are added to the final date
  rather than interrupting the ODE, and release dynamics are a two-branch mixture.
* **No robotics or physical-world gate.** The ASI definition is cognitive.
  Wet-lab-dependent science is covered only by the demonstration lag.
