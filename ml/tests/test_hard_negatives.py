"""Tests confirming legitimate hard negatives exhibit surface suspicion while retaining label 0."""

import json
import networkx as nx
import pandas as pd
import pytest


@pytest.fixture
def dataset():
    customers = pd.read_parquet("data/raw/customers.parquet")
    orders = pd.read_parquet("data/raw/orders.parquet")
    refunds = pd.read_parquet("data/raw/refunds.parquet")
    rings = pd.read_parquet("data/raw/ground_truth_rings.parquet")
    
    with open("data/splits/train_groups.json") as f:
        train = json.load(f)
    with open("data/splits/test_groups.json") as f:
        test = json.load(f)
        
    return customers, orders, refunds, rings, train, test


def test_shared_housing_graph_connectivity_label_zero(dataset):
    """Hostel/office entities create high-degree graph components, but their refund events are label 0."""
    customers, orders, refunds, rings, _, _ = dataset

    # Identify abuse customer IDs
    abuse_cids = set()
    for _, row in rings.iterrows():
        abuse_cids.update(json.loads(row["customer_ids"]))

    # Build graph of customer <-> address
    g = nx.Graph()
    for _, row in orders.iterrows():
        g.add_edge(row["customer_id"], row["address_id"])

    # Find high-degree addresses (hostels/offices shared by > 10 distinct customers)
    addr_degrees = {n: d for n, d in g.degree() if n.startswith("ADDR_") and d >= 10}
    assert len(addr_degrees) > 0, "Expected high-degree shared addresses (hostels/offices)"

    # Get non-abuse customers sharing these addresses
    shared_hostel_custs = set()
    for addr in addr_degrees:
        custs = set(g.neighbors(addr)) - abuse_cids
        shared_hostel_custs.update(custs)

    assert len(shared_hostel_custs) > 50, "Expected significant population in shared housing"

    # Verify all their refund requests have coordinated_refund_abuse = 0
    hostel_refunds = refunds[refunds["customer_id"].isin(shared_hostel_custs)]
    if len(hostel_refunds) > 0:
        assert (hostel_refunds["coordinated_refund_abuse"] == 0).all(), \
            "Legitimate hostel customers must strictly retain label 0"


def test_heavy_returner_high_refund_rate_label_zero(dataset):
    """Heavy returners exhibit high individual refund rates (>= 35%) but retain label 0."""
    customers, orders, refunds, rings, _, _ = dataset

    abuse_cids = set()
    for _, row in rings.iterrows():
        abuse_cids.update(json.loads(row["customer_ids"]))

    # Compute customer refund rates for legitimate customers with >= 4 orders
    order_counts = orders.groupby("customer_id").size()
    refund_counts = refunds.groupby("customer_id").size()

    df_stats = pd.DataFrame({"orders": order_counts, "refunds": refund_counts}).fillna(0)
    df_stats["refund_rate"] = df_stats["refunds"] / df_stats["orders"]

    # Filter non-abuse customers with >= 4 orders and refund_rate >= 0.35
    legit_heavy = df_stats[(df_stats.index.isin(set(customers["customer_id"]) - abuse_cids)) & 
                           (df_stats["orders"] >= 4) & 
                           (df_stats["refund_rate"] >= 0.35)]

    assert len(legit_heavy) >= 50, "Expected at least 50 legitimate heavy returners"

    # Verify their refunds are labeled 0
    heavy_refunds = refunds[refunds["customer_id"].isin(legit_heavy.index)]
    assert (heavy_refunds["coordinated_refund_abuse"] == 0).all(), \
        "Legitimate heavy returners must strictly retain label 0"


def test_sale_buyer_temporal_synchronization_label_zero(dataset):
    """Legitimate sale buyers exhibit synchronized order timing during sale days but retain label 0."""
    customers, orders, refunds, rings, _, _ = dataset

    abuse_cids = set()
    for _, row in rings.iterrows():
        abuse_cids.update(json.loads(row["customer_ids"]))

    # Check non-abuse orders
    legit_orders = orders[~orders["customer_id"].isin(abuse_cids)].copy()
    legit_orders["dt"] = pd.to_datetime(legit_orders["timestamp"])

    # Count orders on peak sale days (day 25, 60, 110, 150)
    start_dt = legit_orders["dt"].min()
    legit_orders["day_idx"] = (legit_orders["dt"] - start_dt).dt.total_seconds() // 86400

    peak_day_orders = legit_orders[legit_orders["day_idx"].isin([25, 60, 110, 150])]
    assert len(peak_day_orders) > 100, "Expected synchronized sale event orders"

    # All legitimate refunds associated with these sale orders must have label 0
    peak_order_ids = set(peak_day_orders["order_id"])
    peak_refunds = refunds[refunds["order_id"].isin(peak_order_ids)]
    if len(peak_refunds) > 0:
        assert (peak_refunds["coordinated_refund_abuse"] == 0).all(), \
            "Legitimate sale buyer refunds must strictly retain label 0"
