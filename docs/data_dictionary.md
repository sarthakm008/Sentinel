# Data Dictionary — Sentinel Synthetic World

This document formally specifies the data model, entity attributes, event tables, and label semantics for the Sentinel benchmark.

---

## 1. Relational Entity Tables

### Customers (`data/raw/customers.parquet`)
| Column | Type | Description |
|---|---|---|
| `customer_id` | String (PK) | Unique synthetic customer identifier (`CUS_000001`) |
| `account_created_at` | ISO Timestamp | Synthetic timestamp when account was registered |
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
| `attack_start_day` | Integer | Simulation day when attack begins |
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
