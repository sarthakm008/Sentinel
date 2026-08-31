"""CLI script to generate synthetic e-commerce dataset for Sentinel."""

import argparse
from datetime import datetime
import json
import os
import time
import numpy as np
import pandas as pd

from ml.config.data_config import DataConfig
from ml.data_generation.abuse_rings import AbuseRingGenerator
from ml.data_generation.entities import Merchant
from ml.data_generation.legitimate import LegitimateGenerator
from ml.data_generation.splitter import GroupAwareSplitter
from ml.data_generation.transactions import TransactionEngine


def generate_dataset(config: DataConfig, output_dir: str = "data"):
    start_wall = time.time()
    print(f"=== Generating Sentinel Synthetic World (Seed: {config.seed}) ===")
    
    rng = np.random.default_rng(config.seed)
    start_time = datetime(2026, 1, 1, 0, 0, 0)
    
    raw_dir = os.path.join(output_dir, "raw")
    splits_dir = os.path.join(output_dir, "splits")
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(splits_dir, exist_ok=True)

    # 1. Initialize Merchants
    merchants = []
    for i in range(1, config.n_merchants + 1):
        cat = config.categories[(i - 1) % len(config.categories)]
        base_rr = config.category_refund_rates[cat]
        merchants.append(Merchant(
            merchant_id=f"MER_{i:03d}",
            name=f"Merchant_{cat.capitalize()}_{i}",
            primary_category=cat,
            base_refund_rate=base_rr
        ))

    id_state = {"cust": 0, "dev": 0, "addr": 0, "pm": 0}

    # 2. Generate Legitimate Populations
    print("[1/5] Generating Legitimate Populations...")
    legit_gen = LegitimateGenerator(rng, start_time, config.simulation_days)
    
    all_customers = []
    all_devices = []
    all_addresses = []
    all_payments = []
    cust_bindings = {}

    target_legit_customers = int(config.n_customers_target * 0.95)

    # Generate archetypes
    for arch, prop in config.legit_proportions.items():
        count = int(round(target_legit_customers * prop))
        if arch == "independent":
            c, d, a, p, b = legit_gen.generate_independent(count, merchants, id_state)
        elif arch == "family":
            c, d, a, p, b = legit_gen.generate_families(count, merchants, id_state)
        elif arch == "hostel":
            c, d, a, p, b = legit_gen.generate_hostels(count, merchants, id_state)
        elif arch == "office":
            c, d, a, p, b = legit_gen.generate_offices(count, merchants, id_state)
        elif arch == "heavy_returner":
            c, d, a, p, b = legit_gen.generate_heavy_returners(count, merchants, id_state)
        elif arch == "gift_buyer":
            c, d, a, p, b = legit_gen.generate_gift_buyers(count, merchants, id_state)
        elif arch == "sale_buyer":
            c, d, a, p, b = legit_gen.generate_sale_buyers(count, merchants, id_state)
        else:
            continue

        for cid, binding in b.items():
            binding["archetype"] = arch
        all_customers.extend(c)
        all_devices.extend(d)
        all_addresses.extend(a)
        all_payments.extend(p)
        cust_bindings.update(b)

    print(f"  -> Generated {len(all_customers):,} legitimate customers")

    # 3. Generate Abuse Rings (A through F)
    print("[2/5] Generating Abuse Rings (Topologies A-F)...")
    ring_gen = AbuseRingGenerator(rng, start_time, config.simulation_days)
    rings = []

    ring_idx = 0
    for ring_type, prop in config.abuse_type_proportions.items():
        n_type_rings = int(round(config.n_abuse_rings * prop))
        for _ in range(n_type_rings):
            ring_idx += 1
            ring, c, d, a, p, b = ring_gen.generate_ring(ring_type, ring_idx, merchants, id_state)
            for cid, binding in b.items():
                binding["archetype"] = ring_type
            rings.append(ring)
            all_customers.extend(c)
            all_devices.extend(d)
            all_addresses.extend(a)
            all_payments.extend(p)
            cust_bindings.update(b)

    print(f"  -> Generated {len(rings):,} abuse rings ({len(all_customers) - target_legit_customers:,} abuse accounts)")
    print(f"  -> Total entities: {len(all_customers):,} customers, {len(all_devices):,} devices, {len(all_addresses):,} addresses, {len(all_payments):,} payments")

    # 4. Simulate Transactions & Refunds
    print("[3/5] Simulating Orders and Refunds across 180 days...")
    tx_engine = TransactionEngine(config, rng, start_time)
    orders, refunds = tx_engine.simulate(all_customers, cust_bindings, merchants)

    df_orders = pd.DataFrame(orders)
    df_refunds = pd.DataFrame(refunds)

    abuse_refunds = df_refunds[df_refunds["coordinated_refund_abuse"] == 1]
    abuse_refund_pct = len(abuse_refunds) / len(df_refunds) * 100

    print(f"  -> Simulated {len(df_orders):,} orders")
    print(f"  -> Simulated {len(df_refunds):,} refunds ({len(abuse_refunds):,} coordinated abuse, {abuse_refund_pct:.2f}%)")

    # 5. Group-Aware Graph Partitioning
    print("[4/5] Computing Group-Aware Graph Partitioning (Train / Val / Test)...")
    splitter = GroupAwareSplitter(rng, config.train_ratio, config.val_ratio, config.test_ratio)
    rings_dict = [{"ring_id": r.ring_id, "ring_type": r.ring_type, "customers": r.customer_ids} for r in rings]
    splits = splitter.partition(all_customers, cust_bindings, rings_dict)

    # 6. Marginal Distribution Validation: Type F vs Types A-E
    print("[5/5] Auditing Marginal Matching (Ring Type F vs Rings A-E)...")
    type_f_rings = [r for r in rings if r.ring_type == "type_f_structural_shift"]
    other_rings = [r for r in rings if r.ring_type != "type_f_structural_shift"]

    f_cust_ids = {cid for r in type_f_rings for cid in r.customer_ids}
    other_cust_ids = {cid for r in other_rings for cid in r.customer_ids}

    f_sizes = [len(r.customer_ids) for r in type_f_rings]
    other_sizes = [len(r.customer_ids) for r in other_rings]

    f_orders = df_orders[df_orders["customer_id"].isin(f_cust_ids)]
    other_orders = df_orders[df_orders["customer_id"].isin(other_cust_ids)]

    f_refunds = df_refunds[df_refunds["customer_id"].isin(f_cust_ids)]
    other_refunds = df_refunds[df_refunds["customer_id"].isin(other_cust_ids)]

    f_mean_size = float(np.mean(f_sizes))
    other_mean_size = float(np.mean(other_sizes))
    f_mean_amount = float(f_orders["amount"].mean())
    other_mean_amount = float(other_orders["amount"].mean())
    f_refund_rate = float(len(f_refunds) / max(1, len(f_orders)))
    other_refund_rate = float(len(other_refunds) / max(1, len(other_orders)))

    marginal_stats = {
        "type_f_ring_count": len(type_f_rings),
        "type_f_customer_count": len(f_cust_ids),
        "type_f_mean_ring_size": round(f_mean_size, 2),
        "other_mean_ring_size": round(other_mean_size, 2),
        "type_f_mean_order_amount": round(f_mean_amount, 2),
        "other_mean_order_amount": round(other_mean_amount, 2),
        "type_f_refund_rate": round(f_refund_rate, 4),
        "other_refund_rate": round(other_refund_rate, 4),
    }

    print(f"  Marginal Matching Results:")
    print(f"    Mean Ring Size:      Type F = {f_mean_size:.1f} vs Types A-E = {other_mean_size:.1f}")
    print(f"    Mean Order Amount:   Type F = INR {f_mean_amount:.2f} vs Types A-E = INR {other_mean_amount:.2f}")
    print(f"    Refund Rate:         Type F = {f_refund_rate:.3f} vs Types A-E = {other_refund_rate:.3f}")

    # 7. Write Data Tables to Parquet
    df_customers = pd.DataFrame([{
        "customer_id": c.customer_id,
        "account_created_at": c.account_created_at.isoformat(),
        "merchant_id": c.merchant_id,
        "segment": c.segment,
    } for c in all_customers])

    df_devices = pd.DataFrame([{
        "device_id": d.device_id,
        "device_type": d.device_type,
    } for d in all_devices])

    df_addresses = pd.DataFrame([{
        "address_id": a.address_id,
        "region": a.region,
        "address_type": a.address_type,
    } for a in all_addresses])

    df_payments = pd.DataFrame([{
        "payment_token_id": p.payment_token_id,
        "payment_type": p.payment_type,
    } for p in all_payments])

    # Isolated ground truth table (strictly never used by feature extraction)
    df_ground_truth_rings = pd.DataFrame([{
        "ring_id": r.ring_id,
        "ring_type": r.ring_type,
        "customer_ids": json.dumps(r.customer_ids),
        "target_merchant_ids": json.dumps(r.target_merchant_ids),
        "attack_start_day": r.attack_start_day,
        "attack_duration_days": r.attack_duration_days,
        "structure_class": r.structure_class,
        "is_abuse": r.is_abuse,
    } for r in rings])

    df_customers.to_parquet(os.path.join(raw_dir, "customers.parquet"), index=False)
    df_devices.to_parquet(os.path.join(raw_dir, "devices.parquet"), index=False)
    df_addresses.to_parquet(os.path.join(raw_dir, "addresses.parquet"), index=False)
    df_payments.to_parquet(os.path.join(raw_dir, "payment_tokens.parquet"), index=False)
    df_orders.to_parquet(os.path.join(raw_dir, "orders.parquet"), index=False)
    df_refunds.to_parquet(os.path.join(raw_dir, "refunds.parquet"), index=False)
    df_ground_truth_rings.to_parquet(os.path.join(raw_dir, "ground_truth_rings.parquet"), index=False)

    # 8. Write Splits Manifests
    with open(os.path.join(splits_dir, "train_groups.json"), "w") as f:
        json.dump(splits["train"], f, indent=2)
    with open(os.path.join(splits_dir, "validation_groups.json"), "w") as f:
        json.dump(splits["validation"], f, indent=2)
    with open(os.path.join(splits_dir, "test_groups.json"), "w") as f:
        json.dump(splits["test"], f, indent=2)

    split_manifest = {
        "generated_at": datetime.utcnow().isoformat(),
        "seed": config.seed,
        "simulation_days": config.simulation_days,
        "splits_summary": {
            k: {
                "customers": len(v["customers"]),
                "devices": len(v["devices"]),
                "addresses": len(v["addresses"]),
                "payment_tokens": len(v["payment_tokens"]),
                "components": v["component_count"],
            } for k, v in splits.items()
        },
        "marginal_stats": marginal_stats,
    }
    with open(os.path.join(splits_dir, "split_manifest.json"), "w") as f:
        json.dump(split_manifest, f, indent=2)

    # 9. Write Generation Metadata
    metadata = {
        "dataset_version": "1.0.0",
        "generated_at": datetime.utcnow().isoformat(),
        "seed": config.seed,
        "scale": {
            "customers": len(df_customers),
            "devices": len(df_devices),
            "addresses": len(df_addresses),
            "payment_tokens": len(df_payments),
            "orders": len(df_orders),
            "refunds": len(df_refunds),
            "coordinated_abuse_refunds": int(df_refunds["coordinated_refund_abuse"].sum()),
            "abuse_rings": len(rings),
        },
        "marginal_matching": marginal_stats,
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    duration = time.time() - start_wall
    print(f"=== Synthetic World Generated Successfully in {duration:.2f}s ===")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Sentinel Synthetic Dataset")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory")
    args = parser.parse_args()

    cfg = DataConfig(seed=args.seed)
    generate_dataset(cfg, output_dir=args.output_dir)
