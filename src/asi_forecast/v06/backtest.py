"""Backtest: what did the unchanged v0.5.1 model imply for October 2026?

The v0.5.1 engine is run unchanged (its own YAML, its own seed) and its implied
state at 2026-10 (four months after its 2026-06 start) is compared with the
evidence recorded in ``evidence_tables/v0_6_evidence_2026.csv``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..helpers import load_config, project_root
from ..monte_carlo import simulate_forecast

MONTHS_ELAPSED = 4  # 2026-06 (v0.5.1 start) -> 2026-10 (evidence cut-off)


def v05_expectations(sims: int = 20000, seed: int = 42) -> dict[str, float]:
    config = load_config(project_root() / "forecast_inputs" / "base_forecast_inputs.yaml")
    frame = simulate_forecast(config, sims=sims, seed=seed)
    horizon_oct = frame["current_agent_task_horizon_hours"] * 2.0 ** (
        MONTHS_ELAPSED / frame["adjusted_agent_time_horizon_doubling_months"]
    )
    return {
        "horizon_jun_median_h": float(frame["current_agent_task_horizon_hours"].median()),
        "horizon_oct_median_h": float(horizon_oct.median()),
        "horizon_oct_p90_h": float(np.percentile(horizon_oct, 90)),
        "doubling_median_mo": float(frame["adjusted_agent_time_horizon_doubling_months"].median()),
        "compute_median_x": float(frame["effective_compute_growth_x_per_year"].median()),
        "algo_median_x": float(frame["algorithmic_efficiency_x_per_year"].median()),
        "p_coding_by_oct": float(np.mean(frame["coding_automation_months"] <= MONTHS_ELAPSED)),
        "p_agi_by_oct": float(np.mean(frame["agi_arrival_months"] <= MONTHS_ELAPSED)),
        "coding_median_months": float(frame["coding_automation_months"].median()),
        "rnd_lag_median_mo": float(frame["ai_rnd_automation_lag_after_agi_months"].median()),
        "infra_median_mo": float(frame["infrastructure_friction_months"].median()),
        "public_delay_median_mo": float(frame["internal_to_public_delay_months"].median()),
    }


def backtest_table(sims: int = 20000) -> pd.DataFrame:
    e = v05_expectations(sims)
    rows = [
        (
            "autonomous task horizon (50%)",
            f"{e['horizon_jun_median_h']:.0f}h at 2026-06 -> {e['horizon_oct_median_h']:.0f}h at 2026-10 (p90 {e['horizon_oct_p90_h']:.0f}h)",
            ">=16h (CI 8.5-55h) already in Mar 2026 (Mythos Preview); ~30-50h implied for Oct 2026 (v0.6 median 32h); METR suite saturating",
            f"{np.log2(32.0 / e['horizon_oct_median_h']):.1f} doublings too low at 2026-10, and falling further behind (doubling {e['doubling_median_mo']:.1f} vs ~4 months)",
            "too slow",
            "H0: v0.5.1 sampled median 15h at 2026-06 -> v0.6 median 32h at 2026-10",
            "METR_MYTHOS_TH_2026_05; ANTH_RSI_2026_06",
        ),
        (
            "horizon doubling time",
            f"{e['doubling_median_mo']:.1f} months (after compute rescale)",
            "2.9 mo since 2024, 4.3 mo since 2023 (TH1.1); Anthropic ~4 mo",
            "~3 months too long",
            "too slow",
            "doubling median 7 -> 4.5 months",
            "METR_TH11_2026_01",
        ),
        (
            "reasoning / maths",
            "not modelled (no variable)",
            "First Lean-verified autonomous resolutions of significant open Erdos problems (3% at $300); all FrontierMath Tier 4 solved cumulatively",
            "structural omission",
            "n/a",
            "ASI demonstration lag + multidomain gate added",
            "EPOCH_FME_2026_09",
        ),
        (
            "coding automation",
            f"P(coding gate by 2026-10) = {e['p_coding_by_oct']:.3f}; median {e['coding_median_months']:.0f} months after 2026-06",
            ">80% of merged code AI-authored at Anthropic; code quality ~parity; but no lab would replace all engineers (not 'Automated Coder')",
            "roughly calibrated on the gate; too slow on the trend feeding it",
            "slightly too slow",
            "coding gate folded into horizon threshold + generality gap",
            "ANTH_RSI_2026_06; ANTH_MYTHOS51_SC_2026_09",
        ),
        (
            "agent reliability",
            "not modelled (only 50% horizons)",
            ">50% of successful 4-8h agent tasks need >=1 human intervention (OpenAI); open-ended task success 76% (Anthropic)",
            "structural omission",
            "n/a",
            "autonomy discount in A_R&D; 80%-vs-50% horizon gap in AGI threshold",
            "OAI_RESEARCH_ACCEL_2026_09",
        ),
        (
            "AI-R&D automation before AGI",
            f"zero by construction (R&D automation only starts after AGI; lag median {e['rnd_lag_median_mo']:.1f} mo)",
            "Substantial supervised automation already (A_R&D ~0.57 supervised, ~0.35 autonomous); 3.1 agent-workdays per human workday at OpenAI; but no AI-attributable 2x acceleration",
            "structural miss: R&D automation is gradual and precedes AGI",
            "too late (on onset) / too early (on impact)",
            "explicit A_R&D(t) and automation-fraction dynamics",
            "OAI_RESEARCH_ACCEL_2026_09; ANTH_MYTHOS5_SC_2026_06",
        ),
        (
            "compute growth",
            f"{e['compute_median_x']:.2f}x/yr",
            "Epoch: frontier training compute 5x/yr (4-6x); OpenAI ~4x; global ~3x",
            "slightly low",
            "too slow",
            "0.62 OOM/yr (4.2x) with explicit post-2028 slowdown",
            "EPOCH_TRENDS_2026; EPOCH_LAB_COMPUTE_2026_05",
        ),
        (
            "algorithmic efficiency",
            f"{e['algo_median_x']:.2f}x/yr",
            "No new primary estimate; Epoch notes scale-dependence could lower the research-attributable share",
            "approximately calibrated",
            "none",
            "0.50 OOM/yr baseline, now a takeoff input",
            "EPOCH_ALGO_2024; EPOCH_SCALE_DEP_2026_02",
        ),
        (
            "infrastructure",
            f"fresh {e['infra_median_mo']:.0f}-month build starting only after AGI (floor 12 mo)",
            "GW sites built in ~2.1 yr continuously pre-AGI; largest-site compute doubling every 7 months; 2028 sites at ~half power trend",
            "mis-specified (double-counts compute trend; creates hard 12-month lag floor)",
            "too late (for lag)",
            "calendar compute path + post-2028 slowdown; 24-month response delay for AI-driven boosts",
            "EPOCH_TRENDS_2026; EPOCH_DC_POWER_2026",
        ),
        (
            "internal -> public delay",
            f"median {e['public_delay_median_mo']:.0f} months",
            "Mythos Preview: internal -> partners in ~6 weeks, safeguarded public in ~3.5 months; Astra limited preview within weeks",
            "too long for the normal path",
            "too late",
            "mixture: 75% staged release (median 4 mo) / 25% secrecy (median 18 mo)",
            "ANTH_MYTHOS_PREVIEW_SC_2026_04; OAI_ASTRA_SC_2026_09",
        ),
        (
            "AGI by 2026-10",
            f"P = {e['p_agi_by_oct']:.3f} (impossible by construction)",
            "H1 (transition regime) best supported; H2 not satisfied but ~10% definitional slack",
            "model could not represent 'already here'",
            "n/a",
            "explicit P(H2)=0.10",
            "OAI_ASTRA_SC_2026_09; ANTH_MYTHOS51_SC_2026_09",
        ),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "variable",
            "v0.5.1 expectation (Oct 2026)",
            "observed by 2026-10-06",
            "forecast error",
            "direction of miss",
            "parameter update implied",
            "sources",
        ],
    )


def attribution_table(config: dict, sims: int = 40000, seed: int = 20261006) -> pd.DataFrame:
    """Cumulatively revert v0.6 AGI-stage assumptions to v0.5.1-like values.

    The two engines differ structurally, so this is an attribution WITHIN the v0.6
    engine: each step re-imposes one v0.5.1 assumption on top of the previous step
    and records the shift in medians. Reverse reading = contribution of each update.
    """
    import copy

    from ..helpers import index_to_month, month_to_index
    from .engine import simulate_v06

    start = month_to_index(config["simulation"]["start_month"])
    steps = [
        ("v0.6 baseline", lambda c: c),
        ("doubling time back to v0.5.1 (median 7.9 mo)", lambda c: _upd(c, "agi_stage", "doubling_months", median=7.9, p95=13.0)),
        ("current horizon back to v0.5.1 path (22h at 2026-10)", lambda c: _upd(c, "agi_stage", "current_horizon_hours", median=22.0, p95=75.0)),
        ("no 'already AGI' mass (v0.5.1: impossible)", lambda c: _upd(c, "agi_status", "p_already_agi", value=0.0)),
        ("no pre-AGI acceleration (v0.5.1: none)", lambda c: _set_fixed(c, "agi_stage", "per_doubling_ratio", 1.0)),
        ("15% late tail landing ~2040-2052 (v0.5.1 mixture)", lambda c: _upd(_upd(c, "agi_stage", "paradigm_wall_probability", value=0.15), "agi_stage", "paradigm_wall_wait_years", median=24.0, p95=45.0)),
    ]
    rows = []
    cfg = copy.deepcopy(config)
    for label, func in steps:
        cfg = func(cfg)
        frame = simulate_v06(cfg, sims, seed)
        rows.append(
            {
                "cumulative step": label,
                "AGI median": index_to_month(start + int(np.ceil(frame["agi_months"].median()))),
                "lag median (months)": float(frame["agi_to_asi_lag_months"].median()),
                "internal ASI median": index_to_month(start + int(np.ceil(frame["internal_asi_months"].median()))),
                "P(internal ASI <= 2030)": float(np.mean(frame["internal_asi_month_index"] <= month_to_index("2030-12"))),
            }
        )
    return pd.DataFrame(rows)


def _upd(config: dict, section: str, key: str, **fields) -> dict:
    import copy

    cfg = copy.deepcopy(config)
    cfg[section][key].update(fields)
    return cfg


def _set_fixed(config: dict, section: str, key: str, value: float) -> dict:
    import copy

    cfg = copy.deepcopy(config)
    spec = cfg[section][key]
    for field in ("low", "mode", "high", "median", "p95"):
        spec.pop(field, None)
    spec["dist"] = "fixed"
    spec["value"] = value
    return cfg
