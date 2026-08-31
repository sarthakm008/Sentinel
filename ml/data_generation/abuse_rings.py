"""Abuse Ring generator for Sentinel (Rings A through F)."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np

from ml.data_generation.entities import Address, Customer, Device, Merchant, PaymentToken


@dataclass
class AbuseRing:
    ring_id: str
    ring_type: str  # type_a_dense, type_b_partial, type_c_sparse, type_d_temporal, type_e_mixed, type_f_structural_shift
    customer_ids: List[str]
    target_merchant_ids: List[str]
    attack_start_day: int
    attack_duration_days: int
    target_category: str
    is_abuse: bool = True
    structure_class: str = "standard"


class AbuseRingGenerator:
    """Generates coordinated refund abuse rings across topologies A-F."""

    def __init__(self, rng: np.random.Generator, start_time: datetime, simulation_days: int):
        self.rng = rng
        self.start_time = start_time
        self.simulation_days = simulation_days
        
        self.device_types = ["mobile", "desktop", "tablet"]
        self.device_probs = [0.70, 0.22, 0.08]
        self.payment_types = ["upi", "credit_card", "debit_card", "netbanking"]
        self.payment_probs = [0.55, 0.25, 0.15, 0.05]
        self.regions = ["North", "South", "East", "West", "Central"]

    def _sample_ring_size(self) -> int:
        """Sample ring size from a common distribution across all types to ensure marginal matching."""
        return int(self.rng.integers(4, 28))

    def _sample_account_creation_time(self, attack_start_day: int) -> datetime:
        """Sample account creation time relative to attack start day."""
        lead_time = self.rng.uniform(2, 90)
        creation_day = max(-180, attack_start_day - lead_time)
        return self.start_time + timedelta(days=creation_day, seconds=int(self.rng.integers(0, 86400)))

    def generate_ring(
        self,
        ring_type: str,
        ring_idx: int,
        merchants: List[Merchant],
        id_state: Dict[str, int]
    ) -> Tuple[AbuseRing, List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        ring_id = f"RING_{ring_idx:04d}"
        size = self._sample_ring_size()
        
        attack_start_day = int(self.rng.integers(15, max(16, self.simulation_days - 20)))
        attack_duration_days = int(self.rng.integers(3, 21))
        
        m = self.rng.choice(merchants)
        target_merchant_ids = [m.merchant_id]
        target_category = m.primary_category

        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        if ring_type == "type_a_dense":
            id_state["addr"] += 1
            aid = f"ADDR_{id_state['addr']:06d}"
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))

            n_devs = int(self.rng.integers(1, 3))
            shared_devs = []
            for _ in range(n_devs):
                id_state["dev"] += 1
                did = f"DEV_{id_state['dev']:06d}"
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                shared_devs.append(did)

            n_pms = int(self.rng.integers(1, 3))
            shared_pms = []
            for _ in range(n_pms):
                id_state["pm"] += 1
                pid = f"PM_{id_state['pm']:06d}"
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                shared_pms.append(pid)

            for _ in range(size):
                id_state["cust"] += 1
                cid = f"CUS_{id_state['cust']:06d}"
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)
                cust_bindings[cid] = {
                    "devices": shared_devs,
                    "addresses": [aid],
                    "payments": shared_pms,
                    "refund_propensity": self.rng.uniform(0.75, 0.92),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": attack_duration_days,
                }

        elif ring_type == "type_b_partial":
            n_devs = max(2, size // 3)
            ring_devs = []
            for _ in range(n_devs):
                id_state["dev"] += 1
                did = f"DEV_{id_state['dev']:06d}"
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                ring_devs.append(did)

            n_addrs = max(2, size // 3)
            ring_addrs = []
            for _ in range(n_addrs):
                id_state["addr"] += 1
                aid = f"ADDR_{id_state['addr']:06d}"
                addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
                ring_addrs.append(aid)

            n_pms = max(2, size // 4)
            ring_pms = []
            for _ in range(n_pms):
                id_state["pm"] += 1
                pid = f"PM_{id_state['pm']:06d}"
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                ring_pms.append(pid)

            for i in range(size):
                id_state["cust"] += 1
                cid = f"CUS_{id_state['cust']:06d}"
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)

                assigned_devs = [ring_devs[i % len(ring_devs)]]
                assigned_addrs = [ring_addrs[(i // 2) % len(ring_addrs)]]
                assigned_pms = [ring_pms[(i // 3) % len(ring_pms)]]

                cust_bindings[cid] = {
                    "devices": assigned_devs,
                    "addresses": assigned_addrs,
                    "payments": assigned_pms,
                    "refund_propensity": self.rng.uniform(0.70, 0.90),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": attack_duration_days,
                }

        elif ring_type == "type_c_sparse":
            for _ in range(size):
                id_state["cust"] += 1
                id_state["dev"] += 1
                id_state["addr"] += 1
                id_state["pm"] += 1

                cid = f"CUS_{id_state['cust']:06d}"
                did = f"DEV_{id_state['dev']:06d}"
                aid = f"ADDR_{id_state['addr']:06d}"
                pid = f"PM_{id_state['pm']:06d}"

                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

                cust_bindings[cid] = {
                    "devices": [did],
                    "addresses": [aid],
                    "payments": [pid],
                    "refund_propensity": self.rng.uniform(0.75, 0.92),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": attack_duration_days,
                    "tight_reason": "defective_item",
                }

        elif ring_type == "type_d_temporal":
            for _ in range(size):
                id_state["cust"] += 1
                id_state["dev"] += 1
                id_state["addr"] += 1
                id_state["pm"] += 1

                cid = f"CUS_{id_state['cust']:06d}"
                did = f"DEV_{id_state['dev']:06d}"
                aid = f"ADDR_{id_state['addr']:06d}"
                pid = f"PM_{id_state['pm']:06d}"

                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

                cust_bindings[cid] = {
                    "devices": [did],
                    "addresses": [aid],
                    "payments": [pid],
                    "refund_propensity": self.rng.uniform(0.70, 0.90),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": min(attack_duration_days, 5),
                    "burst_mode": True,
                }

        elif ring_type == "type_e_mixed":
            id_state["pm"] += 1
            central_pm = f"PM_{id_state['pm']:06d}"
            payments.append(PaymentToken(payment_token_id=central_pm, payment_type="credit_card"))

            for _ in range(size):
                id_state["cust"] += 1
                id_state["dev"] += 1
                id_state["addr"] += 1

                cid = f"CUS_{id_state['cust']:06d}"
                did = f"DEV_{id_state['dev']:06d}"
                aid = f"ADDR_{id_state['addr']:06d}"

                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))

                cust_bindings[cid] = {
                    "devices": [did],
                    "addresses": [aid],
                    "payments": [central_pm],
                    "refund_propensity": self.rng.uniform(0.70, 0.90),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": attack_duration_days,
                }

        elif ring_type == "type_f_structural_shift":
            chain_devs, chain_addrs, chain_pms = [], [], []

            for i in range(size):
                id_state["cust"] += 1
                cid = f"CUS_{id_state['cust']:06d}"
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._sample_account_creation_time(attack_start_day),
                    merchant_id=m.merchant_id,
                    segment="standard",
                    archetype=ring_type,
                    ring_id=ring_id,
                    is_abuse=True
                )
                customers.append(c)

                if i == 0:
                    id_state["dev"] += 1
                    id_state["addr"] += 1
                    id_state["pm"] += 1
                    did = f"DEV_{id_state['dev']:06d}"
                    aid = f"ADDR_{id_state['addr']:06d}"
                    pid = f"PM_{id_state['pm']:06d}"
                    devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                    addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
                    payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                    chain_devs.append(did)
                    chain_addrs.append(aid)
                    chain_pms.append(pid)
                    assigned_dev = did
                    assigned_addr = aid
                    assigned_pm = pid
                else:
                    link_type = i % 3
                    if link_type == 0:
                        assigned_dev = chain_devs[-1]
                        id_state["addr"] += 1
                        id_state["pm"] += 1
                        assigned_addr = f"ADDR_{id_state['addr']:06d}"
                        assigned_pm = f"PM_{id_state['pm']:06d}"
                        addresses.append(Address(address_id=assigned_addr, region=self.rng.choice(self.regions), address_type="standard"))
                        payments.append(PaymentToken(payment_token_id=assigned_pm, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                        chain_addrs.append(assigned_addr)
                        chain_pms.append(assigned_pm)
                    elif link_type == 1:
                        assigned_addr = chain_addrs[-1]
                        id_state["dev"] += 1
                        id_state["pm"] += 1
                        assigned_dev = f"DEV_{id_state['dev']:06d}"
                        assigned_pm = f"PM_{id_state['pm']:06d}"
                        devices.append(Device(device_id=assigned_dev, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                        payments.append(PaymentToken(payment_token_id=assigned_pm, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                        chain_devs.append(assigned_dev)
                        chain_pms.append(assigned_pm)
                    else:
                        assigned_pm = chain_pms[-1]
                        id_state["dev"] += 1
                        id_state["addr"] += 1
                        assigned_dev = f"DEV_{id_state['dev']:06d}"
                        assigned_addr = f"ADDR_{id_state['addr']:06d}"
                        devices.append(Device(device_id=assigned_dev, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                        addresses.append(Address(address_id=assigned_addr, region=self.rng.choice(self.regions), address_type="standard"))
                        chain_devs.append(assigned_dev)
                        chain_addrs.append(assigned_addr)

                cust_bindings[cid] = {
                    "devices": [assigned_dev],
                    "addresses": [assigned_addr],
                    "payments": [assigned_pm],
                    "refund_propensity": self.rng.uniform(0.70, 0.90),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                    "ring_id": ring_id,
                    "is_abuse": True,
                    "attack_start_day": attack_start_day,
                    "attack_duration_days": attack_duration_days,
                }

        ring = AbuseRing(
            ring_id=ring_id,
            ring_type=ring_type,
            customer_ids=[c.customer_id for c in customers],
            target_merchant_ids=target_merchant_ids,
            attack_start_day=attack_start_day,
            attack_duration_days=attack_duration_days,
            target_category=target_category,
            is_abuse=True,
            structure_class="relay_chain" if ring_type == "type_f_structural_shift" else "standard"
        )

        return ring, customers, devices, addresses, payments, cust_bindings
