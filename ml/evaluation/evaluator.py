"""Evaluation suite, validation threshold selector, economic cost modeling, and reporting."""

import json
import os
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

from ml.models.trainer import SentinelModelWrapper


class ActionPolicy:
    """Action policy thresholds mapping risk probability to merchant decisions."""

    def __init__(self, threshold_optimal: float, review_cost: float = 50.0, friction_cost: float = 150.0):
        self.threshold_optimal = threshold_optimal
        self.review_cost = review_cost
        self.friction_cost = friction_cost
        
        # Policy boundaries
        self.threshold_low = max(0.10, threshold_optimal * 0.5)
        self.threshold_high = min(0.90, threshold_optimal + (1.0 - threshold_optimal) * 0.5)

    def decide(self, prob: float) -> str:
        if prob < self.threshold_low:
            return "approve"  # allow
        elif prob < self.threshold_optimal:
            return "verify"   # verify
        elif prob < self.threshold_high:
            return "review"   # manual review
        else:
            return "hold"     # block / hold


class SentinelEvaluator:
    """Evaluates Sentinel model suite on validation and held-out test sets."""

    def __init__(
        self,
        review_cost: float = 50.0,
        friction_cost: float = 150.0,
        artifacts_dir: str = "artifacts",
    ):
        self.review_cost = review_cost
        self.friction_cost = friction_cost
        self.artifacts_dir = artifacts_dir
        self.metrics_dir = os.path.join(artifacts_dir, "metrics")
        self.plots_dir = os.path.join(artifacts_dir, "plots")
        self.reports_dir = os.path.join(artifacts_dir, "reports")

        os.makedirs(self.metrics_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def compute_financial_cost(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        refund_amounts: np.ndarray
    ) -> Dict[str, float]:
        """Computes expected economic loss under prototype cost assumptions."""
        fn_mask = (y_true == 1) & (y_pred == 0)
        fp_mask = (y_true == 0) & (y_pred == 1)
        tp_mask = (y_true == 1) & (y_pred == 1)

        fn_cost = float(refund_amounts[fn_mask].sum())
        fp_cost = float(fp_mask.sum() * (self.review_cost + self.friction_cost))
        tp_cost = float(tp_mask.sum() * self.review_cost)
        total_loss = fn_cost + fp_cost + tp_cost

        return {
            "false_negative_loss": round(fn_cost, 2),
            "false_positive_loss": round(fp_cost, 2),
            "review_cost_tp": round(tp_cost, 2),
            "total_expected_loss": round(total_loss, 2),
            "fn_count": int(fn_mask.sum()),
            "fp_count": int(fp_mask.sum()),
            "tp_count": int(tp_mask.sum()),
            "tn_count": int(((y_true == 0) & (y_pred == 0)).sum()),
        }

    def select_threshold_on_validation(
        self,
        model: SentinelModelWrapper,
        df_val: pd.DataFrame
    ) -> Tuple[float, Dict[str, float]]:
        """Sweeps threshold on validation set to find cost-minimizing threshold."""
        y_val = df_val["label"].values
        amounts_val = df_val["refund_amount"].values
        probs_val = model.predict_proba(df_val)

        thresholds = np.linspace(0.05, 0.95, 91)
        best_threshold = 0.50
        min_loss = float("inf")
        best_costs = {}

        for th in thresholds:
            preds = (probs_val >= th).astype(int)
            costs = self.compute_financial_cost(y_val, preds, amounts_val)
            if costs["total_expected_loss"] < min_loss:
                min_loss = costs["total_expected_loss"]
                best_threshold = float(th)
                best_costs = costs

        return best_threshold, best_costs

    def evaluate_model_on_dataset(
        self,
        model: SentinelModelWrapper,
        df_eval: pd.DataFrame,
        threshold: float,
        dataset_name: str = "test"
    ) -> Dict:
        """Evaluates a model on a given dataset using a frozen threshold."""
        y_true = df_eval["label"].values
        amounts = df_eval["refund_amount"].values
        probs = model.predict_proba(df_eval)
        preds = (probs >= threshold).astype(int)

        prec = float(precision_score(y_true, preds, zero_division=0))
        rec = float(recall_score(y_true, preds, zero_division=0))
        f1 = float(f1_score(y_true, preds, zero_division=0))
        pr_auc = float(average_precision_score(y_true, probs))
        roc_auc = float(roc_auc_score(y_true, probs))

        costs = self.compute_financial_cost(y_true, preds, amounts)

        return {
            "model_name": model.name,
            "dataset": dataset_name,
            "sample_count": len(df_eval),
            "positive_count": int(y_true.sum()),
            "frozen_threshold": round(threshold, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "financial_metrics": costs,
            "probabilities": probs,
            "labels": y_true,
            "amounts": amounts,
        }

    def run_full_evaluation(
        self,
        models: Dict[str, SentinelModelWrapper],
        df_val: pd.DataFrame,
        df_test: pd.DataFrame,
        rings_df: pd.DataFrame
    ) -> Dict:
        print("=== Running Full Validation and Held-Out Test Evaluation ===")
        
        # 1. Validation Threshold Selection
        thresholds = {}
        for name, model in models.items():
            th, _ = self.select_threshold_on_validation(model, df_val)
            thresholds[name] = th
            print(f"  [{name}] Validation-Selected Cost-Minimizing Threshold: {th:.2f}")

        with open(os.path.join(self.metrics_dir, "threshold.json"), "w") as f:
            json.dump(thresholds, f, indent=2)

        # 2. Evaluate on Full Held-Out Test Set
        test_results = {}
        for name, model in models.items():
            res = self.evaluate_model_on_dataset(model, df_test, thresholds[name], dataset_name="held_out_test")
            test_results[name] = res

        # 3. Compute Loss Avoided vs Baseline
        baseline_loss = test_results["baseline"]["financial_metrics"]["total_expected_loss"]
        for name in models:
            loss = test_results[name]["financial_metrics"]["total_expected_loss"]
            loss_avoided = baseline_loss - loss
            test_results[name]["loss_avoided_vs_baseline_inr"] = round(loss_avoided, 2)

        # 4. Evaluate Structural Shift: Ring Type F Subset
        print("=== Evaluating Out-of-Distribution Shift: Ring Type F ===")
        type_f_rings = rings_df[rings_df["ring_type"] == "type_f_structural_shift"]
        type_f_custs = set()
        for _, r in type_f_rings.iterrows():
            type_f_custs.update(json.loads(r["customer_ids"]))

        df_test_type_f = df_test[df_test["customer_id"].isin(type_f_custs)].copy()

        type_f_eval = {}
        for name, model in models.items():
            f_res = self.evaluate_model_on_dataset(model, df_test_type_f, thresholds[name], dataset_name="ring_type_f_shift")
            type_f_eval[name] = f_res

        # 5. Future-Period Temporal Holdout Evaluation (last 60 days of 180-day timeline)
        print("=== Evaluating Future-Period Temporal Holdout (Days 120-180) ===")
        t_ref_series = pd.to_datetime(df_test["timestamp_refund"], format="ISO8601")
        t_min = t_ref_series.min()
        day_indices = (t_ref_series - t_min).dt.total_seconds() / 86400.0
        
        df_test_future = df_test[day_indices >= 120.0].copy()
        future_eval = {}
        for name, model in models.items():
            fut_res = self.evaluate_model_on_dataset(model, df_test_future, thresholds[name], dataset_name="future_period_holdout")
            future_eval[name] = fut_res

        # 6. Save Metric JSONs (without raw numpy arrays)
        clean_summary = {}
        for name in models:
            clean_res = {k: v for k, v in test_results[name].items() if k not in ["probabilities", "labels", "amounts"]}
            clean_summary[name] = clean_res
            with open(os.path.join(self.metrics_dir, f"{name}.json"), "w") as f:
                json.dump(clean_res, f, indent=2)

        with open(os.path.join(self.metrics_dir, "ablation.json"), "w") as f:
            json.dump(clean_summary, f, indent=2)

        type_f_clean = {k: {k2: v2 for k2, v2 in v.items() if k2 not in ["probabilities", "labels", "amounts"]} for k, v in type_f_eval.items()}
        with open(os.path.join(self.metrics_dir, "structural_shift_f.json"), "w") as f:
            json.dump(type_f_clean, f, indent=2)

        future_clean = {k: {k2: v2 for k2, v2 in v.items() if k2 not in ["probabilities", "labels", "amounts"]} for k, v in future_eval.items()}
        with open(os.path.join(self.metrics_dir, "future_period.json"), "w") as f:
            json.dump(future_clean, f, indent=2)

        # 7. Generate Evaluation Plots
        self._generate_plots(test_results, thresholds)

        # 8. Generate Comprehensive Evaluation Report
        self._generate_markdown_report(test_results, type_f_eval, future_eval, thresholds)

        return {
            "test_summary": clean_summary,
            "type_f_summary": type_f_clean,
            "future_summary": future_clean,
            "thresholds": thresholds,
        }

    def _generate_plots(self, test_results: Dict, thresholds: Dict):
        colors = {
            "baseline": "#6c757d",
            "graph_enhanced": "#0d6efd",
            "temporal_enhanced": "#fd7e14",
            "sentinel": "#198754",
            "graph_only": "#6f42c1",
            "growth_only": "#20c997",
            "sentinel_interaction": "#e83e8c",
        }
        labels_map = {
            "baseline": "Behavioral Baseline",
            "graph_enhanced": "Graph-Enhanced",
            "temporal_enhanced": "Temporal-Enhanced",
            "sentinel": "Full Sentinel",
            "graph_only": "Graph-Only",
            "growth_only": "Growth-Only",
            "sentinel_interaction": "Sentinel + Interaction",
        }

        # Plot 1: Precision-Recall Curves
        plt.figure(figsize=(8, 6))
        for name, res in test_results.items():
            prec, rec, _ = precision_recall_curve(res["labels"], res["probabilities"])
            plt.plot(rec, prec, label=f"{labels_map[name]} (PR-AUC = {res['pr_auc']:.3f})", color=colors[name], lw=2)
        plt.xlabel("Recall", fontsize=12)
        plt.ylabel("Precision", fontsize=12)
        plt.title("Precision-Recall Curves on Held-Out Test Set", fontsize=14)
        plt.legend(loc="lower left", fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "precision_recall.png"), dpi=150)
        plt.close()

        # Plot 2: ROC Curves
        plt.figure(figsize=(8, 6))
        for name, res in test_results.items():
            fpr, tpr, _ = roc_curve(res["labels"], res["probabilities"])
            plt.plot(fpr, tpr, label=f"{labels_map[name]} (ROC-AUC = {res['roc_auc']:.3f})", color=colors[name], lw=2)
        plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
        plt.xlabel("False Positive Rate", fontsize=12)
        plt.ylabel("True Positive Rate", fontsize=12)
        plt.title("ROC Curves on Held-Out Test Set", fontsize=14)
        plt.legend(loc="lower right", fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "roc_curves.png"), dpi=150)
        plt.close()

        # Plot 3: Ablation Bar Comparison
        models_list = list(test_results.keys())
        pr_aucs = [test_results[m]["pr_auc"] for m in models_list]
        f1s = [test_results[m]["f1"] for m in models_list]
        losses = [test_results[m]["financial_metrics"]["total_expected_loss"] / 1000.0 for m in models_list]

        x = np.arange(len(models_list))
        width = 0.25

        fig, ax1 = plt.subplots(figsize=(10, 6))
        rects1 = ax1.bar(x - width, pr_aucs, width, label="PR-AUC", color="#0d6efd")
        rects2 = ax1.bar(x, f1s, width, label="F1 Score", color="#198754")
        ax1.set_ylabel("Score [0 - 1]", fontsize=12)
        ax1.set_ylim(0, 1.05)
        ax1.set_xticks(x)
        ax1.set_xticklabels([labels_map[m] for m in models_list], fontsize=11)

        ax2 = ax1.twinx()
        rects3 = ax2.bar(x + width, losses, width, label="Total Loss (k INR)", color="#dc3545", alpha=0.8)
        ax2.set_ylabel("Expected Loss (k INR)", fontsize=12, color="#dc3545")

        plt.title("Ablation Study: Metrics and Financial Impact Comparison", fontsize=14)
        fig.tight_layout()
        plt.savefig(os.path.join(self.plots_dir, "ablation_comparison.png"), dpi=150)
        plt.close()

    def _generate_markdown_report(
        self,
        test_results: Dict,
        type_f_eval: Dict,
        future_eval: Dict,
        thresholds: Dict
    ):
        report_path = os.path.join(self.reports_dir, "evaluation_summary.md")
        
        lines = [
            "# Sentinel — Scientific Evaluation Summary",
            "",
            "## 1. Executive Summary & Core Hypothesis",
            "",
            "> **Question:** Does adding relationship and temporal intelligence materially improve detection of coordinated refund abuse compared with a strong individual-level behavioral baseline, on a genuinely held-out test set with no entity/ring leakage?",
            "",
            "### Primary Comparison on Held-Out Test Set",
            "",
            "| Model | PR-AUC | ROC-AUC | Precision | Recall | F1 Score | Total Expected Loss (INR) | Loss Avoided vs Baseline |",
            "|---|---|---|---|---|---|---|---|",
            f"| **Behavioral Baseline** | {test_results['baseline']['pr_auc']:.4f} | {test_results['baseline']['roc_auc']:.4f} | {test_results['baseline']['precision']:.4f} | {test_results['baseline']['recall']:.4f} | {test_results['baseline']['f1']:.4f} | INR {test_results['baseline']['financial_metrics']['total_expected_loss']:,.2f} | — |",
            f"| **Graph-Enhanced** | {test_results['graph_enhanced']['pr_auc']:.4f} | {test_results['graph_enhanced']['roc_auc']:.4f} | {test_results['graph_enhanced']['precision']:.4f} | {test_results['graph_enhanced']['recall']:.4f} | {test_results['graph_enhanced']['f1']:.4f} | INR {test_results['graph_enhanced']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['graph_enhanced']['loss_avoided_vs_baseline_inr']:,.2f} |",
            f"| **Temporal-Enhanced** | {test_results['temporal_enhanced']['pr_auc']:.4f} | {test_results['temporal_enhanced']['roc_auc']:.4f} | {test_results['temporal_enhanced']['precision']:.4f} | {test_results['temporal_enhanced']['recall']:.4f} | {test_results['temporal_enhanced']['f1']:.4f} | INR {test_results['temporal_enhanced']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['temporal_enhanced']['loss_avoided_vs_baseline_inr']:,.2f} |",
            f"| **Full Sentinel** | **{test_results['sentinel']['pr_auc']:.4f}** | **{test_results['sentinel']['roc_auc']:.4f}** | **{test_results['sentinel']['precision']:.4f}** | **{test_results['sentinel']['recall']:.4f}** | **{test_results['sentinel']['f1']:.4f}** | **INR {test_results['sentinel']['financial_metrics']['total_expected_loss']:,.2f}** | **INR {test_results['sentinel']['loss_avoided_vs_baseline_inr']:,.2f}** |",
            f"| **Graph-Only** | {test_results['graph_only']['pr_auc']:.4f} | {test_results['graph_only']['roc_auc']:.4f} | {test_results['graph_only']['precision']:.4f} | {test_results['graph_only']['recall']:.4f} | {test_results['graph_only']['f1']:.4f} | INR {test_results['graph_only']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['graph_only']['loss_avoided_vs_baseline_inr']:,.2f} |",
            f"| **Sentinel + Interaction** | {test_results['sentinel_interaction']['pr_auc']:.4f} | {test_results['sentinel_interaction']['roc_auc']:.4f} | {test_results['sentinel_interaction']['precision']:.4f} | {test_results['sentinel_interaction']['recall']:.4f} | {test_results['sentinel_interaction']['f1']:.4f} | INR {test_results['sentinel_interaction']['financial_metrics']['total_expected_loss']:,.2f} | INR {test_results['sentinel_interaction']['loss_avoided_vs_baseline_inr']:,.2f} |",
            "",
            "---",
            "",
            "## 2. Out-of-Distribution Generalization: Ring Type F (Structural Shift)",
            "",
            "Ring Type F represents relay chains and slow-drip campaigns where marginals match standard rings.",
            "",
            "| Model | PR-AUC (Type F) | Precision (Type F) | Recall (Type F) | F1 Score (Type F) |",
            "|---|---|---|---|---|",
            f"| **Behavioral Baseline** | {type_f_eval['baseline']['pr_auc']:.4f} | {type_f_eval['baseline']['precision']:.4f} | {type_f_eval['baseline']['recall']:.4f} | {type_f_eval['baseline']['f1']:.4f} |",
            f"| **Graph-Enhanced** | {type_f_eval['graph_enhanced']['pr_auc']:.4f} | {type_f_eval['graph_enhanced']['precision']:.4f} | {type_f_eval['graph_enhanced']['recall']:.4f} | {type_f_eval['graph_enhanced']['f1']:.4f} |",
            f"| **Temporal-Enhanced** | {type_f_eval['temporal_enhanced']['pr_auc']:.4f} | {type_f_eval['temporal_enhanced']['precision']:.4f} | {type_f_eval['temporal_enhanced']['recall']:.4f} | {type_f_eval['temporal_enhanced']['f1']:.4f} |",
            f"| **Full Sentinel** | **{type_f_eval['sentinel']['pr_auc']:.4f}** | **{type_f_eval['sentinel']['precision']:.4f}** | **{type_f_eval['sentinel']['recall']:.4f}** | **{type_f_eval['sentinel']['f1']:.4f}** |",
            f"| **Graph-Only** | {type_f_eval['graph_only']['pr_auc']:.4f} | {type_f_eval['graph_only']['precision']:.4f} | {type_f_eval['graph_only']['recall']:.4f} | {type_f_eval['graph_only']['f1']:.4f} |",
            f"| **Sentinel + Interaction** | {type_f_eval['sentinel_interaction']['pr_auc']:.4f} | {type_f_eval['sentinel_interaction']['precision']:.4f} | {type_f_eval['sentinel_interaction']['recall']:.4f} | {type_f_eval['sentinel_interaction']['f1']:.4f} |",
            "",
            "---",
            "",
            "## 3. Future-Period Temporal Holdout (Days 120–180)",
            "",
            "| Model | PR-AUC (Future) | Precision (Future) | Recall (Future) | F1 Score (Future) |",
            "|---|---|---|---|---|",
            f"| **Behavioral Baseline** | {future_eval['baseline']['pr_auc']:.4f} | {future_eval['baseline']['precision']:.4f} | {future_eval['baseline']['recall']:.4f} | {future_eval['baseline']['f1']:.4f} |",
            f"| **Graph-Enhanced** | {future_eval['graph_enhanced']['pr_auc']:.4f} | {future_eval['graph_enhanced']['precision']:.4f} | {future_eval['graph_enhanced']['recall']:.4f} | {future_eval['graph_enhanced']['f1']:.4f} |",
            f"| **Temporal-Enhanced** | {future_eval['temporal_enhanced']['pr_auc']:.4f} | {future_eval['temporal_enhanced']['precision']:.4f} | {future_eval['temporal_enhanced']['recall']:.4f} | {future_eval['temporal_enhanced']['f1']:.4f} |",
            f"| **Full Sentinel** | **{future_eval['sentinel']['pr_auc']:.4f}** | **{future_eval['sentinel']['precision']:.4f}** | **{future_eval['sentinel']['recall']:.4f}** | **{future_eval['sentinel']['f1']:.4f}** |",
            f"| **Graph-Only** | {future_eval['graph_only']['pr_auc']:.4f} | {future_eval['graph_only']['precision']:.4f} | {future_eval['graph_only']['recall']:.4f} | {future_eval['graph_only']['f1']:.4f} |",
            f"| **Sentinel + Interaction** | {future_eval['sentinel_interaction']['pr_auc']:.4f} | {future_eval['sentinel_interaction']['precision']:.4f} | {future_eval['sentinel_interaction']['recall']:.4f} | {future_eval['sentinel_interaction']['f1']:.4f} |",
            "",
            "---",
            "",
            "## 4. Frozen Validation Thresholds & Cost Model Parameters",
            "",
            "- **Review Cost (C_review):** INR 50.00",
            "- **Customer Friction Cost (C_friction):** INR 150.00",
            "- **Threshold Selection:** Minimized validation expected financial loss.",
            "- **Frozen Thresholds:**",
            f"  - Baseline: {thresholds['baseline']:.2f}",
            f"  - Graph-Enhanced: {thresholds['graph_enhanced']:.2f}",
            f"  - Temporal-Enhanced: {thresholds['temporal_enhanced']:.2f}",
            f"  - Full Sentinel: {thresholds['sentinel']:.2f}",
            f"  - Graph-Only: {thresholds['graph_only']:.2f}",
            f"  - Growth-Only: {thresholds['growth_only']:.2f}",
            f"  - Sentinel + Interaction: {thresholds['sentinel_interaction']:.2f}",
            ""
        ]

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"  -> Generated evaluation summary report: {report_path}")
