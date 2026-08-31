"""Model evaluation and artifact verification tests for Phase 2."""

import json
import os
import pytest
import pandas as pd

from ml.models.trainer import SentinelModelWrapper


def test_models_exist_and_load():
    """All 4 model artifacts must exist and be loadable."""
    model_paths = {
        "baseline": "artifacts/models/baseline_model.joblib",
        "graph_enhanced": "artifacts/models/graph_model.joblib",
        "temporal_enhanced": "artifacts/models/temporal_model.joblib",
        "sentinel": "artifacts/models/sentinel_model.joblib",
    }
    for name, path in model_paths.items():
        assert os.path.exists(path), f"Model artifact {path} does not exist"
        wrapper = SentinelModelWrapper.load(path)
        assert wrapper.name == name
        assert len(wrapper.feature_names) > 0


def test_metric_artifacts_exist():
    """All expected metric JSON files must exist."""
    required_metrics = [
        "artifacts/metrics/baseline.json",
        "artifacts/metrics/graph_enhanced.json",
        "artifacts/metrics/temporal_enhanced.json",
        "artifacts/metrics/sentinel.json",
        "artifacts/metrics/ablation.json",
        "artifacts/metrics/threshold.json",
        "artifacts/metrics/structural_shift_f.json",
        "artifacts/metrics/future_period.json",
    ]
    for path in required_metrics:
        assert os.path.exists(path), f"Required metric artifact {path} does not exist"
        with open(path) as f:
            data = json.load(f)
            assert len(data) > 0, f"Metric artifact {path} is empty"


def test_plot_and_report_artifacts_exist():
    """All required evaluation plots and report markdown must exist."""
    required_plots = [
        "artifacts/plots/precision_recall.png",
        "artifacts/plots/roc_curves.png",
        "artifacts/plots/ablation_comparison.png",
    ]
    for path in required_plots:
        assert os.path.exists(path), f"Plot artifact {path} does not exist"
        assert os.path.getsize(path) > 1000, f"Plot artifact {path} is suspiciously small"

    report_path = "artifacts/reports/evaluation_summary.md"
    assert os.path.exists(report_path), f"Report {report_path} does not exist"
    with open(report_path, encoding="utf-8") as f:
        content = f.read()
        assert "Behavioral Baseline" in content
        assert "Full Sentinel" in content
        assert "Ring Type F" in content
