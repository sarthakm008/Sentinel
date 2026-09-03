"""Core Graph Feature Computations for Phase 3 and Phase 4.

Pure functions operating on point-in-time state.
"""

import math
import networkx as nx
import pandas as pd
from typing import Dict, List, Set, Tuple


def compute_entity_rarity(
    shared_entities: Set[str],
    entity_customer_degree: Dict[str, Set[str]]
) -> float:
    """Compute max entity rarity for a set of shared entities.

    Rarity = 1 / log(1 + degree) where degree = number of distinct customers
    who have ever shared this entity (strictly before t_ref).

    Args:
        shared_entities: Set of entity IDs (DEV_, ADDR_, PM_) shared by current customer
        entity_customer_degree: Mapping from entity_id to set of customer_ids

    Returns:
        Maximum rarity across shared entities, or 0.0 if no shared entities.
    """
    if not shared_entities:
        return 0.0

    max_rarity = 0.0
    for eid in shared_entities:
        customers = entity_customer_degree.get(eid, set())
        deg = len(customers)
        if deg <= 1:
            rarity = 0.0
        else:
            rarity = 1.0 / math.log(1.0 + deg)
        if rarity > max_rarity:
            max_rarity = rarity
    return max_rarity


def compute_risk_concentration(
    connected_custs: Set[str],
    cust_orders: Dict[str, List[tuple]],
    cust_refunds: Dict[str, List[tuple]],
    t_ref
) -> tuple:
    """Compute neighbor max refund rate and top-3 risk mass.

    Args:
        connected_custs: 1-hop neighbor customer IDs (excluding current)
        cust_orders: PIT order history {cid: [(dt, amount, did, aid, pid), ...]}
        cust_refunds: PIT refund history {cid: [(dt, amount), ...]}
        t_ref: Current refund timestamp (strict cutoff)

    Returns:
        (max_refund_rate, risk_mass_top3)
    """
    if not connected_custs:
        return 0.0, 0.0

    neighbor_rates = []
    for n_cid in connected_custs:
        # Strict PIT: only orders/refunds before t_ref
        n_ord = len([o for o in cust_orders.get(n_cid, []) if o[0] < t_ref])
        n_ref = len([r for r in cust_refunds.get(n_cid, []) if r[0] < t_ref])
        n_rr = n_ref / max(1, n_ord)
        neighbor_rates.append(n_rr)

    if not neighbor_rates:
        return 0.0, 0.0

    max_rr = max(neighbor_rates)
    risk_mass = sum(sorted(neighbor_rates, reverse=True)[:3])
    return max_rr, risk_mass


def compute_recency(
    shared_entities: Set[str],
    entity_customer_timestamps: Dict[str, Dict[str, object]],
    cid: str,
    t_ref
) -> float:
    """Compute minimum hours since last shared interaction for a set of entities.

    Args:
        shared_entities: Set of entity IDs shared by current customer
        entity_customer_timestamps: {eid: {cid: last_seen_dt}}
        cid: Current customer ID
        t_ref: Current refund timestamp

    Returns:
        Minimum recency in hours across shared entities.
        Returns 1e6 if no shared entities or no prior interaction recorded.
    """
    if not shared_entities:
        return 1e6

    min_recency = 1e6
    for eid in shared_entities:
        cust_map = entity_customer_timestamps.get(eid, {})
        last_seen = cust_map.get(cid)
        if last_seen is not None:
            recency_h = (t_ref - last_seen).total_seconds() / 3600.0
            if recency_h < min_recency:
                min_recency = recency_h
    return min_recency


def get_shared_entity_ids(
    g_pit,
    cid: str,
    entity_prefix: str
) -> Set[str]:
    """Get entity IDs of a specific type shared by current customer.

    Args:
        g_pit: Point-in-time NetworkX graph
        cid: Current customer ID
        entity_prefix: One of "DEV_", "ADDR_", "PM_"

    Returns:
        Set of entity IDs of the given type connected to cid in g_pit.
    """
    if not g_pit.has_node(cid):
        return set()

    shared = set()
    for neighbor in g_pit.neighbors(cid):
        if neighbor.startswith(entity_prefix):
            shared.add(neighbor)
    return shared


def get_connected_customers(
    g_pit,
    cid: str,
    shared_dev_entities: Set[str],
    shared_addr_entities: Set[str],
    shared_pm_entities: Set[str]
) -> Set[str]:
    """Get all 1-hop connected customers via shared entities.

    Args:
        g_pit: Point-in-time NetworkX graph
        cid: Current customer ID
        shared_dev_entities: Device IDs shared by current customer
        shared_addr_entities: Address IDs shared by current customer
        shared_pm_entities: Payment token IDs shared by current customer

    Returns:
        Set of connected customer IDs (excluding cid).
    """
    connected = set()
    for eid in shared_dev_entities.union(shared_addr_entities).union(shared_pm_entities):
        if g_pit.has_node(eid):
            for n in g_pit.neighbors(eid):
                if n.startswith("CUS_") and n != cid:
                    connected.add(n)
    return connected


def compute_all_core_graph_features(
    g_pit,
    cid: str,
    t_ref,
    cust_orders: Dict[str, List[tuple]],
    cust_refunds: Dict[str, List[tuple]],
    entity_customer_degree: Dict[str, Set[str]],
    entity_customer_timestamps: Dict[str, Dict[str, object]],
    did: str,
    aid: str,
    pid: str
) -> Dict[str, float]:
    """Compute all 7 Core Graph features for a single refund event.

    Args:
        g_pit: Point-in-time bipartite graph
        cid: Current customer ID
        t_ref: Current refund timestamp
        cust_orders: PIT order history
        cust_refunds: PIT refund history
        entity_customer_degree: {eid: set of customer_ids}
        entity_customer_timestamps: {eid: {cid: last_seen_dt}}
        did: Current device ID
        aid: Current address ID
        pid: Current payment token ID

    Returns:
        Dictionary of 7 Core Graph feature values.
    """
    # Get shared entity IDs (not customer counts)
    shared_dev_entities = get_shared_entity_ids(g_pit, cid, "DEV_")
    shared_addr_entities = get_shared_entity_ids(g_pit, cid, "ADDR_")
    shared_pm_entities = get_shared_entity_ids(g_pit, cid, "PM_")

    # Connected customers via shared entities
    connected_custs = get_connected_customers(
        g_pit, cid,
        shared_dev_entities, shared_addr_entities, shared_pm_entities
    )

    # Entity Rarity
    device_rarity = compute_entity_rarity(shared_dev_entities, entity_customer_degree)
    address_rarity = compute_entity_rarity(shared_addr_entities, entity_customer_degree)
    payment_rarity = compute_entity_rarity(shared_pm_entities, entity_customer_degree)

    # Risk Concentration
    max_rr, risk_mass = compute_risk_concentration(
        connected_custs, cust_orders, cust_refunds, t_ref
    )

    # Temporal Recency
    device_recency = compute_recency(
        shared_dev_entities, entity_customer_timestamps, cid, t_ref
    )
    address_recency = compute_recency(
        shared_addr_entities, entity_customer_timestamps, cid, t_ref
    )

    return {
        "graph_shared_device_rarity": device_rarity,
        "graph_shared_address_rarity": address_rarity,
        "graph_shared_payment_rarity": payment_rarity,
        "graph_neighbor_max_refund_rate": max_rr,
        "graph_neighbor_risk_mass": risk_mass,
        "graph_shared_device_recency_h": device_recency,
        "graph_shared_address_recency_h": address_recency,
    }


def compute_component_event_growth(
    g_pit,
    cid: str,
    t_ref,
    cust_orders: Dict[str, List[tuple]],
    comp_events: Dict[str, List[Tuple]],
) -> float:
    """Compute component event growth rate for the customer's connected component.

    Measures the ratio of events in the customer's connected component over the
    recent 24-hour window compared to the preceding 24-hour window.

    PIT-safe: Only considers events with timestamp < t_ref. The component is
    defined by the connected component of the customer in the PIT graph at t_ref.
    Historical events are attributed to the component they belonged to at the time
    of the event, which is naturally handled by collecting events from all current
    component members' histories (which only contain events that occurred before
    t_ref and reflect the graph structure at the time of those events).

    Args:
        g_pit: Point-in-time bipartite graph
        cid: Current customer ID
        t_ref: Current refund timestamp (strict cutoff)
        cust_orders: PIT order history {cid: [(dt, amount, did, aid, pid), ...]}
        comp_events: Component event tracking {cid: [(dt, event_type), ...]}

    Returns:
        Growth ratio = events(component, [t-24h, t)) / max(1, events(component, [t-48h, t-24h)))
        Returns 0.0 if no current component or no events in recent window.
    """
    if not g_pit.has_node(cid):
        return 0.0

    # Get current component members (1-hop connected customers + self)
    component_members = set(nx.node_connected_component(g_pit, cid))

    t_24h_ago = t_ref - pd.Timedelta(hours=24)
    t_48h_ago = t_ref - pd.Timedelta(hours=48)

    recent_events = 0
    prior_events = 0

    for member_cid in component_members:
        for ev_t, ev_type in comp_events.get(member_cid, []):
            if ev_t >= t_24h_ago and ev_t < t_ref:
                recent_events += 1
            elif ev_t >= t_48h_ago and ev_t < t_24h_ago:
                prior_events += 1

    if recent_events == 0:
        return 0.0

    return float(recent_events) / float(max(1, prior_events))


def compute_component_new_neighbors(
    g_pit,
    cid: str,
    t_ref,
    comp_events: Dict[str, List[Tuple]],
) -> float:
    """Compute number of new neighbors appearing in the component during recent 24h window.

    Measures customers who appeared in the component during the recent 24-hour window
    but were not present in the component during the preceding 24-hour window.

    PIT-safe: Uses comp_events timestamps which are strictly < t_ref.
    A customer is considered "in the component" at a given timestamp if they
    appear in comp_events at that timestamp (i.e., they had an event while
    connected to the component).

    Args:
        g_pit: Point-in-time bipartite graph
        cid: Current customer ID
        t_ref: Current refund timestamp (strict cutoff)
        comp_events: Component event tracking {cid: [(dt, event_type), ...]}

    Returns:
        Number of new neighbors = neighbors in [t-24h, t) minus neighbors in [t-48h, t-24h)
        Returns 0.0 if no current component or no neighbors in recent window.
        Excludes the customer themselves from the count.
    """
    if not g_pit.has_node(cid):
        return 0.0

    # Get current component members for reference
    component_members = set(nx.node_connected_component(g_pit, cid))

    t_24h_ago = t_ref - pd.Timedelta(hours=24)
    t_48h_ago = t_ref - pd.Timedelta(hours=48)

    recent_neighbors = set()
    prior_neighbors = set()

    for member_cid in component_members:
        if member_cid == cid:
            continue
        for ev_t, ev_type in comp_events.get(member_cid, []):
            if ev_t >= t_24h_ago and ev_t < t_ref:
                recent_neighbors.add(member_cid)
            elif ev_t >= t_48h_ago and ev_t < t_24h_ago:
                prior_neighbors.add(member_cid)

    new_neighbors = recent_neighbors - prior_neighbors
    return float(len(new_neighbors))


def compute_graph_neighbor_sync_ratio(
    connected_custs: Set[str],
    t_ref,
    comp_events: Dict[str, List[Tuple]],
) -> float:
    """
    Compute fraction of neighbor events that are refunds in 1h window.

    Measures the fraction of 1-hop neighbor events that are refunds in the
    preceding 1-hour window. This captures local temporal synchronization
    of refund activity among directly connected customers.

    PIT-safe: Only considers events with timestamp < t_ref. The 1-hop
    neighborhood is defined by the PIT graph at t_ref (edges from orders
    with event_time < t_ref). The target customer's own events are excluded.

    Args:
        connected_custs: 1-hop neighbor customer IDs (excluding current)
        t_ref: Current refund timestamp (strict cutoff)
        comp_events: Component event tracking {cid: [(dt, event_type), ...]}

    Returns:
        neighbor_refunds_1h / max(1, neighbor_events_1h)
        Returns 0.0 if no neighbors or no neighbor events in window.
    """
    if not connected_custs:
        return 0.0

    t_1h_ago = t_ref - pd.Timedelta(hours=1)

    neighbor_events_1h = 0
    neighbor_refunds_1h = 0

    for n_cid in connected_custs:
        for ev_t, ev_type in comp_events.get(n_cid, []):
            if ev_t >= t_1h_ago and ev_t < t_ref:
                neighbor_events_1h += 1
                if ev_type == "refund":
                    neighbor_refunds_1h += 1

    if neighbor_events_1h == 0:
        return 0.0

    return float(neighbor_refunds_1h) / float(neighbor_events_1h)