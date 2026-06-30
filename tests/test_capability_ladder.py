from pathlib import Path

import yaml


def test_capability_ladder_has_ordered_checkpoints():
    root = Path(__file__).resolve().parents[1]
    ladder = yaml.safe_load((root / "forecast_inputs" / "capability_ladder.yaml").read_text())

    checkpoints = ladder["checkpoints"]

    assert [checkpoint["id"] for checkpoint in checkpoints] == [
        "CP1",
        "CP2",
        "CP3",
        "CP4",
        "CP5",
        "CP6",
        "CP7",
    ]
    assert [checkpoint["order"] for checkpoint in checkpoints] == list(range(1, 8))
    for checkpoint in checkpoints:
        assert checkpoint["name"]
        assert checkpoint["refined_metric"]
        assert checkpoint["why_it_matters"]
        assert checkpoint["model_mapping"]["primary_stage"]
        assert checkpoint["model_mapping"]["informs"]
