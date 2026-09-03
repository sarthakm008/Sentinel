"""Benchmark Hardness and Scientific Shortcut Elimination Tests for Phase 2.5."""

import json
import os
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from ml.features.extractor import ALL_FEATURES, PointInTimeFeatureExtractor


def compute_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Compute Cohen's d effect size between two samples."""
    nx, ny = len(x), len(y)
    vx, vy = np.var(x, ddof=1), np.var(y, ddof=1)
    pooled_sd = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / max(1, (nx + ny - 2)))
    if pooled_sd == 0:
        return 0.0
    return float(abs(np.mean(x) - np.mean(y)) / pooled_sd)


@pytest.fixture(scope="module")
def processed_datasets():
    df_train = pd.read_parquet("data/processed/features_train.parquet")
    df_val = pd.read_parquet("data/processed/features_validation.parquet")
    df_test = pd.read_parquet("data/processed/features_test.parquet")
    rings_df = pd.read_parquet("data/raw/ground_truth_rings.parquet")
    return df_train, df_val, df_test, rings_df


def test_no_near_perfect_univariate_shortcut(processed_datasets):
    """Assert refund_delay_hours and customer_account_age_days have univariate ROC-AUC < 0.65."""
    df_train, df_val, df_test, _ = processed_datasets
    
    for name, df in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        y = df["label"].values
        
        # 1. Refund Delay
        delay_vals = df["refund_delay_hours"].values
        auc_delay = max(roc_auc_score(y, delay_vals), 1.0 - roc_auc_score(y, delay_vals))
        assert auc_delay < 0.65, f"[{name}] refund_delay_hours univariate ROC-AUC is too high: {auc_delay:.4f} (must be < 0.65)"
        
        # 2. Account Age
        age_vals = df["customer_account_age_days"].values
        auc_age = max(roc_auc_score(y, age_vals), 1.0 - roc_auc_score(y, age_vals))
        assert auc_age < 0.65, f"[{name}] customer_account_age_days univariate ROC-AUC is too high: {auc_age:.4f} (must be < 0.65)"


def test_no_near_perfect_univariate_shortcut_core_graph(processed_datasets):
    """Assert Core Graph features have univariate ROC-AUC < 0.90 (no near-perfect shortcuts).
    
    Core Graph features are legitimate predictive signals and may have moderate AUC (0.6-0.75).
    Only near-deterministic shortcuts (AUC >= 0.90) are failures.
    """
    df_train, df_val, df_test, _ = processed_datasets
    
    core_graph_features = [
        "graph_shared_device_rarity",
        "graph_shared_address_rarity",
        "graph_shared_payment_rarity",
        "graph_neighbor_max_refund_rate",
        "graph_neighbor_risk_mass",
        "graph_shared_device_recency_h",
        "graph_shared_address_recency_h",
    ]
    
    for name, df in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        y = df["label"].values
        
        for feat in core_graph_features:
            vals = df[feat].values
            auc = max(roc_auc_score(y, vals), 1.0 - roc_auc_score(y, vals))
            assert auc < 0.90, f"[{name}] {feat} univariate ROC-AUC is near-perfect: {auc:.4f} (must be < 0.90)"


def test_no_near_perfect_univariate_feature(processed_datasets):
    """Assert no single raw feature achieves near-perfect univariate ROC-AUC (>= 0.90).
    
    Moderately predictive behavioral features (e.g., customer_refund_rate) are expected
    and valid. Only near-deterministic shortcuts (AUC >= 0.90) are failures.
    """
    df_train, _, _, _ = processed_datasets
    y_train = df_train["label"].values

    feature_aucs = []
    for feat in ALL_FEATURES:
        vals = df_train[feat].values
        auc = max(roc_auc_score(y_train, vals), 1.0 - roc_auc_score(y_train, vals))
        feature_aucs.append((feat, auc))

    # Sort by AUC descending and report top features
    feature_aucs.sort(key=lambda x: x[1], reverse=True)
    
    print("\n=== Top Univariate Feature AUCs (Train) ===")
    for feat, auc in feature_aucs[:10]:
        print(f"  {feat}: {auc:.4f}")

    # Fail only on near-perfect separation (AUC >= 0.90)
    for feat, auc in feature_aucs:
        assert auc < 0.90, f"Raw feature {feat} has near-perfect univariate ROC-AUC: {auc:.4f} (limit 0.90)"


def test_distribution_overlap_cohens_d(processed_datasets):
    """Assert standardized mean difference (Cohen's d) is < 0.50 for delay and age."""
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    d_delay = compute_cohens_d(pos["refund_delay_hours"].values, neg["refund_delay_hours"].values)
    d_age = compute_cohens_d(pos["customer_account_age_days"].values, neg["customer_account_age_days"].values)

    assert d_delay < 0.50, f"Cohen's d for refund_delay_hours is too high: {d_delay:.4f} (must be < 0.50)"
    assert d_age < 0.50, f"Cohen's d for customer_account_age_days is too high: {d_age:.4f} (must be < 0.50)"


def test_distribution_overlap_cohens_d_core_graph(processed_datasets):
    """Assert Cohen's d < 1.0 for Core Graph features (moderate effect sizes acceptable).
    
    Core Graph features are legitimate predictive signals. Large effect sizes (d < 1.0)
    are expected for features that genuinely discriminate between abuse and legitimate.
    Only extreme effect sizes (d >= 1.0) would suggest a potential shortcut.
    """
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    core_graph_features = [
        "graph_shared_device_rarity",
        "graph_shared_address_rarity",
        "graph_shared_payment_rarity",
        "graph_neighbor_max_refund_rate",
        "graph_neighbor_risk_mass",
        "graph_shared_device_recency_h",
        "graph_shared_address_recency_h",
    ]
    
    for feat in core_graph_features:
        d = compute_cohens_d(pos[feat].values, neg[feat].values)
        assert d < 1.0, f"Cohen's d for {feat} is extreme: {d:.4f} (must be < 1.0)"


def test_quantile_overlap_coverage(processed_datasets):
    """Assert quantiles for delay and age show substantial mutual coverage."""
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    # Check that 25th-75th IQR of positives heavily overlaps with negatives
    pos_q25_delay, pos_q75_delay = pos["refund_delay_hours"].quantile(0.25), pos["refund_delay_hours"].quantile(0.75)
    neg_q25_delay, neg_q75_delay = neg["refund_delay_hours"].quantile(0.25), neg["refund_delay_hours"].quantile(0.75)

    overlap_delay = min(pos_q75_delay, neg_q75_delay) - max(pos_q25_delay, neg_q25_delay)
    assert overlap_delay > 0, "No IQR overlap in refund delay distributions"

    pos_q25_age, pos_q75_age = pos["customer_account_age_days"].quantile(0.25), pos["customer_account_age_days"].quantile(0.75)
    neg_q25_age, neg_q75_age = neg["customer_account_age_days"].quantile(0.25), neg["customer_account_age_days"].quantile(0.75)

    overlap_age = min(pos_q75_age, neg_q75_age) - max(pos_q25_age, neg_q25_age)
    assert overlap_age > 0, "No IQR overlap in account age distributions"


def test_quantile_overlap_coverage_core_graph(processed_datasets):
    """Assert Core Graph features have reasonable distributions.
    
    Verifies features have non-zero variance in both classes and are not
    completely separated (which would indicate a shortcut).
    """
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    core_graph_features = [
        "graph_shared_device_rarity",
        "graph_shared_address_rarity",
        "graph_shared_payment_rarity",
        "graph_neighbor_max_refund_rate",
        "graph_neighbor_risk_mass",
        "graph_shared_device_recency_h",
        "graph_shared_address_recency_h",
    ]
    
    for feat in core_graph_features:
        # Both classes should have non-zero variance
        assert pos[feat].var() > 0, f"{feat} has zero variance in positive class"
        assert neg[feat].var() > 0, f"{feat} has zero variance in negative class"
        
        # Neither class should be completely separated from the other
        # (min/max of one class should not be completely outside the other)
        pos_min, pos_max = pos[feat].min(), pos[feat].max()
        neg_min, neg_max = neg[feat].min(), neg[feat].max()
        
        # At least some overlap in ranges
        range_overlap = min(pos_max, neg_max) - max(pos_min, neg_min)
        assert range_overlap >= 0, f"{feat} has completely separated ranges: pos=[{pos_min:.4f}, {pos_max:.4f}], neg=[{neg_min:.4f}, {neg_max:.4f}]"


def test_split_prevalence_balance(processed_datasets):
    """Assert standard split prevalence (Train, Val, Test A-E) is balanced within +- 3.5%."""
    df_train, df_val, df_test, rings_df = processed_datasets
    
    # Exclude Type F from Test to measure standard split prevalence
    type_f_rings = rings_df[rings_df["ring_type"] == "type_f_structural_shift"]
    type_f_custs = set()
    for _, r in type_f_rings.iterrows():
        type_f_custs.update(json.loads(r["customer_ids"]))

    df_test_standard = df_test[~df_test["customer_id"].isin(type_f_custs)]

    prev_train = df_train["label"].mean()
    prev_val = df_val["label"].mean()
    prev_test_std = df_test_standard["label"].mean()

    assert abs(prev_train - prev_val) < 0.035, f"Train vs Val prevalence difference too large: {prev_train:.3f} vs {prev_val:.3f}"
    assert abs(prev_train - prev_test_std) < 0.035, f"Train vs Test (A-E) prevalence difference too large: {prev_train:.3f} vs {prev_test_std:.3f}"


def test_no_near_perfect_univariate_shortcut_interaction(processed_datasets):
    """Assert interaction feature has univariate ROC-AUC < 0.90 (no near-perfect shortcuts).
    
    Interaction features are legitimate predictive signals and may have moderate AUC (0.6-0.75).
    Only near-deterministic shortcuts (AUC >= 0.90) are failures.
    """
    df_train, df_val, df_test, _ = processed_datasets
    
    interaction_features = [
        "graph_neighbor_synchronized_refund_ratio_1h",
    ]
    
    for name, df in [("Train", df_train), ("Val", df_val), ("Test", df_test)]:
        y = df["label"].values
        
        for feat in interaction_features:
            vals = df[feat].values
            auc = max(roc_auc_score(y, vals), 1.0 - roc_auc_score(y, vals))
            assert auc < 0.90, f"[{name}] {feat} univariate ROC-AUC is near-perfect: {auc:.4f} (must be < 0.90)"


def test_distribution_overlap_cohens_d_interaction(processed_datasets):
    """Assert Cohen's d < 1.0 for Interaction features (moderate effect sizes acceptable).
    
    Interaction features are legitimate predictive signals. Large effect sizes (d < 1.0)
    are expected for features that genuinely discriminate between abuse and legitimate.
    Only extreme effect sizes (d >= 1.0) would suggest a potential shortcut.
    """
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    interaction_features = [
        "graph_neighbor_synchronized_refund_ratio_1h",
    ]
    
    for feat in interaction_features:
        d = compute_cohens_d(pos[feat].values, neg[feat].values)
        assert d < 1.0, f"Cohen's d for {feat} is extreme: {d:.4f} (must be < 1.0)"


def test_quantile_overlap_coverage_interaction(processed_datasets):
    """Assert range overlap for Interaction features.
    
    Verifies features have non-zero variance in both classes and are not
    completely separated (which would indicate a shortcut).
    """
    df_train, _, _, _ = processed_datasets
    pos = df_train[df_train["label"] == 1]
    neg = df_train[df_train["label"] == 0]

    interaction_features = [
        "graph_neighbor_synchronized_refund_ratio_1h",
    ]
    
    for feat in interaction_features:
        # Both classes should have non-zero variance
        assert pos[feat].var() > 0, f"{feat} has zero variance in positive class"
        assert neg[feat].var() > 0, f"{feat} has zero variance in negative class"
        
        # Neither class should be completely separated from the other
        # (min/max of one class should not be completely outside the other)
        pos_min, pos_max = pos[feat].min(), pos[feat].max()
        neg_min, neg_max = neg[feat].min(), neg[feat].max()
        
        # At least some overlap in ranges
        range_overlap = min(pos_max, neg_max) - max(pos_min, neg_min)
        assert range_overlap >= 0, f"{feat} has completely separated ranges: pos=[{pos_min:.4f}, {pos_max:.4f}], neg=[{neg_min:.4f}, {neg_max:.4f}]"
