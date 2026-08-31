"""Point-in-Time Feature Extractor for Sentinel Models."""

from datetime import datetime
import json
import os
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
import numpy as np
import pandas as pd


BEHAVIORAL_FEATURES = [
    "customer_order_count",
    "customer_refund_count",
    "customer_refund_rate",
    "customer_total_order_value",
    "customer_total_refund_value",
    "customer_mean_order_value",
    "customer_mean_refund_value",
    "customer_account_age_days",
    "customer_orders_last_24h",
    "customer_refunds_last_24h",
    "customer_refunds_last_7d",
    "customer_unique_devices",
    "customer_unique_addresses",
    "customer_unique_payments",
    "order_amount",
    "refund_delay_hours",
    "amount_ratio_vs_customer_mean",
    "category_baseline_refund_rate",
]

GRAPH_FEATURES = [
    "graph_shared_device_customers",
    "graph_shared_address_customers",
    "graph_shared_payment_customers",
    "graph_total_connected_customers",
    "graph_two_hop_customer_count",
    "graph_component_size",
    "graph_neighbor_mean_refund_rate",
    "graph_neighbor_high_refund_count",
]

TEMPORAL_FEATURES = [
    "temporal_cluster_events_last_15m",
    "temporal_cluster_events_last_1h",
    "temporal_cluster_events_last_24h",
    "temporal_synchronized_refund_ratio_1h",
    "temporal_account_creation_burst_24h",
    "temporal_min_inter_event_delay_min",
]

ALL_FEATURES = BEHAVIORAL_FEATURES + GRAPH_FEATURES + TEMPORAL_FEATURES


class PointInTimeFeatureExtractor:
    """Extracts features for refund events with strict point-in-time correctness."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        self.splits_dir = os.path.join(data_dir, "splits")

    def load_raw_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        customers = pd.read_parquet(os.path.join(self.raw_dir, "customers.parquet"))
        orders = pd.read_parquet(os.path.join(self.raw_dir, "orders.parquet"))
        refunds = pd.read_parquet(os.path.join(self.raw_dir, "refunds.parquet"))
        return customers, orders, refunds

    def extract_features(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Extracts feature matrices for Train, Validation, and Test splits."""
        customers_df, orders_df, refunds_df = self.load_raw_data()

        # Parse timestamps
        customers_df["dt_created"] = pd.to_datetime(customers_df["account_created_at"], format="ISO8601")
        orders_df["dt_order"] = pd.to_datetime(orders_df["timestamp"], format="ISO8601")
        refunds_df["dt_refund"] = pd.to_datetime(refunds_df["timestamp"], format="ISO8601")

        # Merge refund with order details
        df_refund_events = refunds_df.merge(
            orders_df[["order_id", "dt_order", "amount", "product_category", "device_id", "address_id", "payment_token_id"]],
            on="order_id",
            suffixes=("_refund", "_order")
        )
        df_refund_events = df_refund_events.merge(
            customers_df[["customer_id", "dt_created", "segment"]],
            on="customer_id"
        )

        # Precompute category baseline refund rates from orders
        cat_order_counts = orders_df.groupby("product_category").size()
        cat_merged = refunds_df.merge(orders_df[["order_id", "product_category"]], on="order_id")
        cat_refund_counts = cat_merged.groupby("product_category").size()
        cat_rates = (cat_refund_counts / cat_order_counts).to_dict()

        # Prepare unified timeline of all historical events (orders and refunds) for point-in-time indexing
        cust_created_map = customers_df.set_index("customer_id")["dt_created"].to_dict()

        # Build chronological event list
        order_records = []
        for _, row in orders_df.iterrows():
            order_records.append({
                "type": "order",
                "id": row["order_id"],
                "customer_id": row["customer_id"],
                "dt": row["dt_order"],
                "amount": float(row["amount"]),
                "device_id": row["device_id"],
                "address_id": row["address_id"],
                "payment_token_id": row["payment_token_id"],
            })

        refund_records = []
        for _, row in refunds_df.iterrows():
            refund_records.append({
                "type": "refund",
                "id": row["refund_id"],
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "dt": row["dt_refund"],
                "amount": float(row["amount"]),
            })

        # Combine all events and sort strictly chronologically
        all_events = sorted(order_records + refund_records, key=lambda x: x["dt"])

        # Sort refund events to extract features chronologically
        df_refund_events = df_refund_events.sort_values("dt_refund").reset_index(drop=True)

        # Point-in-time tracking data structures
        cust_orders = {}  # cid -> list of (dt, amount, did, aid, pid)
        cust_refunds = {}  # cid -> list of (dt, amount)
        
        # Bipartite entity graph tracking (point-in-time)
        g_pit = nx.Graph()
        
        # Component activity tracking for temporal windows: cluster_id -> list of (dt, event_type)
        comp_events = {}  # node -> list of (dt, event_type)

        event_idx = 0
        n_all_events = len(all_events)
        features_list = []

        print(f"Extracting point-in-time features for {len(df_refund_events):,} refund events...")

        for row_idx, ref_row in df_refund_events.iterrows():
            t_ref = ref_row["dt_refund"]
            cid = ref_row["customer_id"]
            oid = ref_row["order_id"]
            t_ord = ref_row["dt_order"]
            ord_amount = float(ref_row["amount_order"])
            ref_amount = float(ref_row["amount_refund"])
            cat = ref_row["product_category"]
            did = ref_row["device_id"]
            aid = ref_row["address_id"]
            pid = ref_row["payment_token_id"]
            t_created = ref_row["dt_created"]

            # Advance point-in-time state up to strictly before t_ref
            while event_idx < n_all_events and all_events[event_idx]["dt"] < t_ref:
                ev = all_events[event_idx]
                e_cid = ev["customer_id"]
                e_dt = ev["dt"]

                if ev["type"] == "order":
                    if e_cid not in cust_orders:
                        cust_orders[e_cid] = []
                    cust_orders[e_cid].append((e_dt, ev["amount"], ev["device_id"], ev["address_id"], ev["payment_token_id"]))

                    # Add edges to point-in-time graph
                    g_pit.add_edge(e_cid, ev["device_id"])
                    g_pit.add_edge(e_cid, ev["address_id"])
                    g_pit.add_edge(e_cid, ev["payment_token_id"])

                    # Log to component events
                    if e_cid not in comp_events:
                        comp_events[e_cid] = []
                    comp_events[e_cid].append((e_dt, "order"))

                elif ev["type"] == "refund":
                    if e_cid not in cust_refunds:
                        cust_refunds[e_cid] = []
                    cust_refunds[e_cid].append((e_dt, ev["amount"]))

                    if e_cid not in comp_events:
                        comp_events[e_cid] = []
                    comp_events[e_cid].append((e_dt, "refund"))

                event_idx += 1

            # === 1. Behavioral Features ===
            history_orders = [o for o in cust_orders.get(cid, []) if o[0] <= t_ord]
            history_refunds = cust_refunds.get(cid, [])

            c_order_count = len(history_orders)
            c_refund_count = len(history_refunds)
            c_refund_rate = c_refund_count / max(1, c_order_count)

            c_total_order_val = sum(o[1] for o in history_orders) if history_orders else ord_amount
            c_total_refund_val = sum(r[1] for r in history_refunds) if history_refunds else 0.0
            c_mean_order_val = c_total_order_val / max(1, c_order_count)
            c_mean_refund_val = (c_total_refund_val / c_refund_count) if c_refund_count > 0 else 0.0

            c_account_age_days = max(0.0, (t_ref - t_created).total_seconds() / 86400.0)

            t_24h_ago = t_ref - pd.Timedelta(hours=24)
            t_7d_ago = t_ref - pd.Timedelta(days=7)

            c_orders_24h = sum(1 for o in history_orders if o[0] >= t_24h_ago)
            c_refunds_24h = sum(1 for r in history_refunds if r[0] >= t_24h_ago)
            c_refunds_7d = sum(1 for r in history_refunds if r[0] >= t_7d_ago)

            c_devices = {o[2] for o in history_orders}.union({did})
            c_addrs = {o[3] for o in history_orders}.union({aid})
            c_pms = {o[4] for o in history_orders}.union({pid})

            delay_hours = max(0.0, (t_ref - t_ord).total_seconds() / 3600.0)
            amount_ratio = ord_amount / max(1.0, c_mean_order_val)
            cat_base_rr = cat_rates.get(cat, 0.10)

            # === 2. Graph Features ===
            shared_dev_custs = set()
            shared_addr_custs = set()
            shared_pm_custs = set()

            if g_pit.has_node(did):
                shared_dev_custs = {n for n in g_pit.neighbors(did) if n.startswith("CUS_") and n != cid}
            if g_pit.has_node(aid):
                shared_addr_custs = {n for n in g_pit.neighbors(aid) if n.startswith("CUS_") and n != cid}
            if g_pit.has_node(pid):
                shared_pm_custs = {n for n in g_pit.neighbors(pid) if n.startswith("CUS_") and n != cid}

            connected_custs = shared_dev_custs.union(shared_addr_custs).union(shared_pm_custs)
            two_hop_custs = set()
            for n_cid in connected_custs:
                if g_pit.has_node(n_cid):
                    for entity_node in g_pit.neighbors(n_cid):
                        if g_pit.has_node(entity_node):
                            two_hop_custs.update({n for n in g_pit.neighbors(entity_node) if n.startswith("CUS_") and n != cid})

            # Component size
            if g_pit.has_node(cid):
                comp_size = len(nx.node_connected_component(g_pit, cid))
            else:
                comp_size = 1

            # Neighbor refund statistics
            neighbor_refund_rates = []
            neighbor_high_refund_count = 0
            for n_cid in connected_custs:
                n_ord = len(cust_orders.get(n_cid, []))
                n_ref = len(cust_refunds.get(n_cid, []))
                n_rr = n_ref / max(1, n_ord)
                neighbor_refund_rates.append(n_rr)
                if n_rr >= 0.35 and n_ref >= 1:
                    neighbor_high_refund_count += 1

            neighbor_mean_rr = float(np.mean(neighbor_refund_rates)) if neighbor_refund_rates else 0.0

            # === 3. Temporal Features ===
            # Collect events from 1-hop connected cluster in recent windows
            recent_events = []
            cluster_members = connected_custs.union({cid})
            for m_cid in cluster_members:
                for ev_t, ev_type in comp_events.get(m_cid, []):
                    recent_events.append((ev_t, ev_type))

            t_15m_ago = t_ref - pd.Timedelta(minutes=15)
            t_1h_ago = t_ref - pd.Timedelta(hours=1)

            events_15m = sum(1 for e in recent_events if t_15m_ago <= e[0] < t_ref)
            events_1h = sum(1 for e in recent_events if t_1h_ago <= e[0] < t_ref)
            events_24h = sum(1 for e in recent_events if t_24h_ago <= e[0] < t_ref)
            refunds_1h = sum(1 for e in recent_events if t_1h_ago <= e[0] < t_ref and e[1] == "refund")

            sync_refund_ratio_1h = refunds_1h / max(1, events_1h)

            # Account creation burst in component (how many component accounts registered within 24h of this customer)
            creation_burst_count = 0
            for m_cid in cluster_members:
                if m_cid != cid and m_cid in cust_created_map:
                    if abs((cust_created_map[m_cid] - t_created).total_seconds()) <= 86400:
                        creation_burst_count += 1

            # Inter-event delay to previous event in component
            prior_events = [e[0] for e in recent_events if e[0] < t_ref]
            if prior_events:
                last_dt = max(prior_events)
                inter_delay_min = max(0.1, (t_ref - last_dt).total_seconds() / 60.0)
            else:
                inter_delay_min = 1440.0  # 1 day default

            feat_record = {
                "refund_id": ref_row["refund_id"],
                "order_id": oid,
                "customer_id": cid,
                "timestamp_refund": t_ref.isoformat(),
                "timestamp_order": t_ord.isoformat(),
                "refund_amount": ref_amount,
                "label": int(ref_row["coordinated_refund_abuse"]),
                # Behavioral
                "customer_order_count": c_order_count,
                "customer_refund_count": c_refund_count,
                "customer_refund_rate": c_refund_rate,
                "customer_total_order_value": c_total_order_val,
                "customer_total_refund_value": c_total_refund_val,
                "customer_mean_order_value": c_mean_order_val,
                "customer_mean_refund_value": c_mean_refund_val,
                "customer_account_age_days": c_account_age_days,
                "customer_orders_last_24h": c_orders_24h,
                "customer_refunds_last_24h": c_refunds_24h,
                "customer_refunds_last_7d": c_refunds_7d,
                "customer_unique_devices": len(c_devices),
                "customer_unique_addresses": len(c_addrs),
                "customer_unique_payments": len(c_pms),
                "order_amount": ord_amount,
                "refund_delay_hours": delay_hours,
                "amount_ratio_vs_customer_mean": amount_ratio,
                "category_baseline_refund_rate": cat_base_rr,
                # Graph
                "graph_shared_device_customers": len(shared_dev_custs),
                "graph_shared_address_customers": len(shared_addr_custs),
                "graph_shared_payment_customers": len(shared_pm_custs),
                "graph_total_connected_customers": len(connected_custs),
                "graph_two_hop_customer_count": len(two_hop_custs),
                "graph_component_size": comp_size,
                "graph_neighbor_mean_refund_rate": neighbor_mean_rr,
                "graph_neighbor_high_refund_count": neighbor_high_refund_count,
                # Temporal
                "temporal_cluster_events_last_15m": events_15m,
                "temporal_cluster_events_last_1h": events_1h,
                "temporal_cluster_events_last_24h": events_24h,
                "temporal_synchronized_refund_ratio_1h": sync_refund_ratio_1h,
                "temporal_account_creation_burst_24h": creation_burst_count,
                "temporal_min_inter_event_delay_min": inter_delay_min,
            }
            features_list.append(feat_record)

        df_features = pd.DataFrame(features_list)

        # Ingest split manifests
        with open(os.path.join(self.splits_dir, "train_groups.json")) as f:
            train_custs = set(json.load(f)["customers"])
        with open(os.path.join(self.splits_dir, "validation_groups.json")) as f:
            val_custs = set(json.load(f)["customers"])
        with open(os.path.join(self.splits_dir, "test_groups.json")) as f:
            test_custs = set(json.load(f)["customers"])

        df_train = df_features[df_features["customer_id"].isin(train_custs)].copy()
        df_val = df_features[df_features["customer_id"].isin(val_custs)].copy()
        df_test = df_features[df_features["customer_id"].isin(test_custs)].copy()

        # Save processed feature caches for fast re-use
        processed_dir = os.path.join(self.data_dir, "processed")
        os.makedirs(processed_dir, exist_ok=True)
        df_train.to_parquet(os.path.join(processed_dir, "features_train.parquet"), index=False)
        df_val.to_parquet(os.path.join(processed_dir, "features_validation.parquet"), index=False)
        df_test.to_parquet(os.path.join(processed_dir, "features_test.parquet"), index=False)

        print(f"Extracted feature datasets: Train ({len(df_train):,}), Val ({len(df_val):,}), Test ({len(df_test):,})")
        return df_train, df_val, df_test
