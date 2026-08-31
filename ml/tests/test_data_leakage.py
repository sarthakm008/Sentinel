"""Programmatic anti-leakage test suite for Phase 1."""

import json
import os
import pytest
import pandas as pd


@pytest.fixture
def split_data():
    splits_dir = "data/splits"
    with open(os.path.join(splits_dir, "train_groups.json")) as f:
        train = json.load(f)
    with open(os.path.join(splits_dir, "validation_groups.json")) as f:
        val = json.load(f)
    with open(os.path.join(splits_dir, "test_groups.json")) as f:
        test = json.load(f)
    return train, val, test


def test_customer_disjointness(split_data):
    train, val, test = split_data
    train_c = set(train["customers"])
    val_c = set(val["customers"])
    test_c = set(test["customers"])

    assert len(train_c.intersection(val_c)) == 0, "Customer leakage between Train and Val"
    assert len(train_c.intersection(test_c)) == 0, "Customer leakage between Train and Test"
    assert len(val_c.intersection(test_c)) == 0, "Customer leakage between Val and Test"


def test_device_disjointness(split_data):
    train, val, test = split_data
    train_d = set(train["devices"])
    val_d = set(val["devices"])
    test_d = set(test["devices"])

    assert len(train_d.intersection(val_d)) == 0, "Device leakage between Train and Val"
    assert len(train_d.intersection(test_d)) == 0, "Device leakage between Train and Test"
    assert len(val_d.intersection(test_d)) == 0, "Device leakage between Val and Test"


def test_address_disjointness(split_data):
    train, val, test = split_data
    train_a = set(train["addresses"])
    val_a = set(val["addresses"])
    test_a = set(test["addresses"])

    assert len(train_a.intersection(val_a)) == 0, "Address leakage between Train and Val"
    assert len(train_a.intersection(test_a)) == 0, "Address leakage between Train and Test"
    assert len(val_a.intersection(test_a)) == 0, "Address leakage between Val and Test"


def test_payment_disjointness(split_data):
    train, val, test = split_data
    train_p = set(train["payment_tokens"])
    val_p = set(val["payment_tokens"])
    test_p = set(test["payment_tokens"])

    assert len(train_p.intersection(val_p)) == 0, "Payment token leakage between Train and Val"
    assert len(train_p.intersection(test_p)) == 0, "Payment token leakage between Train and Test"
    assert len(val_p.intersection(test_p)) == 0, "Payment token leakage between Val and Test"


def test_ring_type_f_isolation(split_data):
    """Ring Type F (Structural Shift) must exist strictly in the test split."""
    train, val, test = split_data
    rings_df = pd.read_parquet("data/raw/ground_truth_rings.parquet")
    
    type_f_rings = rings_df[rings_df["ring_type"] == "type_f_structural_shift"]
    assert len(type_f_rings) > 0, "Type F rings must exist in the dataset"

    type_f_custs = set()
    for _, row in type_f_rings.iterrows():
        c_ids = json.loads(row["customer_ids"])
        type_f_custs.update(c_ids)

    train_c = set(train["customers"])
    val_c = set(val["customers"])
    test_c = set(test["customers"])

    assert len(type_f_custs.intersection(train_c)) == 0, "Type F rings leaked into Train split"
    assert len(type_f_custs.intersection(val_c)) == 0, "Type F rings leaked into Val split"
    assert type_f_custs.issubset(test_c), "All Type F ring accounts must be in Test split"


def test_no_forbidden_columns_in_raw_tables():
    """Ensure raw event tables do not contain ground truth leakage columns."""
    orders_df = pd.read_parquet("data/raw/orders.parquet")
    refunds_df = pd.read_parquet("data/raw/refunds.parquet")
    customers_df = pd.read_parquet("data/raw/customers.parquet")

    forbidden = {"ring_id", "is_abuse", "fraud_ring_score", "generator_abuse_probability", "archetype"}
    
    assert not forbidden.intersection(set(orders_df.columns)), "Forbidden column in orders table"
    assert not forbidden.intersection(set(customers_df.columns)), "Forbidden column in customers table"
    
    # In refunds table, only coordinated_refund_abuse (the target label) is permitted
    refund_forbidden = forbidden - {"coordinated_refund_abuse"}
    assert not refund_forbidden.intersection(set(refunds_df.columns)), "Forbidden column in refunds table"
