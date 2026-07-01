"""Load and validate plain-text evidence tables."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .helpers import project_root


EXPECTED_COLUMNS = {
    "extracted_assumptions.csv": {
        "source_id",
        "date_extracted",
        "target_variable",
        "extracted_claim_text",
        "quantified_value",
        "unit",
        "assessor_notes",
    },
    "trend_inputs.csv": {
        "date",
        "metric_name",
        "value",
        "unit",
        "source_id",
        "data_type",
    },
    "outside_forecasts.csv": {
        "date_recorded",
        "forecaster_name",
        "p25_date",
        "median_date",
        "p75_date",
        "definition_used",
    },
    "data_inventory.csv": {
        "category",
        "exact_variable_name",
        "unit",
        "ideal_source",
        "backup_source",
        "update_frequency",
        "reliability",
        "conversion_to_model_input",
        "scraping_status",
    },
    "agi_evidence.csv": {
        "source_id",
        "date",
        "target",
        "claim",
        "quantified_value",
        "unit",
        "confidence",
        "notes",
        "url",
    },
    "asi_evidence.csv": {
        "source_id",
        "date",
        "target",
        "claim",
        "quantified_value",
        "unit",
        "confidence",
        "notes",
        "url",
    },
    "intermediate_milestones.csv": {
        "source_id",
        "date",
        "milestone",
        "claim",
        "variable",
        "low",
        "mode",
        "high",
        "unit",
        "confidence",
        "notes",
        "url",
    },
    # v0.5 authoritative provenance for the live engine parameters. Each row maps a
    # sampled input / structural constant (param_name) to a source, quote, and regime.
    "v0_5_parameter_sources.csv": {
        "param_name",
        "value",
        "units",
        "regime",
        "source_id",
        "source_url",
        "source_quote",
        "justification_summary",
    },
}


def evidence_tables_dir() -> Path:
    """Return the evidence table directory."""
    return project_root() / "evidence_tables"


def load_evidence_table(filename: str) -> pd.DataFrame:
    """Load one evidence table and validate its required columns."""
    if filename not in EXPECTED_COLUMNS:
        raise ValueError(f"Unknown evidence table: {filename}")

    path = evidence_tables_dir() / filename
    frame = pd.read_csv(path)
    missing = EXPECTED_COLUMNS[filename] - set(frame.columns)
    if missing:
        raise ValueError(f"{filename} is missing columns: {sorted(missing)}")
    return frame


def load_all_evidence_tables() -> dict[str, pd.DataFrame]:
    """Load all known evidence tables."""
    return {
        filename: load_evidence_table(filename)
        for filename in sorted(EXPECTED_COLUMNS)
    }
