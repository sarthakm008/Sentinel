"""CLI script to run ablation study and generate metrics, plots, and evaluation reports."""

import argparse
import os
import pandas as pd

from ml.evaluation.evaluator import SentinelEvaluator
from ml.models.trainer import SentinelModelWrapper


def run_evaluation(data_dir: str = "data", artifacts_dir: str = "artifacts"):
    print("=== Sentinel Evaluation & Ablation Suite ===")

    models_dir = os.path.join(artifacts_dir, "models")
    processed_val = os.path.join(data_dir, "processed", "features_validation.parquet")
    processed_test = os.path.join(data_dir, "processed", "features_test.parquet")
    raw_rings = os.path.join(data_dir, "raw", "ground_truth_rings.parquet")

    # Load feature matrices
    df_val = pd.read_parquet(processed_val)
    df_test = pd.read_parquet(processed_test)
    rings_df = pd.read_parquet(raw_rings)

    # Load trained models
    models = {
        "baseline": SentinelModelWrapper.load(os.path.join(models_dir, "baseline_model.joblib")),
        "graph_enhanced": SentinelModelWrapper.load(os.path.join(models_dir, "graph_model.joblib")),
        "temporal_enhanced": SentinelModelWrapper.load(os.path.join(models_dir, "temporal_model.joblib")),
        "sentinel": SentinelModelWrapper.load(os.path.join(models_dir, "sentinel_model.joblib")),
        "graph_only": SentinelModelWrapper.load(os.path.join(models_dir, "graph_only_model.joblib")),
        "growth_only": SentinelModelWrapper.load(os.path.join(models_dir, "growth_only_model.joblib")),
        "sentinel_interaction": SentinelModelWrapper.load(os.path.join(models_dir, "sentinel_interaction_model.joblib")),
    }

    evaluator = SentinelEvaluator(artifacts_dir=artifacts_dir)
    results = evaluator.run_full_evaluation(models, df_val, df_test, rings_df)

    print("\n=== Evaluation Completed Successfully ===")
    print("Summary of Held-Out Test Set Results:")
    for m_name, res in results["test_summary"].items():
        loss = res["financial_metrics"]["total_expected_loss"]
        loss_avoided = res.get("loss_avoided_vs_baseline_inr", 0.0)
        print(f"  [{m_name:18s}] PR-AUC: {res['pr_auc']:.4f} | F1: {res['f1']:.4f} | Precision: {res['precision']:.4f} | Recall: {res['recall']:.4f} | Loss: INR {loss:,.2f} | Loss Avoided: INR {loss_avoided:,.2f}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate Sentinel Model Suite")
    parser.add_argument("--data-dir", type=str, default="data")
    parser.add_argument("--artifacts-dir", type=str, default="artifacts")
    args = parser.parse_args()

    run_evaluation(data_dir=args.data_dir, artifacts_dir=args.artifacts_dir)
