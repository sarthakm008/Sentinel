"""Legitimate population generator for Sentinel."""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import numpy as np

from ml.data_generation.entities import Address, Customer, Device, Merchant, PaymentToken


class LegitimateGenerator:
    """Generates realistic legitimate customer populations and shared entity bindings."""

    def __init__(self, rng: np.random.Generator, start_time: datetime, simulation_days: int):
        self.rng = rng
        self.start_time = start_time
        self.simulation_days = simulation_days
        
        self.device_types = ["mobile", "desktop", "tablet"]
        self.device_probs = [0.70, 0.22, 0.08]
        self.payment_types = ["upi", "credit_card", "debit_card", "netbanking"]
        self.payment_probs = [0.55, 0.25, 0.15, 0.05]
        self.regions = ["North", "South", "East", "West", "Central"]
        self.segments = ["standard", "premium", "budget", "frequent_buyer"]
        self.segment_probs = [0.55, 0.15, 0.20, 0.10]

    def _random_creation_time(self) -> datetime:
        offset_days = self.rng.uniform(-365, self.simulation_days * 0.8)
        return self.start_time + timedelta(days=offset_days, seconds=int(self.rng.integers(0, 86400)))

    def generate_independent(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        for _ in range(count):
            id_state["cust"] += 1
            id_state["dev"] += 1
            id_state["addr"] += 1
            id_state["pm"] += 1

            cid = f"CUS_{id_state['cust']:06d}"
            did = f"DEV_{id_state['dev']:06d}"
            aid = f"ADDR_{id_state['addr']:06d}"
            pid = f"PM_{id_state['pm']:06d}"

            m = self.rng.choice(merchants)
            c = Customer(
                customer_id=cid,
                account_created_at=self._random_creation_time(),
                merchant_id=m.merchant_id,
                segment=self.rng.choice(self.segments, p=self.segment_probs),
                archetype="independent",
                is_abuse=False
            )
            customers.append(c)

            devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
            payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

            cust_bindings[cid] = {
                "devices": [did],
                "addresses": [aid],
                "payments": [pid],
                "refund_propensity": self.rng.uniform(0.05, 0.12),
                "order_rate": self.rng.uniform(0.015, 0.035),
            }

        return customers, devices, addresses, payments, cust_bindings

    def generate_families(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        generated = 0
        while generated < count:
            fam_size = int(self.rng.integers(2, 6))
            if generated + fam_size > count:
                fam_size = count - generated

            id_state["addr"] += 1
            aid = f"ADDR_{id_state['addr']:06d}"
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="household"))

            n_devs = int(self.rng.integers(1, 3))
            fam_devs = []
            for _ in range(n_devs):
                id_state["dev"] += 1
                did = f"DEV_{id_state['dev']:06d}"
                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                fam_devs.append(did)

            n_pms = int(self.rng.integers(1, 3))
            fam_pms = []
            for _ in range(n_pms):
                id_state["pm"] += 1
                pid = f"PM_{id_state['pm']:06d}"
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))
                fam_pms.append(pid)

            m = self.rng.choice(merchants)
            for _ in range(fam_size):
                id_state["cust"] += 1
                cid = f"CUS_{id_state['cust']:06d}"
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._random_creation_time(),
                    merchant_id=m.merchant_id,
                    segment=self.rng.choice(self.segments, p=self.segment_probs),
                    archetype="family",
                    is_abuse=False
                )
                customers.append(c)

                cust_bindings[cid] = {
                    "devices": fam_devs,
                    "addresses": [aid],
                    "payments": fam_pms,
                    "refund_propensity": self.rng.uniform(0.06, 0.14),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                }

            generated += fam_size

        return customers, devices, addresses, payments, cust_bindings

    def generate_hostels(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        generated = 0
        while generated < count:
            hostel_size = int(self.rng.integers(15, 45))
            if generated + hostel_size > count:
                hostel_size = count - generated

            id_state["addr"] += 1
            aid = f"ADDR_{id_state['addr']:06d}"
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="hostel"))

            for _ in range(hostel_size):
                id_state["cust"] += 1
                id_state["dev"] += 1
                id_state["pm"] += 1

                cid = f"CUS_{id_state['cust']:06d}"
                did = f"DEV_{id_state['dev']:06d}"
                pid = f"PM_{id_state['pm']:06d}"

                m = self.rng.choice(merchants)
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._random_creation_time(),
                    merchant_id=m.merchant_id,
                    segment=self.rng.choice(self.segments, p=self.segment_probs),
                    archetype="hostel",
                    is_abuse=False
                )
                customers.append(c)

                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

                cust_bindings[cid] = {
                    "devices": [did],
                    "addresses": [aid],
                    "payments": [pid],
                    "refund_propensity": self.rng.uniform(0.04, 0.10),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                }

            generated += hostel_size

        return customers, devices, addresses, payments, cust_bindings

    def generate_offices(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        generated = 0
        while generated < count:
            office_size = int(self.rng.integers(25, 75))
            if generated + office_size > count:
                office_size = count - generated

            id_state["addr"] += 1
            aid = f"ADDR_{id_state['addr']:06d}"
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="office"))

            for _ in range(office_size):
                id_state["cust"] += 1
                id_state["dev"] += 1
                id_state["pm"] += 1

                cid = f"CUS_{id_state['cust']:06d}"
                did = f"DEV_{id_state['dev']:06d}"
                pid = f"PM_{id_state['pm']:06d}"

                m = self.rng.choice(merchants)
                c = Customer(
                    customer_id=cid,
                    account_created_at=self._random_creation_time(),
                    merchant_id=m.merchant_id,
                    segment=self.rng.choice(self.segments, p=self.segment_probs),
                    archetype="office",
                    is_abuse=False
                )
                customers.append(c)

                devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
                payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

                cust_bindings[cid] = {
                    "devices": [did],
                    "addresses": [aid],
                    "payments": [pid],
                    "refund_propensity": self.rng.uniform(0.03, 0.08),
                    "order_rate": self.rng.uniform(0.015, 0.035),
                }

            generated += office_size

        return customers, devices, addresses, payments, cust_bindings

    def generate_heavy_returners(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        """Critical hard negative: high individual refund rate (40-60%) but 0 shared graph edges."""
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        apparel_merchants = [m for m in merchants if m.primary_category in ["apparel", "footwear"]]
        target_merchants = apparel_merchants if apparel_merchants else merchants

        for _ in range(count):
            id_state["cust"] += 1
            id_state["dev"] += 1
            id_state["addr"] += 1
            id_state["pm"] += 1

            cid = f"CUS_{id_state['cust']:06d}"
            did = f"DEV_{id_state['dev']:06d}"
            aid = f"ADDR_{id_state['addr']:06d}"
            pid = f"PM_{id_state['pm']:06d}"

            m = self.rng.choice(target_merchants)
            c = Customer(
                customer_id=cid,
                account_created_at=self._random_creation_time(),
                merchant_id=m.merchant_id,
                segment="frequent_buyer",
                archetype="heavy_returner",
                is_abuse=False
            )
            customers.append(c)

            devices.append(Device(device_id=did, device_type="mobile"))
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
            payments.append(PaymentToken(payment_token_id=pid, payment_type="upi"))

            cust_bindings[cid] = {
                "devices": [did],
                "addresses": [aid],
                "payments": [pid],
                "refund_propensity": self.rng.uniform(0.42, 0.65),
                "order_rate": self.rng.uniform(0.025, 0.050),
            }

        return customers, devices, addresses, payments, cust_bindings

    def generate_gift_buyers(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        for _ in range(count):
            id_state["cust"] += 1
            id_state["dev"] += 1
            id_state["pm"] += 1

            cid = f"CUS_{id_state['cust']:06d}"
            did = f"DEV_{id_state['dev']:06d}"
            pid = f"PM_{id_state['pm']:06d}"

            m = self.rng.choice(merchants)
            c = Customer(
                customer_id=cid,
                account_created_at=self._random_creation_time(),
                merchant_id=m.merchant_id,
                segment=self.rng.choice(self.segments, p=self.segment_probs),
                archetype="gift_buyer",
                is_abuse=False
            )
            customers.append(c)

            devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
            payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

            n_addrs = int(self.rng.integers(3, 7))
            user_addrs = []
            for _ in range(n_addrs):
                id_state["addr"] += 1
                aid = f"ADDR_{id_state['addr']:06d}"
                addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
                user_addrs.append(aid)

            cust_bindings[cid] = {
                "devices": [did],
                "addresses": user_addrs,
                "payments": [pid],
                "refund_propensity": self.rng.uniform(0.04, 0.10),
                "order_rate": self.rng.uniform(0.015, 0.035),
            }

        return customers, devices, addresses, payments, cust_bindings

    def generate_sale_buyers(
        self, count: int, merchants: List[Merchant], id_state: Dict[str, int]
    ) -> Tuple[List[Customer], List[Device], List[Address], List[PaymentToken], Dict[str, Dict]]:
        customers, devices, addresses, payments = [], [], [], []
        cust_bindings = {}

        for _ in range(count):
            id_state["cust"] += 1
            id_state["dev"] += 1
            id_state["addr"] += 1
            id_state["pm"] += 1

            cid = f"CUS_{id_state['cust']:06d}"
            did = f"DEV_{id_state['dev']:06d}"
            aid = f"ADDR_{id_state['addr']:06d}"
            pid = f"PM_{id_state['pm']:06d}"

            m = self.rng.choice(merchants)
            c = Customer(
                customer_id=cid,
                account_created_at=self._random_creation_time(),
                merchant_id=m.merchant_id,
                segment="budget",
                archetype="sale_buyer",
                is_abuse=False
            )
            customers.append(c)

            devices.append(Device(device_id=did, device_type=self.rng.choice(self.device_types, p=self.device_probs)))
            addresses.append(Address(address_id=aid, region=self.rng.choice(self.regions), address_type="standard"))
            payments.append(PaymentToken(payment_token_id=pid, payment_type=self.rng.choice(self.payment_types, p=self.payment_probs)))

            cust_bindings[cid] = {
                "devices": [did],
                "addresses": [aid],
                "payments": [pid],
                "refund_propensity": self.rng.uniform(0.06, 0.14),
                "order_rate": self.rng.uniform(0.015, 0.035),
                "is_sale_buyer": True,
            }

        return customers, devices, addresses, payments, cust_bindings
