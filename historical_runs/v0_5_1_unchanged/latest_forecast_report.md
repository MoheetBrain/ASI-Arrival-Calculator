# AGI and ASI Arrival Forecast Report

Generated from scenario `base` with `100,000` simulations and random seed `42`.

This report is conditional on the editable inputs in `forecast_inputs/base_forecast_inputs.yaml`. It is not a claim that AGI or ASI will arrive in a specific month.

## Calibration Status

This is an auditable structural prototype running in a FAST-TAKEOFF REGIME. It is NOT a consensus forecast. Every live parameter now traces to a source in `evidence_tables/v0_5_parameter_sources.csv`, but the post-AGI cognitive lags (AI R&D lag, superhuman-researcher lag) are tagged `stress_test` / `aggressive` there, not baseline estimates. The resulting dates therefore sit years earlier than external anchors:

| Source | Median AGI/TAI |
|---|---|
| This model (fast-takeoff) | ~2031 |
| ESPAI 2023 HLMI | 2047 |
| Cotra Bio Anchors TAI | 2052 |

The ~16-year gap vs ESPAI is a property of the aggressive priors, not an independent empirical finding. Long-tail note: the mixture prevents a hard upper wall but shifts the median slightly via a max() operation (a documented calibration risk).

## What Was Forecast

The forecast estimates three month-level distributions:

- **AGI / transformative general AI**: broadly human-level or expert-level general cognitive capability.
- **Internal ASI**: capability-and-agency ASI inside a lab, company, government, or restricted deployment.
- **Public ASI**: comparable ASI capability becoming publicly visible or broadly accessible.

Most public evidence is about AGI, coding agents, compute, benchmarks, and AI R&D automation. ASI is further downstream. This repo therefore forecasts AGI first, then models the uncertain transition from AGI to ASI.

## AGI Forecast

- Median: **2031-07**
- 50% interval: **2030-08 to 2032-12**
- 90% interval: **2029-08 to 2056-11**

## Internal ASI Forecast

- Median: **2034-05**
- 50% interval: **2033-03 to 2036-02**
- 90% interval: **2031-12 to 2059-08**

## Public ASI Forecast

- Median: **2035-11**
- 50% interval: **2034-09 to 2037-08**
- 90% interval: **2033-05 to 2061-03**

## AGI-to-ASI Transition Metrics

| Metric | Value |
|---|---:|
| `median_agi_to_internal_asi_lag_months` | 30.90 |
| `median_agi_to_internal_asi_lag_years` | 2.58 |
| `median_internal_to_public_delay_months` | 16.73 |

## Stage-Gate Timeline

| Stage | Median calendar month | 50% offset interval |
|---|---:|---:|
| Strong coding automation | 2029-09 | 30.2 to 49.4 months |
| Long-horizon agent reliability | 2028-10 | 21.0 to 35.2 months |
| Broad general capability | 2030-02 | 34.9 to 54.4 months |
| AGI | 2031-07 | 49.3 to 77.3 months |
| Internal ASI | 2034-05 | 80.6 to 115.1 months |
| Public ASI | 2035-11 | 98.1 to 133.8 months |

## Forecast Drivers: AGI

| Input variable | Spearman correlation | Interpretation |
|---|---:|---|
| `agent_time_horizon_doubling_months` | 0.550 | Higher `agent_time_horizon_doubling_months` is associated with later agi in this simulation. |
| `effective_compute_growth_x_per_year` | -0.396 | Higher `effective_compute_growth_x_per_year` is associated with earlier agi in this simulation. |
| `algorithmic_efficiency_x_per_year` | -0.342 | Higher `algorithmic_efficiency_x_per_year` is associated with earlier agi in this simulation. |
| `current_agent_task_horizon_hours` | -0.300 | Higher `current_agent_task_horizon_hours` is associated with earlier agi in this simulation. |
| `coding_automation_threshold_human_hours` | 0.209 | Higher `coding_automation_threshold_human_hours` is associated with later agi in this simulation. |
| `agi_integration_lag_months` | 0.180 | Higher `agi_integration_lag_months` is associated with later agi in this simulation. |
| `compute_governance_friction_months` | 0.119 | Higher `compute_governance_friction_months` is associated with later agi in this simulation. |
| `general_capability_lag_after_coding_months` | 0.111 | Higher `general_capability_lag_after_coding_months` is associated with later agi in this simulation. |
| `infrastructure_friction_months` | 0.008 | Higher `infrastructure_friction_months` is associated with later agi in this simulation. |
| `phase_overlap_coefficient` | -0.004 | Higher `phase_overlap_coefficient` is associated with earlier agi in this simulation. |

## Forecast Drivers: Internal ASI

| Input variable | Spearman correlation | Interpretation |
|---|---:|---|
| `agent_time_horizon_doubling_months` | 0.446 | Higher `agent_time_horizon_doubling_months` is associated with later internal_asi in this simulation. |
| `infrastructure_friction_months` | 0.371 | Higher `infrastructure_friction_months` is associated with later internal_asi in this simulation. |
| `effective_compute_growth_x_per_year` | -0.320 | Higher `effective_compute_growth_x_per_year` is associated with earlier internal_asi in this simulation. |
| `algorithmic_efficiency_x_per_year` | -0.281 | Higher `algorithmic_efficiency_x_per_year` is associated with earlier internal_asi in this simulation. |
| `current_agent_task_horizon_hours` | -0.247 | Higher `current_agent_task_horizon_hours` is associated with earlier internal_asi in this simulation. |
| `coding_automation_threshold_human_hours` | 0.171 | Higher `coding_automation_threshold_human_hours` is associated with later internal_asi in this simulation. |
| `agi_integration_lag_months` | 0.143 | Higher `agi_integration_lag_months` is associated with later internal_asi in this simulation. |
| `compute_governance_friction_months` | 0.098 | Higher `compute_governance_friction_months` is associated with later internal_asi in this simulation. |
| `phase_overlap_coefficient` | -0.092 | Higher `phase_overlap_coefficient` is associated with earlier internal_asi in this simulation. |
| `general_capability_lag_after_coding_months` | 0.089 | Higher `general_capability_lag_after_coding_months` is associated with later internal_asi in this simulation. |

## Forecast Drivers: Public ASI

| Input variable | Spearman correlation | Interpretation |
|---|---:|---|
| `agent_time_horizon_doubling_months` | 0.424 | Higher `agent_time_horizon_doubling_months` is associated with later public_asi in this simulation. |
| `infrastructure_friction_months` | 0.354 | Higher `infrastructure_friction_months` is associated with later public_asi in this simulation. |
| `effective_compute_growth_x_per_year` | -0.305 | Higher `effective_compute_growth_x_per_year` is associated with earlier public_asi in this simulation. |
| `algorithmic_efficiency_x_per_year` | -0.269 | Higher `algorithmic_efficiency_x_per_year` is associated with earlier public_asi in this simulation. |
| `current_agent_task_horizon_hours` | -0.235 | Higher `current_agent_task_horizon_hours` is associated with earlier public_asi in this simulation. |
| `secrecy_visibility_delay_months` | 0.190 | Higher `secrecy_visibility_delay_months` is associated with later public_asi in this simulation. |
| `coding_automation_threshold_human_hours` | 0.162 | Higher `coding_automation_threshold_human_hours` is associated with later public_asi in this simulation. |
| `agi_integration_lag_months` | 0.136 | Higher `agi_integration_lag_months` is associated with later public_asi in this simulation. |
| `compute_governance_friction_months` | 0.093 | Higher `compute_governance_friction_months` is associated with later public_asi in this simulation. |
| `phase_overlap_coefficient` | -0.088 | Higher `phase_overlap_coefficient` is associated with earlier public_asi in this simulation. |

## Forecast Drivers: AGI-to-ASI Lag

| Input variable | Spearman correlation | Interpretation |
|---|---:|---|
| `infrastructure_friction_months` | 0.922 | Higher `infrastructure_friction_months` is associated with later agi_to_asi_lag in this simulation. |
| `phase_overlap_coefficient` | -0.250 | Higher `phase_overlap_coefficient` is associated with earlier agi_to_asi_lag in this simulation. |
| `takeoff_lag_months` | 0.173 | Higher `takeoff_lag_months` is associated with later agi_to_asi_lag in this simulation. |
| `superhuman_ai_researcher_lag_months` | 0.104 | Higher `superhuman_ai_researcher_lag_months` is associated with later agi_to_asi_lag in this simulation. |
| `ai_rnd_automation_lag_after_agi_months` | 0.072 | Higher `ai_rnd_automation_lag_after_agi_months` is associated with later agi_to_asi_lag in this simulation. |
| `algorithmic_efficiency_x_per_year` | -0.010 | Higher `algorithmic_efficiency_x_per_year` is associated with earlier agi_to_asi_lag in this simulation. |
| `compute_governance_friction_months` | 0.006 | Higher `compute_governance_friction_months` is associated with later agi_to_asi_lag in this simulation. |
| `agent_time_horizon_doubling_months` | 0.005 | Higher `agent_time_horizon_doubling_months` is associated with later agi_to_asi_lag in this simulation. |
| `deployment_governance_delay_months` | 0.005 | Higher `deployment_governance_delay_months` is associated with later agi_to_asi_lag in this simulation. |
| `current_agent_task_horizon_hours` | -0.004 | Higher `current_agent_task_horizon_hours` is associated with earlier agi_to_asi_lag in this simulation. |

## Interpretation

The median is the 50/50 month: half of simulated futures arrive before it, and half arrive after it. The 50% interval contains the middle half of simulations. The 90% interval contains the central 90% of simulations.

More simulations reduce numerical noise. They do not make bad assumptions true.

## Capability Ladder Context

The 7-checkpoint capability ladder is a qualitative screen, not a separate forecast target. It helps decide whether new evidence should update AGI timing, AGI-to-ASI transition lags, infrastructure friction, AI R&D automation, recursive-progress assumptions, or the internal ASI threshold.

| Checkpoint | Refined metric | Main model implication |
|---|---|---|
| Contextual Invariance | Lossless semantic retrieval across a continuous 10^8-token context with less than 0.01% needle-in-a-haystack decay. | Long-horizon reliability and AGI integration. |
| Autonomous Formal Verification | Closed-loop proof generation for an unverified conjecture or non-trivial software kernel in a verified proof assistant, with zero human prompting. | General capability, AI R&D automation, and superhuman AI researcher lags. |
| Horizon-Unbounded Agency | A 336-hour production run across cross-domain engineering objectives with dynamic self-correction and 0% fatal exceptions. | Agent task horizon and autonomous engineering thresholds. |
| Exascale Infrastructure Hardening | Orchestration of a distributed optical cluster drawing >=1.2 GW, with >99.99% utilization and 30-day fault-tolerant checkpointing. | Compute growth, infrastructure friction, and governance constraints. |
| Recursive Synthetic Iteration | Five generations of monotonic gains from fully synthetic data loops without model collapse. | Takeoff lag and algorithmic efficiency. |
| Meta-Architectural Optimization | Automated validation of a new architecture or training paradigm that reduces FLOPs by >=10% against state-of-the-art baselines. | Algorithmic efficiency and superhuman AI researcher assumptions. |
| Asymmetric Takeoff Divergence | Cross-domain capability accumulation faster than 100x the cumulative human engineering baseline per hour. | Takeoff dynamics and the internal ASI threshold. |

## Convergence

The run used 10 batches. The inter-batch median range was 2.00 months, so the numerical convergence check did not pass the under-one-month rule.

## Limitations

- AGI and ASI are not the same target.
- Most existing evidence directly informs AGI or intermediate milestones, not ASI itself.
- The AGI-to-ASI transition is structurally uncertain and depends on AI R&D automation, superhuman AI researcher emergence, takeoff dynamics, infrastructure, and governance.
- Internal ASI and public ASI can diverge because deployment may be delayed.
- Spearman sensitivity is an association measure, not causal proof.
- Week-level precision is rejected; outputs are rounded to months.
