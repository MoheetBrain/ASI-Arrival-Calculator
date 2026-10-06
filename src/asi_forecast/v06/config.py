"""Load, validate and scenario-merge the v0.6 inputs file.

The v0.6 inputs live in ``forecast_inputs/v0_6/inputs.yaml``. Scenarios are
deep-merged overrides declared inside that file, so every scenario remains a
fully auditable YAML diff against the evidence-weighted baseline.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterator

import yaml

from ..helpers import project_root


SUPPORTED_DISTS = {"lognormal", "logitnormal", "triangular", "uniform", "fixed"}
EVIDENCE_CLASSES = {
    "EMPIRICAL_CAPABILITY_RESULT",
    "EMPIRICAL_INFRASTRUCTURE_RESULT",
    "ACADEMIC_ANALYSIS",
    "EXPERT_FORECAST",
    "FRONTIER_LAB_LEADER_FORECAST",
    "STRATEGIC_MARKETING_STATEMENT",
    "THEORETICAL_ARGUMENT",
    "AUTHOR_PRIOR",
}
TRACE_FIELDS = (
    "units",
    "sources",
    "evidence_class",
    "interpretation",
    "rationale",
    "correlation_group",
    "last_updated",
)
PARAMETER_SECTIONS = ("agi_status", "agi_stage", "progress_inputs", "takeoff", "deployment")


def v06_config_path() -> Path:
    """Default v0.6 inputs file."""
    return project_root() / "forecast_inputs" / "v0_6" / "inputs.yaml"


def is_v06_file(path: str | Path) -> bool:
    """Return True when the YAML file declares ``model_version: "0.6"``."""
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return isinstance(raw, dict) and str(raw.get("model_version")) == "0.6"


def _deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def scenario_names(config: dict) -> list[str]:
    return list(config.get("scenarios", {}).keys())


def apply_v06_scenario(config: dict, scenario: str) -> dict:
    """Return a copy of the baseline with the named scenario's overrides merged in."""
    scenarios = config.get("scenarios", {})
    if scenario in ("base", "baseline"):
        merged = copy.deepcopy(config)
        merged["active_scenario"] = "baseline"
        return merged
    if scenario not in scenarios:
        raise ValueError(
            f"Unknown v0.6 scenario {scenario!r}; available: {sorted(scenarios)}"
        )
    merged = _deep_merge(config, scenarios[scenario].get("overrides", {}))
    merged["active_scenario"] = scenario
    validate_v06_config(merged)
    return merged


def load_v06_config(path: str | Path | None = None, scenario: str = "baseline") -> dict:
    """Read, validate and scenario-merge a v0.6 inputs file."""
    path = Path(path) if path else v06_config_path()
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict) or str(config.get("model_version")) != "0.6":
        raise ValueError(f"{path} is not a v0.6 inputs file (model_version != '0.6')")
    validate_v06_config(config)
    return apply_v06_scenario(config, scenario)


# ----------------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------------

def _validate_dist(spec: dict, name: str) -> None:
    dist = spec.get("dist")
    if dist not in SUPPORTED_DISTS:
        raise ValueError(f"{name}: unsupported dist {dist!r}")
    if dist in ("lognormal", "logitnormal"):
        median, p95 = float(spec["median"]), float(spec["p95"])
        if dist == "lognormal" and not (0 < median <= p95):
            raise ValueError(f"{name}: lognormal needs 0 < median <= p95")
        if dist == "logitnormal" and not (0 < median <= p95 < 1):
            raise ValueError(f"{name}: logitnormal needs 0 < median <= p95 < 1")
    elif dist == "triangular":
        if not float(spec["low"]) <= float(spec["mode"]) <= float(spec["high"]):
            raise ValueError(f"{name}: triangular needs low <= mode <= high")
    elif dist == "uniform":
        if not float(spec["low"]) <= float(spec["high"]):
            raise ValueError(f"{name}: uniform needs low <= high")
    elif dist == "fixed":
        float(spec["value"])
    clip = spec.get("clip")
    if clip is not None and not float(clip[0]) <= float(clip[1]):
        raise ValueError(f"{name}: clip must be [low, high]")
    loading = float(spec.get("latent_loading", 0.0))
    if not -1.0 <= loading <= 1.0:
        raise ValueError(f"{name}: latent_loading must be in [-1, 1]")


def iter_parameters(config: dict) -> Iterator[tuple[str, dict]]:
    """Yield (dotted_name, spec) for every sampled/fixed parameter with trace fields."""
    for section in PARAMETER_SECTIONS:
        for key, spec in config.get(section, {}).items():
            if isinstance(spec, dict) and "dist" in spec:
                yield f"{section}.{key}", spec
    for key, spec in config["takeoff"].get("regime_parameters", {}).items():
        yield f"takeoff.regime_parameters.{key}", spec
    rnd = config.get("rnd_automation_today", {})
    if "autonomy_discount" in rnd:
        yield "rnd_automation_today.autonomy_discount", rnd["autonomy_discount"]


def validate_v06_config(config: dict) -> None:
    """Structural validation. Raises ValueError on the first problem found."""
    for section in ("simulation", *PARAMETER_SECTIONS, "rnd_automation_today"):
        if section not in config:
            raise ValueError(f"v0.6 config missing section: {section}")
    for name, spec in iter_parameters(config):
        if "by_regime" in spec:
            regimes = config["takeoff"]["regimes"]
            missing = set(regimes) - set(spec["by_regime"])
            if missing:
                raise ValueError(f"{name}: by_regime missing {sorted(missing)}")
            for regime, sub in spec["by_regime"].items():
                _validate_dist(sub, f"{name}[{regime}]")
        else:
            _validate_dist(spec, name)
    takeoff = config["takeoff"]
    regimes = takeoff["regimes"]
    weights = takeoff.get("regime_weights_override") or takeoff["regime_prior"]["weights"]
    if set(weights) != set(regimes):
        raise ValueError("regime weights must name exactly the declared regimes")
    if abs(sum(float(w) for w in weights.values()) - 1.0) > 1e-6:
        raise ValueError("regime weights must sum to 1")
    for item in takeoff.get("regime_evidence", []):
        if set(item["likelihood"]) != set(regimes):
            raise ValueError(f"regime evidence {item['id']} must cover every regime")
        if any(float(v) <= 0 for v in item["likelihood"].values()):
            raise ValueError(f"regime evidence {item['id']}: likelihoods must be > 0")
    for name, row in config["rnd_automation_today"]["components"].items():
        weight, low, mode, high = (float(v) for v in row)
        if not (0 <= low <= mode <= high <= 1) or weight < 0:
            raise ValueError(f"rnd component {name}: need 0<=low<=mode<=high<=1")
    total_weight = sum(float(row[0]) for row in config["rnd_automation_today"]["components"].values())
    if abs(total_weight - 1.0) > 1e-6:
        raise ValueError(f"rnd component weights must sum to 1, got {total_weight}")


def traceability_problems(config: dict) -> list[str]:
    """Return a list of missing trace fields / bad evidence classes (empty = OK)."""
    problems: list[str] = []
    for name, spec in iter_parameters(config):
        for field in TRACE_FIELDS:
            value = spec.get(field)
            if value in (None, "", []):
                problems.append(f"{name}: missing {field}")
        classes = spec.get("evidence_class") or []
        classes = [classes] if isinstance(classes, str) else classes
        for item in classes:
            if item not in EVIDENCE_CLASSES:
                problems.append(f"{name}: unknown evidence_class {item}")
    return problems


def all_source_ids(config: dict) -> set[str]:
    """Every source_id referenced anywhere in the inputs file."""
    ids: set[str] = set()
    for _, spec in iter_parameters(config):
        ids.update(spec.get("sources", []))
    takeoff = config["takeoff"]
    ids.update(takeoff["regime_prior"].get("sources", []))
    for item in takeoff.get("regime_evidence", []):
        ids.update(item.get("sources", []))
    ids.update(config["rnd_automation_today"].get("component_sources", []))
    return ids


def _dist_text(spec: dict) -> str:
    dist = spec["dist"]
    if dist == "fixed":
        return f"fixed {spec['value']}"
    if dist in ("lognormal", "logitnormal"):
        text = f"{dist}(median={spec['median']}, p95={spec['p95']})"
    elif dist == "triangular":
        text = f"triangular({spec['low']}, {spec['mode']}, {spec['high']})"
    else:
        text = f"uniform({spec['low']}, {spec['high']})"
    if spec.get("clip"):
        text += f" clip{list(spec['clip'])}"
    return text


def parameter_table(config: dict) -> "pd.DataFrame":
    """One row per live parameter (per regime for regime parameters)."""
    import pandas as pd

    rows = []
    for name, spec in iter_parameters(config):
        variants = spec["by_regime"].items() if "by_regime" in spec else [(None, spec)]
        for regime, sub in variants:
            classes = spec.get("evidence_class", [])
            rows.append(
                {
                    "parameter": name if regime is None else f"{name}[{regime}]",
                    "distribution": _dist_text(sub),
                    "latent_loading": spec.get("latent_loading", 0.0),
                    "units": spec.get("units", ""),
                    "sources": ";".join(spec.get("sources", [])),
                    "evidence_class": ";".join([classes] if isinstance(classes, str) else classes),
                    "interpretation": spec.get("interpretation", ""),
                    "reason_for_distribution": " ".join(str(spec.get("rationale", "")).split()),
                    "correlation_group": spec.get("correlation_group", ""),
                    "last_updated": spec.get("last_updated", ""),
                }
            )
    return pd.DataFrame(rows)
