"""Order and refund transaction simulation engine across the 180-day timeline."""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

from ml.config.data_config import DataConfig
from ml.data_generation.entities import Customer, Merchant


class TransactionEngine:
    """Generates continuous 180-day order and refund transactions with realistic temporal dynamics."""

    def __init__(self, config: DataConfig, rng: np.random.Generator, start_time: datetime):
        self.config = config
        self.rng = rng
        self.start_time = start_time
        self.simulation_days = config.simulation_days
        
        # Category price parameters (mu, sigma for lognormal)
        self.category_pricing = {
            "electronics": (8.2, 0.7),     # ~3,600 INR median
            "apparel": (7.4, 0.6),         # ~1,600 INR median
            "footwear": (7.8, 0.5),        # ~2,400 INR median
            "home_kitchen": (7.6, 0.6),    # ~2,000 INR median
            "beauty": (6.9, 0.5),          # ~1,000 INR median
            "books": (6.2, 0.4),           # ~500 INR median
        }

    def simulate(
        self,
        customers: List[Customer],
        cust_bindings: Dict[str, Dict],
        merchants: List[Merchant]
    ) -> Tuple[List[Dict], List[Dict]]:
        merchant_map = {m.merchant_id: m for m in merchants}
        merchant_ids = list(merchant_map.keys())

        orders = []
        refunds = []

        order_counter = 0
        refund_counter = 0

        # Merchant flash sale event days
        sale_event_days = [25, 60, 110, 150]

        for cust in customers:
            cid = cust.customer_id
            bindings = cust_bindings[cid]
            creation_time = cust.account_created_at

            sim_start_offset = max(0.0, (creation_time - self.start_time).total_seconds() / 86400.0)
            active_days = max(1.0, self.simulation_days - sim_start_offset)
            
            is_abuse = bindings.get("is_abuse", False)
            is_sale_buyer = bindings.get("is_sale_buyer", False)
            attack_start = bindings.get("attack_start_day", 0)
            attack_dur = bindings.get("attack_duration_days", 0)
            attack_end = attack_start + attack_dur

            # Baseline order count from Poisson distribution (~2-5 orders per account)
            base_order_rate = bindings.get("order_rate", 0.025)
            n_baseline_orders = int(self.rng.poisson(base_order_rate * active_days))
            n_baseline_orders = max(1, min(n_baseline_orders, 12))

            order_times = []
            for _ in range(n_baseline_orders):
                day = self.rng.uniform(sim_start_offset, self.simulation_days)
                order_times.append((day, False))

            # Flash sale buyer extra orders
            if is_sale_buyer:
                for sale_day in sale_event_days:
                    if sale_day >= sim_start_offset and self.rng.random() < 0.70:
                        minute_offset = self.rng.uniform(0, 90) / 1440.0
                        order_times.append((sale_day + minute_offset, False))

            # Abuse ring attack orders
            if is_abuse and attack_start >= sim_start_offset:
                n_attack_orders = int(self.rng.integers(1, 3))
                for _ in range(n_attack_orders):
                    attack_day = self.rng.uniform(attack_start, min(attack_end, self.simulation_days - 1))
                    order_times.append((attack_day, True))

            order_times.sort(key=lambda x: x[0])

            # Generate individual order & refund records
            for day_offset, in_attack in order_times:
                order_counter += 1
                oid = f"ORD_{order_counter:08d}"
                order_dt = self.start_time + timedelta(days=day_offset)

                m_id = cust.merchant_id if (self.rng.random() < 0.85) else self.rng.choice(merchant_ids)
                merchant = merchant_map[m_id]
                category = merchant.primary_category

                mu, sigma = self.category_pricing.get(category, (7.5, 0.6))
                amount = float(np.round(self.rng.lognormal(mu, sigma), 2))
                amount = max(199.0, min(amount, 45000.0))

                dev_id = self.rng.choice(bindings["devices"])
                addr_id = self.rng.choice(bindings["addresses"])
                pm_id = self.rng.choice(bindings["payments"])

                orders.append({
                    "order_id": oid,
                    "customer_id": cid,
                    "merchant_id": m_id,
                    "timestamp": order_dt.isoformat(),
                    "amount": amount,
                    "product_category": category,
                    "device_id": dev_id,
                    "address_id": addr_id,
                    "payment_token_id": pm_id,
                })

                # Determine if refunded
                refund_propensity = bindings.get("refund_propensity", 0.08)

                if in_attack:
                    should_refund = self.rng.random() < 0.85
                else:
                    should_refund = self.rng.random() < refund_propensity

                if should_refund:
                    refund_counter += 1
                    rid = f"REF_{refund_counter:07d}"

                    # Delay between order and refund (strictly > 0)
                    if in_attack:
                        delay_days = self.rng.uniform(0.75, 4.5)
                    else:
                        delay_days = self.rng.uniform(1.0, 12.0)

                    refund_dt = order_dt + timedelta(days=delay_days)

                    refund_amount = amount if self.rng.random() < 0.92 else float(np.round(amount * self.rng.uniform(0.5, 0.9), 2))

                    if in_attack and bindings.get("tight_reason"):
                        reason = bindings["tight_reason"]
                    else:
                        reason = self.rng.choice(self.config.refund_reasons)

                    is_coordinated_abuse = 1 if in_attack else 0

                    refunds.append({
                        "refund_id": rid,
                        "order_id": oid,
                        "customer_id": cid,
                        "timestamp": refund_dt.isoformat(),
                        "amount": refund_amount,
                        "reason_category": reason,
                        "status": "processed",
                        "coordinated_refund_abuse": is_coordinated_abuse,
                    })

        return orders, refunds
