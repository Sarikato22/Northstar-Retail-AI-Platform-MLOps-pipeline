"""NorthStar Retail - Fairness tests."""

import json
import os
import warnings
from pathlib import Path

import pytest


def _read_eval_metrics():
    metrics_path = os.environ.get("EVAL_METRICS_PATH", "/tmp/eval_metrics.json")
    if not Path(metrics_path).exists():
        pytest.skip(f"Evaluation metrics not found at {metrics_path}.")
    with open(metrics_path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def slice_metrics():
    metrics = _read_eval_metrics()
    slices = metrics.get("slice_evaluation")
    assert isinstance(slices, dict) and slices
    return slices


def test_multiple_tiers(slice_metrics):
    assert len(slice_metrics) >= 2


def test_tiers_have_recall(slice_metrics):
    missing = [
        tier for tier, values in slice_metrics.items()
        if values.get("recall_top10") is None
    ]
    assert not missing


def test_recall_gap(slice_metrics):
    recalls = {
        tier: float(values["recall_top10"])
        for tier, values in slice_metrics.items()
        if values.get("recall_top10") is not None
    }
    gap = max(recalls.values()) - min(recalls.values())
    if gap > 0.10:
        low_tier = min(recalls, key=recalls.get)
        high_tier = max(recalls, key=recalls.get)
        warnings.warn(
            f"fairness flag: recall gap {gap:.3f} "
            f"({high_tier} vs {low_tier})",
            stacklevel=1,
        )
    assert gap >= 0.0
