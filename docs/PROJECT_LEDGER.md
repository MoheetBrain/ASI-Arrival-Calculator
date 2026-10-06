# Project Ledger

Append-only chronological record. Entries before this ledger existed are summarised
from `CHANGELOG.md` and git history; they are not reconstructed verbatim.

---

## Entry 1: 2026-10-06 17:10 BST

- **Branch:** `v0.6-recalibration` (from `main` @ `a33ad3e`)
- **Project stage:** v0.5.1 → v0.6.0, full recalibration on evidence to 2026-10-06.
- **Prior history (summary):** v0.3.0 stage-gated triangular model; v0.4.0
  constants exposed in YAML; v0.5.0 empirical recalibration; v0.5.1 traceable
  evidence layer (merged as PR #1).
- **Objective of the change:** recalculate AGI, internal-ASI and public-ASI arrival
  distributions without anchoring on v0.5.1, using verified 2026 evidence and a
  causally grounded AGI→ASI takeoff model.
- **Files and systems changed:**
  - **Added:**
    - `src/asi_forecast/v06/` (engine, config, sampling, regimes, rnd_automation,
      metrics, sensitivity, backtest, report);
    - `forecast_inputs/v0_6/inputs.yaml`;
    - `evidence_tables/v0_6_evidence_2026.csv` and `v0_6_parameter_sources.csv`;
    - `evidence_notes/2026_leader_statements.md` and `2026_ai_rnd_automation.md`;
    - `research_note/2026_10_model_audit.md` and `2026_10_recalibration.md`;
    - `historical_runs/v0_5_1_unchanged/` and `historical_runs/v0_6_0/`;
    - three new test files;
    - `docs/`.
  - **Modified:**
    - `cli.py` (v0.6 default engine, `--sensitivity-sims`, scenario argument);
    - `pyproject.toml` and `requirements.txt` (version 0.6.0, `tabulate`);
    - `__init__.py`, `README.md`, `CHANGELOG.md`, `.gitignore`;
    - `agi_definition.yaml` and `asi_definition.yaml` (operational sections appended);
    - `evidence_notes/README.md`.
  - **Unchanged (hash-pinned):** the v0.5.1 inputs and engine.
- **What was completed:**
  - the audit, and an unchanged reproduction of v0.5.1;
  - an evidence sweep across METR, Anthropic, OpenAI, DeepMind, Epoch, Forethought,
    AI Futures, US policy and leader statements;
  - the new engine, recalibrated inputs, the A/B/C scenarios, the sensitivity suite,
    the backtest and attribution, and the report and dashboard.
- **Decisions made and why:**
  - **Lags.** Replaced the fixed post-AGI lags and the 12–60 month infrastructure
    floor with an AI-R&D feedback ODE. The old floor double-counted the compute trend
    and made fast takeoff impossible.
  - **Tail.** Replaced the 15% late-tail teleport with a causal paradigm-wall branch.
  - **H2.** Added an explicit P(H2)=0.10.
  - **Cap placement.** Applied the compute cap to the progress rate (Epoch/Forethought
    semantics). The first implementation applied it to research input, which made the
    "fast" regime slower than even Epoch's skeptical cap; this was caught and fixed
    before any output was published.
  - **Recursive regime.** Tightened its parameters and classified on the software
    rate, so the regime's dynamics match its own definition (now tested).
- **Tests and verification actually executed:**
  - `pytest`: 62 passed (37 existing and 25 new).
  - CLI runs: `run` at 10k and 100k, `drivers` at 100k/40k, `report` at 100k/40k.
  - A 500k stability run; three-seed stability; batch convergence.
- **Results:**
  - **Scenario A:** AGI median 2029-01 (80%: 2026-10 to 2033-10); internal ASI
    2032-04 (2029-05 to 2038-10); public ASI 2033-02 (2029-12 to 2039-11).
  - **Lag:** median 34.5 months; P(<1y) = 5.2%; P(<2y) = 26.8%.
  - **Internal ASI by year:** P(by 2030) = 31.8%; P(by 2035) = 80.7%.
  - **Scenario B:** internal ASI 2029-07. **Scenario C:** internal ASI 2038-09.
  - **Regime posterior:** bottlenecked 0.363, moderate 0.379, fast 0.196,
    recursive 0.061.
- **Failures or unresolved uncertainty:**
  - The dominant inputs (ASI gap in OOM, AGI threshold) are judgement inputs.
  - The regime likelihood ratios are judgements.
  - Several sources were verified only through search excerpts or secondary reports
    (flagged per row).
  - The METR horizon is saturating.
  - The A_R&D interval is too narrow.
- **Effect on the overall project:** v0.6 becomes the default forecast. Relative to
  v0.5.1, the internal-ASI median moved 2.1 years earlier, the lag became
  capability-dependent and slightly longer at the median, and the artificial tails
  are gone. v0.5.1 is still reproducible.
- **Next intended step:** merge after review, then refresh the inputs when METR's
  next long-task suite or a lab's AI-attributable acceleration measurement is
  published.
