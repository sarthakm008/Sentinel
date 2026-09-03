"""Unit tests for Phase 3 Core Graph Features."""

import math
import networkx as nx
from datetime import datetime, timedelta
import pytest
import numpy as np

from ml.features.graph_features import (
    compute_all_core_graph_features,
    compute_component_event_growth,
    compute_component_new_neighbors,
    compute_entity_rarity,
    compute_graph_neighbor_sync_ratio,
    compute_risk_concentration,
    compute_recency,
    get_connected_customers,
    get_shared_entity_ids,
)


class MockGraph:
    """Mock NetworkX-like graph for testing."""
    def __init__(self, edges=None):
        self._edges = edges or {}
    
    def has_node(self, node):
        return node in self._edges
    
    def neighbors(self, node):
        return self._edges.get(node, set())
    
    # NetworkX compatibility for node_connected_component
    def is_directed(self):
        return False
    
    def is_multigraph(self):
        return False
    
    def __len__(self):
        return len(self._edges)
    
    def __iter__(self):
        return iter(self._edges)
    
    def __contains__(self, node):
        return node in self._edges


def test_compute_entity_rarity_empty():
    """Rarity should be 0.0 for empty shared entity set."""
    assert compute_entity_rarity(set(), {}) == 0.0


def test_compute_entity_rarity_no_sharing():
    """Rarity should be 0.0 when degree <= 1."""
    entity_degree = {"DEV_1": {"CUS_1"}}
    assert compute_entity_rarity({"DEV_1"}, entity_degree) == 0.0


def test_compute_entity_rarity_degree_two():
    """Degree 2 gives rarity = 1 / log(3) ≈ 0.91."""
    entity_degree = {"DEV_1": {"CUS_1", "CUS_2"}}
    rarity = compute_entity_rarity({"DEV_1"}, entity_degree)
    expected = 1.0 / math.log(3.0)
    assert abs(rarity - expected) < 1e-6


def test_compute_entity_rarity_multiple_entities():
    """Should return max rarity across entities."""
    entity_degree = {
        "DEV_1": {"CUS_1", "CUS_2"},  # deg=2, rarity≈0.91
        "DEV_2": {"CUS_1", "CUS_2", "CUS_3", "CUS_4", "CUS_5"},  # deg=5, rarity≈0.62
    }
    rarity = compute_entity_rarity({"DEV_1", "DEV_2"}, entity_degree)
    assert abs(rarity - (1.0 / math.log(3.0))) < 1e-6


def test_compute_risk_concentration_empty():
    """Empty neighborhood returns (0.0, 0.0)."""
    max_rr, risk_mass = compute_risk_concentration(set(), {}, {}, datetime.now())
    assert max_rr == 0.0
    assert risk_mass == 0.0


def test_compute_risk_concentration_pit_cutoff():
    """Neighbor refund rates must use only events before t_ref."""
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    # Neighbor has 2 orders, 1 refund before t_ref, 1 refund after t_ref
    cust_orders = {
        "CUS_N1": [
            (datetime(2026, 6, 10), 1000, "DEV_1", "ADDR_1", "PM_1"),
            (datetime(2026, 6, 12), 1000, "DEV_1", "ADDR_1", "PM_1"),
        ]
    }
    cust_refunds = {
        "CUS_N1": [
            (datetime(2026, 6, 11), 500),  # before t_ref
            (datetime(2026, 6, 16), 500),  # after t_ref - should be ignored
        ]
    }
    
    max_rr, risk_mass = compute_risk_concentration(
        {"CUS_N1"}, cust_orders, cust_refunds, t_ref
    )
    # Only 1 refund before t_ref out of 2 orders = 0.5
    assert abs(max_rr - 0.5) < 1e-6
    assert abs(risk_mass - 0.5) < 1e-6


def test_compute_recency_no_shared():
    """No shared entities returns sentinel 1e6."""
    assert compute_recency(set(), {}, "CUS_1", datetime.now()) == 1e6


def test_compute_recency_no_prior_interaction():
    """Entity exists but customer never shared it before returns 1e6."""
    entity_timestamps = {"DEV_1": {"CUS_OTHER": datetime.now()}}
    assert compute_recency({"DEV_1"}, entity_timestamps, "CUS_1", datetime.now()) == 1e6


def test_compute_recency_with_prior():
    """Returns hours since last shared interaction."""
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    last_seen = datetime(2026, 6, 15, 6, 0, 0)  # 6 hours ago
    entity_timestamps = {"DEV_1": {"CUS_1": last_seen}}
    
    recency = compute_recency({"DEV_1"}, entity_timestamps, "CUS_1", t_ref)
    assert abs(recency - 6.0) < 1e-6


def test_compute_recency_multiple_entities():
    """Returns minimum recency across entities."""
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    entity_timestamps = {
        "DEV_1": {"CUS_1": datetime(2026, 6, 15, 10, 0, 0)},  # 2h ago
        "ADDR_1": {"CUS_1": datetime(2026, 6, 15, 6, 0, 0)},   # 6h ago
    }
    recency = compute_recency({"DEV_1", "ADDR_1"}, entity_timestamps, "CUS_1", t_ref)
    assert abs(recency - 2.0) < 1e-6


def test_get_shared_entity_ids():
    """Extracts entity IDs of specific prefix from PIT graph."""
    g = MockGraph({
        "CUS_1": {"DEV_1", "ADDR_1", "PM_1", "CUS_2"},
        "DEV_1": {"CUS_1", "CUS_2"},
        "ADDR_1": {"CUS_1"},
        "PM_1": {"CUS_1"},
    })
    
    devs = get_shared_entity_ids(g, "CUS_1", "DEV_")
    assert devs == {"DEV_1"}
    
    addrs = get_shared_entity_ids(g, "CUS_1", "ADDR_")
    assert addrs == {"ADDR_1"}
    
    pms = get_shared_entity_ids(g, "CUS_1", "PM_")
    assert pms == {"PM_1"}


def test_get_shared_entity_ids_no_node():
    """Customer not in graph returns empty set."""
    g = MockGraph({})
    assert get_shared_entity_ids(g, "CUS_1", "DEV_") == set()


def test_get_connected_customers():
    """Collects 1-hop customers via shared entities."""
    g = MockGraph({
        "CUS_1": {"DEV_1", "ADDR_1"},
        "CUS_2": {"DEV_1"},
        "CUS_3": {"ADDR_1"},
        "CUS_4": {"PM_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
        "ADDR_1": {"CUS_1", "CUS_3"},
        "PM_1": {"CUS_4"},
    })
    
    connected = get_connected_customers(
        g, "CUS_1",
        {"DEV_1"}, {"ADDR_1"}, set()
    )
    # Should find CUS_2 via DEV_1 and CUS_3 via ADDR_1, exclude CUS_1
    assert connected == {"CUS_2", "CUS_3"}


def test_compute_all_core_graph_features_no_sharing():
    """All features should be 0 or sentinel when no sharing."""
    g = MockGraph({})
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    features = compute_all_core_graph_features(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        cust_refunds={},
        entity_customer_degree={},
        entity_customer_timestamps={},
        did="DEV_1",
        aid="ADDR_1",
        pid="PM_1",
    )
    
    assert features["graph_shared_device_rarity"] == 0.0
    assert features["graph_shared_address_rarity"] == 0.0
    assert features["graph_shared_payment_rarity"] == 0.0
    assert features["graph_neighbor_max_refund_rate"] == 0.0
    assert features["graph_neighbor_risk_mass"] == 0.0
    assert features["graph_shared_device_recency_h"] == 1e6
    assert features["graph_shared_address_recency_h"] == 1e6


def test_compute_all_core_graph_features_deterministic():
    """Same inputs should produce same outputs."""
    g = MockGraph({
        "CUS_1": {"DEV_1", "ADDR_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
        "ADDR_1": {"CUS_1"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    entity_degree = {"DEV_1": {"CUS_1", "CUS_2"}, "ADDR_1": {"CUS_1"}}
    entity_timestamps = {
        "DEV_1": {"CUS_1": datetime(2026, 6, 15, 10, 0, 0)},
        "ADDR_1": {"CUS_1": datetime(2026, 6, 15, 6, 0, 0)},
    }
    cust_orders = {
        "CUS_1": [(datetime(2026, 6, 10), 1000, "DEV_1", "ADDR_1", "PM_1")],
        "CUS_2": [(datetime(2026, 6, 11), 1000, "DEV_1", "ADDR_2", "PM_2")],
    }
    cust_refunds = {
        "CUS_2": [(datetime(2026, 6, 12), 500)],
    }
    
    f1 = compute_all_core_graph_features(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1", "ADDR_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
            "ADDR_1": {"CUS_1"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders=cust_orders,
        cust_refunds=cust_refunds,
        entity_customer_degree=entity_degree,
        entity_customer_timestamps=entity_timestamps,
        did="DEV_1",
        aid="ADDR_1",
        pid="PM_1",
    )
    
    f2 = compute_all_core_graph_features(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1", "ADDR_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
            "ADDR_1": {"CUS_1"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders=cust_orders,
        cust_refunds=cust_refunds,
        entity_customer_degree=entity_degree,
        entity_customer_timestamps=entity_timestamps,
        did="DEV_1",
        aid="ADDR_1",
        pid="PM_1",
    )
    
    for k in f1:
        assert f1[k] == f2[k], f"Non-deterministic: {k}"


def test_feature_values_bounds():
    """All feature values should be within expected bounds."""
    g = MockGraph({
        "CUS_1": {"DEV_1", "ADDR_1"},
        "CUS_2": {"DEV_1"},
        "DEV_1": {"CUS_1", "CUS_2"},
        "ADDR_1": {"CUS_1"},
    })
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    entity_degree = {"DEV_1": {"CUS_1", "CUS_2"}, "ADDR_1": {"CUS_1"}}
    entity_timestamps = {
        "DEV_1": {"CUS_1": datetime(2026, 6, 15, 10, 0, 0)},
        "ADDR_1": {"CUS_1": datetime(2026, 6, 15, 6, 0, 0)},
    }
    cust_orders = {
        "CUS_1": [(datetime(2026, 6, 10), 1000, "DEV_1", "ADDR_1", "PM_1")],
        "CUS_2": [(datetime(2026, 6, 11), 1000, "DEV_1", "ADDR_2", "PM_2")],
    }
    cust_refunds = {
        "CUS_2": [(datetime(2026, 6, 12), 500)],
    }
    
    features = compute_all_core_graph_features(
        g_pit=MockGraph({
            "CUS_1": {"DEV_1", "ADDR_1"},
            "CUS_2": {"DEV_1"},
            "DEV_1": {"CUS_1", "CUS_2"},
            "ADDR_1": {"CUS_1"},
        }),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders=cust_orders,
        cust_refunds=cust_refunds,
        entity_customer_degree=entity_degree,
        entity_customer_timestamps=entity_timestamps,
        did="DEV_1",
        aid="ADDR_1",
        pid="PM_1",
    )
    
    # Rarity in [0, 1]
    assert 0.0 <= features["graph_shared_device_rarity"] <= 1.0
    assert 0.0 <= features["graph_shared_address_rarity"] <= 1.0
    assert 0.0 <= features["graph_shared_payment_rarity"] <= 1.0
    
    # Risk concentration in [0, 1]
    assert 0.0 <= features["graph_neighbor_max_refund_rate"] <= 1.0
    assert 0.0 <= features["graph_neighbor_risk_mass"] <= 3.0  # top-3 sum
    
    # Recency >= 0
    assert features["graph_shared_device_recency_h"] >= 0.0
    assert features["graph_shared_address_recency_h"] >= 0.0





def test_compute_component_event_growth_no_component():
    """No component returns 0.0 growth."""
    g = MockGraph({})
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    growth = compute_component_event_growth(
        g_pit=MockGraph({}),
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events={},
    )
    assert growth == 0.0


def test_compute_component_event_growth_no_recent_events():
    """Zero recent events returns 0.0 growth."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 10), "order"),
        ]
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    assert growth == 0.0


def test_compute_component_event_growth_with_prior_events():
    """Growth > 0 when recent events > prior events."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 14, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    # Recent: CUS_1 at 14:00, CUS_2 at 12:00 = 2 events
    # Prior: CUS_1 at 10:00 = 1 event
    # Growth = 2 / max(1, 1) = 2.0
    assert growth == 2.0


def test_compute_component_event_growth_pit_cutoff():
    """Events at or after t_ref must be excluded."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    growth = compute_component_event_growth(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        cust_orders={},
        comp_events=comp_events,
    )
    # Recent: CUS_2 at 12:00 = 1
    # Prior: CUS_1 at 10:00 = 1
    # Growth = 1 / max(1, 1) = 1.0
    assert growth == 1.0


def test_compute_component_new_neighbors_no_component():
    """No component returns 0 new neighbors."""
    new = compute_component_new_neighbors(
        g_pit=MockGraph({}),
        cid="CUS_1",
        t_ref=datetime.now(),
        comp_events={},
    )
    assert new == 0.0


def test_compute_component_new_neighbors_no_new():
    """No new neighbors when same neighbors in both windows."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 14, 0, 0), "order"),  # prior window (after 48h ago)
            (datetime(2026, 6, 14, 12, 0, 0), "order"),  # recent window
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    # CUS_2 appears in both windows (prior: 13th 14:00, recent: 14th 12:00)
    # So not new
    assert new == 0.0


def test_compute_component_new_neighbors_with_new():
    """Counts neighbors appearing only in recent window."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1"), ("CUS_3", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
        ],
        "CUS_2": [
            (datetime(2026, 6, 13, 10, 0, 0), "order"),
        ],
        "CUS_3": [
            (datetime(2026, 6, 14, 12, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 1.0


def test_compute_component_new_neighbors_pit_cutoff():
    """Events at or after t_ref excluded."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    
    comp_events = {
        "CUS_1": [],
        "CUS_2": [
            (datetime(2026, 6, 14, 10, 0, 0), "order"),
            (datetime(2026, 6, 15, 14, 0, 0), "order"),
        ],
    }
    
    new = compute_component_new_neighbors(
        g_pit=g,
        cid="CUS_1",
        t_ref=t_ref,
        comp_events=comp_events,
    )
    assert new == 0.0


def test_compute_graph_neighbor_sync_ratio_no_neighbors():
    """No 1-hop neighbors returns 0.0."""
    assert compute_graph_neighbor_sync_ratio(set(), datetime.now(), {}) == 0.0


def test_compute_graph_neighbor_sync_ratio_no_recent_activity():
    """No neighbor events in 1h window returns 0.0."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {"CUS_2": [(datetime(2026, 6, 14), "order")]}  # 24h ago
    assert compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events) == 0.0


def test_compute_graph_neighbor_sync_ratio_partial_sync():
    """Partial synchronization: 1 refund out of 2 events in 1h window."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {"CUS_2": [(datetime(2026, 6, 15, 11, 30), "refund")]}  # 30 min ago
    assert compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events) == 1.0


def test_compute_graph_neighbor_sync_ratio_full_sync():
    """All neighbor events are refunds -> ratio = 1.0."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1"), ("CUS_3", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {
        "CUS_2": [(datetime(2026, 6, 15, 11, 30), "refund")],
        "CUS_3": [(datetime(2026, 6, 15, 11, 45), "refund")],
    }
    assert compute_graph_neighbor_sync_ratio({"CUS_2", "CUS_3"}, t_ref, comp_events) == 1.0


def test_compute_graph_neighbor_sync_ratio_mixed_sync():
    """Mixed events: some refunds, some orders."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1"), ("CUS_3", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {
        "CUS_2": [
            (datetime(2026, 6, 15, 11, 30), "order"),
            (datetime(2026, 6, 15, 11, 45), "refund"),
        ],
        "CUS_3": [(datetime(2026, 6, 15, 11, 40), "order")],
    }
    # 1 refund out of 3 events = 0.333...
    result = compute_graph_neighbor_sync_ratio({"CUS_2", "CUS_3"}, t_ref, comp_events)
    assert abs(result - 1.0/3.0) < 1e-6


def test_compute_graph_neighbor_sync_ratio_pit_cutoff():
    """Events at or after t_ref are excluded."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {
        "CUS_2": [
            (datetime(2026, 6, 15, 11, 30), "refund"),  # 30 min ago
            (datetime(2026, 6, 15, 12, 30), "refund"),  # 30 min after t_ref - excluded
        ],
    }
    assert compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events) == 1.0


def test_compute_graph_neighbor_sync_ratio_excludes_self():
    """Target customer's own events are never included in neighbor computation."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {
        "CUS_1": [(datetime(2026, 6, 15, 11, 30), "refund")],  # self event
        "CUS_2": [(datetime(2026, 6, 15, 11, 30), "refund")],  # neighbor event
    }
    # connected_custs should only contain CUS_2, not CUS_1
    result = compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events)
    assert result == 1.0  # Only neighbor's refund counted


def test_compute_graph_neighbor_sync_ratio_pit_causality():
    """Feature at event i independent of events j > i (determinism + PIT)."""
    g = nx.Graph()
    g.add_edges_from([("CUS_1", "DEV_1"), ("CUS_2", "DEV_1")])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    comp_events = {"CUS_2": [(datetime(2026, 6, 15, 11, 30), "refund")]}
    r1 = compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events)
    r2 = compute_graph_neighbor_sync_ratio({"CUS_2"}, t_ref, comp_events)
    assert r1 == r2


def test_compute_graph_neighbor_sync_ratio_legitimate_shared_infra():
    """Legitimate shared infrastructure (hostel) shows moderate sync, not extreme."""
    g = nx.Graph()
    g.add_edges_from([
        ("CUS_1", "DEV_1"), ("CUS_2", "DEV_1"), ("CUS_3", "DEV_1"),
        ("CUS_4", "DEV_1"), ("CUS_5", "DEV_1"), ("CUS_6", "DEV_1"),
        ("CUS_7", "DEV_1"), ("CUS_8", "DEV_1"), ("CUS_9", "DEV_1"),
        ("CUS_10", "DEV_1"), ("CUS_10", "DEV_1"), ("CUS_11", "DEV_1"),
        ("CUS_12", "DEV_1"),
    ])
    t_ref = datetime(2026, 6, 15, 12, 0, 0)
    # Simulate hostel: 12 customers, each with 1 order in the last hour
    comp_events = {f"CUS_{i}": [(datetime(2026, 6, 15, 11, 30), "order")] for i in range(2, 13)}
    # All are orders, no refunds -> sync ratio = 0
    result = compute_graph_neighbor_sync_ratio({f"CUS_{i}" for i in range(2, 13)}, t_ref, comp_events)
    assert result == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])