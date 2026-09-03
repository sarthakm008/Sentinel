# Data Dictionary — Sentinel Synthetic World

This document formally specifies the data model, entity attributes, event tables, and label semantics for the Sentinel benchmark.

---

## 1. Relational Entity Tables

### Customers (`data/raw/customers.parquet`)
| Column | Type | Description |
|---|---|---|
| `customer_id` | String (PK) | Unique synthetic customer identifier (`CUS_000001`) |
| `account_created_at` | ISO Timestamp | Synthetic timestamp when account was registered. **Shared distribution for legitimate and abuse:** uniform over [-365, +144] days relative to simulation start (2026-01-01). |
| `merchant_id` | String (FK) | Primary merchant associated with the customer |
| `segment` | String | Customer spending profile (`standard`, `premium`, `budget`, `frequent_buyer`) |

### Devices (`data/raw/devices.parquet`)
| Column | Type | Description |
|---|---|---|
| `device_id` | String (PK) | Unique synthetic hardware/browser fingerprint (`DEV_000001`) |
| `device_type` | String | Device category (`mobile`, `desktop`, `tablet`) |

### Addresses (`data/raw/addresses.parquet`)
| Column | Type | Description |
|---|---|---|
| `address_id` | String (PK) | Unique shipping/billing location (`ADDR_000001`) |
| `region` | String | Geographic zone (`North`, `South`, `East`, `West`, `Central`) |
| `address_type` | String | Building archetype (`standard`, `household`, `hostel`, `office`) |

### Payment Tokens (`data/raw/payment_tokens.parquet`)
| Column | Type | Description |
|---|---|---|
| `payment_token_id` | String (PK) | Pseudonymous payment instrument (`PM_000001`) |
| `payment_type` | String | Payment method (`upi`, `credit_card`, `debit_card`, `netbanking`) |

---

## 2. Transaction Event Tables

### Orders (`data/raw/orders.parquet`)
| Column | Type | Description |
|---|---|---|
| `order_id` | String (PK) | Unique order identifier (`ORD_00000001`) |
| `customer_id` | String (FK) | Purchasing customer |
| `merchant_id` | String (FK) | Merchant where order was placed |
| `timestamp` | ISO Timestamp | Order placement timestamp |
| `amount` | Float | Transaction basket value in INR |
| `product_category` | String | Category (`electronics`, `apparel`, `footwear`, `home_kitchen`, `beauty`, `books`) |
| `device_id` | String (FK) | Device used during checkout |
| `address_id` | String (FK) | Shipping delivery address |
| `payment_token_id` | String (FK) | Payment instrument token used |

### Refunds (`data/raw/refunds.parquet`)
| Column | Type | Description |
|---|---|---|
| `refund_id` | String (PK) | Unique refund event identifier (`REF_0000001`) |
| `order_id` | String (FK) | Order against which refund is claimed |
| `customer_id` | String (FK) | Customer requesting the refund |
| `timestamp` | ISO Timestamp | Refund request timestamp ($t_{\text{refund}} \ge t_{\text{order}}$) |
| `amount` | Float | Refunded amount in INR |
| `reason_category` | String | Stated reason (`wrong_size`, `defective_item`, `not_as_described`, `arrived_late`, `damaged_in_transit`, `changed_mind`) |
| `status` | String | Operational status (`processed`) |
| `coordinated_refund_abuse` | Integer (0 or 1) | **Target Ground-Truth Label** |

**Refund Delay Generation (Phase 2.5):** Refund delays (`refund_delay_hours = (timestamp - order_timestamp) / 3600`) are sampled from a **shared three-component lognormal mixture** for both legitimate and abuse refunds, eliminating the previous generator artifact where abuse and legitimate delays followed different distributions. Mixture components (weight, lognormal μ, lognormal σ, min_days, max_days):
1. Standard logistics (50%): μ=1.1, σ=0.45, clipped to [1.0, 10.0] days — median ~3.5 days
2. Extended processing (35%): μ=1.8, σ=0.50, clipped to [3.0, 21.0] days — median ~6.5 days  
3. Dispute/resolution (15%): μ=2.5, σ=0.60, clipped to [7.0, 45.0] days — median ~12 days

---

## 3. Isolated Metadata

### Ground Truth Rings (`data/raw/ground_truth_rings.parquet`)
> [!IMPORTANT]
> This table is **strictly isolated**. It is used exclusively for dataset generation bookkeeping and adversarial evaluation. Feature extraction pipelines and production scoring endpoints are strictly prohibited from loading this file.

| Column | Type | Description |
|---|---|---|
| `ring_id` | String (PK) | Ring identifier (`RING_0001`) |
| `ring_type` | String | Topology archetype (`type_a_dense`, `type_b_partial`, `type_c_sparse`, `type_d_temporal`, `type_e_mixed`, `type_f_structural_shift`) |
| `customer_ids` | JSON String | Array of member customer IDs |
| `target_merchant_ids` | JSON String | Targeted merchant IDs |
| `attack_start_day` | Integer | Simulation day when attack begins. **Sampled after all ring member accounts are created** to ensure account age at attack time follows the same marginal distribution as legitimate customers. |
| `attack_duration_days` | Integer | Duration of attack campaign |
| `structure_class` | String | Graph structure class (`standard`, `relay_chain`) |
| `is_abuse` | Boolean | True |

---

## 4. Label Semantics

`coordinated_refund_abuse = 1` if and only if:
1. The refund request originates from a customer in a verified abuse ring.
2. The refund occurs during an active attack campaign.
3. The event satisfies the coordinated refund exploitation criteria.

Refund requests by legitimate customers (including high returners, hostels, and shared households) are strictly assigned `0`.

---

## 5. Feature Definitions (Phase 2.5)

### Behavioral Features (18)
- `customer_order_count`, `customer_refund_count`, `customer_refund_rate`
- `customer_total_order_value`, `customer_total_refund_value`
- `customer_mean_order_value`, `customer_mean_refund_value`
- `customer_account_age_days` — **Shared generation:** account age at refund time computed as `(t_refund - account_created_at) / 86400`. Both legitimate and abuse accounts draw `account_created_at` from the same uniform distribution over [-365, +144] days relative to simulation start. Abuse `attack_start_day` is sampled *after* account creation, ensuring comparable age marginals at refund time.
- `customer_orders_last_24h`, `customer_refunds_last_24h`, `customer_refunds_last_7d`
- `customer_unique_devices`, `customer_unique_addresses`, `customer_unique_payments`
- `order_amount`, `refund_delay_hours` — **Shared generation:** see Refund Delay Generation above.
- `amount_ratio_vs_customer_mean`, `category_baseline_refund_rate`

### Graph Features (13)

#### Existing Graph Features (6)
- `graph_shared_device_customers` — Number of other customers sharing at least one device
- `graph_shared_address_customers` — Number of other customers sharing at least one address
- `graph_shared_payment_customers` — Number of other customers sharing at least one payment token
- `graph_component_size` — Size of connected component in customer-entity bipartite graph
- `graph_neighbor_mean_refund_rate` — Mean refund rate of 1-hop connected customers
- `graph_neighbor_high_refund_count` — Count of 1-hop neighbors with refund rate ≥ 0.35 and ≥ 1 refund

#### Core Graph Features — Phase 3 (7)

**Entity Rarity (3)** — Measures how selectively an entity is shared. Low-degree sharing (few customers) is more suspicious than high-degree sharing (hostels, offices). For each entity type E ∈ {device, address, payment}:
```
rarity(E) = max_{e ∈ shared_entities(E)} 1 / log(1 + degree(e))
```
where `degree(e)` = number of distinct customers who have ever shared entity `e` strictly before `t_refund`.

- `graph_shared_device_rarity` — Maximum rarity across shared devices
- `graph_shared_address_rarity` — Maximum rarity across shared addresses
- `graph_shared_payment_rarity` — Maximum rarity across shared payment tokens

*Expected behavior:* Hostel address (degree 50) → rarity ≈ 0.18; Family device (degree 3) → rarity ≈ 0.63; Abuse ring device (degree 2–8) → rarity ≈ 0.3–0.9.

**Risk Concentration (2)** — Captures concentrated risk in the neighborhood that mean refund rate dilutes.

- `graph_neighbor_max_refund_rate` — Maximum refund rate among 1-hop connected customers (strictly before `t_refund`)
- `graph_neighbor_risk_mass` — Sum of top-3 neighbor refund rates among 1-hop connected customers

*Expected behavior:* Isolated heavy returner → 0.0; Legitimate hostel → low; Abuse ring → high; Type F relay chain → high risk mass.

**Temporal Graph Recency (2)** — Hours since the customer last shared each entity type with any other customer.

- `graph_shared_device_recency_h` — Minimum hours since last shared device interaction (strictly before `t_refund`)
- `graph_shared_address_recency_h` — Minimum hours since last shared address interaction (strictly before `t_refund`)

*Expected behavior:* Active family sharing → hours; Hostel → hours; Coordinated abuse burst → minutes-hours; Stale office sharing → days-weeks.

#### Phase 4 Growth Features (2) — Structural Dynamics

**Component Activity Growth (1)** — Measures recent activity in the customer's PIT connected component relative to the preceding 24-hour window.

```
graph_component_event_growth_24h = events(component, [t-24h, t)) / max(1, events(component, [t-48h, t-24h)))
```

where `component` = connected component of the customer in the PIT bipartite graph at `t_ref`. Events are all order and refund events from component members with timestamps in the respective windows. PIT-safe: only events with `event_time < t_ref` are counted. The component is evaluated at `t_ref`; historical events are naturally attributed to their component at the time they occurred.

*Expected behavior:* Abuse rings (especially Type F relay chains) show rapid component growth during attack; legitimate shared infrastructure (hostels, offices) shows stable activity.

**Component New Neighbors (1)** — Measures customers newly appearing in the component during the recent 24-hour window compared with the preceding 24-hour window.

```
graph_component_new_neighbors_24h = |neighbors(component, [t-24h, t)) \ neighbors(component, [t-48h, t-24h))|
```

where `neighbors(component, window)` = set of distinct customers in the component who had at least one event in the window. PIT-safe: only events with `event_time < t_ref` are considered. The component is evaluated at `t_ref`; historical neighborhood membership is naturally captured by the timestamps in `comp_events`.

*Expected behavior:* Type F relay chains show sequential neighbor acquisition; legitimate shared infrastructure (hostels, offices) has stable neighborhood.

*Removed in Phase 2.5 (redundant/collinear):* `graph_total_connected_customers` (union of three shared-entity counts), `graph_two_hop_customer_count` (highly collinear with component size).

#### Phase 5 Interaction Features (1) — Graph-Temporal Fusion

**Graph-Neighborhood Synchronization (1)** — Measures the fraction of 1-hop neighbor events that are refunds in the preceding 1-hour window.

```
graph_neighbor_synchronized_refund_ratio_1h = neighbor_refunds_1h / max(1, neighbor_events_1h)
```

where:
- `neighbor_events_1h` = count of all order and refund events from 1-hop connected customers in `[t-1h, t_ref)`
- `neighbor_refunds_1h` = count of refund events from 1-hop connected customers in `[t-1h, t_ref)`

PIT-safe: only events with `event_time < t_ref` are counted. The 1-hop neighborhood is defined by the PIT graph at `t_ref` (customers sharing at least one device, address, or payment token). The target customer's own events are excluded.

*Expected behavior:* Coordinated abuse rings show high synchronization (many neighbors refunding simultaneously); legitimate shared infrastructure shows low synchronization (refunds are independent).

### Temporal Features (6)
- `temporal_cluster_events_last_15m`, `temporal_cluster_events_last_1h`, `temporal_cluster_events_last_24h`
- `temporal_synchronized_refund_ratio_1h`
- `temporal_account_creation_burst_24h` — Count of cluster members with account creation within 24h of this customer
- `temporal_min_inter_event_delay_min`

**Total Features: 40 (18 behavioral + 16 graph + 6 temporal)**
