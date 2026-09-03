"""Evaluation API endpoints."""

import json
import os
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from backend.app.schemas.risk import EvaluationResponse, EvaluationMetrics

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

METRICS_DIR = "artifacts/metrics"


def load_json(filename: str) -> Dict[str, Any]:
    path = os.path.join(METRICS_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"Metrics file {filename} not found")
    with open(path) as f:
        return json.load(f)


@router.get("", response_model=EvaluationResponse)
async def get_evaluation():
    """Get full evaluation metrics from artifacts."""
    # Load ablation (main test set results for all models)
    ablation = load_json("ablation.json")

    # Load structural shift (Type F)
    type_f = load_json("structural_shift_f.json")

    # Load future period
    future = load_json("future_period.json")

    # Load thresholds
    thresholds = load_json("threshold.json")

    # Build production candidate (Full Sentinel)
    sentinel = ablation["sentinel"]
    production_candidate = EvaluationMetrics(
        model_name="Full Sentinel (Production)",
        pr_auc=sentinel["pr_auc"],
        roc_auc=sentinel["roc_auc"],
        precision=sentinel["precision"],
        recall=sentinel["recall"],
        f1=sentinel["f1"],
        total_expected_loss=sentinel["financial_metrics"]["total_expected_loss"],
        loss_avoided_vs_baseline=sentinel.get("loss_avoided_vs_baseline_inr", 0.0),
        frozen_threshold=sentinel["frozen_threshold"],
        sample_count=sentinel["sample_count"],
        positive_count=sentinel["positive_count"],
    )

    # Build ablation list (excluding sentinel_interaction which is experimental)
    ablation_models = []
    for name in ["baseline", "graph_enhanced", "temporal_enhanced", "sentinel", "graph_only", "growth_only"]:
        m = ablation[name]
        ablation_models.append(EvaluationMetrics(
            model_name=name,
            pr_auc=m["pr_auc"],
            roc_auc=m["roc_auc"],
            precision=m["precision"],
            recall=m["recall"],
            f1=m["f1"],
            total_expected_loss=m["financial_metrics"]["total_expected_loss"],
            loss_avoided_vs_baseline=m.get("loss_avoided_vs_baseline_inr", 0.0),
            frozen_threshold=m["frozen_threshold"],
            sample_count=m["sample_count"],
            positive_count=m["positive_count"],
        ))

    # Build Type F list
    type_f_models = []
    for name in ["baseline", "graph_enhanced", "temporal_enhanced", "sentinel", "graph_only", "growth_only"]:
        m = type_f[name]
        type_f_models.append(EvaluationMetrics(
            model_name=name,
            pr_auc=m["pr_auc"],
            roc_auc=m["roc_auc"],
            precision=m["precision"],
            recall=m["recall"],
            f1=m["f1"],
            total_expected_loss=m["financial_metrics"]["total_expected_loss"],
            loss_avoided_vs_baseline=m.get("loss_avoided_vs_baseline_inr", 0.0),
            frozen_threshold=m["frozen_threshold"],
            sample_count=m["sample_count"],
            positive_count=m["positive_count"],
        ))

    # Build future period list
    future_models = []
    for name in ["baseline", "graph_enhanced", "temporal_enhanced", "sentinel", "graph_only", "growth_only"]:
        m = future[name]
        future_models.append(EvaluationMetrics(
            model_name=name,
            pr_auc=m["pr_auc"],
            roc_auc=m["roc_auc"],
            precision=m["precision"],
            recall=m["recall"],
            f1=m["f1"],
            total_expected_loss=m["financial_metrics"]["total_expected_loss"],
            loss_avoided_vs_baseline=m.get("loss_avoided_vs_baseline_inr", 0.0),
            frozen_threshold=m["frozen_threshold"],
            sample_count=m["sample_count"],
            positive_count=m["positive_count"],
        ))

    # Phase 5 experiment result
    phase5 = {
        "feature": "graph_neighbor_synchronized_refund_ratio_1h",
        "delta_pr_auc": 0.0004,
        "ci_lower": -0.0089,
        "ci_upper": 0.0097,
        "decision": "STOP",
        "reason": "95% CI includes zero — not statistically significant",
        "model": "Sentinel + Interaction (40 features) — REJECTED",
    }

    return EvaluationResponse(
        production_candidate=production_candidate,
        ablation=ablation_models,
        type_f=type_f_models,
        future_period=future_models,
        phase5_experiment=phase5,
        thresholds=thresholds,
    )