"""Every live engine parameter must trace to a sourced evidence row.

This enforces the v0.5 traceability contract: each sampled input and each exposed
structural constant has a row in evidence_tables/v0_5_parameter_sources.csv with a
source_id, source_url, source_quote, and regime. Prevents silent reintroduction of
unsourced "magic numbers".
"""

import pandas as pd

from asi_forecast.forecast_model import SAMPLED_INPUT_COLUMNS
from asi_forecast.load_data import load_evidence_table


REQUIRED_STRUCTURAL_PARAMS = {
    "task_horizon_double_count_dampening_exponent",
    "long_tail_sigma",
    "correlation_compute_algo",
    "correlation_compute_doubling",
}

VALID_REGIMES = {
    "baseline",
    "conservative",
    "aggressive",
    "stress_test",
    "mechanical",
    "weak_prior",
    "external",
}


def _sources():
    return load_evidence_table("v0_5_parameter_sources.csv")


def test_every_sampled_input_has_a_source_row():
    params = set(_sources()["param_name"])
    missing = [c for c in SAMPLED_INPUT_COLUMNS if c not in params]
    assert not missing, f"sampled inputs without evidence rows: {missing}"


def test_structural_constants_have_source_rows():
    params = set(_sources()["param_name"])
    missing = [p for p in REQUIRED_STRUCTURAL_PARAMS if p not in params]
    assert not missing, f"structural constants without evidence rows: {missing}"


def test_every_row_has_source_and_regime():
    df = _sources()
    for _, row in df.iterrows():
        assert str(row["source_id"]).strip(), f"{row['param_name']}: empty source_id"
        assert str(row["source_url"]).startswith("http") or row["source_url"] == "(asi.txt)", (
            f"{row['param_name']}: source_url not a URL"
        )
        assert str(row["source_quote"]).strip(), f"{row['param_name']}: empty quote"
        assert row["regime"] in VALID_REGIMES, f"{row['param_name']}: bad regime {row['regime']}"


def test_aggressive_lags_are_flagged_not_baseline():
    """The cognitive-lag pull-forward must be honestly tagged, not sold as baseline."""
    df = _sources().set_index("param_name")
    for p in ("ai_rnd_automation_lag_after_agi_months", "superhuman_ai_researcher_lag_months"):
        assert df.loc[p, "regime"] in {"stress_test", "aggressive"}, (
            f"{p} must be flagged stress_test/aggressive, got {df.loc[p,'regime']}"
        )
