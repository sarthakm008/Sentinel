"""Benchmark audit script to generate side-by-side Before/After diagnostic metrics."""

import json
import os
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


def compute_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    nx, ny = len(x), len(y)
    vx, vy = np.var(x, ddof=1), np.var(y, ddof=1)
    pooled_sd = np.sqrt(((nx - 1) * vx + (ny - 1) * vy) / max(1, (nx + ny - 2)))
    if pooled_sd == 0:
        return 0.0
    return float(abs(np.mean(x) - np.mean(y)) / pooled_sd)


def run_benchmark_audit():
    print("=== Sentinel Benchmark Audit (Phase 2.5) ===")

    df_train = pd.read_parquet("data/processed/features_train.parquet")
    df_val = pd.read_parquet("data/processed/features_validation.parquet")
    df_test = pd.read_parquet("data/processed/features_test.parquet")
    rings_df = pd.read_parquet("data/raw/ground_truth_rings.parquet")

    pos_tr = df_train[df_train["label"] == 1]
    neg_tr = df_train[df_train["label"] == 0]

    # 1. Distribution Diagnostics for Delay
    delay_pos = pos_tr["refund_delay_hours"].values
    delay_neg = neg_tr["refund_delay_hours"].values
    d_delay = compute_cohens_d(delay_pos, delay_neg)
    auc_delay = max(roc_auc_score(df_train["label"], df_train["refund_delay_hours"]), 1.0 - roc_auc_score(df_train["label"], df_train["refund_delay_hours"]))

    print("\n--- 1. Refund Delay Distribution Diagnostics (Train) ---")
    print(f"  Positives: Mean={np.mean(delay_pos):.2f}h, Median={np.median(delay_pos):.2f}h, P10={np.percentile(delay_pos, 10):.2f}h, P25={np.percentile(delay_pos, 25):.2f}h, P75={np.percentile(delay_pos, 75):.2f}h, P90={np.percentile(delay_pos, 90):.2f}h")
    print(f"  Negatives: Mean={np.mean(delay_neg):.2f}h, Median={np.median(delay_neg):.2f}h, P10={np.percentile(delay_neg, 10):.2f}h, P25={np.percentile(delay_neg, 25):.2f}h, P75={np.percentile(delay_neg, 75):.2f}h, P90={np.percentile(delay_neg, 90):.2f}h")
    print(f"  Standardized Mean Diff (Cohen's d): {d_delay:.4f}")
    print(f"  Univariate ROC-AUC                 : {auc_delay:.4f}")

    # 2. Distribution Diagnostics for Account Age
    age_pos = pos_tr["customer_account_age_days"].values
    age_neg = neg_tr["customer_account_age_days"].values
    d_age = compute_cohens_d(age_pos, age_neg)
    auc_age = max(roc_auc_score(df_train["label"], df_train["customer_account_age_days"]), 1.0 - roc_auc_score(df_train["label"], df_train["customer_account_age_days"]))

    print("\n--- 2. Customer Account Age Distribution Diagnostics (Train) ---")
    print(f"  Positives: Mean={np.mean(age_pos):.2f}d, Median={np.median(age_pos):.2f}d, P10={np.percentile(age_pos, 10):.2f}d, P25={np.percentile(age_pos, 25):.2f}d, P75={np.percentile(age_pos, 75):.2f}d, P90={np.percentile(age_pos, 90):.2f}d")
    print(f"  Negatives: Mean={np.mean(age_neg):.2f}d, Median={np.median(age_neg):.2f}d, P10={np.percentile(age_neg, 10):.2f}d, P25={np.percentile(age_neg, 25):.2f}d, P75={np.percentile(age_neg, 75):.2f}d, P90={np.percentile(age_neg, 90):.2f}d")
    print(f"  Standardized Mean Diff (Cohen's d): {d_age:.4f}")
    print(f"  Univariate ROC-AUC                 : {auc_age:.4f}")

    # 3. Prevalence Diagnostics
    type_f_rings = rings_df[rings_df["ring_type"] == "type_f_structural_shift"]
    type_f_custs = set()
    for _, r in type_f_rings.iterrows():
        type_f_custs.update(json.loads(r["customer_ids"]))
    
    df_test_std = df_test[~df_test["customer_id"].isin(type_f_custs)]
    df_test_f = df_test[df_test["customer_id"].isin(type_f_custs)]

    print("\n--- 3. Partition Prevalences ---")
    print(f"  Train Split       : {len(df_train):,} events, {df_train['label'].sum():,} abuse ({df_train['label'].mean()*100:.2f}%)")
    print(f"  Validation Split  : {len(df_val):,} events, {df_val['label'].sum():,} abuse ({df_val['label'].mean()*100:.2f}%)")
    print(f"  Test Split (A-E)  : {len(df_test_std):,} events, {df_test_std['label'].sum():,} abuse ({df_test_std['label'].mean()*100:.2f}%)")
    print(f"  Test Split (Type F): {len(df_test_f):,} events, {df_test_f['label'].sum():,} abuse ({df_test_f['label'].mean()*100:.2f}%)")
    print(f"  Full Test Split   : {len(df_test):,} events, {df_test['label'].sum():,} abuse ({df_test['label'].mean()*100:.2f}%)")

    # 4. Ring F Isolation Verification
    train_custs = set(df_train["customer_id"])
    val_custs = set(df_val["customer_id"])
    test_custs = set(df_test["customer_id"])
    
    f_in_train = len(type_f_custs.intersection(train_custs))
    f_in_val = len(type_f_custs.intersection(val_custs))
    f_in_test = len(type_f_custs.intersection(test_custs))
    print("\n--- 4. Ring Type F Isolation ---")
    print(f"  Type F customers in Train: {f_in_train} (must be 0)")
    print(f"  Type F customers in Val  : {f_in_val} (must be 0)")
    print(f"  Type F customers in Test : {f_in_test} (100% isolated in Test)")


if __name__ == "__main__":
    run_benchmark_audit()
