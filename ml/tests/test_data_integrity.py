"""Data integrity, temporal causality, and shortcut audit tests for Phase 1."""

import json
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score


@pytest.fixture
def data_tables():
    customers = pd.read_parquet("data/raw/customers.parquet")
    devices = pd.read_parquet("data/raw/devices.parquet")
    addresses = pd.read_parquet("data/raw/addresses.parquet")
    payments = pd.read_parquet("data/raw/payment_tokens.parquet")
    orders = pd.read_parquet("data/raw/orders.parquet")
    refunds = pd.read_parquet("data/raw/refunds.parquet")
    rings = pd.read_parquet("data/raw/ground_truth_rings.parquet")
    return customers, devices, addresses, payments, orders, refunds, rings


def test_temporal_causality(data_tables):
    """Assert for every refund, timestamp_refund >= timestamp_order."""
    _, _, _, _, orders, refunds, _ = data_tables
    
    merged = refunds.merge(orders[["order_id", "timestamp"]], on="order_id", suffixes=("_ref", "_ord"))
    
    t_ref = pd.to_datetime(merged["timestamp_ref"], format="ISO8601")
    t_ord = pd.to_datetime(merged["timestamp_ord"], format="ISO8601")
    
    diff_seconds = (t_ref - t_ord).dt.total_seconds()
    
    # Assert causality
    assert (diff_seconds >= 0).all(), "Found refund timestamp occurring before order timestamp"
    assert diff_seconds.min() >= 3600 * 6, "Expected at least a few hours between order and refund"


def test_schema_and_counts(data_tables):
    """Assert non-empty tables and expected schemas."""
    customers, devices, addresses, payments, orders, refunds, rings = data_tables

    assert len(customers) >= 40000, f"Expected >= 40,000 customers, got {len(customers)}"
    assert len(devices) >= 25000, f"Expected >= 25,000 devices, got {len(devices)}"
    assert len(addresses) >= 20000, f"Expected >= 20,000 addresses, got {len(addresses)}"
    assert len(payments) >= 25000, f"Expected >= 25,000 payment tokens, got {len(payments)}"
    assert len(orders) >= 100000, f"Expected >= 100,000 orders, got {len(orders)}"
    assert len(refunds) >= 10000, f"Expected >= 10,000 refunds, got {len(refunds)}"
    assert len(rings) >= 100, f"Expected >= 100 abuse rings, got {len(rings)}"

    # Abuse refund balance check (between 8% and 25%)
    abuse_ratio = refunds["coordinated_refund_abuse"].mean()
    assert 0.08 <= abuse_ratio <= 0.25, f"Abuse ratio {abuse_ratio:.3f} outside expected range [0.08, 0.25]"


def test_marginal_matching_type_f_vs_other_rings(data_tables):
    """Validate that Ring Type F marginals match Types A-E closely."""
    _, _, _, _, orders, refunds, rings = data_tables

    type_f_rings = rings[rings["ring_type"] == "type_f_structural_shift"]
    other_rings = rings[rings["ring_type"] != "type_f_structural_shift"]

    f_cids = {cid for _, r in type_f_rings.iterrows() for cid in json.loads(r["customer_ids"])}
    other_cids = {cid for _, r in other_rings.iterrows() for cid in json.loads(r["customer_ids"])}

    # 1. Ring sizes
    f_sizes = [len(json.loads(r["customer_ids"])) for _, r in type_f_rings.iterrows()]
    other_sizes = [len(json.loads(r["customer_ids"])) for _, r in other_rings.iterrows()]
    size_ratio = np.mean(f_sizes) / np.mean(other_sizes)
    assert 0.75 <= size_ratio <= 1.25, f"Ring size mismatch ratio: {size_ratio:.2f}"

    # 2. Mean order amounts
    f_orders = orders[orders["customer_id"].isin(f_cids)]
    other_orders = orders[orders["customer_id"].isin(other_cids)]
    amount_ratio = f_orders["amount"].mean() / other_orders["amount"].mean()
    assert 0.80 <= amount_ratio <= 1.20, f"Order amount mismatch ratio: {amount_ratio:.2f}"

    # 3. Refund rates
    f_refunds = refunds[refunds["customer_id"].isin(f_cids)]
    other_refunds = refunds[refunds["customer_id"].isin(other_cids)]
    f_rr = len(f_refunds) / len(f_orders)
    other_rr = len(other_refunds) / len(other_orders)
    rr_ratio = f_rr / other_rr
    assert 0.80 <= rr_ratio <= 1.20, f"Refund rate mismatch ratio: {rr_ratio:.2f}"


def test_shortcut_and_leakage_audit(data_tables):
    """Audit single raw tabular features to reject near-perfect predictors (ROC-AUC > 0.90)."""
    customers, _, _, _, orders, refunds, _ = data_tables

    merged = refunds.merge(orders, on="order_id", suffixes=("_ref", "_ord"))
    merged = merged.merge(customers, left_on="customer_id_ref", right_on="customer_id")

    y = merged["coordinated_refund_abuse"].values

    # Test numerical features
    audit_results = {}
    
    # 1. Refund amount
    auc_ref_amount = roc_auc_score(y, merged["amount_ref"].values)
    auc_ref_amount = max(auc_ref_amount, 1 - auc_ref_amount)
    audit_results["refund_amount"] = auc_ref_amount

    # 2. Order amount
    auc_ord_amount = roc_auc_score(y, merged["amount_ord"].values)
    auc_ord_amount = max(auc_ord_amount, 1 - auc_ord_amount)
    audit_results["order_amount"] = auc_ord_amount

    # 3. Order-to-refund delay
    t_ref = pd.to_datetime(merged["timestamp_ref"], format="ISO8601")
    t_ord = pd.to_datetime(merged["timestamp_ord"], format="ISO8601")
    delay_hours = (t_ref - t_ord).dt.total_seconds() / 3600.0
    auc_delay = roc_auc_score(y, delay_hours)
    auc_delay = max(auc_delay, 1 - auc_delay)
    audit_results["delay_hours"] = auc_delay

    # 4. Account age at refund time
    t_created = pd.to_datetime(merged["account_created_at"], format="ISO8601")
    account_age_days = (t_ref - t_created).dt.total_seconds() / 86400.0
    auc_age = roc_auc_score(y, account_age_days)
    auc_age = max(auc_age, 1 - auc_age)
    audit_results["account_age_days"] = auc_age

    print("\n=== Single-Feature Shortcut Audit Results ===")
    for feat, score in audit_results.items():
        flag = " [FLAGGED > 0.75]" if score > 0.75 else ""
        print(f"  {feat:20s}: ROC-AUC = {score:.4f}{flag}")

    # Assert no single feature has near-perfect ROC-AUC > 0.90
    for feat, score in audit_results.items():
        assert score < 0.90, f"Feature '{feat}' has near-perfect ROC-AUC {score:.4f} > 0.90 (shortcut violation)"
