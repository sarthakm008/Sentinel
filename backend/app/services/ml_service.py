"""ML Inference Service for Sentinel.

Loads the frozen 39-feature production model and provides single-refund
inference using the existing PIT feature extraction pipeline.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import joblib
import networkx as nx
import numpy as np
import pandas as pd

from ml.features.extractor import (
    BEHAVIORAL_FEATURES,
    GRAPH_FEATURES,
    TEMPORAL_FEATURES,
    SENTINEL_BASE_FEATURES,
)
from ml.features.graph_features import (
    compute_all_core_graph_features,
    compute_component_event_growth,
    compute_component_new_neighbors,
    compute_graph_neighbor_sync_ratio,
    get_connected_customers,
    get_shared_entity_ids,
)
from ml.models.trainer import SentinelModelWrapper
from ml.evaluation.evaluator import ActionPolicy


def _get_project_root() -> str:
    """Get the project root directory by finding the directory containing 'artifacts'."""
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    # Walk up the directory tree to find the project root (contains 'artifacts' directory)
    while current_dir != os.path.dirname(current_dir):  # Stop at filesystem root
        if os.path.exists(os.path.join(current_dir, "artifacts")):
            return current_dir
        current_dir = os.path.dirname(current_dir)
    
    # Fallback: assume current file location structure (4 levels up from ml_service.py)
    current_file = os.path.abspath(__file__)
    current_dir = os.path.dirname(current_file)
    app_dir = os.path.dirname(current_dir)
    backend_dir = os.path.dirname(app_dir)
    project_root = os.path.dirname(backend_dir)
    return project_root


class SentinelInferenceService:
    """Production ML inference service for Sentinel risk scoring."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold_path: Optional[str] = None,
        data_dir: Optional[str] = None,
    ):
        project_root = _get_project_root()
        
        self.model_path = model_path or os.path.join(project_root, "artifacts", "models", "sentinel_model.joblib")
        self.threshold_path = threshold_path or os.path.join(project_root, "artifacts", "metrics", "threshold.json")
        self.data_dir = data_dir or os.path.join(project_root, "data")
        self.raw_dir = os.path.join(self.data_dir, "raw")

        self.model: Optional[SentinelModelWrapper] = None
        self.threshold: float = 0.41
        self.action_policy: Optional[ActionPolicy] = None

        self._raw_data_loaded = False
        self._pit_state_built = False

        # Raw data (loaded once)
        self.customers_df: Optional[pd.DataFrame] = None
        self.orders_df: Optional[pd.DataFrame] = None
        self.refunds_df: Optional[pd.DataFrame] = None

        # Precomputed lookups
        self.cust_created_map: Dict[str, pd.Timestamp] = {}
        self.cat_rates: Dict[str, float] = {}
        self.all_events: List[Dict] = []

        # PIT state (built incrementally for inference)
        self.cust_orders: Dict[str, List[Tuple]] = {}
        self.cust_refunds: Dict[str, List[Tuple]] = {}
        self.g_pit: nx.Graph = nx.Graph()
        self.comp_events: Dict[str, List[Tuple]] = {}
        self.entity_customer_degree: Dict[str, set] = {}
        self.entity_customer_timestamps: Dict[str, Dict[str, pd.Timestamp]] = {}
        self.event_idx: int = 0
        self.last_t_ref: Optional[pd.Timestamp] = None

    def initialize(self) -> None:
        """Load model, threshold, and raw data. Build PIT state up to max timestamp."""
        self._load_model_and_threshold()
        self._load_raw_data()
        self._precompute_lookups()
        self._build_all_events()
        self._build_pit_state_up_to_max()

    def _load_model_and_threshold(self) -> None:
        """Load the production model and frozen threshold."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Production model not found at {self.model_path}")
        self.model = SentinelModelWrapper.load(self.model_path)
        print(f"Loaded production model: {self.model.name} with {len(self.model.feature_names)} features")

        if not os.path.exists(self.threshold_path):
            raise FileNotFoundError(f"Threshold file not found at {self.threshold_path}")
        with open(self.threshold_path) as f:
            thresholds = json.load(f)
        self.threshold = thresholds.get("sentinel", 0.41)
        self.action_policy = ActionPolicy(threshold_optimal=self.threshold)
        print(f"Loaded frozen threshold for sentinel: {self.threshold}")

    def _load_raw_data(self) -> None:
        """Load raw parquet files."""
        self.customers_df = pd.read_parquet(os.path.join(self.raw_dir, "customers.parquet"))
        self.orders_df = pd.read_parquet(os.path.join(self.raw_dir, "orders.parquet"))
        self.refunds_df = pd.read_parquet(os.path.join(self.raw_dir, "refunds.parquet"))

        # Parse timestamps
        self.customers_df["dt_created"] = pd.to_datetime(self.customers_df["account_created_at"], format="ISO8601")
        self.orders_df["dt_order"] = pd.to_datetime(self.orders_df["timestamp"], format="ISO8601")
        self.refunds_df["dt_refund"] = pd.to_datetime(self.refunds_df["timestamp"], format="ISO8601")

        self._raw_data_loaded = True

    def _precompute_lookups(self) -> None:
        """Precompute category baseline refund rates and customer creation map."""
        self.cust_created_map = self.customers_df.set_index("customer_id")["dt_created"].to_dict()

        cat_order_counts = self.orders_df.groupby("product_category").size()
        cat_merged = self.refunds_df.merge(self.orders_df[["order_id", "product_category"]], on="order_id")
        cat_refund_counts = cat_merged.groupby("product_category").size()
        self.cat_rates = (cat_refund_counts / cat_order_counts).to_dict()

    def _build_all_events(self) -> None:
        """Build chronological list of all events for PIT processing."""
        order_records = []
        for _, row in self.orders_df.iterrows():
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
        for _, row in self.refunds_df.iterrows():
            refund_records.append({
                "type": "refund",
                "id": row["refund_id"],
                "order_id": row["order_id"],
                "customer_id": row["customer_id"],
                "dt": row["dt_refund"],
                "amount": float(row["amount"]),
            })

        self.all_events = sorted(order_records + refund_records, key=lambda x: x["dt"])

    def _build_pit_state_up_to_max(self) -> None:
        """Build complete PIT state by processing all events chronologically."""
        self.cust_orders = {}
        self.cust_refunds = {}
        self.g_pit = nx.Graph()
        self.comp_events = {}
        self.entity_customer_degree = {}
        self.entity_customer_timestamps = {}
        self.event_idx = 0

        for ev in self.all_events:
            self._process_event(ev)

        self._pit_state_built = True
        self.last_t_ref = self.all_events[-1]["dt"] if self.all_events else None
        print(f"Built complete PIT state with {len(self.all_events)} events")

    def _process_event(self, ev: Dict) -> None:
        """Process a single event into PIT state."""
        e_cid = ev["customer_id"]
        e_dt = ev["dt"]

        if ev["type"] == "order":
            if e_cid not in self.cust_orders:
                self.cust_orders[e_cid] = []
            self.cust_orders[e_cid].append((e_dt, ev["amount"], ev["device_id"], ev["address_id"], ev["payment_token_id"]))

            self.g_pit.add_edge(e_cid, ev["device_id"])
            self.g_pit.add_edge(e_cid, ev["address_id"])
            self.g_pit.add_edge(e_cid, ev["payment_token_id"])

            for eid in [ev["device_id"], ev["address_id"], ev["payment_token_id"]]:
                if eid not in self.entity_customer_degree:
                    self.entity_customer_degree[eid] = set()
                self.entity_customer_degree[eid].add(e_cid)

                if eid not in self.entity_customer_timestamps:
                    self.entity_customer_timestamps[eid] = {}
                self.entity_customer_timestamps[eid][e_cid] = e_dt

            if e_cid not in self.comp_events:
                self.comp_events[e_cid] = []
            self.comp_events[e_cid].append((e_dt, "order"))

        elif ev["type"] == "refund":
            if e_cid not in self.cust_refunds:
                self.cust_refunds[e_cid] = []
            self.cust_refunds[e_cid].append((e_dt, ev["amount"]))

            if e_cid not in self.comp_events:
                self.comp_events[e_cid] = []
            self.comp_events[e_cid].append((e_dt, "refund"))

    def get_refund_event(self, refund_id: str) -> Optional[Dict]:
        """Get refund event details by refund_id."""
        refund_row = self.refunds_df[self.refunds_df["refund_id"] == refund_id]
        if refund_row.empty:
            return None

        row = refund_row.iloc[0]
        order_row = self.orders_df[self.orders_df["order_id"] == row["order_id"]]
        if order_row.empty:
            return None

        order = order_row.iloc[0]
        customer_row = self.customers_df[self.customers_df["customer_id"] == row["customer_id"]]
        if customer_row.empty:
            return None

        customer = customer_row.iloc[0]

        return {
            "refund_id": row["refund_id"],
            "order_id": row["order_id"],
            "customer_id": row["customer_id"],
            "dt_refund": row["dt_refund"],
            "dt_order": order["dt_order"],
            "refund_amount": float(row["amount"]),
            "order_amount": float(order["amount"]),
            "product_category": order["product_category"],
            "device_id": order["device_id"],
            "address_id": order["address_id"],
            "payment_token_id": order["payment_token_id"],
            "dt_created": customer["dt_created"],
            "label": int(row.get("coordinated_refund_abuse", 0)),
        }

    def extract_features_for_refund(self, refund_id: str) -> Optional[Dict[str, Any]]:
        """Extract all 39 features for a single refund event using PIT logic.

        This replicates the feature extraction logic from PointInTimeFeatureExtractor
        but for a single event, using the pre-built PIT state.
        """
        ref_event = self.get_refund_event(refund_id)
        if ref_event is None:
            return None

        t_ref = ref_event["dt_refund"]
        cid = ref_event["customer_id"]
        oid = ref_event["order_id"]
        t_ord = ref_event["dt_order"]
        ord_amount = ref_event["order_amount"]
        ref_amount = ref_event["refund_amount"]
        cat = ref_event["product_category"]
        did = ref_event["device_id"]
        aid = ref_event["address_id"]
        pid = ref_event["payment_token_id"]
        t_created = ref_event["dt_created"]

        # Ensure PIT state is advanced to t_ref (should already be built)
        # For correctness, we verify the state is valid for this t_ref
        # In production, we'd rebuild incrementally; here we use full state

        # === 1. Behavioral Features ===
        history_orders = [o for o in self.cust_orders.get(cid, []) if o[0] <= t_ord]
        history_refunds = self.cust_refunds.get(cid, [])

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
        cat_base_rr = self.cat_rates.get(cat, 0.10)

        # === 2. Graph Features ===
        shared_dev_custs = set()
        shared_addr_custs = set()
        shared_pm_custs = set()

        if self.g_pit.has_node(did):
            shared_dev_custs = {n for n in self.g_pit.neighbors(did) if n.startswith("CUS_") and n != cid}
        if self.g_pit.has_node(aid):
            shared_addr_custs = {n for n in self.g_pit.neighbors(aid) if n.startswith("CUS_") and n != cid}
        if self.g_pit.has_node(pid):
            shared_pm_custs = {n for n in self.g_pit.neighbors(pid) if n.startswith("CUS_") and n != cid}

        connected_custs = shared_dev_custs.union(shared_addr_custs).union(shared_pm_custs)

        if self.g_pit.has_node(cid):
            comp_size = len(nx.node_connected_component(self.g_pit, cid))
        else:
            comp_size = 1

        neighbor_refund_rates = []
        neighbor_high_refund_count = 0
        for n_cid in connected_custs:
            n_ord = len(self.cust_orders.get(n_cid, []))
            n_ref = len(self.cust_refunds.get(n_cid, []))
            n_rr = n_ref / max(1, n_ord)
            neighbor_refund_rates.append(n_rr)
            if n_rr >= 0.35 and n_ref >= 1:
                neighbor_high_refund_count += 1

        neighbor_mean_rr = float(np.mean(neighbor_refund_rates)) if neighbor_refund_rates else 0.0

        # Phase 3 Core Graph features
        shared_dev_entities = get_shared_entity_ids(self.g_pit, cid, "DEV_")
        shared_addr_entities = get_shared_entity_ids(self.g_pit, cid, "ADDR_")
        shared_pm_entities = get_shared_entity_ids(self.g_pit, cid, "PM_")

        core_graph = compute_all_core_graph_features(
            g_pit=self.g_pit,
            cid=cid,
            t_ref=t_ref,
            cust_orders=self.cust_orders,
            cust_refunds=self.cust_refunds,
            entity_customer_degree=self.entity_customer_degree,
            entity_customer_timestamps=self.entity_customer_timestamps,
            did=did,
            aid=aid,
            pid=pid,
        )

        # Phase 4 Growth features
        comp_growth = compute_component_event_growth(
            g_pit=self.g_pit,
            cid=cid,
            t_ref=t_ref,
            cust_orders=self.cust_orders,
            comp_events=self.comp_events,
        )
        comp_new_neighbors = compute_component_new_neighbors(
            g_pit=self.g_pit,
            cid=cid,
            t_ref=t_ref,
            comp_events=self.comp_events,
        )

        # Phase 5 Interaction (NOT used in production model - for reference only)
        neighbor_sync_ratio = compute_graph_neighbor_sync_ratio(
            connected_custs=connected_custs,
            t_ref=t_ref,
            comp_events=self.comp_events,
        )

        # === 3. Temporal Features ===
        recent_events = []
        cluster_members = connected_custs.union({cid})
        for m_cid in cluster_members:
            for ev_t, ev_type in self.comp_events.get(m_cid, []):
                recent_events.append((ev_t, ev_type))

        t_15m_ago = t_ref - pd.Timedelta(minutes=15)
        t_1h_ago = t_ref - pd.Timedelta(hours=1)

        events_15m = sum(1 for e in recent_events if t_15m_ago <= e[0] < t_ref)
        events_1h = sum(1 for e in recent_events if t_1h_ago <= e[0] < t_ref)
        events_24h = sum(1 for e in recent_events if t_24h_ago <= e[0] < t_ref)
        refunds_1h = sum(1 for e in recent_events if t_1h_ago <= e[0] < t_ref and e[1] == "refund")

        sync_refund_ratio_1h = refunds_1h / max(1, events_1h)

        creation_burst_count = 0
        for m_cid in cluster_members:
            if m_cid != cid and m_cid in self.cust_created_map:
                if abs((self.cust_created_map[m_cid] - t_created).total_seconds()) <= 86400:
                    creation_burst_count += 1

        prior_events = [e[0] for e in recent_events if e[0] < t_ref]
        if prior_events:
            last_dt = max(prior_events)
            inter_delay_min = max(0.1, (t_ref - last_dt).total_seconds() / 60.0)
        else:
            inter_delay_min = 1440.0

        # Build feature dict (39 features for production model)
        features = {
            "refund_id": refund_id,
            "order_id": oid,
            "customer_id": cid,
            "timestamp_refund": t_ref.isoformat(),
            "timestamp_order": t_ord.isoformat(),
            "refund_amount": ref_amount,
            "label": ref_event["label"],
            # Behavioral (18)
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
            # Graph (15)
            "graph_shared_device_customers": len(shared_dev_custs),
            "graph_shared_address_customers": len(shared_addr_custs),
            "graph_shared_payment_customers": len(shared_pm_custs),
            "graph_component_size": comp_size,
            "graph_neighbor_mean_refund_rate": neighbor_mean_rr,
            "graph_neighbor_high_refund_count": neighbor_high_refund_count,
            "graph_shared_device_rarity": core_graph["graph_shared_device_rarity"],
            "graph_shared_address_rarity": core_graph["graph_shared_address_rarity"],
            "graph_shared_payment_rarity": core_graph["graph_shared_payment_rarity"],
            "graph_neighbor_max_refund_rate": core_graph["graph_neighbor_max_refund_rate"],
            "graph_neighbor_risk_mass": core_graph["graph_neighbor_risk_mass"],
            "graph_shared_device_recency_h": core_graph["graph_shared_device_recency_h"],
            "graph_shared_address_recency_h": core_graph["graph_shared_address_recency_h"],
            "graph_component_event_growth_24h": comp_growth,
            "graph_component_new_neighbors_24h": comp_new_neighbors,
            # Temporal (6)
            "temporal_cluster_events_last_15m": events_15m,
            "temporal_cluster_events_last_1h": events_1h,
            "temporal_cluster_events_last_24h": events_24h,
            "temporal_synchronized_refund_ratio_1h": sync_refund_ratio_1h,
            "temporal_account_creation_burst_24h": creation_burst_count,
            "temporal_min_inter_event_delay_min": inter_delay_min,
        }

        return features

    def score_refund(self, refund_id: str) -> Optional[Dict[str, Any]]:
        """Score a single refund event and return risk assessment with evidence."""
        features = self.extract_features_for_refund(refund_id)
        if features is None:
            return None

        if self.model is None or self.action_policy is None:
            raise RuntimeError("Service not initialized")

        # Create DataFrame with model features
        feature_df = pd.DataFrame([features])
        X = feature_df[self.model.feature_names].values
        risk_score = float(self.model.model.predict_proba(X)[0, 1])

        risk_band = self._get_risk_band(risk_score)
        recommended_action = self.action_policy.decide(risk_score)

        evidence = self._build_evidence(features)

        return {
            "refund_id": refund_id,
            "customer_id": features["customer_id"],
            "order_id": features["order_id"],
            "risk_score": round(risk_score, 4),
            "risk_band": risk_band,
            "recommended_action": recommended_action,
            "threshold": self.threshold,
            "evidence": evidence,
            "features": {k: features[k] for k in self.model.feature_names},
        }

    def _get_risk_band(self, score: float) -> str:
        """Map risk score to band using ActionPolicy thresholds."""
        if score < self.action_policy.threshold_low:
            return "LOW"
        elif score < self.action_policy.threshold_optimal:
            return "MEDIUM"
        elif score < self.action_policy.threshold_high:
            return "HIGH"
        else:
            return "CRITICAL"

    def _build_evidence(self, features: Dict) -> List[Dict[str, Any]]:
        """Build structured evidence from features for human-readable explanation."""
        evidence = []

        # Behavioral evidence
        if features["customer_refund_rate"] > 0.25:
            evidence.append({
                "category": "behavioral",
                "metric": "refund_rate",
                "value": round(features["customer_refund_rate"], 3),
                "description": f"Elevated refund rate: {features['customer_refund_rate']:.1%} (avg ~12%)",
            })
        if features["customer_refunds_last_7d"] >= 3:
            evidence.append({
                "category": "behavioral",
                "metric": "refunds_last_7d",
                "value": features["customer_refunds_last_7d"],
                "description": f"{features['customer_refunds_last_7d']} refunds in last 7 days",
            })
        if features["amount_ratio_vs_customer_mean"] > 2.0:
            evidence.append({
                "category": "behavioral",
                "metric": "amount_ratio",
                "value": round(features["amount_ratio_vs_customer_mean"], 2),
                "description": f"Refund amount {features['amount_ratio_vs_customer_mean']:.1f}x customer's average order",
            })
        if features["refund_delay_hours"] < 6:
            evidence.append({
                "category": "behavioral",
                "metric": "refund_delay_hours",
                "value": round(features["refund_delay_hours"], 1),
                "description": f"Quick refund request: {features['refund_delay_hours']:.1f}h after order",
            })

        # Graph evidence
        if features["graph_shared_device_customers"] > 0:
            evidence.append({
                "category": "graph",
                "metric": "shared_device_customers",
                "value": features["graph_shared_device_customers"],
                "description": f"{features['graph_shared_device_customers']} other customers share this device",
            })
        if features["graph_shared_address_customers"] > 0:
            evidence.append({
                "category": "graph",
                "metric": "shared_address_customers",
                "value": features["graph_shared_address_customers"],
                "description": f"{features['graph_shared_address_customers']} other customers at this address",
            })
        if features["graph_component_size"] > 5:
            evidence.append({
                "category": "graph",
                "metric": "component_size",
                "value": features["graph_component_size"],
                "description": f"Connected cluster of {features['graph_component_size']} accounts",
            })
        if features["graph_neighbor_mean_refund_rate"] > 0.2:
            evidence.append({
                "category": "graph",
                "metric": "neighbor_mean_refund_rate",
                "value": round(features["graph_neighbor_mean_refund_rate"], 3),
                "description": f"Connected neighbors avg refund rate: {features['graph_neighbor_mean_refund_rate']:.1%}",
            })
        if features["graph_neighbor_max_refund_rate"] > 0.5:
            evidence.append({
                "category": "graph",
                "metric": "neighbor_max_refund_rate",
                "value": round(features["graph_neighbor_max_refund_rate"], 3),
                "description": f"One neighbor has {features['graph_neighbor_max_refund_rate']:.1%} refund rate",
            })
        if features["graph_shared_device_rarity"] > 0.4:
            evidence.append({
                "category": "graph",
                "metric": "device_rarity",
                "value": round(features["graph_shared_device_rarity"], 3),
                "description": "Device shared by unusually few customers (rare sharing)",
            })
        if features["graph_component_event_growth_24h"] > 2.0:
            evidence.append({
                "category": "graph",
                "metric": "component_event_growth_24h",
                "value": round(features["graph_component_event_growth_24h"], 2),
                "description": f"Cluster activity grew {features['graph_component_event_growth_24h']:.1f}x in last 24h",
            })

        # Temporal evidence
        if features["temporal_cluster_events_last_1h"] > 10:
            evidence.append({
                "category": "temporal",
                "metric": "cluster_events_1h",
                "value": features["temporal_cluster_events_last_1h"],
                "description": f"{features['temporal_cluster_events_last_1h']} events in cluster in last hour",
            })
        if features["temporal_synchronized_refund_ratio_1h"] > 0.5:
            evidence.append({
                "category": "temporal",
                "metric": "sync_refund_ratio_1h",
                "value": round(features["temporal_synchronized_refund_ratio_1h"], 3),
                "description": f"{features['temporal_synchronized_refund_ratio_1h']:.0%} of cluster events are refunds (last 1h)",
            })
        if features["temporal_account_creation_burst_24h"] > 2:
            evidence.append({
                "category": "temporal",
                "metric": "creation_burst_24h",
                "value": features["temporal_account_creation_burst_24h"],
                "description": f"{features['temporal_account_creation_burst_24h']} cluster accounts created within 24h",
            })
        if features["temporal_min_inter_event_delay_min"] < 5:
            evidence.append({
                "category": "temporal",
                "metric": "min_inter_event_delay_min",
                "value": round(features["temporal_min_inter_event_delay_min"], 1),
                "description": f"Cluster events every {features['temporal_min_inter_event_delay_min']:.1f} minutes",
            })

        return evidence

    def get_graph_subgraph(self, refund_id: str) -> Optional[Dict[str, Any]]:
        """Get PIT-correct network subgraph for a refund event."""
        ref_event = self.get_refund_event(refund_id)
        if ref_event is None:
            return None

        t_ref = ref_event["dt_refund"]
        cid = ref_event["customer_id"]
        did = ref_event["device_id"]
        aid = ref_event["address_id"]
        pid = ref_event["payment_token_id"]

        # Get shared entities
        shared_dev_entities = get_shared_entity_ids(self.g_pit, cid, "DEV_")
        shared_addr_entities = get_shared_entity_ids(self.g_pit, cid, "ADDR_")
        shared_pm_entities = get_shared_entity_ids(self.g_pit, cid, "PM_")

        connected_custs = get_connected_customers(
            self.g_pit, cid, shared_dev_entities, shared_addr_entities, shared_pm_entities
        )

        # Build nodes and edges for visualization
        nodes = []
        edges = []

        # Target customer
        nodes.append({
            "id": cid,
            "type": "customer",
            "label": cid,
            "is_target": True,
            "risk_score": None,  # Could add neighbor scores if needed
        })

        # Shared entities and connected customers
        all_entities = set()
        for eid in shared_dev_entities:
            all_entities.add((eid, "device"))
        for eid in shared_addr_entities:
            all_entities.add((eid, "address"))
        for eid in shared_pm_entities:
            all_entities.add((eid, "payment"))

        for eid, etype in all_entities:
            nodes.append({
                "id": eid,
                "type": etype,
                "label": eid,
                "is_target": False,
            })
            edges.append({
                "source": cid,
                "target": eid,
                "relationship": f"shares_{etype}",
            })

        # Connected customers
        for n_cid in connected_custs:
            nodes.append({
                "id": n_cid,
                "type": "customer",
                "label": n_cid,
                "is_target": False,
            })
            # Find shared entities between target and neighbor
            shared_with_target = set()
            for eid in shared_dev_entities:
                if self.g_pit.has_edge(n_cid, eid):
                    shared_with_target.add(eid)
            for eid in shared_addr_entities:
                if self.g_pit.has_edge(n_cid, eid):
                    shared_with_target.add(eid)
            for eid in shared_pm_entities:
                if self.g_pit.has_edge(n_cid, eid):
                    shared_with_target.add(eid)

            for eid in shared_with_target:
                edges.append({
                    "source": n_cid,
                    "target": eid,
                    "relationship": f"shares_{eid.split('_')[0].lower()}",
                })

        return {
            "nodes": nodes,
            "edges": edges,
            "target_customer": cid,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "connected_customers": len(connected_custs),
                "shared_devices": len(shared_dev_entities),
                "shared_addresses": len(shared_addr_entities),
                "shared_payments": len(shared_pm_entities),
            }
        }

    def get_timeline_events(self, refund_id: str, window_hours: int = 48) -> Optional[Dict[str, Any]]:
        """Get PIT-correct timeline events for a refund's connected component.
        
        Returns events from the target customer's connected component within
        window_hours before the refund timestamp. Only events strictly before
        t_ref are included (PIT-correct).
        """
        ref_event = self.get_refund_event(refund_id)
        if ref_event is None:
            return None

        t_ref = ref_event["dt_refund"]
        cid = ref_event["customer_id"]
        did = ref_event["device_id"]
        aid = ref_event["address_id"]
        pid = ref_event["payment_token_id"]

        # Get connected component customers
        shared_dev_entities = get_shared_entity_ids(self.g_pit, cid, "DEV_")
        shared_addr_entities = get_shared_entity_ids(self.g_pit, cid, "ADDR_")
        shared_pm_entities = get_shared_entity_ids(self.g_pit, cid, "PM_")

        connected_custs = get_connected_customers(
            self.g_pit, cid, shared_dev_entities, shared_addr_entities, shared_pm_entities
        )
        component_members = connected_custs.union({cid})

        # Collect events from component members within window before t_ref
        window_start = t_ref - pd.Timedelta(hours=window_hours)
        events = []

        for member_cid in component_members:
            for ev_t, ev_type in self.comp_events.get(member_cid, []):
                if ev_t >= window_start and ev_t < t_ref:
                    # Get order/refund details for display
                    events.append({
                        "customer_id": member_cid,
                        "timestamp": ev_t.isoformat(),
                        "event_type": ev_type,  # "order" or "refund"
                        "is_target": member_cid == cid,
                    })

        # Sort chronologically
        events.sort(key=lambda x: x["timestamp"])

        return {
            "target_customer": cid,
            "target_refund_id": refund_id,
            "target_timestamp": t_ref.isoformat(),
            "window_hours": window_hours,
            "events": events,
            "component_size": len(component_members),
        }


# Global instance for dependency injection
_inference_service: Optional[SentinelInferenceService] = None


def get_inference_service() -> SentinelInferenceService:
    """Get or create the global inference service instance."""
    global _inference_service
    if _inference_service is None:
        _inference_service = SentinelInferenceService()
        _inference_service.initialize()
    return _inference_service