"""v0.6 Monte Carlo engine: horizon-gated AGI + feedback-driven AGI->ASI takeoff.

Notation (all per simulated world; time t in months from ``start_month``)

AGI stage
    d(t)   = d0 * rho^(n(t)) * (c0 + s0) / (c(t) + s0)        months per doubling
    dn/dt  = 1 / d(t)                                          horizon doublings
    n_AGI  = log2(H_threshold / H0) + g                        g = generality gap
    T_AGI  = first t with n(t) >= n_AGI   (+ pre-AGI pause)
    with P(H2) T_AGI = 0 ("already AGI"), and with P(wall) T_AGI >= wall wait.
    c(t) = compute growth (OOM/yr) on the calendar path: c0 before the slowdown
    year, c0*m_late after it. Horizon growth is proportional to effective-compute
    growth (METR: log-horizon is ~linear in log effective compute), so a compute
    slowdown lengthens doublings causally instead of via an ad-hoc tail.

AGI -> internal ASI (local time tau since AGI, monthly Euler steps)
    f(tau)   = expit(logit f_AGI + kappa * E)                 automation fraction A_R&D
    U_lab    = 1 / ((1 - f) + f / (k0 * 10^S))                Amdahl research-labour multiplier
    M(tau)   = M0 * 10^(xi * E)                               compute-bottleneck cap
    U_eff    = (1 + 1/M) / (1/U_lab + 1/M)                    soft cap (=1 when U_lab=1)
    r_eff    = r * max(0.05, 1 - S / L)                       returns decline toward limits
    X        = max(0, S - s0 * tau)                           software progress beyond trend
    dS/dtau  = s0 * U_eff^p * 10^(-(p / r_eff) * X)           software OOM/yr
    dC/dtau  = c(t) * (1 + h * [tau >= infra_delay])          compute OOM/yr
    E = S + C;  capability reached when E >= G (asi_gap_oom)
    T_iASI = T_AGI + tau_G + training_cycle + demonstration (+ post-AGI pause)
    T_pASI = T_iASI + deployment delay (normal or secrecy branch)

The semi-endogenous form is Jones/Davidson: with full automation U ~ 10^S, so
dS/dtau ~ 10^{S p (1 - 1/r)}; progress accelerates iff r > 1 (Forethought).
Partial automation (f < 1) caps U_lab at 1/(1-f) (Amdahl), so research-taste
automation (kappa) decides whether the loop ever closes. Regimes are sampled
from the Bayesian posterior; lag times are outputs, never inputs.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy.special import expit, logit

from ..helpers import index_to_month, month_to_index
from .regimes import regime_posterior
from .sampling import correlated_uniform, inverse_cdf, sample

REGIME_ORDER = ["bottlenecked", "moderate", "fast", "recursive"]

# (output column, config section, key) for every non-regime sampled input.
SHARED_INPUTS = [
    ("h0_hours", "agi_stage", "current_horizon_hours"),
    ("doubling_months", "agi_stage", "doubling_months"),
    ("per_doubling_ratio", "agi_stage", "per_doubling_ratio"),
    ("agi_threshold_hours", "agi_stage", "agi_threshold_hours"),
    ("generality_gap_doublings", "agi_stage", "generality_gap_doublings"),
    ("wall_wait_years", "agi_stage", "paradigm_wall_wait_years"),
    ("pre_agi_pause_draw_months", "agi_stage", "pre_agi_pause_months"),
    ("compute_growth_oom", "progress_inputs", "compute_growth_oom_per_year"),
    ("compute_slowdown_year", "progress_inputs", "compute_slowdown_year"),
    ("compute_late_multiplier", "progress_inputs", "compute_late_multiplier"),
    ("software_progress_oom", "progress_inputs", "software_progress_oom_per_year"),
    ("asi_gap_oom", "takeoff", "asi_gap_oom"),
    ("effective_limit_oom", "takeoff", "effective_limit_oom"),
    ("training_cycle_lag_months", "takeoff", "training_cycle_lag_months"),
    ("demonstration_lag_months", "takeoff", "demonstration_lag_months"),
    ("post_agi_pause_draw_months", "takeoff", "post_agi_pause_months"),
    ("normal_delay_months", "deployment", "normal_delay_months"),
    ("secrecy_delay_months", "deployment", "secrecy_delay_months"),
]

REGIME_INPUTS = [
    ("f_agi", "automation_fraction_at_agi"),
    ("kappa", "taste_automation_per_oom"),
    ("p_parallel", "parallel_labour_returns"),
    ("r_software", "returns_to_software_rd"),
    ("compute_cap_m0", "compute_bottleneck_cap"),
    ("xi_experiment", "experiment_efficiency_coupling"),
    ("k0_ai_labour", "ai_labour_advantage"),
    ("hardware_boost", "hardware_feedback_boost"),
]

BERNOULLI_INPUTS = [
    ("already_agi", "agi_status", "p_already_agi"),
    ("paradigm_wall", "agi_stage", "paradigm_wall_probability"),
    ("pre_agi_pause", "agi_stage", "pre_agi_pause_probability"),
    ("post_agi_pause", "takeoff", "post_agi_pause_probability"),
    ("secrecy", "deployment", "secrecy_probability"),
]

SAMPLED_INPUTS_V06 = (
    ["latent_z", "regime_index"]
    + [c for c, _, _ in SHARED_INPUTS]
    + [c for c, _ in REGIME_INPUTS]
    + [c for c, _, _ in BERNOULLI_INPUTS]
)


def _start_year(start_month: str) -> float:
    year, month = (int(v) for v in start_month.split("-"))
    return year + (month - 1) / 12.0


def _compute_rate(
    calendar_months: np.ndarray, start_year: float, c0: np.ndarray, slow_year: np.ndarray, m_late: np.ndarray
) -> np.ndarray:
    """Calendar compute-growth path (OOM/yr)."""
    year = start_year + calendar_months / 12.0
    return np.where(year >= slow_year, c0 * m_late, c0)


def sample_inputs(
    config: dict,
    sims: int,
    rng: np.random.Generator,
    fixed: dict | None = None,
    fixed_quantile: dict | None = None,
) -> dict[str, np.ndarray]:
    """Draw every input.

    ``fixed`` maps output column -> constant; ``fixed_quantile`` maps output column
    -> quantile q in (0,1) of that input's own distribution (per regime for regime
    parameters). All random draws are still consumed, so ablations use common
    random numbers and differ from the baseline only in the overridden inputs.
    """
    fixed = fixed or {}
    fixed_quantile = fixed_quantile or {}
    latent = rng.standard_normal(sims)
    out: dict[str, np.ndarray] = {"latent_z": latent}

    for column, section, key in SHARED_INPUTS:
        spec = config[section][key]
        out[column] = sample(spec, rng, latent)
        if column in fixed_quantile:
            out[column] = inverse_cdf(spec, np.full(sims, float(fixed_quantile[column])))

    for column, section, key in BERNOULLI_INPUTS:
        probability = float(config[section][key]["value"])
        out[column] = rng.random(sims) < probability

    takeoff = config["takeoff"]
    weights = regime_posterior(takeoff)
    cumulative = np.cumsum([weights[r] for r in REGIME_ORDER])
    u_reg = correlated_uniform(rng, latent, float(takeoff.get("regime_latent_loading", 0.0)))
    regime_index = np.searchsorted(cumulative, u_reg, side="right").clip(0, len(REGIME_ORDER) - 1)
    out["regime_index"] = regime_index

    for column, key in REGIME_INPUTS:
        spec = takeoff["regime_parameters"][key]
        u = correlated_uniform(rng, latent, float(spec.get("latent_loading", 0.0)))
        if column in fixed_quantile:
            u = np.full(sims, float(fixed_quantile[column]))
        values = np.empty(sims)
        for i, regime in enumerate(REGIME_ORDER):
            mask = regime_index == i
            if mask.any():
                values[mask] = inverse_cdf(spec["by_regime"][regime], u[mask])
        out[column] = values

    for column, value in fixed.items():
        if column not in out:
            raise KeyError(f"cannot fix unknown input {column!r}")
        dtype = out[column].dtype
        out[column] = np.full(sims, value, dtype=dtype)
    return out


def _agi_stage(inp: dict, n_months: int, start_year: float) -> tuple[np.ndarray, np.ndarray]:
    """Return (AGI offset in months, censored flag)."""
    sims = inp["h0_hours"].shape[0]
    log2h0 = np.log2(inp["h0_hours"])
    target = np.log2(inp["agi_threshold_hours"]) + inp["generality_gap_doublings"]
    n = np.zeros(sims)  # doublings achieved since start
    need = np.maximum(target - log2h0, 0.0)
    crossing = np.where(need <= 0, 0.0, np.nan)
    c0, s0 = inp["compute_growth_oom"], inp["software_progress_oom"]
    base = c0 + s0
    for month in range(n_months):
        active = np.isnan(crossing)
        if not active.any():
            break
        c_now = _compute_rate(np.full(sims, float(month)), start_year, c0, inp["compute_slowdown_year"], inp["compute_late_multiplier"])
        doubling = inp["doubling_months"] * inp["per_doubling_ratio"] ** n * base / (c_now + s0)
        doubling = np.clip(doubling, 0.25, 600.0)
        step = 1.0 / doubling
        reach = active & (n + step >= need)
        crossing[reach] = month + (need[reach] - n[reach]) / step[reach]
        n = np.where(active, n + step, n)
    censored = np.isnan(crossing)
    crossing = np.where(censored, float(n_months), crossing)

    agi = crossing + np.where(inp["pre_agi_pause"], inp["pre_agi_pause_draw_months"], 0.0)
    agi = np.where(inp["paradigm_wall"], np.maximum(agi, inp["wall_wait_years"] * 12.0), agi)
    agi = np.where(inp["already_agi"], 0.0, agi)
    censored = censored & ~inp["already_agi"] & ~inp["paradigm_wall"]
    return np.minimum(agi, float(n_months)), censored | (agi >= n_months)


def _instant_software_rate(
    f_logit0, kappa, k0, m0, xi, r, p, s0, limit, s_level, c_level, tau_years
) -> np.ndarray:
    """Software progress (OOM/yr), automation fraction, and progress speed-up.

    The compute-bottleneck cap ``M`` bounds the speed-up of the software
    PROGRESS RATE (Epoch's "max speed of AI software progress at fixed compute",
    ~6x at rho=-0.4; Forethought argues 32x+), so it is applied after the
    parallel-labour exponent p, not to research input.
    """
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        capability = s_level + c_level
        f = expit(f_logit0 + kappa * capability)
        u_lab = 1.0 / ((1.0 - f) + f / (k0 * 10.0 ** np.minimum(s_level, 300.0)))
        raw_speedup = u_lab ** p
        cap = m0 * 10.0 ** np.minimum(xi * capability, 300.0)
        speedup = (1.0 + 1.0 / cap) / (1.0 / raw_speedup + 1.0 / cap)
        r_eff = r * np.maximum(0.05, 1.0 - s_level / limit)
        excess = np.maximum(0.0, s_level - s0 * tau_years)
        rate = s0 * speedup * 10.0 ** (-(p / r_eff) * excess)
    return rate, f, speedup


def _takeoff(inp: dict, agi: np.ndarray, n_months: int, start_year: float, infra_delay: float) -> dict[str, np.ndarray]:
    """Integrate the feedback dynamics from each world's AGI date."""
    sims = agi.shape[0]
    f0 = logit(np.clip(inp["f_agi"], 1e-6, 1 - 1e-6))
    args = (
        f0, inp["kappa"], inp["k0_ai_labour"], inp["compute_cap_m0"], inp["xi_experiment"],
        inp["r_software"], inp["p_parallel"], inp["software_progress_oom"], inp["effective_limit_oom"],
    )
    gap = inp["asi_gap_oom"]
    s_lvl = np.zeros(sims)
    c_lvl = np.zeros(sims)
    tau_g = np.full(sims, np.nan)
    rate0 = np.full(sims, np.nan)
    rate_end = np.full(sims, np.nan)
    soft0 = np.full(sims, np.nan)
    soft_end = np.full(sims, np.nan)
    f_end = np.full(sims, np.nan)
    u_end = np.full(sims, np.nan)
    remaining = np.maximum(n_months - agi, 0.0)
    max_steps = int(math.ceil(remaining.max())) + 1 if sims else 0

    for k in range(max_steps):
        active = np.isnan(tau_g) & (k < remaining)
        if not active.any():
            break
        tau_years = k / 12.0
        s_rate, f_now, u_now = _instant_software_rate(*args, s_lvl, c_lvl, tau_years)
        c_cal = _compute_rate(agi + k, start_year, inp["compute_growth_oom"], inp["compute_slowdown_year"], inp["compute_late_multiplier"])
        c_rate = c_cal * (1.0 + inp["hardware_boost"] * (k >= infra_delay))
        rate = s_rate + c_rate  # OOM / year
        if k == 0:
            rate0 = rate.copy()
            soft0 = s_rate.copy()
        capability = s_lvl + c_lvl
        step = rate / 12.0
        reach = active & (capability + step >= gap)
        tau_g[reach] = k + (gap[reach] - capability[reach]) / step[reach]
        rate_end[reach] = rate[reach]
        soft_end[reach] = s_rate[reach]
        f_end[reach] = f_now[reach]
        u_end[reach] = u_now[reach]
        s_lvl = np.where(active, s_lvl + s_rate / 12.0, s_lvl)
        c_lvl = np.where(active, c_lvl + c_rate / 12.0, c_lvl)

    censored = np.isnan(tau_g)
    tau_g = np.where(censored, remaining, tau_g)

    # Instantaneous loop gain at AGI: d log10(software rate) / d OOM of software,
    # evaluated with the feedback "switched on" (excess progress = the increment).
    probe = 0.1
    base_rate, _, _ = _instant_software_rate(*args, np.zeros(sims), np.zeros(sims), 0.0)
    bumped, _, _ = _instant_software_rate(*args, np.full(sims, probe), np.zeros(sims), 0.0)
    loop_gain = np.log10(bumped / base_rate) / probe
    return {
        "takeoff_capability_months": tau_g,
        "takeoff_censored": censored,
        "progress_rate_at_agi_oom_per_year": rate0,
        "progress_rate_at_asi_oom_per_year": rate_end,
        "software_rate_at_agi_oom_per_year": soft0,
        "software_rate_at_asi_oom_per_year": soft_end,
        "automation_fraction_at_asi": f_end,
        "research_speedup_at_asi": u_end,
        "loop_gain_log10_per_oom": loop_gain,
    }


def classify_dynamics(accel_ratio: np.ndarray, paused: np.ndarray) -> np.ndarray:
    """SUBCRITICAL / LINEAR / SUPERLINEAR / PUNCTUATED from simulated trajectories.

    ``accel_ratio`` is the AI-R&D (software) progress rate when ASI capability is
    reached divided by the rate at AGI. Exogenous compute growth is excluded so
    the label describes the feedback loop itself. PUNCTUATED = a post-AGI pause
    (bottleneck) interrupted a non-decaying loop.
    """
    labels = np.where(accel_ratio < 0.8, "SUBCRITICAL", np.where(accel_ratio <= 1.5, "LINEAR", "SUPERLINEAR"))
    return np.where(paused & (accel_ratio >= 0.8), "PUNCTUATED", labels)


def simulate_v06(
    config: dict,
    sims: int | None = None,
    seed: int | None = None,
    fixed: dict | None = None,
    fixed_quantile: dict | None = None,
) -> pd.DataFrame:
    """Run the v0.6 forecast and return one row per simulated world."""
    sim_cfg = config["simulation"]
    sims = int(sims or sim_cfg["default_sims"])
    seed = int(seed if seed is not None else sim_cfg["random_seed"])
    if sims <= 0:
        raise ValueError("sims must be positive")
    rng = np.random.default_rng(seed)
    start_index = month_to_index(sim_cfg["start_month"])
    n_months = month_to_index(sim_cfg["horizon_month"]) - start_index
    start_year = _start_year(sim_cfg["start_month"])

    inp = sample_inputs(config, sims, rng, fixed, fixed_quantile)
    agi, agi_censored = _agi_stage(inp, n_months, start_year)
    infra_delay = float(config["takeoff"]["infra_response_delay_months"]["value"])
    tk = _takeoff(inp, agi, n_months, start_year, infra_delay)

    post_pause = np.where(inp["post_agi_pause"], inp["post_agi_pause_draw_months"], 0.0)
    lag = (
        tk["takeoff_capability_months"]
        + inp["training_cycle_lag_months"]
        + inp["demonstration_lag_months"]
        + post_pause
    )
    internal = np.minimum(agi + lag, float(n_months))
    public_delay = np.where(inp["secrecy"], inp["secrecy_delay_months"], inp["normal_delay_months"])
    public = np.minimum(internal + public_delay, float(n_months))
    lag = internal - agi

    frame = pd.DataFrame({"sim_id": np.arange(1, sims + 1)})
    for column, values in inp.items():
        frame[column] = values
    frame["regime"] = np.array(REGIME_ORDER)[inp["regime_index"]]
    frame["agi_months"] = agi
    frame["agi_censored"] = agi_censored
    for column, values in tk.items():
        frame[column] = values
    frame["post_agi_pause_months"] = post_pause
    frame["agi_to_asi_lag_months"] = lag
    frame["internal_asi_months"] = internal
    frame["public_delay_months"] = public - internal
    frame["public_asi_months"] = public
    frame["internal_censored"] = tk["takeoff_censored"] | (agi + lag >= n_months)
    frame["accel_ratio"] = frame["software_rate_at_asi_oom_per_year"] / frame["software_rate_at_agi_oom_per_year"]
    frame["dynamics_class"] = classify_dynamics(frame["accel_ratio"].fillna(0.0).to_numpy(), inp["post_agi_pause"])

    # Month indices: AGI "by month m" when its offset is <= m (offset 0 => start month).
    for name, offsets in (("agi", agi), ("internal_asi", internal), ("public_asi", public)):
        idx = start_index + np.ceil(np.round(offsets, 9)).astype(int)
        frame[f"{name}_month_index"] = idx
        frame[f"{name}_month"] = [index_to_month(i) for i in idx]
    # Compatibility aliases used by the v0.5 report/plot helpers.
    frame["agi_arrival_months"] = frame["agi_months"]
    frame["internal_asi_arrival_months"] = frame["internal_asi_months"]
    frame["public_asi_arrival_months"] = frame["public_asi_months"]
    frame["internal_to_public_delay_months"] = frame["public_delay_months"]
    return frame
