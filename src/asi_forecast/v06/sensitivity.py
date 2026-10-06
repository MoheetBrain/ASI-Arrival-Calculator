"""Sensitivity analysis for the v0.6 engine.

1. Spearman rank correlations of every sampled input with each target.
2. Factor tornado: each named factor is pinned at its "slow" (p10/p90) and
   "fast" quantile with common random numbers; the swing in medians is reported.
3. Leave-one-factor-out structural ablations (switch a mechanism off).
4. Alternate-prior checks (regime prior, ASI gap, AGI threshold, v0.5 doubling).
"""

from __future__ import annotations

import copy
from typing import Callable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from ..helpers import month_to_index
from .engine import SAMPLED_INPUTS_V06, simulate_v06

TARGET_COLUMNS = {
    "agi": "agi_months",
    "agi_to_asi_lag": "agi_to_asi_lag_months",
    "internal_asi": "internal_asi_months",
    "public_asi": "public_asi_months",
}

# True = larger value means FASTER progress / earlier arrival.
LARGER_IS_FASTER = {
    "h0_hours": True,
    "doubling_months": False,
    "per_doubling_ratio": False,
    "agi_threshold_hours": False,
    "generality_gap_doublings": False,
    "wall_wait_years": False,
    "pre_agi_pause_draw_months": False,
    "compute_growth_oom": True,
    "compute_slowdown_year": True,
    "compute_late_multiplier": True,
    "software_progress_oom": True,
    "asi_gap_oom": False,
    "effective_limit_oom": True,
    "training_cycle_lag_months": False,
    "demonstration_lag_months": False,
    "post_agi_pause_draw_months": False,
    "normal_delay_months": False,
    "secrecy_delay_months": False,
    "f_agi": True,
    "kappa": True,
    "p_parallel": True,
    "r_software": True,
    "compute_cap_m0": True,
    "xi_experiment": True,
    "k0_ai_labour": True,
    "hardware_boost": True,
}

FACTORS: dict[str, list[str]] = {
    "AI-R&D automation (f_AGI, taste automation)": ["f_agi", "kappa"],
    "autonomous task horizon (H0, doubling, acceleration)": ["h0_hours", "doubling_months", "per_doubling_ratio"],
    "AGI threshold definition (gate, generality gap)": ["agi_threshold_hours", "generality_gap_doublings"],
    "algorithmic efficiency baseline": ["software_progress_oom"],
    "compute growth": ["compute_growth_oom"],
    "energy/capex slowdown (date, size)": ["compute_slowdown_year", "compute_late_multiplier"],
    "post-AGI feedback gain (r, p, compute cap, experiments, AI labour)": [
        "r_software", "p_parallel", "compute_cap_m0", "xi_experiment", "k0_ai_labour",
    ],
    "training-cycle duration": ["training_cycle_lag_months"],
    "hardware/infrastructure response": ["hardware_boost"],
    "ASI capability gap (OOM)": ["asi_gap_oom"],
}


def _governance(config: dict, fast: bool) -> dict:
    cfg = copy.deepcopy(config)
    if fast:
        cfg["agi_stage"]["pre_agi_pause_probability"]["value"] = 0.0
        cfg["takeoff"]["post_agi_pause_probability"]["value"] = 0.0
        cfg["deployment"]["secrecy_probability"]["value"] = 0.0
    else:
        for section, key in (
            ("agi_stage", "pre_agi_pause_probability"),
            ("takeoff", "post_agi_pause_probability"),
            ("deployment", "secrecy_probability"),
        ):
            cfg[section][key]["value"] = min(1.0, 2.0 * float(cfg[section][key]["value"]))
    return cfg


def _summ(frame: pd.DataFrame, config: dict) -> dict:
    cutoff = month_to_index("2030-12")
    return {
        "agi_median_months": float(frame["agi_months"].median()),
        "lag_median_months": float(frame["agi_to_asi_lag_months"].median()),
        "internal_median_months": float(frame["internal_asi_months"].median()),
        "public_median_months": float(frame["public_asi_months"].median()),
        "P(internal<=2030)": float(np.mean(frame["internal_asi_month_index"].to_numpy() <= cutoff)),
    }


def spearman_drivers(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for target, column in TARGET_COLUMNS.items():
        y = frame[column].to_numpy()
        for name in SAMPLED_INPUTS_V06:
            x = frame[name].to_numpy().astype(float)
            if np.nanstd(x) == 0:
                rho = np.nan
            else:
                rho = float(spearmanr(x, y).statistic)
            rows.append({"target": target, "input": name, "spearman": rho})
    table = pd.DataFrame(rows)
    table["abs"] = table["spearman"].abs()
    table = table.sort_values(["target", "abs"], ascending=[True, False])
    table["rank"] = table.groupby("target").cumcount() + 1
    return table.drop(columns="abs").reset_index(drop=True)


def factor_tornado(config: dict, sims: int, seed: int) -> pd.DataFrame:
    base = _summ(simulate_v06(config, sims, seed), config)
    rows = []
    for factor, columns in FACTORS.items():
        result = {"factor": factor}
        for label, fast in (("slow", False), ("fast", True)):
            quantiles = {
                c: (0.9 if LARGER_IS_FASTER[c] == fast else 0.1) for c in columns
            }
            summ = _summ(simulate_v06(config, sims, seed, fixed_quantile=quantiles), config)
            for key, value in summ.items():
                result[f"{label}:{key}"] = value
        rows.append(result)
    gov ={"factor": "governance (pauses, secrecy: off vs doubled)"}
    for label, fast in (("slow", False), ("fast", True)):
        summ = _summ(simulate_v06(_governance(config, fast), sims, seed), config)
        for key, value in summ.items():
            gov[f"{label}:{key}"] = value
    rows.append(gov)
    table = pd.DataFrame(rows)
    for key in base:
        table[f"swing:{key}"] = (table[f"slow:{key}"] - table[f"fast:{key}"]).abs()
    table.attrs["baseline"] = base
    return table.sort_values("swing:internal_median_months", ascending=False).reset_index(drop=True)


def _set(path: str, value) -> Callable[[dict], dict]:
    def apply(config: dict) -> dict:
        cfg = copy.deepcopy(config)
        node = cfg
        keys = path.split(".")
        for key in keys[:-1]:
            node = node[key]
        node[keys[-1]] = value
        return cfg

    return apply


def _chain(*funcs: Callable[[dict], dict]) -> Callable[[dict], dict]:
    def apply(config: dict) -> dict:
        for func in funcs:
            config = func(config)
        return config

    return apply


def _zero_loadings(config: dict) -> dict:
    cfg = copy.deepcopy(config)
    for section in ("agi_stage", "progress_inputs", "takeoff", "deployment"):
        for spec in cfg[section].values():
            if isinstance(spec, dict) and "latent_loading" in spec:
                spec["latent_loading"] = 0.0
    for spec in cfg["takeoff"]["regime_parameters"].values():
        spec["latent_loading"] = 0.0
    cfg["takeoff"]["regime_latent_loading"] = 0.0
    return cfg


def _only_regime(name: str) -> Callable[[dict], dict]:
    weights = {r: (1.0 if r == name else 0.0) for r in ("bottlenecked", "moderate", "fast", "recursive")}
    return _set("takeoff.regime_weights_override", weights)


def _prior_only(config: dict) -> dict:
    cfg = copy.deepcopy(config)
    cfg["takeoff"]["regime_weights_override"] = dict(cfg["takeoff"]["regime_prior"]["weights"])
    return cfg


ABLATIONS: dict[str, Callable[[dict], dict]] = {
    "no 'already AGI' mass (P(H2)=0)": _set("agi_status.p_already_agi.value", 0.0),
    "no paradigm wall": _set("agi_stage.paradigm_wall_probability.value", 0.0),
    "no compute/energy slowdown (m_late=1)": _set(
        "progress_inputs.compute_late_multiplier", {"dist": "fixed", "value": 1.0}
    ),
    "no pauses (pre- and post-AGI)": _chain(
        _set("agi_stage.pre_agi_pause_probability.value", 0.0),
        _set("takeoff.post_agi_pause_probability.value", 0.0),
    ),
    "no generality gap": _set("agi_stage.generality_gap_doublings", {"dist": "fixed", "value": 0.0}),
    "no pre-AGI acceleration (ratio=1)": _set("agi_stage.per_doubling_ratio", {"dist": "fixed", "value": 1.0}),
    "no secrecy branch": _set("deployment.secrecy_probability.value", 0.0),
    "no latent correlation": _zero_loadings,
    "regime weights = prior (ignore 2026 evidence)": _prior_only,
    "regime = bottlenecked only": _only_regime("bottlenecked"),
    "regime = moderate only": _only_regime("moderate"),
    "regime = fast only": _only_regime("fast"),
    "regime = recursive only": _only_regime("recursive"),
}

ALTERNATE_PRIORS: dict[str, Callable[[dict], dict]] = {
    "uniform regime prior + 2026 evidence": _chain(
        _set("takeoff.regime_prior.weights", {"bottlenecked": 0.25, "moderate": 0.25, "fast": 0.25, "recursive": 0.25}),
    ),
    "ASI gap median 1.5 OOM": _set("takeoff.asi_gap_oom.median", 1.5),
    "ASI gap median 5 OOM": _chain(_set("takeoff.asi_gap_oom.median", 5.0), _set("takeoff.asi_gap_oom.p95", 10.0)),
    "AGI gate 168h (METR 'one month')": _chain(_set("agi_stage.agi_threshold_hours.median", 168.0), _set("agi_stage.agi_threshold_hours.p95", 1300.0)),
    "AGI gate 10,000h (AI Futures AC-like)": _chain(_set("agi_stage.agi_threshold_hours.median", 10000.0), _set("agi_stage.agi_threshold_hours.p95", 60000.0)),
    "v0.5.1 doubling time (7 months)": _chain(_set("agi_stage.doubling_months.median", 7.0), _set("agi_stage.doubling_months.p95", 12.0)),
    "P(H2) = 0.20": _set("agi_status.p_already_agi.value", 0.20),
    "paradigm wall 25%": _set("agi_stage.paradigm_wall_probability.value", 0.25),
}


def run_variants(config: dict, variants: dict[str, Callable[[dict], dict]], sims: int, seed: int) -> pd.DataFrame:
    rows = [{"variant": "baseline", **_summ(simulate_v06(config, sims, seed), config)}]
    for name, func in variants.items():
        rows.append({"variant": name, **_summ(simulate_v06(func(config), sims, seed), config)})
    table = pd.DataFrame(rows)
    base = table.iloc[0]
    for key in ("agi_median_months", "lag_median_months", "internal_median_months", "public_median_months"):
        table[f"delta:{key}"] = table[key] - base[key]
    return table
